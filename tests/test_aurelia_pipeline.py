"""Aceptación end-to-end de orquestación/consumo, con datos exclusivamente sintéticos."""
from contextlib import closing
import csv
import hashlib
import json
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from aurelia import pipeline,analytics,v2,warehouse


class PipelineTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.output=self.root/'run'

    def run_pipeline(self):
        return pipeline.run(self.output,42,30)

    def snapshot(self):
        return {p.relative_to(self.output).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
                for p in self.output.rglob('*') if p.is_file()}

    def assert_no_publication(self):
        self.assertFalse(self.output.exists())
        self.assertFalse(list(self.root.glob('.aurelia-*')))

    def test_fresh_run_acceptance_and_complete_exports(self):
        result=self.run_pipeline();self.assertEqual(result['status'],'success')
        self.assertEqual(pipeline.verify(self.output)['status'],'PASSED')
        self.assertEqual(result['row_counts'],{'analytics_orders':30,'analytics_items':70,'analytics_products':3,
                                             'analytics_payments':35,'analytics_returns':5,'analytics_refunds':7})
        self.assertEqual(len(list((self.output/'exports').glob('*.csv'))),6)
        self.assertEqual(len(self.snapshot()),15)

    def test_second_run_unchanged_all_artifact_bytes_preserved(self):
        self.run_pipeline();before=self.snapshot()
        self.assertEqual(self.run_pipeline()['status'],'unchanged')
        self.assertEqual(self.snapshot(),before)

    def test_independent_runs_same_seed_byte_reproducible(self):
        self.run_pipeline();other=self.root/'other';pipeline.run(other,42,30)
        for relative,digest in self.snapshot().items():
            self.assertEqual(hashlib.sha256((other/relative).read_bytes()).hexdigest(),digest,relative)

    def test_different_configuration_never_overwrites_previous_run(self):
        self.run_pipeline();before=self.snapshot()
        for seed,orders in [(7,30),(42,12)]:
            with self.subTest(seed=seed,orders=orders),self.assertRaises(ValueError):
                pipeline.run(self.output,seed,orders)
            self.assertEqual(self.snapshot(),before)

    def test_invalid_inputs_no_final_directory(self):
        for seed,orders in [(-1,30),(42,5),(True,30),(42,10001)]:
            with self.subTest(seed=seed,orders=orders),self.assertRaises(ValueError):
                pipeline.run(self.output,seed,orders)
            self.assert_no_publication()

    def test_failures_at_each_stage_leave_no_publication(self):
        for owner,name in [(v2,'generate'),(v2,'build'),(analytics,'install'),(analytics,'validate'),
                           (analytics,'export'),(analytics,'validate_exports')]:
            with self.subTest(stage=name),patch.object(owner,name,side_effect=OSError('controlled failure')):
                with self.assertRaises(OSError):self.run_pipeline()
                self.assert_no_publication()

    def test_partial_csv_write_failure_never_published(self):
        def fail(database,directory):
            Path(directory).mkdir();(Path(directory)/'partial.csv').write_text('partial',encoding='utf-8')
            raise OSError('controlled write failure')
        with patch.object(analytics,'export',side_effect=fail):
            with self.assertRaises(OSError):self.run_pipeline()
        self.assert_no_publication()

    def test_final_directory_publication_failure_is_closed(self):
        rename=pipeline.os.rename
        def fail(source,destination,*args,**kwargs):
            if Path(destination)==self.output:raise PermissionError('controlled final publication')
            return rename(source,destination,*args,**kwargs)
        with patch.object(pipeline.os,'rename',side_effect=fail):
            with self.assertRaises(PermissionError):self.run_pipeline()
        self.assert_no_publication()

    def test_rejected_adjustments_not_exposed_as_consumption(self):
        generate=v2.generate
        def adverse(directory,seed,orders):return generate(directory,seed,orders,True)
        with patch.object(v2,'generate',side_effect=adverse):
            with self.assertRaises(ValueError):self.run_pipeline()
        self.assert_no_publication()

    def test_unknown_existing_directory_is_preserved(self):
        self.output.mkdir();p=self.output/'unrelated.txt';p.write_text('keep',encoding='utf-8')
        with self.assertRaises(OSError):self.run_pipeline()
        self.assertEqual(p.read_text(),'keep');self.assertFalse((self.output/'warehouse.sqlite').exists())

    def test_lock_collision_never_removed_or_bypassed(self):
        lock=self.root/'.aurelia-run.lock';lock.write_text('another owner',encoding='utf-8')
        with self.assertRaises(FileExistsError):self.run_pipeline()
        self.assertEqual(lock.read_text(),'another owner');self.assertFalse(self.output.exists())

    def test_csv_and_manifest_tampering_detected(self):
        self.run_pipeline();path=self.output/'exports/analytics_orders.csv';original=path.read_bytes()
        path.write_bytes(original+b'corrupt\n')
        with self.assertRaises(ValueError):pipeline.verify(self.output)
        with self.assertRaises(ValueError):self.run_pipeline()
        self.assertEqual(path.read_bytes(),original+b'corrupt\n')

    def test_manifest_rehash_does_not_hide_wrong_csv_values(self):
        self.run_pipeline();p=self.output/'exports/analytics_orders.csv'
        with p.open(encoding='utf-8',newline='') as f:rows=list(csv.reader(f))
        rows[1][6]='999999'
        with p.open('w',encoding='utf-8',newline='') as f:csv.writer(f,lineterminator='\n').writerows(rows)
        manifest_path=self.output/'run_manifest.json';manifest=json.loads(manifest_path.read_text())
        digest=hashlib.sha256(p.read_bytes()).hexdigest();manifest['files']['exports/analytics_orders.csv']=digest
        manifest['exports']['analytics_orders']['sha256']=digest
        manifest_path.write_text(json.dumps(manifest),encoding='utf-8')
        with self.assertRaises(ValueError):pipeline.verify(self.output)

    def test_independent_source_oracle_detects_broken_sql_view(self):
        self.run_pipeline();db=self.output/'warehouse.sqlite'
        with closing(sqlite3.connect(db)) as c:
            c.execute('DROP VIEW analytics_refunds')
            c.execute('CREATE VIEW analytics_refunds AS '+analytics.SQL['analytics_refunds'].replace('f.posted_cents posted_refund_cents','f.posted_cents*2 posted_refund_cents'));c.commit()
        with self.assertRaises(ValueError):analytics.validate(db,self.output/'inputs')

    def test_money_conservation_and_product_grain(self):
        self.run_pipeline()
        with closing(warehouse.read_only(self.output/'warehouse.sqlite')) as db:
            sums=db.execute('SELECT SUM(original_captured_cents),SUM(posted_refund_cents),SUM(net_captured_cents),SUM(returned_units) FROM analytics_orders').fetchone()
            self.assertEqual(sums,(92000,1400,90600,3))
            self.assertEqual(db.execute('SELECT SUM(original_captured_cents),SUM(posted_refund_cents),SUM(net_captured_cents) FROM analytics_payments').fetchone(),sums[:3])
            self.assertEqual(db.execute('SELECT SUM(posted_refund_cents) FROM analytics_refunds').fetchone(),(1400,))
            self.assertEqual(db.execute('SELECT SUM(returned_units) FROM analytics_products').fetchone(),(3,))
            self.assertEqual(db.execute('SELECT SUM(paid_item_cents) FROM analytics_products').fetchone(),(92000,))
            self.assertEqual(db.execute('SELECT COUNT(*),COUNT(DISTINCT product_code) FROM analytics_products').fetchone(),(3,3))
            self.assertNotIn('posted_refund_cents',analytics.VIEWS['analytics_products'][1])

    def test_csv_headers_nulls_values_and_stable_order(self):
        self.run_pipeline()
        for name,(key,columns) in analytics.VIEWS.items():
            with (self.output/'exports'/(name+'.csv')).open(encoding='utf-8',newline='') as f:
                reader=csv.DictReader(f);rows=list(reader);self.assertEqual(reader.fieldnames,list(columns))
            self.assertTrue(all(r['synthetic']=='1' and r['currency']=='USD' for r in rows))
        with (self.output/'exports/analytics_refunds.csv').open(encoding='utf-8',newline='') as f:
            rows=list(csv.DictReader(f))
        self.assertTrue(any(r['refund_reason']=='GOODWILL' and r['return_id']=='' for r in rows))
        self.assertTrue(any(r['refund_status']=='REQUESTED' and r['completed_at_utc']=='' for r in rows))

    def test_protected_destination_rejected(self):
        for path in [ROOT/'data/evidence/no',ROOT/'data/raw/no',ROOT/'src/no',ROOT/'untracked-output']:
            with self.assertRaises(ValueError):pipeline.run(path)

    def test_cli_run_verify_and_failures(self):
        cli=[sys.executable,'-B','-X','utf8','-m','src.aurelia.pipeline']
        def run(*args):return subprocess.run(cli+list(args),cwd=ROOT,capture_output=True,text=True,encoding='utf-8')
        for status in ['success','unchanged']:
            r=run('run','--output',str(self.output),'--seed','42','--orders','30')
            self.assertEqual(r.returncode,0,r.stderr);self.assertEqual(json.loads(r.stdout)['status'],status)
        self.assertEqual(run('verify','--output',str(self.output)).returncode,0)
        self.assertEqual(run('run','--output',str(self.output),'--seed','7').returncode,1)
        self.assertEqual(run('run','--output',str(self.root/'invalid'),'--orders','1').returncode,1)
        self.assertEqual(run().returncode,2)


if __name__=='__main__':unittest.main()
