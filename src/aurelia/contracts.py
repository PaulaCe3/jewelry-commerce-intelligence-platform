"""Contrato sintético v1. No representa políticas de una empresa real."""
from datetime import datetime
import hashlib
import json
from pathlib import Path

VERSION = 'aurelia-synthetic-v1'
ENTITIES = ('orders', 'items', 'payments')
FIELDS = {
    'orders': {'order_id', 'ordered_at', 'status', 'currency', 'expected_cents'},
    'items': {'order_id', 'item_no', 'product_code', 'quantity', 'unit_price_cents'},
    'payments': {'order_id', 'payment_no', 'status', 'amount_cents'},
}
ROOT = Path(__file__).resolve().parents[2]


def encode(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':'), allow_nan=False)


def sha256(path):
    result = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1048576), b''):
            result.update(block)
    return result.hexdigest()


def safe_destination(path):
    path = Path(path).resolve()
    for folder in ['data/raw', 'data/processed', 'data/evidence', 'src', 'tests', 'tools', 'docs', '.git']:
        protected = ROOT / folder
        if path == protected or protected in path.parents or path in protected.parents:
            raise ValueError('Destino solapado con una ruta protegida.')
    if path == ROOT:
        raise ValueError('No usar la raíz como destino.')
    return path


def parse_json(text):
    def unique(pairs):
        obj = {}
        for key, value in pairs:
            if key in obj:
                raise ValueError('Clave JSON repetida.')
            obj[key] = value
        return obj
    def reject(_):
        raise ValueError('Constante no finita.')
    return json.loads(text, object_pairs_hook=unique, parse_constant=reject)


def shape_error(entity, row):
    if type(row) is not dict or set(row) != FIELDS[entity]:
        return 'FIELDS'
    if type(row['order_id']) is not str or not row['order_id'].startswith('SIM-O-') or not row['order_id'][6:].isdigit():
        return 'ORDER_ID'
    ints = {'orders': ['expected_cents'], 'items': ['item_no', 'quantity', 'unit_price_cents'],
            'payments': ['payment_no', 'amount_cents']}[entity]
    for name in ints:
        value = row[name]
        if type(value) is not int or value < (0 if name == 'expected_cents' else 1) or value > 10**9:
            return 'INTEGER_RANGE'
    if entity == 'orders':
        if row['currency'] != 'USD' or type(row['currency']) is not str:
            return 'CURRENCY'
        if type(row['status']) is not str or row['status'] not in ('OPEN', 'PAID', 'CANCELLED'):
            return 'ORDER_STATUS'
        try:
            if type(row['ordered_at']) is not str:
                return 'DATE'
            dt = datetime.strptime(row['ordered_at'], '%Y-%m-%dT%H:%M:%SZ')
            if dt.strftime('%Y-%m-%dT%H:%M:%SZ') != row['ordered_at']:
                return 'DATE'
        except ValueError:
            return 'DATE'
    elif entity == 'items':
        if type(row['product_code']) is not str or row['product_code'] not in ('SIM-RING', 'SIM-EARRING', 'SIM-PENDANT'):
            return 'PRODUCT'
    elif type(row['status']) is not str or row['status'] not in ('CAPTURED', 'FAILED'):
        return 'PAYMENT_STATUS'
    return None
