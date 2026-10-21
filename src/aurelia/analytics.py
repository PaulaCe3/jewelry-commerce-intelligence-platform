"""Contrato de consumo v1 sobre snapshots sintéticos Aurelia v2."""
from collections import Counter, defaultdict
from contextlib import closing
import csv
from pathlib import Path
import sqlite3

from .contracts import parse_json, sha256
from . import warehouse, v2

VERSION = 'aurelia-consumption-v1'
VIEWS = {
    'analytics_orders': ('order_id', ('synthetic','order_id','order_at_utc','order_date','order_status','currency','expected_item_cents','original_captured_cents','posted_refund_cents','committed_refund_cents','net_captured_cents','returned_units')),
    'analytics_items': ('order_id,item_no', ('synthetic','order_id','item_no','product_code','order_at_utc','order_status','currency','quantity','unit_price_cents','line_amount_cents','returned_units','reserved_return_units')),
    'analytics_products': ('product_code', ('synthetic','product_code','currency','item_records','ordered_units','paid_units','paid_item_cents','returned_units')),
    'analytics_payments': ('order_id,payment_no', ('synthetic','order_id','payment_no','order_at_utc','order_status','payment_status','currency','recorded_amount_cents','original_captured_cents','posted_refund_cents','committed_refund_cents','net_captured_cents','available_refund_cents')),
    'analytics_returns': ('return_id', ('synthetic','return_id','order_id','item_no','requested_at_utc','received_at_utc','return_status','currency','event_quantity','received_units','reserved_units','received_value_cents')),
    'analytics_refunds': ('refund_id', ('synthetic','refund_id','order_id','payment_no','return_id','refund_reason','requested_at_utc','completed_at_utc','refund_status','currency','recorded_amount_cents','posted_refund_cents','committed_refund_cents')),
}
SQL = {
    'analytics_orders': '''SELECT 1 synthetic,o.order_id,o.ordered_at order_at_utc,substr(o.ordered_at,1,10) order_date,
        o.status order_status,o.currency,o.expected_cents expected_item_cents,r.original_captured_cents,
        r.posted_refund_cents,r.committed_refund_cents,r.net_captured_cents,r.returned_units
        FROM int_order o JOIN order_adjustment_reconciliation r ON r.order_id=o.order_id''',
    'analytics_items': '''SELECT 1 synthetic,i.order_id,i.item_no,i.product_code,o.ordered_at order_at_utc,
        o.status order_status,o.currency,i.quantity,i.unit_price_cents,f.line_amount_cents,r.returned_units,r.reserved_return_units
        FROM int_item i JOIN int_order o ON o.order_id=i.order_id
        JOIN fact_item f ON f.order_id=i.order_id AND f.item_no=i.item_no
        JOIN item_return_reconciliation r ON r.order_id=i.order_id AND r.item_no=i.item_no''',
    'analytics_products': '''SELECT 1 synthetic,product_code,'USD' currency,COUNT(*) item_records,SUM(quantity) ordered_units,
        SUM(CASE WHEN order_status='PAID' THEN quantity ELSE 0 END) paid_units,
        SUM(CASE WHEN order_status='PAID' THEN line_amount_cents ELSE 0 END) paid_item_cents,SUM(returned_units) returned_units
        FROM analytics_items GROUP BY product_code''',
    'analytics_payments': '''SELECT 1 synthetic,p.order_id,p.payment_no,o.ordered_at order_at_utc,o.status order_status,
        p.status payment_status,o.currency,p.amount_cents recorded_amount_cents,r.original_captured_cents,
        r.posted_refund_cents,r.committed_refund_cents,r.net_captured_cents,r.available_refund_cents
        FROM int_payment p JOIN int_order o ON o.order_id=p.order_id
        JOIN payment_adjustment_reconciliation r ON r.order_id=p.order_id AND r.payment_no=p.payment_no''',
    'analytics_returns': '''SELECT 1 synthetic,r.return_id,r.order_id,r.item_no,r.requested_at requested_at_utc,
        r.received_at received_at_utc,r.status return_status,r.currency,r.quantity event_quantity,
        f.received_units,f.reserved_units,f.received_value_cents
        FROM int_return r JOIN fact_return f ON f.return_id=r.return_id''',
    'analytics_refunds': '''SELECT 1 synthetic,r.refund_id,r.order_id,r.payment_no,r.return_id,r.reason refund_reason,
        r.requested_at requested_at_utc,r.completed_at completed_at_utc,r.status refund_status,r.currency,
        r.amount_cents recorded_amount_cents,f.posted_cents posted_refund_cents,f.committed_cents committed_refund_cents
        FROM int_refund r JOIN fact_refund f ON f.refund_id=r.refund_id''',
}


def install(database):
    """Solo sobre la base nueva privada del orquestador; no sobre bases publicadas."""
    with closing(sqlite3.connect(database)) as db:
        if db.execute('PRAGMA user_version').fetchone() != (2,):
            raise ValueError('Consumo exige v2.')
        if db.execute('SELECT status FROM adjustment_batch').fetchone() != ('ACCEPTED',):
            raise ValueError('No publicar consumo de ajustes rechazados.')
        with db:
            for name, sql in SQL.items():
                db.execute(f'CREATE VIEW {name} AS {sql}')
            db.execute('CREATE TABLE consumption_contract (version TEXT PRIMARY KEY NOT NULL)')
            db.execute('INSERT INTO consumption_contract VALUES (?)', (VERSION,))


def expected_rows(inputs):
    """Oráculo de aceptación independiente de los SELECT/vistas del Warehouse."""
    inputs = Path(inputs)
    def read(path):
        with path.open(encoding='utf-8') as f:
            return [parse_json(t) for t in f]
    orders=read(inputs/'base/orders.jsonl');items=read(inputs/'base/items.jsonl');payments=read(inputs/'base/payments.jsonl')
    returns=read(inputs/'returns.jsonl');refunds=read(inputs/'refunds.jsonl')
    order_map={o['order_id']:o for o in orders}
    returned=defaultdict(int);reserved=defaultdict(int)
    for r in returns:
        key=(r['order_id'],r['item_no'])
        if r['status']=='RECEIVED':returned[key]+=r['quantity']
        if r['status'] in ('REQUESTED','RECEIVED'):reserved[key]+=r['quantity']
    posted=defaultdict(int);committed=defaultdict(int)
    for r in refunds:
        key=(r['order_id'],r['payment_no'])
        if r['status']=='COMPLETED':posted[key]+=r['amount_cents']
        if r['status'] in ('REQUESTED','COMPLETED'):committed[key]+=r['amount_cents']
    original_order=defaultdict(int);posted_order=defaultdict(int);committed_order=defaultdict(int);returned_order=defaultdict(int)
    result={k:[] for k in VIEWS}
    for p in payments:
        oid=p['order_id'];key=(oid,p['payment_no']);o=order_map[oid]
        original=p['amount_cents'] if p['status']=='CAPTURED' else 0
        original_order[oid]+=original;posted_order[oid]+=posted[key];committed_order[oid]+=committed[key]
        result['analytics_payments'].append((1,oid,p['payment_no'],o['ordered_at'],o['status'],p['status'],o['currency'],p['amount_cents'],original,posted[key],committed[key],original-posted[key],original-committed[key]))
    products={};item_map={}
    for i in items:
        oid=i['order_id'];key=(oid,i['item_no']);o=order_map[oid];amount=i['quantity']*i['unit_price_cents'];item_map[key]=i
        result['analytics_items'].append((1,oid,i['item_no'],i['product_code'],o['ordered_at'],o['status'],o['currency'],i['quantity'],i['unit_price_cents'],amount,returned[key],reserved[key]))
        returned_order[oid]+=returned[key]
        metrics=products.setdefault(i['product_code'],[0,0,0,0,0]);metrics[0]+=1;metrics[1]+=i['quantity'];metrics[4]+=returned[key]
        if o['status']=='PAID':metrics[2]+=i['quantity'];metrics[3]+=amount
    for product,metrics in products.items():result['analytics_products'].append((1,product,'USD',*metrics))
    for o in orders:
        oid=o['order_id']
        result['analytics_orders'].append((1,oid,o['ordered_at'],o['ordered_at'][:10],o['status'],o['currency'],o['expected_cents'],original_order[oid],posted_order[oid],committed_order[oid],original_order[oid]-posted_order[oid],returned_order[oid]))
    for r in returns:
        received=r['quantity'] if r['status']=='RECEIVED' else 0
        reserved_units=r['quantity'] if r['status'] in ('REQUESTED','RECEIVED') else 0
        result['analytics_returns'].append((1,r['return_id'],r['order_id'],r['item_no'],r['requested_at'],r['received_at'],r['status'],r['currency'],r['quantity'],received,reserved_units,received*item_map[(r['order_id'],r['item_no'])]['unit_price_cents']))
    for r in refunds:
        posted_cents=r['amount_cents'] if r['status']=='COMPLETED' else 0
        committed_cents=r['amount_cents'] if r['status'] in ('REQUESTED','COMPLETED') else 0
        result['analytics_refunds'].append((1,r['refund_id'],r['order_id'],r['payment_no'],r['return_id'],r['reason'],r['requested_at'],r['completed_at'],r['status'],r['currency'],r['amount_cents'],posted_cents,committed_cents))
    return result


def validate(database, inputs):
    expected=expected_rows(inputs);counts={}
    with closing(warehouse.read_only(database)) as db:
        if db.execute('PRAGMA integrity_check').fetchone()!=('ok',) or db.execute('PRAGMA foreign_key_check').fetchall():
            raise ValueError('Integridad de consumo inválida.')
        if db.execute('SELECT version FROM consumption_contract').fetchall()!=[(VERSION,)]:
            raise ValueError('Contrato de consumo incompatible.')
        for name,(key,columns) in VIEWS.items():
            cursor=db.execute(f'SELECT * FROM {name} ORDER BY {key}')
            if tuple(c[0] for c in cursor.description)!=columns:
                raise ValueError('Columnas de consumo incompatibles: '+name)
            rows=cursor.fetchall()
            if Counter(rows)!=Counter(expected[name]):
                raise ValueError('Consumo distinto de la evidencia fuente: '+name)
            keys=key.split(',');indexes=[columns.index(k) for k in keys]
            if len({tuple(row[i] for i in indexes) for row in rows})!=len(rows):
                raise ValueError('Granularidad duplicada: '+name)
            counts[name]=len(rows)
    return {'status':'PASSED','synthetic':True,'consumption_version':VERSION,'row_counts':counts,
            'checks':['sqlite_integrity','foreign_keys','column_contracts','unique_grains','all_view_rows_vs_source']}


def export(database, directory):
    directory=Path(directory);directory.mkdir(exist_ok=False)
    result={}
    with closing(warehouse.read_only(database)) as db:
        for name,(key,columns) in VIEWS.items():
            path=directory/(name+'.csv');count=0
            with path.open('x',encoding='utf-8',newline='') as f:
                writer=csv.writer(f,lineterminator='\n');writer.writerow(columns)
                for row in db.execute(f'SELECT * FROM {name} ORDER BY {key}'):
                    writer.writerow(row);count+=1
            result[name]={'file':path.name,'rows':count,'columns':list(columns),'key':key.split(','),'sha256':sha256(path)}
    return result


def validate_exports(database,directory):
    """Comprueba cabecera, orden, valores y nulos del CSV contra las vistas."""
    with closing(warehouse.read_only(database)) as db:
        for name,(key,columns) in VIEWS.items():
            with (Path(directory)/(name+'.csv')).open(encoding='utf-8',newline='') as f:
                reader=csv.reader(f)
                if next(reader,None)!=list(columns):raise ValueError('Cabecera CSV incompatible.')
                sentinel=object()
                rows=iter(db.execute(f'SELECT * FROM {name} ORDER BY {key}'))
                while True:
                    a,b=next(reader,sentinel),next(rows,sentinel)
                    if a is sentinel and b is sentinel:break
                    if a is sentinel or b is sentinel or a!=['' if v is None else str(v) for v in b]:
                        raise ValueError('Contenido CSV incompatible.')
