"""Pruebas autónomas de la simulación; ningún resultado representa ventas reales."""
from contextlib import closing
import hashlib
import json
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from aurelia.contracts import ENTITIES, encode, sha256
from aurelia.generator import generate
from aurelia import warehouse


class AureliaTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / 'normal'
        self.database = self.root / 'aurelia.sqlite'
        generate(self.source, seed=42, orders=30)

    def rows(self, entity):
        return [json.loads(line) for line in (self.source / f'{entity}.jsonl').read_text(encoding='utf-8').splitlines()]

    def mutate(self, entity, change):
        rows = self.rows(entity)
        change(rows)
        p = self.source / f'{entity}.jsonl'
        p.write_text(''.join(encode(r)+'\n' for r in rows), encoding='utf-8', newline='\n')
        manifest = json.loads((self.source / 'manifest.json').read_text())
        manifest['files'][entity] = {'sha256': sha256(p), 'records': len(rows)}
        (self.source / 'manifest.json').write_text(encode(manifest)+'\n', encoding='utf-8')

    def accepted(self):
        result = warehouse.build(self.source, self.database)
        self.assertEqual(result['status'], 'ACCEPTED')
        return result

    def rejected(self, rule):
        result = warehouse.build(self.source, self.database)
        self.assertEqual(result['status'], 'REJECTED')
        self.assertIn(rule, warehouse.inspect(self.database, 'rejections')['rules'])
        with closing(sqlite3.connect(self.database)) as db:
            for table in ['int_order','int_item','int_payment','fact_item','fact_payment']:
                self.assertEqual(db.execute(f'SELECT COUNT(*) FROM {table}').fetchone()[0],0)
            expected = sum(len(self.rows(e)) for e in ENTITIES)
            self.assertEqual(db.execute('SELECT COUNT(*) FROM stg_record').fetchone()[0],expected)

    def test_deterministic_files_same_seed_and_changed_seed(self):
        same, other = self.root / 'same', self.root / 'other'
        generate(same, 42, 30)
        generate(other, 99, 30)
        for name in ['manifest.json','orders.jsonl','items.jsonl','payments.jsonl']:
            self.assertEqual((same/name).read_bytes(),(self.source/name).read_bytes())
        self.assertNotEqual((other/'items.jsonl').read_bytes(),(self.source/'items.jsonl').read_bytes())

    def test_generator_rejects_invalid_seed_count_existing_and_protected(self):
        for seed,count in [(-1,30),(True,30),(42,5),(42,10001)]:
            with self.assertRaises(ValueError):
                generate(self.root/'invalid',seed,count)
        with self.assertRaises(FileExistsError):
            generate(self.source)
        with self.assertRaises(ValueError):
            generate(ROOT/'data/raw/forbidden')

    def test_source_hashes_and_row_reconstruction(self):
        before = {p.name:sha256(p) for p in self.source.iterdir()}
        self.accepted()
        with closing(sqlite3.connect(self.database)) as db:
            for e in ENTITIES:
                reconstructed=''.join(text for (text,) in db.execute('SELECT raw_text FROM stg_record WHERE entity=? ORDER BY source_line',(e,)))
                self.assertEqual(reconstructed.encode(),(self.source/f'{e}.jsonl').read_bytes())
        self.assertEqual(before,{p.name:sha256(p) for p in self.source.iterdir()})

    def test_primary_keys_foreign_keys_and_integrity(self):
        self.accepted()
        with closing(sqlite3.connect(self.database)) as db:
            db.execute('PRAGMA foreign_keys=ON')
            self.assertEqual(db.execute('PRAGMA integrity_check').fetchone(),('ok',))
            self.assertEqual(db.execute('PRAGMA foreign_key_check').fetchall(),[])
            with self.assertRaises(sqlite3.IntegrityError):
                db.execute('INSERT INTO fact_item SELECT * FROM fact_item LIMIT 1')
            db.rollback()
            with self.assertRaises(sqlite3.IntegrityError):
                db.execute("INSERT INTO int_payment VALUES ('missing',1,'FAILED',100,'missing')")

    def test_record_conservation_integration_and_facts(self):
        self.accepted()
        with closing(sqlite3.connect(self.database)) as db:
            for entity,table,fact in [('orders','int_order',None),('items','int_item','fact_item'),('payments','int_payment','fact_payment')]:
                self.assertEqual(db.execute(f'SELECT COUNT(*) FROM {table}').fetchone()[0],len(self.rows(entity)))
                if fact:
                    self.assertEqual(db.execute(f'SELECT COUNT(*) FROM {fact}').fetchone()[0],len(self.rows(entity)))
            self.assertEqual(db.execute('SELECT COUNT(*) FROM order_reconciliation').fetchone()[0],30)

    def test_independent_integer_amount_reconciliation(self):
        self.accepted()
        totals={o['order_id']:0 for o in self.rows('orders')}
        captures=dict(totals)
        for r in self.rows('items'):
            totals[r['order_id']]+=r['quantity']*r['unit_price_cents']
        for r in self.rows('payments'):
            captures[r['order_id']]+=r['amount_cents'] if r['status']=='CAPTURED' else 0
        with closing(sqlite3.connect(self.database)) as db:
            for order in self.rows('orders'):
                self.assertEqual(order['expected_cents'],totals[order['order_id']])
                self.assertEqual(captures[order['order_id']],order['expected_cents'] if order['status']=='PAID' else 0)
            for oid,item,captured,diff1,diff2 in db.execute('SELECT order_id,item_cents,captured_cents,item_difference_cents,payment_difference_cents FROM order_reconciliation'):
                self.assertEqual((item,captured,diff1,diff2),(totals[oid],captures[oid],0,0))

    def test_deliberate_fanout_and_distinct_are_detectably_wrong(self):
        self.accepted()
        with closing(sqlite3.connect(self.database)) as db:
            good=db.execute("SELECT item_cents,captured_cents FROM order_reconciliation WHERE order_id='SIM-O-000001'").fetchone()
            bad=db.execute("SELECT SUM(i.line_amount_cents),SUM(p.captured_amount_cents) FROM fact_item i JOIN fact_payment p ON i.order_id=p.order_id WHERE i.order_id='SIM-O-000001'").fetchone()
            distinct=db.execute("SELECT SUM(DISTINCT line_amount_cents) FROM fact_item WHERE order_id='SIM-O-000001'").fetchone()[0]
            self.assertEqual(good,(3000,3000))
            self.assertEqual(bad,(6000,9000))
            self.assertEqual(distinct,1000)
            self.assertNotEqual(good,bad)
            self.assertNotEqual(distinct,good[0])

    def test_idempotent_build_preserves_database_bytes(self):
        self.accepted()
        before=sha256(self.database)
        result=warehouse.build(self.source,self.database)
        self.assertEqual(result['action'],'unchanged')
        self.assertEqual(sha256(self.database),before)

    def test_independent_rebuilds_logically_identical(self):
        self.accepted()
        other=self.root/'other.sqlite'
        warehouse.build(self.source,other)
        with closing(sqlite3.connect(self.database)) as a,closing(sqlite3.connect(other)) as b:
            self.assertEqual(list(a.iterdump()),list(b.iterdump()))

    def test_separate_adverse_dataset_is_rejected_with_staging_only(self):
        adverse=self.root/'adverse'
        generate(adverse,42,30,True)
        before={p.name:sha256(p) for p in self.source.iterdir()}
        result=warehouse.build(adverse,self.database)
        self.assertEqual(result['status'],'REJECTED')
        rules=warehouse.inspect(self.database,'rejections')['rules']
        self.assertTrue({'DUPLICATE_KEY','CURRENCY','ORPHAN','INTEGER_RANGE','PAYMENT_RECONCILIATION'} <= set(rules))
        self.assertEqual(warehouse.inspect(self.database)['counts']['fact_item'],0)
        self.assertEqual(before,{p.name:sha256(p) for p in self.source.iterdir()})

    def test_duplicate_order_item_and_payment_keys_rejected(self):
        for e in ENTITIES:
            with self.subTest(entity=e):
                saved=(self.source/f'{e}.jsonl').read_bytes()
                manifest=(self.source/'manifest.json').read_bytes()
                self.mutate(e,lambda rows:rows.append(dict(rows[0])))
                self.rejected('DUPLICATE_KEY')
                self.database.unlink()
                (self.source/f'{e}.jsonl').write_bytes(saved)
                (self.source/'manifest.json').write_bytes(manifest)

    def test_orphan_rejected(self):
        self.mutate('items',lambda rows:rows[0].update(order_id='SIM-O-888888'))
        self.rejected('ORPHAN')

    def test_invalid_currency_type_state_date_extra_field_and_amount(self):
        cases=[('orders',{'currency':'EUR'},'CURRENCY'),('orders',{'status':'REFUNDED'},'ORDER_STATUS'),
               ('orders',{'ordered_at':'2025-02-30T00:00:00Z'},'DATE'),('orders',{'extra':1},'FIELDS'),
               ('items',{'quantity':True},'INTEGER_RANGE'),('items',{'unit_price_cents':-1},'INTEGER_RANGE'),
               ('items',{'product_code':'real-product'},'PRODUCT'),('payments',{'status':'PENDING'},'PAYMENT_STATUS')]
        for entity,changes,rule in cases:
            with self.subTest(changes=changes):
                saved=(self.source/f'{entity}.jsonl').read_bytes();manifest=(self.source/'manifest.json').read_bytes()
                self.mutate(entity,lambda rows:rows[0].update(changes))
                self.rejected(rule)
                self.database.unlink();(self.source/f'{entity}.jsonl').write_bytes(saved);(self.source/'manifest.json').write_bytes(manifest)

    def test_payment_underpayment_or_cancellation_with_capture_rejected(self):
        self.mutate('payments',lambda rows:rows[0].update(amount_cents=1499))
        self.rejected('PAYMENT_RECONCILIATION')

    def test_cancelled_order_cannot_have_capture(self):
        self.mutate('orders',lambda rows:rows[0].update(status='CANCELLED'))
        self.rejected('PAYMENT_RECONCILIATION')

    def test_no_items_rejected(self):
        self.mutate('items',lambda rows:rows.__setitem__(slice(None),[r for r in rows if r['order_id']!='SIM-O-000001']))
        self.rejected('NO_ITEMS')

    def test_manifest_file_hash_and_count_mismatch_fail_closed(self):
        path=self.source/'items.jsonl';original=path.read_bytes()
        path.write_bytes(original+b'\n')
        with self.assertRaises(ValueError):warehouse.build(self.source,self.database)
        self.assertFalse(self.database.exists())
        path.write_bytes(original)
        manifest=json.loads((self.source/'manifest.json').read_text());manifest['files']['items']['records']+=1
        (self.source/'manifest.json').write_text(encode(manifest),encoding='utf-8')
        with self.assertRaises(ValueError):warehouse.build(self.source,self.database)
        self.assertFalse(self.database.exists())

    def test_invalid_json_preserved_as_verifiable_rejection(self):
        path=self.source/'orders.jsonl'
        path.write_bytes(path.read_bytes()+b'{broken}\n')
        manifest=json.loads((self.source/'manifest.json').read_text());manifest['files']['orders']['sha256']=sha256(path);manifest['files']['orders']['records']+=1
        (self.source/'manifest.json').write_text(encode(manifest),encoding='utf-8')
        result=warehouse.build(self.source,self.database)
        self.assertEqual(result['status'],'REJECTED')
        self.assertIn('JSON',warehouse.inspect(self.database,'rejections')['rules'])
        with closing(sqlite3.connect(self.database)) as db:
            self.assertIn(('{broken}\n',),db.execute("SELECT raw_text FROM stg_record WHERE entity='orders'").fetchall())

    def test_failure_mid_staging_or_integration_is_atomic(self):
        stage=warehouse.stage_and_validate
        def fail_staging(db,*args):
            stage(db,*args)
            raise OSError('simulated staging failure')
        integrate=warehouse.integrate
        def fail_integration(db,*args):
            integrate(db,*args)
            raise OSError('simulated integration failure')
        for name,fail in [('stage_and_validate',fail_staging),('integrate',fail_integration)]:
            with self.subTest(name=name),patch.object(warehouse,name,side_effect=fail):
                with self.assertRaises(OSError):warehouse.build(self.source,self.database)
                self.assertFalse(self.database.exists())
                self.assertFalse(list(self.root.glob('.aurelia-*')))

    def test_publication_permission_failure_and_existing_database_untouched(self):
        with patch.object(warehouse.os,'link',side_effect=PermissionError('simulated')):
            with self.assertRaises(PermissionError):warehouse.build(self.source,self.database)
        self.assertFalse(self.database.exists())
        self.accepted();before=sha256(self.database)
        self.mutate('payments',lambda rows:rows[0].update(amount_cents=1))
        with self.assertRaises(ValueError):warehouse.build(self.source,self.database)
        self.assertEqual(sha256(self.database),before)

    def test_database_mutation_detected_on_repeat(self):
        self.accepted()
        with closing(sqlite3.connect(self.database)) as db:
            db.execute('UPDATE fact_item SET line_amount_cents=1');db.commit()
        before=sha256(self.database)
        with self.assertRaises(ValueError):warehouse.build(self.source,self.database)
        self.assertEqual(sha256(self.database),before)

    def test_missing_inputs_and_protected_output_rejected(self):
        with self.assertRaises(OSError):warehouse.build(self.root/'missing',self.database)
        with self.assertRaises(ValueError):warehouse.build(self.source,ROOT/'data/evidence/forbidden.sqlite')
        with self.assertRaises(ValueError):warehouse.build(self.source,self.source/'forbidden.sqlite')

    def test_cli_end_to_end_and_exit_codes(self):
        cli=[sys.executable,'-B','-X','utf8','-m','src.aurelia']
        def run(*args):return subprocess.run(cli+list(args),cwd=ROOT,capture_output=True,text=True,encoding='utf-8')
        generated=self.root/'cli'
        self.assertEqual(run('generate','--output',str(generated),'--seed','7','--orders','12').returncode,0)
        r=run('build','--input',str(generated),'--database',str(self.database))
        self.assertEqual(r.returncode,0,r.stderr)
        self.assertEqual(json.loads(r.stdout)['status'],'ACCEPTED')
        self.assertEqual(run('build','--input',str(generated),'--database',str(self.database)).returncode,0)
        for query in ['summary','reconciliation','rejections']:
            self.assertEqual(run('query','--database',str(self.database),'--query',query).returncode,0)
        adverse=self.root/'cli-bad'
        self.assertEqual(run('generate','--output',str(adverse),'--adverse').returncode,0)
        r=run('build','--input',str(adverse),'--database',str(self.root/'bad.sqlite'))
        self.assertEqual(r.returncode,1,r.stderr)
        self.assertEqual(json.loads(r.stdout)['status'],'REJECTED')
        self.assertEqual(run().returncode,2)
        self.assertEqual(run('query','--database',str(self.root/'absent.sqlite')).returncode,1)


if __name__ == '__main__':
    unittest.main()
