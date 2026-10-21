"""Generador determinista propio: no importa ni consulta datasets externos."""
from datetime import datetime, timedelta
import os
from pathlib import Path
import random
import tempfile

from .contracts import ENTITIES, VERSION, encode, safe_destination, sha256


def generate(directory, seed=42, orders=30, adverse=False):
    directory = safe_destination(directory)
    if type(seed) is not int or not 0 <= seed < 2**32 or type(orders) is not int or not 6 <= orders <= 10000:
        raise ValueError('Semilla uint32; pedidos entre 6 y 10000 para esta versión del generador.')
    if directory.exists():
        raise FileExistsError('El generador exige un directorio nuevo.')
    rng = random.Random(seed)
    rows = {entity: [] for entity in ENTITIES}
    for index in range(orders):
        order_id = f'SIM-O-{index+1:06d}'
        status = ('PAID', 'PAID', 'OPEN', 'CANCELLED', 'PAID', 'OPEN')[index % 6]
        # Caso adverso al join garantizado: 3 artículos de 1000 centavos y 2 pagos de 1500.
        count = 3 if index == 0 else rng.randint(1, 4)
        total = 0
        for number in range(1, count + 1):
            quantity = 1 if index == 0 else rng.randint(1, 3)
            price = 1000 if index == 0 else rng.choice([500, 1000, 1500, 2500])
            rows['items'].append({'order_id': order_id, 'item_no': number,
                                  'product_code': ('SIM-RING', 'SIM-EARRING', 'SIM-PENDANT')[(number-1) % 3],
                                  'quantity': quantity, 'unit_price_cents': price})
            total += quantity * price
        rows['orders'].append({'order_id': order_id, 'ordered_at': (datetime(2025, 1, 1) + timedelta(days=index % 90)).strftime('%Y-%m-%dT%H:%M:%SZ'),
                               'status': status, 'currency': 'USD', 'expected_cents': total})
        if status == 'PAID':
            amounts = [1500, 1500] if index == 0 else [total] if index % 2 else [total // 2, total-total // 2]
            for number, amount in enumerate(amounts, 1):
                rows['payments'].append({'order_id': order_id, 'payment_no': number, 'status': 'CAPTURED', 'amount_cents': amount})
        elif index % 2:
            rows['payments'].append({'order_id': order_id, 'payment_no': 1, 'status': 'FAILED', 'amount_cents': total})
    if adverse:
        # Archivo separado: pruebas inválidas, sin contaminar el conjunto normal.
        rows['orders'].append(dict(rows['orders'][0]))
        rows['orders'][1]['currency'] = 'UNSUPPORTED'
        rows['items'].append(dict(rows['items'][0], order_id='SIM-O-999999'))
        rows['items'][0]['quantity'] = -1
        rows['payments'][0]['amount_cents'] += 1
    directory.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.aurelia-', dir=directory.parent) as temp:
        temp = Path(temp)
        for entity in ENTITIES:
            (temp / f'{entity}.jsonl').write_text(''.join(encode(row) + '\n' for row in rows[entity]), encoding='utf-8', newline='\n')
        manifest = {'contract_version': VERSION, 'synthetic': True, 'creator': 'PLATHEL', 'seed': seed,
                    'scenario': 'invalid_fixture' if adverse else 'normal', 'order_count_requested': orders,
                    'files': {entity: {'sha256': sha256(temp / f'{entity}.jsonl'), 'records': len(rows[entity])} for entity in ENTITIES}}
        (temp / 'manifest.json').write_text(encode(manifest) + '\n', encoding='utf-8', newline='\n')
        # Nunca reemplaza un directorio ajeno. rename publica el conjunto cerrado.
        if directory.exists():
            raise FileExistsError('Destino ya existente.')
        os.rename(temp, directory)
    return manifest
