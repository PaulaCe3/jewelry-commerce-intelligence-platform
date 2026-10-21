"""Pruebas de ajustes sintéticos v2 y compatibilidad estricta de v1."""
from contextlib import closing
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
from aurelia import v2, warehouse as v1
from aurelia.contracts import encode,sha256
from aurelia.generator import generate as generate_v1


class AdjustmentTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.source=self.root/'source';self.db=self.root/'v2.sqlite'
        v2.generate(self.source,42,30)

    def rows(self,entity):
        return [json.loads(t) for t in (self.source/(entity+'.jsonl')).read_text(encoding='utf-8').splitlines()]

    def mutate(self,entity,change):
        rows=self.rows(entity);change(rows)
        p=self.source/(entity+'.jsonl');p.write_text(''.join(encode(r)+'\n' for r in rows),encoding='utf-8',newline='\n')
        manifest=json.loads((self.source/'manifest.json').read_text());manifest['files'][entity]={'sha256':sha256(p),'records':len(rows)}
        (self.source/'manifest.json').write_text(encode(manifest)+'\n',encoding='utf-8')

    def accepted(self):
        r=v2.build(self.source,self.db);self.assertEqual(r['status'],'ACCEPTED');return r

    def rejected(self,rule):
        r=v2.build(self.source,self.db);self.assertEqual(r['status'],'REJECTED')
        self.assertIn(rule,v2.inspect(self.db,'rejections')['rules'])
        with closing(sqlite3.connect(self.db)) as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM fact_return').fetchone()[0],0)
            self.assertEqual(db.execute('SELECT COUNT(*) FROM fact_refund').fetchone()[0],0)
            self.assertEqual(db.execute('SELECT COUNT(*) FROM int_order').fetchone()[0],30)

    def test_generation_determinism_and_exact_v1_base(self):
        same=self.root/'same';v2.generate(same,42,30)
        for p in self.source.rglob('*'):
            if p.is_file():self.assertEqual(p.read_bytes(),(same/p.relative_to(self.source)).read_bytes())
        base=self.root/'original-v1';generate_v1(base,42,30)
        for p in base.iterdir():self.assertEqual(p.read_bytes(),(self.source/'base'/p.name).read_bytes())
        other=self.root/'other';v2.generate(other,7,30)
        self.assertNotEqual((other/'base/items.jsonl').read_bytes(),(base/'items.jsonl').read_bytes())

    def test_all_historical_tables_and_v1_base_bytes_unchanged(self):
        baseline=self.root/'v1.sqlite';v1.build(self.source/'base',baseline);before=sha256(baseline)
        sources={p:sha256(p) for p in self.source.rglob('*') if p.is_file()}
        self.accepted()
        with closing(sqlite3.connect(baseline)) as a,closing(sqlite3.connect(self.db)) as b:
            for table,order in v1.TABLE_ORDER.items():
                self.assertEqual(a.execute(f'SELECT * FROM {table} ORDER BY {order}').fetchall(),b.execute(f'SELECT * FROM {table} ORDER BY {order}').fetchall(),table)
        self.assertEqual(sha256(baseline),before)
        self.assertEqual(sources,{p:sha256(p) for p in sources})

    def test_existing_v1_database_never_migrated_or_overwritten(self):
        v1.build(self.source/'base',self.db);before=sha256(self.db)
        with self.assertRaises(ValueError):v2.build(self.source,self.db)
        self.assertEqual(sha256(self.db),before)
        with self.assertRaises(ValueError):v2.inspect(self.db)
        with self.assertRaises(ValueError):v1.build(self.source,self.root/'wrong.sqlite')
        self.assertFalse((self.root/'wrong.sqlite').exists())

    def test_full_physical_return_without_refund_and_full_financial_refund(self):
        self.accepted()
        orders=v2.inspect(self.db,'orders')['rows'];mapped={r['order_id']:r for r in orders}
        self.assertEqual(mapped['SIM-O-000001']['posted_refund_cents'],900)
        self.assertEqual(mapped['SIM-O-000001']['committed_refund_cents'],1100)
        self.assertEqual(mapped['SIM-O-000001']['net_captured_cents'],2100)
        second=mapped['SIM-O-000002'];self.assertEqual(second['posted_refund_cents'],0);self.assertGreater(second['returned_units'],0)
        third=mapped['SIM-O-000005'];self.assertEqual(third['net_captured_cents'],0);self.assertEqual(third['returned_units'],0)
        with closing(sqlite3.connect(self.db)) as db:
            original=db.execute("SELECT SUM(quantity) FROM fact_item WHERE order_id='SIM-O-000002'").fetchone()[0]
            self.assertEqual(second['returned_units'],original)

    def test_partial_article_quantity_is_supported(self):
        items={ (r['order_id'],r['item_no']):r for r in self.rows('base/items')}
        target=next(r for r in self.rows('returns') if r['status']=='RECEIVED' and r['quantity']<items[(r['order_id'],r['item_no'])]['quantity'])
        self.accepted()
        found=next(r for r in v2.inspect(self.db,'items')['rows'] if (r['order_id'],r['item_no'])==(target['order_id'],target['item_no']))
        self.assertEqual(found['returned_units'],1)
        self.assertGreater(found['original_units'],found['returned_units'])

    def test_independent_refund_and_return_aggregation_no_fanout(self):
        self.accepted()
        refunds=self.rows('refunds');returns=self.rows('returns')
        expected=sum(r['amount_cents'] for r in refunds if r['status']=='COMPLETED')
        committed=sum(r['amount_cents'] for r in refunds if r['status'] in ('REQUESTED','COMPLETED'))
        units=sum(r['quantity'] for r in returns if r['status']=='RECEIVED')
        result=v2.inspect(self.db);self.assertEqual(result['posted_refund_cents'],expected);self.assertEqual(result['committed_refund_cents'],committed);self.assertEqual(result['returned_units'],units)
        self.assertEqual(result['net_captured_cents'],result['original_captured_cents']-expected)
        with closing(sqlite3.connect(self.db)) as db:
            good=db.execute("SELECT posted_refund_cents FROM order_adjustment_reconciliation WHERE order_id='SIM-O-000001'").fetchone()[0]
            bad=db.execute("SELECT SUM(r.posted_cents) FROM fact_item i JOIN fact_refund r ON r.order_id=i.order_id WHERE i.order_id='SIM-O-000001'").fetchone()[0]
            self.assertEqual(good,900);self.assertEqual(bad,2700)
            self.assertNotEqual(good,bad)

    def test_staging_integrity_keys_and_source_reconstruction(self):
        self.accepted()
        with closing(sqlite3.connect(self.db)) as db:
            db.execute('PRAGMA foreign_keys=ON')
            self.assertEqual(db.execute('PRAGMA integrity_check').fetchone(),('ok',));self.assertEqual(db.execute('PRAGMA foreign_key_check').fetchall(),[])
            for e,t in [('returns','fact_return'),('refunds','fact_refund')]:
                self.assertEqual(db.execute(f'SELECT COUNT(*) FROM {t}').fetchone()[0],len(self.rows(e)))
                text=''.join(t for (t,) in db.execute('SELECT raw_text FROM adjustment_staging WHERE entity=? ORDER BY source_line',(e,)))
                self.assertEqual(text.encode(),(self.source/(e+'.jsonl')).read_bytes())
            with self.assertRaises(sqlite3.IntegrityError):db.execute('INSERT INTO fact_refund SELECT * FROM fact_refund LIMIT 1')
            db.rollback()
            with self.assertRaises(sqlite3.IntegrityError):
                db.execute("INSERT INTO int_return VALUES ('SIM-R-999999','missing',1,1,'REQUESTED','2025-01-01T00:00:00Z',NULL,'USD','missing')")

    def test_idempotence_and_logical_rebuild(self):
        self.accepted();before=sha256(self.db)
        self.assertEqual(v2.build(self.source,self.db)['action'],'unchanged');self.assertEqual(sha256(self.db),before)
        other=self.root/'other.sqlite';v2.build(self.source,other)
        with closing(sqlite3.connect(self.db)) as a,closing(sqlite3.connect(other)) as b:
            self.assertEqual(list(a.iterdump()),list(b.iterdump()))

    def test_adverse_limits_are_rejected_not_partially_integrated(self):
        source=self.root/'bad';v2.generate(source,42,30,True)
        result=v2.build(source,self.db);self.assertEqual(result['status'],'REJECTED')
        rules=v2.inspect(self.db,'rejections')['rules'];self.assertTrue({'RETURN_LIMIT','REFUND_PAYMENT_LIMIT','REFUND_ORDER_LIMIT','REFUND_RETURN_LIMIT'}<=set(rules))
        summary=v2.inspect(self.db);self.assertEqual(summary['counts']['fact_return'],0);self.assertEqual(summary['posted_refund_cents'],0);self.assertEqual(summary['net_captured_cents'],summary['original_captured_cents'])

    def test_cumulative_return_limit(self):
        self.mutate('returns',lambda rows:rows.append(dict(rows[0],return_id='SIM-R-999990')))
        self.rejected('RETURN_LIMIT')

    def test_cumulative_refund_return_limit(self):
        self.mutate('refunds',lambda rows:rows.append(dict(rows[0],refund_id='SIM-F-999990',amount_cents=1)))
        self.rejected('REFUND_RETURN_LIMIT')

    def test_cumulative_payment_limit_and_pending_reservation(self):
        # 1000 committed against payment 1 (1500); goodwill 501 would oversubscribe it.
        self.mutate('refunds',lambda rows:rows.append(dict(rows[0],refund_id='SIM-F-999990',reason='GOODWILL',return_id=None,amount_cents=501)))
        self.rejected('REFUND_PAYMENT_LIMIT')

    def test_maximum_boundary_is_accepted(self):
        self.mutate('refunds',lambda rows:rows.append(dict(rows[0],refund_id='SIM-F-999990',reason='GOODWILL',return_id=None,amount_cents=500)))
        self.accepted()
        payment=next(r for r in v2.inspect(self.db,'payments')['rows'] if r['order_id']=='SIM-O-000001' and r['payment_no']==1)
        self.assertEqual(payment['available_refund_cents'],0)

    def test_failed_refunds_do_not_reduce_net_or_reserve(self):
        self.mutate('refunds',lambda rows:rows.extend(dict(rows[4],refund_id=f'SIM-F-{900000+i}') for i in range(10)))
        self.accepted();first=next(r for r in v2.inspect(self.db,'orders')['rows'] if r['order_id']=='SIM-O-000001')
        self.assertEqual(first['posted_refund_cents'],900);self.assertEqual(first['committed_refund_cents'],1100)

    def test_invalid_shapes_dates_currency_states_links_and_references(self):
        cases=[('returns',{'quantity':True},'INTEGER_RANGE'),('returns',{'quantity':0},'INTEGER_RANGE'),
               ('returns',{'currency':'EUR'},'CURRENCY'),('returns',{'status':'UNKNOWN'},'EVENT_STATUS'),
               ('returns',{'received_at':'2025-01-01T00:00:00Z'},'DATE_ORDER'),('returns',{'requested_at':'2020-01-01T00:00:00Z','received_at':'2020-01-02T00:00:00Z'},'BEFORE_ORDER'),
               ('returns',{'item_no':999},'ORPHAN_ITEM'),('refunds',{'payment_no':999},'ORPHAN_PAYMENT'),
               ('refunds',{'return_id':'SIM-R-999999'},'ORPHAN_RETURN'),('refunds',{'reason':'GOODWILL'},'RETURN_LINK'),
               ('refunds',{'completed_at':None},'DATE'),('refunds',{'amount_cents':-1},'INTEGER_RANGE'),
               ('refunds',{'requested_at':'2025-01-03T00:00:00Z'},'BEFORE_RECEIPT'),('refunds',{'extra':1},'FIELDS')]
        for entity,changes,rule in cases:
            with self.subTest(rule=rule,changes=changes):
                saved=(self.source/(entity+'.jsonl')).read_bytes();manifest=(self.source/'manifest.json').read_bytes()
                self.mutate(entity,lambda rows:rows[0].update(changes));self.rejected(rule)
                self.db.unlink();(self.source/(entity+'.jsonl')).write_bytes(saved);(self.source/'manifest.json').write_bytes(manifest)

    def test_return_refund_must_belong_to_same_order_and_received(self):
        rejected_return=next(r for r in self.rows('returns') if r['status']=='REJECTED')
        self.mutate('refunds',lambda rows:rows[0].update(return_id=rejected_return['return_id']))
        self.rejected('RETURN_ORDER_MISMATCH')
        self.assertIn('RETURN_NOT_RECEIVED',v2.inspect(self.db,'rejections')['rules'])

    def test_no_adjustments_preserves_all_original_payments(self):
        for entity in ('returns','refunds'):
            self.mutate(entity,lambda rows:rows.clear())
        self.accepted();result=v2.inspect(self.db)
        self.assertEqual(result['posted_refund_cents'],0)
        self.assertEqual(result['net_captured_cents'],result['original_captured_cents'])
        self.assertEqual(result['counts']['fact_return'],0)

    def test_refund_against_failed_payment_is_rejected(self):
        self.mutate('refunds',lambda rows:rows[0].update(order_id='SIM-O-000004',payment_no=1,reason='GOODWILL',return_id=None))
        self.rejected('PAYMENT_NOT_CAPTURED')

    def test_physical_return_requires_paid_order(self):
        self.mutate('returns',lambda rows:rows[0].update(order_id='SIM-O-000003'))
        self.rejected('ORDER_NOT_PAID')

    def test_duplicate_event_ids(self):
        for e in ('returns','refunds'):
            with self.subTest(entity=e):
                saved=(self.source/(e+'.jsonl')).read_bytes();manifest=(self.source/'manifest.json').read_bytes()
                self.mutate(e,lambda rows:rows.append(dict(rows[0])));self.rejected('DUPLICATE_EVENT')
                self.db.unlink();(self.source/(e+'.jsonl')).write_bytes(saved);(self.source/'manifest.json').write_bytes(manifest)

    def test_manifest_hash_and_counts_rejected(self):
        p=self.source/'refunds.jsonl';original=p.read_bytes();p.write_bytes(original+b'\n')
        with self.assertRaises(ValueError):v2.build(self.source,self.db)
        self.assertFalse(self.db.exists());p.write_bytes(original)
        m=json.loads((self.source/'manifest.json').read_text());m['files']['returns']['records']+=1
        (self.source/'manifest.json').write_text(encode(m),encoding='utf-8')
        with self.assertRaises(ValueError):v2.build(self.source,self.db)
        self.assertFalse(self.db.exists())

    def test_atomic_failure_and_publication_permission_denied(self):
        original=v2.integrate
        def fail(db,rows):original(db,rows);raise OSError('controlled failure after insert')
        with patch.object(v2,'integrate',side_effect=fail):
            with self.assertRaises(OSError):v2.build(self.source,self.db)
        self.assertFalse(self.db.exists());self.assertFalse(list(self.root.glob('.aurelia-*')))
        publish=v2.os.link
        def fail_final(source,destination,*args,**kwargs):
            if Path(destination)==self.db:
                raise PermissionError('controlled final v2 publication failure')
            return publish(source,destination,*args,**kwargs)
        with patch.object(v2.os,'link',side_effect=fail_final):
            with self.assertRaises(PermissionError):v2.build(self.source,self.db)
        self.assertFalse(self.db.exists())

    def test_existing_v2_tampering_rejected_without_overwrite(self):
        self.accepted()
        with closing(sqlite3.connect(self.db)) as db:db.execute('UPDATE fact_refund SET posted_cents=1');db.commit()
        before=sha256(self.db)
        with self.assertRaises(ValueError):v2.build(self.source,self.db)
        self.assertEqual(sha256(self.db),before)

    def test_cli_execution_and_codes(self):
        base=[sys.executable,'-B','-X','utf8','-m','src.aurelia.v2']
        def run(*args):return subprocess.run(base+list(args),cwd=ROOT,capture_output=True,text=True,encoding='utf-8')
        self.assertEqual(run('build','--input',str(self.source),'--database',str(self.db)).returncode,0)
        for query in ['summary','orders','items','payments','rejections']:
            self.assertEqual(run('query','--database',str(self.db),'--query',query).returncode,0)
        bad=self.root/'bad-cli';self.assertEqual(run('generate','--output',str(bad),'--adverse').returncode,0)
        r=run('build','--input',str(bad),'--database',str(self.root/'bad.sqlite'));self.assertEqual(r.returncode,1,r.stderr);self.assertEqual(json.loads(r.stdout)['status'],'REJECTED')
        self.assertEqual(run().returncode,2)


if __name__=='__main__':unittest.main()
