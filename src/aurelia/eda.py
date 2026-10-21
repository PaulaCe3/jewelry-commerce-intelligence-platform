"""EDA descriptivo exclusivo de las seis exportaciones sintéticas Aurelia."""
import argparse
from collections import Counter
from contextlib import closing
import csv
from datetime import date, timedelta
from decimal import Decimal
import hashlib
from html import escape
import json
from pathlib import Path
import sqlite3
import statistics
import tempfile

from .analytics import VIEWS
from .contracts import ROOT


def digest(path):
    with path.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def read_exports(bundle):
    """Compara cada celda CSV con la vista SQLite read-only antes del análisis."""
    bundle = Path(bundle).resolve()
    result = {}
    with closing(sqlite3.connect((bundle/'warehouse.sqlite').as_uri()+'?mode=ro', uri=True)) as db:
        db.execute('PRAGMA query_only=ON')
        if db.execute('SELECT version FROM consumption_contract').fetchall() != [('aurelia-consumption-v1',)]:
            raise ValueError('Contrato de consumo incompatible')
        for name, (keys, columns) in VIEWS.items():
            with (bundle/'exports'/f'{name}.csv').open(encoding='utf-8', newline='') as f:
                rows = list(csv.reader(f))
            if not rows or rows[0] != list(columns) or any(len(r)!=len(columns) for r in rows[1:]):
                raise ValueError('Columnas incompatibles: '+name)
            expected = [[str(v) if v is not None else '' for v in row]
                        for row in db.execute(f'SELECT * FROM {name} ORDER BY {keys}')]
            if rows[1:] != expected:
                raise ValueError('CSV distinto del Warehouse: '+name)
            records = [dict(zip(columns, r)) for r in rows[1:]]
            if any(r['synthetic']!='1' or r['currency']!='USD' for r in records):
                raise ValueError('Solo simulación USD admitida')
            seen = set()
            for r in records:
                key = tuple(r[k] for k in keys.split(','))
                if key in seen:
                    raise ValueError('Clave duplicada: '+name)
                seen.add(key)
                for col in columns:
                    if col.endswith('_cents') or col in {'quantity','returned_units','reserved_return_units','item_records','ordered_units','paid_units','event_quantity','received_units','reserved_units'}:
                        r[col] = int(r[col])
                        if r[col] < 0:
                            raise ValueError('Medida negativa')
            result[name.removeprefix('analytics_')] = records
    return result


def summarize(tables):
    orders, items, payments, returns, refunds = [tables[k] for k in ('orders','items','payments','returns','refunds')]
    if not orders:
        raise ValueError('No hay pedidos para EDA')
    def total(rows, col): return sum(r[col] for r in rows)
    states = Counter(r['order_status'] for r in orders)
    daily = Counter(r['order_date'] for r in orders)
    start, end = min(daily), max(daily)
    d = date.fromisoformat(start)
    timeline = []
    while d <= date.fromisoformat(end):
        timeline.append({'order_date':d.isoformat(),'orders':daily[d.isoformat()]})
        d += timedelta(days=1)
    products = []
    for code in sorted({r['product_code'] for r in items}):
        rows = [r for r in items if r['product_code']==code]
        paid = [r for r in rows if r['order_status']=='PAID']
        row = {'product_code':code,'ordered_units':total(rows,'quantity'),'paid_units':total(paid,'quantity'),
               'paid_item_cents':total(paid,'line_amount_cents'),'returned_units':total(rows,'returned_units')}
        source = next(r for r in tables['products'] if r['product_code']==code)
        if any(row[k]!=source[k] for k in row if k!='product_code'):
            raise ValueError('Agregado de productos no concilia')
        products.append(row)
    captured = total([r for r in payments if r['payment_status']=='CAPTURED'],'recorded_amount_cents')
    completed = total([r for r in refunds if r['refund_status']=='COMPLETED'],'recorded_amount_cents')
    paid_amount = total([r for r in orders if r['order_status']=='PAID'],'expected_item_cents')
    received = total([r for r in returns if r['return_status']=='RECEIVED'],'event_quantity')
    checks = [captured==total(orders,'original_captured_cents')==total(payments,'original_captured_cents'),
              completed==total(orders,'posted_refund_cents')==total(payments,'posted_refund_cents'),
              captured-completed==total(orders,'net_captured_cents')==total(payments,'net_captured_cents'),
              paid_amount==sum(r['paid_item_cents'] for r in products)==captured,
              received==total(orders,'returned_units')==total(items,'returned_units'),
              sum(r['orders'] for r in timeline)==len(orders)]
    if not all(checks):
        raise ValueError('Conciliación entre granularidades fallida')
    distribution = []
    for label, rows in [('ALL',orders),('PAID',[r for r in orders if r['order_status']=='PAID'])]:
        values = sorted(r['expected_item_cents'] for r in rows)
        distribution.append({'population':label,'orders':len(values),'min_cents':min(values) if values else None,
          'max_cents':max(values) if values else None,'mean_cents':str(Decimal(sum(values))/Decimal(len(values))) if values else None,
          'median_cents':str(statistics.median(values)) if values else None})
    # Intervalos explícitos en centavos: [0,1000), [1000,3000), [3000,5000), [5000,+inf).
    histogram = [{'interval_cents':label,'orders':sum(lo<=r['expected_item_cents'] and (hi is None or r['expected_item_cents']<hi) for r in orders)}
                 for lo,hi,label in [(0,1000,'0–999'),(1000,3000,'1000–2999'),(3000,5000,'3000–4999'),(5000,None,'5000+')]]
    return {'synthetic':True,'currency':'USD','row_counts':{k:len(v) for k,v in tables.items()},
      'date_range':{'first_order_date':start,'last_order_date':end},
      'order_states':[{'order_status':k,'orders':states[k]} for k in ('OPEN','PAID','CANCELLED')],
      'daily_orders':timeline,'products':products,
      'money':{'paid_order_item_cents':paid_amount,'captured_cents':captured,'completed_refund_cents':completed,'net_captured_cents':captured-completed},
      'return_states':[{'return_status':k,'events':sum(r['return_status']==k for r in returns),
                        'event_units':total([r for r in returns if r['return_status']==k],'event_quantity')} for k in ('RECEIVED','REQUESTED','REJECTED')],
      'order_amount_distribution':distribution,'order_amount_histogram':histogram,'reconciliation':'PASSED'}


def chart(title, pairs, unit):
    """Barras estáticas accesibles: origen cero, etiquetas y valores, sin dependencias."""
    height = 100+38*len(pairs)
    maximum = max([v for _,v in pairs]+[1])
    parts=[f'<svg xmlns="http://www.w3.org/2000/svg" width="950" height="{height}" role="img"><title>{escape(title)}</title>',
           '<rect width="100%" height="100%" fill="white"/>',
           f'<text x="20" y="25" font-family="sans-serif" font-size="17">{escape(title)} — SINTÉTICO</text>',
           f'<text x="20" y="48" font-family="sans-serif">Unidad: {escape(unit)}; barras desde cero</text>']
    for i,(label,value) in enumerate(pairs):
        y=65+i*38
        parts.extend([f'<text x="20" y="{y+18}" font-family="sans-serif">{escape(str(label))}</text>',
                      f'<rect x="220" y="{y}" width="{value/maximum*580:.3f}" height="24" fill="#27648a"/>',
                      f'<text x="{230+value/maximum*580:.3f}" y="{y+18}" font-family="sans-serif">{value}</text>'])
    return ''.join(parts)+'</svg>\n'


def run(bundle, output):
    bundle, output = Path(bundle).resolve(), Path(output).resolve()
    allowed = ROOT/'data/aurelia/eda'
    if allowed not in output.parents or bundle==output or bundle in output.parents or output in bundle.parents:
        raise ValueError('Usar un destino nuevo bajo data/aurelia/eda, separado de las entradas')
    if output.exists():
        raise FileExistsError('Salida existente: elegir otra ruta')
    sources = [bundle/'warehouse.sqlite']+[bundle/'exports'/f'{k}.csv' for k in VIEWS]
    before = {p.relative_to(bundle).as_posix():digest(p) for p in sources}
    result = summarize(read_exports(bundle))
    result['input_sha256'] = before
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.aurelia-eda-', dir=output.parent) as work:
        stage=Path(work)/'report';stage.mkdir()
        (stage/'results.json').write_text(json.dumps(result,ensure_ascii=False,sort_keys=True,indent=2)+'\n',encoding='utf-8')
        for key in ('order_states','daily_orders','products','return_states','order_amount_distribution','order_amount_histogram'):
            with (stage/(key+'.csv')).open('w',encoding='utf-8',newline='') as f:
                writer=csv.DictWriter(f,fieldnames=list(result[key][0]));writer.writeheader();writer.writerows(result[key])
        plots = {
          'order_states':('Pedidos por estado',[(r['order_status'],r['orders']) for r in result['order_states']],'pedidos'),
          'daily_orders':('Pedidos por fecha UTC',[(r['order_date'],r['orders']) for r in result['daily_orders']],'pedidos/día'),
          'product_units':('Unidades pedidas por producto',[(r['product_code'],r['ordered_units']) for r in result['products']],'unidades, todos los estados'),
          'payment_balance':('Conciliación financiera simulada',[(k,result['money'][k]) for k in ('captured_cents','completed_refund_cents','net_captured_cents')],'centavos USD'),
          'order_amount_histogram':('Distribución de importes esperados',[(r['interval_cents'],r['orders']) for r in result['order_amount_histogram']],'pedidos; intervalos en centavos USD')}
        for key,(title,pairs,unit) in plots.items():
            (stage/(key+'.svg')).write_text(chart(title,pairs,unit),encoding='utf-8')
        if before!={p.relative_to(bundle).as_posix():digest(p) for p in sources}:
            raise ValueError('Entradas cambiaron durante EDA')
        stage.rename(output)
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bundle',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    try:
        result=run(args.bundle,args.output)
    except (OSError,ValueError,sqlite3.Error,KeyError,StopIteration) as exc:
        parser.exit(1,f'EDA no aceptado: {exc}\n')
    print(json.dumps({'synthetic':True,'reconciliation':result['reconciliation'],'money':result['money']},sort_keys=True))


if __name__=='__main__':
    main()
