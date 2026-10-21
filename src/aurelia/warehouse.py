"""Staging, integración y modelo dimensional de la simulación Aurelia v1."""
from collections import Counter, defaultdict
from contextlib import closing
import hashlib
import os
from pathlib import Path
import sqlite3
import tempfile

from .contracts import ENTITIES, VERSION, encode, parse_json, safe_destination, sha256, shape_error

DDL = [
    'CREATE TABLE batch (batch_id TEXT PRIMARY KEY NOT NULL, contract_version TEXT NOT NULL, synthetic INTEGER NOT NULL CHECK(synthetic=1), status TEXT NOT NULL CHECK(status IN (\'ACCEPTED\',\'REJECTED\')), manifest_json TEXT NOT NULL)',
    'CREATE TABLE source_file (entity TEXT PRIMARY KEY NOT NULL, batch_id TEXT NOT NULL REFERENCES batch, sha256 TEXT NOT NULL, records INTEGER NOT NULL)',
    'CREATE TABLE stg_record (technical_id TEXT PRIMARY KEY NOT NULL, entity TEXT NOT NULL REFERENCES source_file, source_line INTEGER NOT NULL, raw_text TEXT NOT NULL, UNIQUE(entity,source_line))',
    'CREATE TABLE rejection (technical_id TEXT NOT NULL REFERENCES stg_record, rule TEXT NOT NULL, detail TEXT NOT NULL, PRIMARY KEY(technical_id,rule))',
    "CREATE TABLE int_order (order_id TEXT PRIMARY KEY NOT NULL, ordered_at TEXT NOT NULL, status TEXT NOT NULL CHECK(status IN ('OPEN','PAID','CANCELLED')), currency TEXT NOT NULL CHECK(currency='USD'), expected_cents INTEGER NOT NULL CHECK(expected_cents>=0), technical_id TEXT NOT NULL UNIQUE REFERENCES stg_record)",
    'CREATE TABLE int_item (order_id TEXT NOT NULL REFERENCES int_order, item_no INTEGER NOT NULL CHECK(item_no>0), product_code TEXT NOT NULL, quantity INTEGER NOT NULL CHECK(quantity>0), unit_price_cents INTEGER NOT NULL CHECK(unit_price_cents>0), technical_id TEXT NOT NULL UNIQUE REFERENCES stg_record, PRIMARY KEY(order_id,item_no))',
    "CREATE TABLE int_payment (order_id TEXT NOT NULL REFERENCES int_order, payment_no INTEGER NOT NULL CHECK(payment_no>0), status TEXT NOT NULL CHECK(status IN ('CAPTURED','FAILED')), amount_cents INTEGER NOT NULL CHECK(amount_cents>0), technical_id TEXT NOT NULL UNIQUE REFERENCES stg_record, PRIMARY KEY(order_id,payment_no))",
    'CREATE TABLE dim_date (date_key TEXT PRIMARY KEY NOT NULL, year INTEGER NOT NULL, month INTEGER NOT NULL, day INTEGER NOT NULL)',
    'CREATE TABLE dim_product (product_key TEXT PRIMARY KEY NOT NULL)',
    'CREATE TABLE dim_order_status (status_key TEXT PRIMARY KEY NOT NULL)',
    'CREATE TABLE dim_payment_status (status_key TEXT PRIMARY KEY NOT NULL)',
    '''CREATE TABLE fact_item (order_id TEXT NOT NULL, item_no INTEGER NOT NULL, date_key TEXT NOT NULL REFERENCES dim_date,
       product_key TEXT NOT NULL REFERENCES dim_product, order_status TEXT NOT NULL REFERENCES dim_order_status,
       quantity INTEGER NOT NULL, line_amount_cents INTEGER NOT NULL, PRIMARY KEY(order_id,item_no),
       FOREIGN KEY(order_id,item_no) REFERENCES int_item)''',
    '''CREATE TABLE fact_payment (order_id TEXT NOT NULL, payment_no INTEGER NOT NULL, date_key TEXT NOT NULL REFERENCES dim_date,
       order_status TEXT NOT NULL REFERENCES dim_order_status, payment_status TEXT NOT NULL REFERENCES dim_payment_status,
       recorded_amount_cents INTEGER NOT NULL, captured_amount_cents INTEGER NOT NULL,
       PRIMARY KEY(order_id,payment_no), FOREIGN KEY(order_id,payment_no) REFERENCES int_payment)''',
    '''CREATE VIEW order_reconciliation AS
       WITH items AS (SELECT order_id,COUNT(*) item_records,SUM(line_amount_cents) item_cents FROM fact_item GROUP BY order_id),
       payments AS (SELECT order_id,COUNT(*) payment_records,SUM(captured_amount_cents) captured_cents FROM fact_payment GROUP BY order_id)
       SELECT o.order_id,o.status,o.currency,o.expected_cents,
         COALESCE(i.item_records,0) item_records,COALESCE(p.payment_records,0) payment_records,
         COALESCE(i.item_cents,0) item_cents,COALESCE(p.captured_cents,0) captured_cents,
         o.expected_cents-COALESCE(i.item_cents,0) item_difference_cents,
         CASE WHEN o.status='PAID' THEN o.expected_cents-COALESCE(p.captured_cents,0) ELSE COALESCE(p.captured_cents,0) END payment_difference_cents
       FROM int_order o LEFT JOIN items i ON i.order_id=o.order_id LEFT JOIN payments p ON p.order_id=o.order_id''',
]
TABLE_ORDER = {'batch': 'batch_id', 'source_file': 'entity', 'stg_record': 'technical_id', 'rejection': 'technical_id,rule',
               'int_order': 'order_id', 'int_item': 'order_id,item_no', 'int_payment': 'order_id,payment_no',
               'dim_date': 'date_key', 'dim_product': 'product_key', 'dim_order_status': 'status_key',
               'dim_payment_status': 'status_key', 'fact_item': 'order_id,item_no', 'fact_payment': 'order_id,payment_no'}


def read_only(path):
    db = sqlite3.connect(Path(path).resolve().as_uri() + '?mode=ro', uri=True)
    db.execute('PRAGMA query_only=ON')
    return db


def inputs(directory):
    directory = Path(directory).resolve()
    manifest = parse_json((directory / 'manifest.json').read_text(encoding='utf-8'))
    keys = {'contract_version', 'synthetic', 'creator', 'seed', 'scenario', 'order_count_requested', 'files'}
    if type(manifest) is not dict or set(manifest) != keys:
        raise ValueError('Contrato de manifiesto incompatible.')
    if manifest['contract_version'] != VERSION or manifest['synthetic'] is not True or manifest['creator'] != 'PLATHEL':
        raise ValueError('Solo se admite la simulación propia identificada.')
    if type(manifest['seed']) is not int or not 0 <= manifest['seed'] < 2**32:
        raise ValueError('Semilla inválida.')
    if type(manifest['order_count_requested']) is not int or not 6 <= manifest['order_count_requested'] <= 10000:
        raise ValueError('Cantidad solicitada incompatible.')
    if type(manifest['scenario']) is not str or manifest['scenario'] not in ('normal', 'invalid_fixture'):
        raise ValueError('Escenario incompatible.')
    if type(manifest['files']) is not dict or set(manifest['files']) != set(ENTITIES):
        raise ValueError('Inventario incompatible.')
    hashes = {'manifest.json': sha256(directory / 'manifest.json')}
    for entity in ENTITIES:
        spec = manifest['files'][entity]
        name = f'{entity}.jsonl'
        if type(spec) is not dict or set(spec) != {'sha256', 'records'} or type(spec['records']) is not int or spec['records'] < 0:
            raise ValueError('Metadatos de archivo incompatibles.')
        hashes[name] = sha256(directory / name)
        if hashes[name] != spec['sha256']:
            raise ValueError('Hash de entrada alterado.')
    return manifest, hashes, hashlib.sha256(encode(hashes).encode()).hexdigest()


def stage_and_validate(db, directory, manifest, batch_id):
    rows = {e: [] for e in ENTITIES}
    rejects = []
    def reject(technical_id, rule, detail):
        rejects.append((technical_id, rule, detail))
    for entity in ENTITIES:
        spec = manifest['files'][entity]
        db.execute('INSERT INTO source_file VALUES (?,?,?,?)', (entity, batch_id, spec['sha256'], spec['records']))
        count = 0
        with (directory / f'{entity}.jsonl').open(encoding='utf-8', newline='') as stream:
            for count, text in enumerate(stream, 1):
                technical_id = f'{spec["sha256"]}:{entity}:{count}'
                db.execute('INSERT INTO stg_record VALUES (?,?,?,?)', (technical_id, entity, count, text))
                try:
                    row = parse_json(text)
                    error = shape_error(entity, row)
                except ValueError:
                    error = 'JSON'
                if error:
                    reject(technical_id, error, 'Registro incompatible con el contrato sintético v1.')
                else:
                    rows[entity].append((technical_id, row))
        if count != spec['records']:
            raise ValueError('Cantidad de registros incompatible con manifiesto; no se acepta staging.')
    # Duplicados son rechazos, nunca INSERT OR IGNORE ni deduplicación silenciosa.
    for entity in ENTITIES:
        counts = Counter((r['order_id'], r.get('item_no', r.get('payment_no'))) for _, r in rows[entity])
        for tid, row in rows[entity]:
            key = (row['order_id'], row.get('item_no', row.get('payment_no')))
            if counts[key] > 1:
                reject(tid, 'DUPLICATE_KEY', 'Clave contractual repetida.')
    orders = {row['order_id']: (tid, row) for tid, row in rows['orders']}
    items, captures = defaultdict(int), defaultdict(int)
    item_counts = Counter()
    for entity in ('items', 'payments'):
        for tid, row in rows[entity]:
            if row['order_id'] not in orders:
                reject(tid, 'ORPHAN', 'Pedido no disponible entre cabeceras válidas.')
            if entity == 'items':
                items[row['order_id']] += row['quantity'] * row['unit_price_cents']
                item_counts[row['order_id']] += 1
            elif row['status'] == 'CAPTURED':
                captures[row['order_id']] += row['amount_cents']
    for order_id, (tid, row) in orders.items():
        if not item_counts[order_id]:
            reject(tid, 'NO_ITEMS', 'Todo pedido v1 requiere al menos un artículo.')
        if items[order_id] != row['expected_cents']:
            reject(tid, 'ITEM_RECONCILIATION', 'Importe esperado distinto de cantidad por precio.')
        expected_captured = row['expected_cents'] if row['status'] == 'PAID' else 0
        if captures[order_id] != expected_captured:
            reject(tid, 'PAYMENT_RECONCILIATION', 'Cobros capturados incompatibles con estado e importe esperado.')
    db.executemany('INSERT INTO rejection VALUES (?,?,?)', rejects)
    return rows, rejects


def integrate(db, rows):
    for tid, r in rows['orders']:
        db.execute('INSERT INTO int_order VALUES (?,?,?,?,?,?)',
                   (r['order_id'], r['ordered_at'], r['status'], r['currency'], r['expected_cents'], tid))
    for tid, r in rows['items']:
        db.execute('INSERT INTO int_item VALUES (?,?,?,?,?,?)',
                   (r['order_id'], r['item_no'], r['product_code'], r['quantity'], r['unit_price_cents'], tid))
    for tid, r in rows['payments']:
        db.execute('INSERT INTO int_payment VALUES (?,?,?,?,?)',
                   (r['order_id'], r['payment_no'], r['status'], r['amount_cents'], tid))
    db.execute("INSERT INTO dim_date SELECT DISTINCT substr(ordered_at,1,10),CAST(substr(ordered_at,1,4) AS INTEGER),CAST(substr(ordered_at,6,2) AS INTEGER),CAST(substr(ordered_at,9,2) AS INTEGER) FROM int_order")
    db.execute('INSERT INTO dim_product SELECT DISTINCT product_code FROM int_item')
    db.execute('INSERT INTO dim_order_status SELECT DISTINCT status FROM int_order')
    db.execute('INSERT INTO dim_payment_status SELECT DISTINCT status FROM int_payment')
    db.execute('''INSERT INTO fact_item SELECT i.order_id,i.item_no,substr(o.ordered_at,1,10),i.product_code,o.status,
                  i.quantity,i.quantity*i.unit_price_cents FROM int_item i JOIN int_order o ON o.order_id=i.order_id''')
    # Date is explicitly order date, NOT a fabricated payment event timestamp.
    db.execute('''INSERT INTO fact_payment SELECT p.order_id,p.payment_no,substr(o.ordered_at,1,10),o.status,p.status,
                  p.amount_cents,CASE WHEN p.status='CAPTURED' THEN p.amount_cents ELSE 0 END
                  FROM int_payment p JOIN int_order o ON o.order_id=p.order_id''')
    for entity, table in [('orders', 'int_order'), ('items', 'int_item'), ('payments', 'int_payment')]:
        if db.execute(f'SELECT COUNT(*) FROM {table}').fetchone()[0] != len(rows[entity]):
            raise ValueError('Pérdida o multiplicación de registros integrados.')
    if db.execute('SELECT COUNT(*) FROM order_reconciliation WHERE item_difference_cents<>0 OR payment_difference_cents<>0').fetchone()[0]:
        raise ValueError('Conciliación dimensional fallida.')
    for fact, table in [('fact_item','int_item'), ('fact_payment','int_payment')]:
        if db.execute(f'SELECT COUNT(*) FROM {fact}').fetchone() != db.execute(f'SELECT COUNT(*) FROM {table}').fetchone():
            raise ValueError('Multiplicación de hechos.')


def equal_databases(left, right):
    sql = "SELECT type,name,sql FROM sqlite_master WHERE name NOT LIKE 'sqlite_%' ORDER BY type,name"
    if left.execute(sql).fetchall() != right.execute(sql).fetchall():
        return False
    if left.execute('PRAGMA user_version').fetchone() != right.execute('PRAGMA user_version').fetchone():
        return False
    sentinel = object()
    for table, order in TABLE_ORDER.items():
        a = iter(left.execute(f'SELECT * FROM {table} ORDER BY {order}'))
        b = iter(right.execute(f'SELECT * FROM {table} ORDER BY {order}'))
        while True:
            x,y = next(a, sentinel), next(b, sentinel)
            if x is sentinel and y is sentinel:
                break
            if x != y:
                return False
    return True


def build(directory, database):
    directory, database = Path(directory).resolve(), safe_destination(database)
    if database.suffix not in ('.sqlite', '.db', '.sqlite3') or directory == database or directory in database.parents:
        raise ValueError('Destino SQLite separado del conjunto fuente.')
    manifest, before, batch_id = inputs(directory)
    database.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.aurelia-', dir=database.parent) as temporary:
        pending = Path(temporary) / 'build.sqlite'
        with closing(sqlite3.connect(pending)) as db:
            db.execute('PRAGMA foreign_keys=ON')
            db.execute('BEGIN IMMEDIATE')
            try:
                for ddl in DDL:
                    db.execute(ddl)
                db.execute('PRAGMA user_version=1')
                db.execute('INSERT INTO batch VALUES (?,?,?,?,?)', (batch_id, VERSION, 1, 'REJECTED', encode(manifest)))
                rows, rejections = stage_and_validate(db, directory, manifest, batch_id)
                status = 'REJECTED' if rejections else 'ACCEPTED'
                if not rejections:
                    integrate(db, rows)
                db.execute('UPDATE batch SET status=?', (status,))
                if inputs(directory)[1] != before:
                    raise ValueError('Entradas cambiaron durante la ejecución.')
                if db.execute('PRAGMA foreign_key_check').fetchall() or db.execute('PRAGMA integrity_check').fetchone() != ('ok',):
                    raise ValueError('Error de integridad SQLite.')
                db.commit()
            except BaseException:
                db.rollback()
                raise
        if database.exists():
            with closing(read_only(pending)) as a, closing(read_only(database)) as b:
                if not equal_databases(a,b):
                    raise ValueError('Destino existente distinto: no se sobrescribe.')
            action = 'unchanged'
        else:
            os.link(pending, database)
            action = 'created'
    return {'synthetic': True, 'contract_version': VERSION, 'status': status, 'action': action,
            'batch_id': batch_id, 'rejections': len(rejections)}


def inspect(database, query='summary'):
    with closing(read_only(database)) as db:
        if db.execute('PRAGMA user_version').fetchone() != (1,):
            raise ValueError('Esquema incompatible.')
        if query == 'rejections':
            return {'synthetic': True, 'rules': dict(db.execute('SELECT rule,COUNT(*) FROM rejection GROUP BY rule'))}
        if query == 'reconciliation':
            return {'synthetic': True, 'orders': [dict(zip([c[0] for c in db.execute('SELECT * FROM order_reconciliation').description], row))
                                                  for row in db.execute('SELECT * FROM order_reconciliation ORDER BY order_id')]}
        if query != 'summary':
            raise ValueError('Consulta desconocida.')
        status = db.execute('SELECT status FROM batch').fetchone()[0]
        return {'synthetic': True, 'currency': 'USD', 'status': status,
                'counts': {table: db.execute(f'SELECT COUNT(*) FROM {table}').fetchone()[0]
                           for table in ['stg_record','rejection','int_order','int_item','int_payment','fact_item','fact_payment']},
                'simulated_paid_item_cents': db.execute("SELECT COALESCE(SUM(line_amount_cents),0) FROM fact_item WHERE order_status='PAID'").fetchone()[0],
                'simulated_captured_cents': db.execute('SELECT COALESCE(SUM(captured_amount_cents),0) FROM fact_payment').fetchone()[0]}
