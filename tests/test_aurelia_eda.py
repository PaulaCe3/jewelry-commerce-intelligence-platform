"""Aceptación EDA: requiere el paquete sintético local, nunca lo regenera."""
import copy
import csv
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from src.aurelia import eda


class EdaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bundle=eda.ROOT/'data/aurelia/runs/seed42-orders30'
        if not (cls.bundle/'warehouse.sqlite').is_file():
            raise RuntimeError('Falta paquete sintético local: integración requerida, no skip')
        cls.tables=eda.read_exports(cls.bundle)

    def test_exact_reconciled_totals(self):
        r=eda.summarize(self.tables)
        self.assertEqual(r['money'],{'paid_order_item_cents':92000,'captured_cents':92000,'completed_refund_cents':1400,'net_captured_cents':90600})
        self.assertEqual(r['row_counts'],{'orders':30,'items':70,'products':3,'payments':35,'returns':5,'refunds':7})

    def test_no_fanout(self):
        t=copy.deepcopy(self.tables)
        t['payments'].append(copy.deepcopy(t['payments'][0]))
        with self.assertRaises(ValueError):eda.summarize(t)

    def test_product_mutation_detected(self):
        t=copy.deepcopy(self.tables);t['products'][0]['ordered_units']+=1
        with self.assertRaises(ValueError):eda.summarize(t)

    def test_daily_histogram_distribution(self):
        r=eda.summarize(self.tables)
        self.assertEqual(sum(x['orders'] for x in r['daily_orders']),30)
        self.assertEqual(sum(x['orders'] for x in r['order_amount_histogram']),30)
        self.assertEqual(r['order_amount_distribution'][0]['orders'],30)
        self.assertEqual(sum(x['event_units'] for x in r['return_states'] if x['return_status']=='RECEIVED'),3)

    def test_csv_alteration_rejected_against_sqlite(self):
        parent=eda.ROOT/'data/aurelia/eda';parent.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(prefix='.aurelia-test-',dir=parent) as d:
            bundle=Path(d)/'input';shutil.copytree(self.bundle,bundle)
            p=bundle/'exports/analytics_orders.csv'
            with p.open(encoding='utf-8',newline='') as f:rows=list(csv.reader(f))
            rows[1][rows[0].index('expected_item_cents')]='999999'
            with p.open('w',encoding='utf-8',newline='') as f:csv.writer(f).writerows(rows)
            with self.assertRaises(ValueError):eda.read_exports(bundle)
            with self.assertRaises(ValueError):eda.run(bundle,Path(d)/'rejected')
            self.assertFalse((Path(d)/'rejected').exists())

    def test_output_reproducibility_and_source_protection(self):
        parent=eda.ROOT/'data/aurelia/eda';parent.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(prefix='.aurelia-test-',dir=parent) as d:
            a,b=Path(d)/'a',Path(d)/'b'
            eda.run(self.bundle,a);eda.run(self.bundle,b)
            self.assertEqual({p.name:eda.digest(p) for p in a.iterdir()},{p.name:eda.digest(p) for p in b.iterdir()})
            for p in a.glob('*.svg'):ET.parse(p)
            self.assertEqual(json.loads((a/'results.json').read_text(encoding='utf-8'))['reconciliation'],'PASSED')
            with self.assertRaises(FileExistsError):eda.run(self.bundle,a)

    def test_protected_destination(self):
        with self.assertRaises(ValueError):eda.run(self.bundle,self.bundle/'eda')
        with self.assertRaises(ValueError):eda.run(self.bundle,eda.ROOT/'docs/new-output')

    def test_cli_failure_and_help(self):
        p=subprocess.run([sys.executable,'-B','-m','src.aurelia.eda','--help'],capture_output=True)
        self.assertEqual(p.returncode,0)
        p=subprocess.run([sys.executable,'-B','-m','src.aurelia.eda','--bundle',str(self.bundle),'--output',str(eda.ROOT/'docs/no-output')],capture_output=True)
        self.assertEqual(p.returncode,1)


if __name__=='__main__':
    unittest.main(verbosity=2)
