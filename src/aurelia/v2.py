"""Aurelia sintética v2: ajustes separados; v1 se reutiliza sin modificarla."""
import argparse
from collections import Counter, defaultdict
from contextlib import closing
from datetime import datetime, timedelta
import hashlib
import os
from pathlib import Path
import sqlite3
import tempfile

from .contracts import encode, parse_json, safe_destination, sha256
from .generator import generate as generate_v1
from . import warehouse as v1

VERSION = 'aurelia-synthetic-v2'
ENTITIES = ('returns', 'refunds')
FIELDS = {
    'returns': {'return_id','order_id','item_no','quantity','status','requested_at','received_at','currency'},
    'refunds': {'refund_id','order_id','payment_no','return_id','reason','status','requested_at','completed_at','amount_cents','currency'},
}
DDL = [
    "CREATE TABLE adjustment_batch (batch_id TEXT PRIMARY KEY NOT NULL, version TEXT NOT NULL, status TEXT NOT NULL CHECK(status IN ('ACCEPTED','REJECTED')), manifest_json TEXT NOT NULL)",
    'CREATE TABLE adjustment_source (entity TEXT PRIMARY KEY NOT NULL, batch_id TEXT NOT NULL REFERENCES adjustment_batch, sha256 TEXT NOT NULL, records INTEGER NOT NULL)',
    'CREATE TABLE adjustment_staging (technical_id TEXT PRIMARY KEY NOT NULL, entity TEXT NOT NULL REFERENCES adjustment_source, source_line INTEGER NOT NULL, raw_text TEXT NOT NULL, UNIQUE(entity,source_line))',
    'CREATE TABLE adjustment_rejection (technical_id TEXT NOT NULL REFERENCES adjustment_staging, rule TEXT NOT NULL, detail TEXT NOT NULL, PRIMARY KEY(technical_id,rule))',
    '''CREATE TABLE int_return (return_id TEXT PRIMARY KEY NOT NULL, order_id TEXT NOT NULL, item_no INTEGER NOT NULL,
       quantity INTEGER NOT NULL CHECK(quantity>0), status TEXT NOT NULL CHECK(status IN ('REQUESTED','RECEIVED','REJECTED')),
       requested_at TEXT NOT NULL, received_at TEXT, currency TEXT NOT NULL CHECK(currency='USD'),
       technical_id TEXT NOT NULL UNIQUE REFERENCES adjustment_staging, FOREIGN KEY(order_id,item_no) REFERENCES int_item)''',
    '''CREATE TABLE int_refund (refund_id TEXT PRIMARY KEY NOT NULL, order_id TEXT NOT NULL, payment_no INTEGER NOT NULL,
       return_id TEXT REFERENCES int_return, reason TEXT NOT NULL CHECK(reason IN ('RETURN','GOODWILL')),
       status TEXT NOT NULL CHECK(status IN ('REQUESTED','COMPLETED','FAILED')), requested_at TEXT NOT NULL, completed_at TEXT,
       amount_cents INTEGER NOT NULL CHECK(amount_cents>0), currency TEXT NOT NULL CHECK(currency='USD'),
       technical_id TEXT NOT NULL UNIQUE REFERENCES adjustment_staging, FOREIGN KEY(order_id,payment_no) REFERENCES int_payment,
       CHECK((reason='RETURN' AND return_id IS NOT NULL) OR (reason='GOODWILL' AND return_id IS NULL)))''',
    'CREATE TABLE dim_adjustment_date (date_key TEXT PRIMARY KEY NOT NULL)',
    'CREATE TABLE dim_return_status (status_key TEXT PRIMARY KEY NOT NULL)',
    'CREATE TABLE dim_refund_status (status_key TEXT PRIMARY KEY NOT NULL)',
    '''CREATE TABLE fact_return (return_id TEXT PRIMARY KEY NOT NULL REFERENCES int_return,
       order_id TEXT NOT NULL,item_no INTEGER NOT NULL, requested_date TEXT NOT NULL REFERENCES dim_adjustment_date,
       received_date TEXT REFERENCES dim_adjustment_date,status TEXT NOT NULL REFERENCES dim_return_status,
       received_units INTEGER NOT NULL,reserved_units INTEGER NOT NULL,received_value_cents INTEGER NOT NULL,
       FOREIGN KEY(order_id,item_no) REFERENCES int_item)''',
    '''CREATE TABLE fact_refund (refund_id TEXT PRIMARY KEY NOT NULL REFERENCES int_refund,
       order_id TEXT NOT NULL,payment_no INTEGER NOT NULL,requested_date TEXT NOT NULL REFERENCES dim_adjustment_date,
       completed_date TEXT REFERENCES dim_adjustment_date,status TEXT NOT NULL REFERENCES dim_refund_status,
       posted_cents INTEGER NOT NULL,committed_cents INTEGER NOT NULL,
       FOREIGN KEY(order_id,payment_no) REFERENCES int_payment)''',
    '''CREATE VIEW payment_adjustment_reconciliation AS
       WITH r AS (SELECT order_id,payment_no,SUM(posted_cents) posted_cents,SUM(committed_cents) committed_cents
                  FROM fact_refund GROUP BY order_id,payment_no)
       SELECT p.order_id,p.payment_no,p.captured_amount_cents original_captured_cents,
         COALESCE(r.posted_cents,0) posted_refund_cents,COALESCE(r.committed_cents,0) committed_refund_cents,
         p.captured_amount_cents-COALESCE(r.posted_cents,0) net_captured_cents,
         p.captured_amount_cents-COALESCE(r.committed_cents,0) available_refund_cents
       FROM fact_payment p LEFT JOIN r ON r.order_id=p.order_id AND r.payment_no=p.payment_no''',
    '''CREATE VIEW item_return_reconciliation AS
       WITH r AS (SELECT order_id,item_no,SUM(received_units) received_units,SUM(reserved_units) reserved_units FROM fact_return GROUP BY order_id,item_no)
       SELECT i.order_id,i.item_no,i.quantity original_units,COALESCE(r.received_units,0) returned_units,
         COALESCE(r.reserved_units,0) reserved_return_units,i.quantity-COALESCE(r.reserved_units,0) available_return_units
       FROM fact_item i LEFT JOIN r ON r.order_id=i.order_id AND r.item_no=i.item_no''',
    '''CREATE VIEW order_adjustment_reconciliation AS
       WITH p AS (SELECT order_id,SUM(original_captured_cents) original_captured_cents,SUM(posted_refund_cents) posted_refund_cents,
                         SUM(committed_refund_cents) committed_refund_cents,SUM(net_captured_cents) net_captured_cents FROM payment_adjustment_reconciliation GROUP BY order_id),
       r AS (SELECT order_id,SUM(returned_units) returned_units FROM item_return_reconciliation GROUP BY order_id)
       SELECT o.order_id,o.currency,COALESCE(p.original_captured_cents,0) original_captured_cents,
         COALESCE(p.posted_refund_cents,0) posted_refund_cents,COALESCE(p.committed_refund_cents,0) committed_refund_cents,
         COALESCE(p.net_captured_cents,0) net_captured_cents,COALESCE(r.returned_units,0) returned_units
       FROM int_order o LEFT JOIN p ON p.order_id=o.order_id LEFT JOIN r ON r.order_id=o.order_id''',
]
TABLE_ORDER = {'adjustment_batch':'batch_id','adjustment_source':'entity','adjustment_staging':'technical_id',
               'adjustment_rejection':'technical_id,rule','int_return':'return_id','int_refund':'refund_id',
               'dim_adjustment_date':'date_key','dim_return_status':'status_key','dim_refund_status':'status_key',
               'fact_return':'return_id','fact_refund':'refund_id'}


def timestamp(value):
    if type(value) is not str:
        raise ValueError('Timestamp textual requerido.')
    result = datetime.strptime(value, '%Y-%m-%dT%H:%M:%SZ')
    if result.strftime('%Y-%m-%dT%H:%M:%SZ') != value:
        raise ValueError('Timestamp no canónico.')
    return result


def shape_error(entity, row):
    if type(row) is not dict or set(row) != FIELDS[entity]:
        return 'FIELDS'
    key = 'return_id' if entity == 'returns' else 'refund_id'
    prefix = 'SIM-R-' if entity == 'returns' else 'SIM-F-'
    if type(row[key]) is not str or not row[key].startswith(prefix) or not row[key][6:].isdigit():
        return 'EVENT_ID'
    if type(row['order_id']) is not str:
        return 'ORDER_ID'
    if row['currency'] != 'USD':
        return 'CURRENCY'
    for name in (['item_no','quantity'] if entity == 'returns' else ['payment_no','amount_cents']):
        if type(row[name]) is not int or not 1 <= row[name] <= 10**9:
            return 'INTEGER_RANGE'
    states = ('REQUESTED','RECEIVED','REJECTED') if entity == 'returns' else ('REQUESTED','COMPLETED','FAILED')
    if type(row['status']) is not str or row['status'] not in states:
        return 'EVENT_STATUS'
    final_key = 'received_at' if entity == 'returns' else 'completed_at'
    finalized = row['status'] == ('RECEIVED' if entity == 'returns' else 'COMPLETED')
    try:
        requested = timestamp(row['requested_at'])
        if finalized:
            if timestamp(row[final_key]) < requested:
                return 'DATE_ORDER'
        elif row[final_key] is not None:
            return 'FINAL_DATE'
    except ValueError:
        return 'DATE'
    if entity == 'refunds':
        if type(row['reason']) is not str or row['reason'] not in ('RETURN','GOODWILL'):
            return 'REFUND_REASON'
        if row['reason'] == 'GOODWILL' and row['return_id'] is not None:
            return 'RETURN_LINK'
        if row['reason'] == 'RETURN' and (type(row['return_id']) is not str or not row['return_id'].startswith('SIM-R-')):
            return 'RETURN_LINK'
    return None


def generate(directory, seed=42, orders=30, adverse=False):
    directory = safe_destination(directory)
    if directory.exists():
        raise FileExistsError('Generar en un directorio nuevo.')
    directory.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.aurelia-', dir=directory.parent) as temp:
        temp = Path(temp)
        generate_v1(temp/'base',seed,orders)  # Bytes idénticos a v1 con esos parámetros.
        base_rows = {e:[parse_json(t) for t in (temp/'base'/f'{e}.jsonl').read_text(encoding='utf-8').splitlines()]
                     for e in ('orders','items','payments')}
        headers = {r['order_id']:r for r in base_rows['orders']}
        paid = [r for r in base_rows['orders'] if r['status']=='PAID']
        returns, refunds = [], []
        def date(order_id, day):
            return (timestamp(headers[order_id]['ordered_at'])+timedelta(days=day)).strftime('%Y-%m-%dT%H:%M:%SZ')
        def ret(item, qty, state='RECEIVED'):
            rid=f'SIM-R-{len(returns)+1:06d}';oid=item['order_id']
            returns.append(dict(return_id=rid,order_id=oid,item_no=item['item_no'],quantity=qty,status=state,
                                requested_at=date(oid,2),received_at=date(oid,3) if state=='RECEIVED' else None,currency='USD'))
            return rid
        def refund(oid,payment_no,amount,return_id=None,state='COMPLETED'):
            refunds.append(dict(refund_id=f'SIM-F-{len(refunds)+1:06d}',order_id=oid,payment_no=payment_no,
                                return_id=return_id,reason='RETURN' if return_id else 'GOODWILL',status=state,
                                requested_at=date(oid,4),completed_at=date(oid,5) if state=='COMPLETED' else None,
                                amount_cents=amount,currency='USD'))
        # Pedido 1: devolución parcial del pedido; reembolso parcial en varios eventos iguales.
        first=next(i for i in base_rows['items'] if i['order_id']==paid[0]['order_id'])
        rid=ret(first,1)
        refund(first['order_id'],1,400,rid)
        refund(first['order_id'],1,400,rid)
        refund(first['order_id'],1,200,rid,'REQUESTED')
        # Compensación sin devolución física, financiera y explícita, sin imputación a productos.
        refund(first['order_id'],2,100)
        refund(first['order_id'],2,100,None,'FAILED')
        # Pedido 2: devolución física completa del pedido sin reembolso todavía.
        second=[i for i in base_rows['items'] if i['order_id']==paid[1]['order_id']]
        for item in second:
            ret(item,item['quantity'])
        # Pedido 3: solicitud física pendiente + rechazada, no recibida ni reembolsada.
        third=next(i for i in base_rows['items'] if i['order_id']==paid[2]['order_id'])
        ret(third,1,'REQUESTED');ret(third,1,'REJECTED')
        for payment in base_rows['payments']:
            if payment['order_id']==third['order_id'] and payment['status']=='CAPTURED':
                refund(third['order_id'],payment['payment_no'],payment['amount_cents'])
        # Si la base ofrece una línea mult(unidad), cubrir también devolución parcial de esa línea.
        partial=next((i for i in base_rows['items'] if headers[i['order_id']]['status']=='PAID'
                      and i['quantity']>1 and i['order_id'] not in {paid[0]['order_id'],paid[1]['order_id'],paid[2]['order_id']}),None)
        if partial is not None:
            ret(partial,1)
        if adverse:
            returns.append(dict(returns[0],return_id='SIM-R-999998',quantity=first['quantity']+1))
            refunds.append(dict(refunds[0],refund_id='SIM-F-999998',amount_cents=1000000000))
        for entity, rows in [('returns',returns),('refunds',refunds)]:
            (temp/f'{entity}.jsonl').write_text(''.join(encode(r)+'\n' for r in rows),encoding='utf-8',newline='\n')
        manifest={'contract_version':VERSION,'synthetic':True,'creator':'PLATHEL','seed':seed,
                  'scenario':'invalid_fixture' if adverse else 'normal','base_manifest_sha256':sha256(temp/'base/manifest.json'),
                  'files':{e:{'sha256':sha256(temp/f'{e}.jsonl'),'records':len(returns if e=='returns' else refunds)} for e in ENTITIES}}
        (temp/'manifest.json').write_text(encode(manifest)+'\n',encoding='utf-8',newline='\n')
        if directory.exists():
            raise FileExistsError('Destino existente.')
        os.rename(temp,directory)
    return manifest


def inputs(directory):
    directory=Path(directory).resolve()
    manifest=parse_json((directory/'manifest.json').read_text(encoding='utf-8'))
    keys={'contract_version','synthetic','creator','seed','scenario','base_manifest_sha256','files'}
    if type(manifest) is not dict or set(manifest)!=keys or manifest['contract_version']!=VERSION or manifest['synthetic'] is not True or manifest['creator']!='PLATHEL':
        raise ValueError('Manifiesto v2 incompatible.')
    if type(manifest['seed']) is not int or not 0<=manifest['seed']<2**32 or type(manifest['scenario']) is not str or manifest['scenario'] not in ('normal','invalid_fixture'):
        raise ValueError('Parámetros de manifiesto incompatibles.')
    base_manifest,base_hashes,_=v1.inputs(directory/'base')
    if base_hashes['manifest.json']!=manifest['base_manifest_sha256'] or base_manifest['seed']!=manifest['seed']:
        raise ValueError('Snapshot base incompatible.')
    if type(manifest['files']) is not dict or set(manifest['files'])!=set(ENTITIES):
        raise ValueError('Inventario v2 incompatible.')
    hashes={'manifest.json':sha256(directory/'manifest.json'),**{'base/'+k:v for k,v in base_hashes.items()}}
    for entity in ENTITIES:
        spec=manifest['files'][entity]
        if type(spec) is not dict or set(spec)!={'records','sha256'} or type(spec['records']) is not int or spec['records']<0:
            raise ValueError('Metadatos de archivo incompatibles.')
        hashes[entity+'.jsonl']=sha256(directory/(entity+'.jsonl'))
        if hashes[entity+'.jsonl']!=spec['sha256']:
            raise ValueError('Hash de ajustes incompatible.')
    return manifest,hashes,hashlib.sha256(encode(hashes).encode()).hexdigest()


def validate(db,directory,manifest,batch_id):
    rows={e:[] for e in ENTITIES};errors={}
    def reject(tid,rule):errors[(tid,rule)]=(tid,rule,'Incumplimiento del contrato sintético v2.')
    for entity in ENTITIES:
        spec=manifest['files'][entity]
        db.execute('INSERT INTO adjustment_source VALUES (?,?,?,?)',(entity,batch_id,spec['sha256'],spec['records']))
        count=0
        with (directory/(entity+'.jsonl')).open(encoding='utf-8',newline='') as stream:
            for count,text in enumerate(stream,1):
                tid=f'{spec["sha256"]}:{entity}:{count}'
                db.execute('INSERT INTO adjustment_staging VALUES (?,?,?,?)',(tid,entity,count,text))
                try:row=parse_json(text);error=shape_error(entity,row)
                except ValueError:error='JSON'
                if error:reject(tid,error)
                else:rows[entity].append((tid,row))
        if count!=spec['records']:raise ValueError('Conteo de ajustes incompatible.')
        key='return_id' if entity=='returns' else 'refund_id'
        counts=Counter(r[key] for _,r in rows[entity])
        for tid,row in rows[entity]:
            if counts[row[key]]>1:reject(tid,'DUPLICATE_EVENT')
    orders={oid:(status,at,currency) for oid,status,at,currency in db.execute('SELECT order_id,status,ordered_at,currency FROM int_order')}
    items={(oid,no):(qty,price) for oid,no,qty,price in db.execute('SELECT order_id,item_no,quantity,unit_price_cents FROM int_item')}
    payments={(oid,no):(status,amount) for oid,no,status,amount in db.execute('SELECT order_id,payment_no,status,amount_cents FROM int_payment')}
    reserved_units=defaultdict(int);return_tids=defaultdict(list)
    return_map={r['return_id']:(tid,r) for tid,r in rows['returns']}
    for tid,r in rows['returns']:
        key=(r['order_id'],r['item_no'])
        if key not in items or r['order_id'] not in orders:reject(tid,'ORPHAN_ITEM');continue
        order=orders[r['order_id']]
        if order[0]!='PAID':reject(tid,'ORDER_NOT_PAID')
        if r['requested_at']<order[1]:reject(tid,'BEFORE_ORDER')
        if r['quantity']>items[key][0]:reject(tid,'RETURN_LIMIT')
        if r['status'] in ('REQUESTED','RECEIVED'):
            reserved_units[key]+=r['quantity'];return_tids[key].append(tid)
    for key,quantity in reserved_units.items():
        if quantity>items[key][0]:
            for tid in return_tids[key]:reject(tid,'RETURN_LIMIT')
    by_payment=defaultdict(int);by_order=defaultdict(int);by_return=defaultdict(int)
    payment_tids=defaultdict(list);order_tids=defaultdict(list);refund_return_tids=defaultdict(list)
    for tid,r in rows['refunds']:
        key=(r['order_id'],r['payment_no'])
        if key not in payments or r['order_id'] not in orders:reject(tid,'ORPHAN_PAYMENT');continue
        payment=payments[key];order=orders[r['order_id']]
        if payment[0]!='CAPTURED':reject(tid,'PAYMENT_NOT_CAPTURED')
        if order[0]!='PAID':reject(tid,'ORDER_NOT_PAID')
        if r['requested_at']<order[1]:reject(tid,'BEFORE_ORDER')
        if r['amount_cents']>payment[1]:reject(tid,'REFUND_PAYMENT_LIMIT')
        if r['reason']=='RETURN':
            if r['return_id'] not in return_map:reject(tid,'ORPHAN_RETURN')
            else:
                _,physical=return_map[r['return_id']]
                item=items.get((physical['order_id'],physical['item_no']))
                if physical['order_id']!=r['order_id']:reject(tid,'RETURN_ORDER_MISMATCH')
                if physical['status']!='RECEIVED' or physical['received_at'] is None:reject(tid,'RETURN_NOT_RECEIVED')
                elif r['requested_at']<physical['received_at']:reject(tid,'BEFORE_RECEIPT')
                if item and r['amount_cents']>physical['quantity']*item[1]:reject(tid,'REFUND_RETURN_LIMIT')
        if r['status'] in ('REQUESTED','COMPLETED'):
            by_payment[key]+=r['amount_cents'];payment_tids[key].append(tid)
            by_order[r['order_id']]+=r['amount_cents'];order_tids[r['order_id']].append(tid)
            if r['return_id'] is not None:
                by_return[r['return_id']]+=r['amount_cents'];refund_return_tids[r['return_id']].append(tid)
    for key,amount in by_payment.items():
        if amount>payments[key][1] or payments[key][0]!='CAPTURED':
            for tid in payment_tids[key]:reject(tid,'REFUND_PAYMENT_LIMIT')
    for oid,amount in by_order.items():
        original=sum(value for (order_id,_),(state,value) in payments.items() if order_id==oid and state=='CAPTURED')
        if amount>original:
            for tid in order_tids[oid]:reject(tid,'REFUND_ORDER_LIMIT')
    for rid,amount in by_return.items():
        if rid in return_map:
            _,r=return_map[rid];item=items.get((r['order_id'],r['item_no']))
            if item and amount>r['quantity']*item[1]:
                for tid in refund_return_tids[rid]:reject(tid,'REFUND_RETURN_LIMIT')
    db.executemany('INSERT INTO adjustment_rejection VALUES (?,?,?)',errors.values())
    return rows,list(errors.values())


def integrate(db,rows):
    for tid,r in rows['returns']:
        db.execute('INSERT INTO int_return VALUES (?,?,?,?,?,?,?,?,?)',tuple(r[k] for k in ['return_id','order_id','item_no','quantity','status','requested_at','received_at','currency'])+(tid,))
    for tid,r in rows['refunds']:
        db.execute('INSERT INTO int_refund VALUES (?,?,?,?,?,?,?,?,?,?,?)',tuple(r[k] for k in ['refund_id','order_id','payment_no','return_id','reason','status','requested_at','completed_at','amount_cents','currency'])+(tid,))
    dates=sorted({r[k][:10] for entity in ENTITIES for _,r in rows[entity] for k in ('requested_at','received_at' if entity=='returns' else 'completed_at') if r[k] is not None})
    db.executemany('INSERT INTO dim_adjustment_date VALUES (?)',((d,) for d in dates))
    db.execute('INSERT INTO dim_return_status SELECT DISTINCT status FROM int_return')
    db.execute('INSERT INTO dim_refund_status SELECT DISTINCT status FROM int_refund')
    db.execute('''INSERT INTO fact_return SELECT r.return_id,r.order_id,r.item_no,substr(r.requested_at,1,10),substr(r.received_at,1,10),r.status,
                  CASE WHEN r.status='RECEIVED' THEN r.quantity ELSE 0 END,
                  CASE WHEN r.status IN ('REQUESTED','RECEIVED') THEN r.quantity ELSE 0 END,
                  CASE WHEN r.status='RECEIVED' THEN r.quantity*i.unit_price_cents ELSE 0 END
                  FROM int_return r JOIN int_item i ON i.order_id=r.order_id AND i.item_no=r.item_no''')
    db.execute('''INSERT INTO fact_refund SELECT refund_id,order_id,payment_no,substr(requested_at,1,10),substr(completed_at,1,10),status,
                  CASE WHEN status='COMPLETED' THEN amount_cents ELSE 0 END,
                  CASE WHEN status IN ('REQUESTED','COMPLETED') THEN amount_cents ELSE 0 END FROM int_refund''')
    for entity,table in [('returns','fact_return'),('refunds','fact_refund')]:
        if db.execute(f'SELECT COUNT(*) FROM {table}').fetchone()[0]!=len(rows[entity]):raise ValueError('Granularidad de ajustes alterada.')
    if db.execute('SELECT COUNT(*) FROM payment_adjustment_reconciliation WHERE net_captured_cents<0 OR available_refund_cents<0').fetchone()[0]:raise ValueError('Límite monetario dimensional violado.')
    if db.execute('SELECT COUNT(*) FROM item_return_reconciliation WHERE available_return_units<0').fetchone()[0]:raise ValueError('Límite físico dimensional violado.')


def equal_databases(a,b):
    if not v1.equal_databases(a,b):return False
    for table,order in TABLE_ORDER.items():
        left=a.execute(f'SELECT * FROM {table} ORDER BY {order}');right=b.execute(f'SELECT * FROM {table} ORDER BY {order}')
        sentinel=object()
        while True:
            x,y=next(left,sentinel),next(right,sentinel)
            if x is sentinel and y is sentinel:break
            if x!=y:return False
    return True


def build(directory,database):
    directory=Path(directory).resolve();database=safe_destination(database)
    if database.suffix not in ('.sqlite','.sqlite3','.db') or directory==database or directory in database.parents:raise ValueError('Destino separado requerido.')
    manifest,before,batch_id=inputs(directory)
    database.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.aurelia-',dir=database.parent) as temporary:
        pending=Path(temporary)/'v2.sqlite'
        base_result=v1.build(directory/'base',pending)
        if base_result['status']!='ACCEPTED':raise ValueError('Snapshot v1 no aceptado; no se añaden ajustes.')
        with closing(sqlite3.connect(pending)) as db:
            db.execute('PRAGMA foreign_keys=ON');db.execute('BEGIN IMMEDIATE')
            try:
                for ddl in DDL:db.execute(ddl)
                db.execute('PRAGMA user_version=2')
                db.execute('INSERT INTO adjustment_batch VALUES (?,?,?,?)',(batch_id,VERSION,'REJECTED',encode(manifest)))
                rows,rejections=validate(db,directory,manifest,batch_id)
                status='REJECTED' if rejections else 'ACCEPTED'
                if not rejections:integrate(db,rows)
                db.execute('UPDATE adjustment_batch SET status=?',(status,))
                if inputs(directory)[1]!=before:raise ValueError('Entradas cambiaron durante carga.')
                if db.execute('PRAGMA foreign_key_check').fetchall() or db.execute('PRAGMA integrity_check').fetchone()!=('ok',):raise ValueError('Integridad SQLite fallida.')
                db.commit()
            except BaseException:db.rollback();raise
        if database.exists():
            with closing(v1.read_only(pending)) as a,closing(v1.read_only(database)) as b:
                if not equal_databases(a,b):raise ValueError('Destino existente distinto; no se migra ni sobrescribe v1.')
            action='unchanged'
        else:os.link(pending,database);action='created'
    return dict(synthetic=True,version=VERSION,status=status,action=action,rejections=len(rejections),batch_id=batch_id)


def inspect(database,query='summary'):
    with closing(v1.read_only(database)) as db:
        if db.execute('PRAGMA user_version').fetchone()!=(2,):raise ValueError('Consulta v2 exige base v2.')
        if query=='rejections':return dict(synthetic=True,rules=dict(db.execute('SELECT rule,COUNT(*) FROM adjustment_rejection GROUP BY rule')))
        views={'orders':'order_adjustment_reconciliation','items':'item_return_reconciliation','payments':'payment_adjustment_reconciliation'}
        if query in views:
            cursor=db.execute(f'SELECT * FROM {views[query]} ORDER BY 1,2')
            return dict(synthetic=True,rows=[dict(zip([c[0] for c in cursor.description],row)) for row in cursor])
        if query!='summary':raise ValueError('Consulta desconocida.')
        original,posted,committed,net,units=db.execute('SELECT COALESCE(SUM(original_captured_cents),0),COALESCE(SUM(posted_refund_cents),0),COALESCE(SUM(committed_refund_cents),0),COALESCE(SUM(net_captured_cents),0),COALESCE(SUM(returned_units),0) FROM order_adjustment_reconciliation').fetchone()
        return dict(synthetic=True,currency='USD',version=VERSION,status=db.execute('SELECT status FROM adjustment_batch').fetchone()[0],
                    original_captured_cents=original,posted_refund_cents=posted,committed_refund_cents=committed,net_captured_cents=net,returned_units=units,
                    counts={t:db.execute(f'SELECT COUNT(*) FROM {t}').fetchone()[0] for t in ['int_order','fact_item','fact_payment','adjustment_staging','adjustment_rejection','fact_return','fact_refund']})


def main():
    parser=argparse.ArgumentParser(description=__doc__);commands=parser.add_subparsers(dest='command',required=True)
    gen=commands.add_parser('generate');gen.add_argument('--output',type=Path,required=True);gen.add_argument('--seed',type=int,default=42);gen.add_argument('--orders',type=int,default=30);gen.add_argument('--adverse',action='store_true')
    loader=commands.add_parser('build');loader.add_argument('--input',type=Path,required=True);loader.add_argument('--database',type=Path,required=True)
    query=commands.add_parser('query');query.add_argument('--database',type=Path,required=True);query.add_argument('--query',choices=['summary','orders','items','payments','rejections'],default='summary')
    args=parser.parse_args()
    try:
        result=generate(args.output,args.seed,args.orders,args.adverse) if args.command=='generate' else build(args.input,args.database) if args.command=='build' else inspect(args.database,args.query)
        print(encode(result));return 1 if args.command=='build' and result['status']=='REJECTED' else 0
    except (ValueError,OSError,UnicodeError,sqlite3.Error):parser.exit(1,'Error: contrato, integridad, destino o permisos v2 incompatibles.\n')


if __name__=='__main__':raise SystemExit(main())
