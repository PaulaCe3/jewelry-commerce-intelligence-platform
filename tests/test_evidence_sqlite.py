"""Fixtures de software temporales; nunca resultados comerciales."""
from collections import Counter
from contextlib import contextmanager
import csv
import hashlib
import io
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
import evidence_sqlite as evidence
from normalize_jewelry import normalize


@contextmanager
def database_connection(path):
    connection = sqlite3.connect(path)
    try:
        with connection:
            yield connection
    finally:
        connection.close()


class EvidenceUnitTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / 'raw').mkdir()
        self.source = self.root / 'raw/input.csv'
        values = ['001', 'comma,value', '"quoted"', '', ' ', '0', 'a', 'b', 'c', '', '', '', 'é']
        stream = io.StringIO(newline='')
        csv.writer(stream, lineterminator='\r\n').writerow(values)
        long = stream.getvalue()
        self.source.write_bytes(('\n' + long + ','.join(['x', 'y', 'z', '1', '', '0.00', 'u', '', '', '', '']) + '\n' + long + 'bad,width').encode('utf-8'))
        self.directory = self.root / 'v1'
        normalize(self.source, self.directory)
        self.records = self.directory / 'records.jsonl'
        self.quality = self.directory / 'quality.json'
        self.database = self.root / 'evidence.sqlite'

    def load(self, database=None):
        return evidence.load(self.records, self.quality, database or self.database)

    def report(self):
        return json.loads(self.quality.read_text(encoding='utf-8'))

    def mutate_report(self, key, value):
        report = self.report()
        report[key] = value
        self.quality.write_text(json.dumps(report), encoding='utf-8')

    def mutate_rows(self, transform, update_hash=True):
        rows = [json.loads(line) for line in self.records.read_text(encoding='utf-8').splitlines()]
        transform(rows)
        self.records.write_text(''.join(json.dumps(row, ensure_ascii=False) + '\n' for row in rows), encoding='utf-8')
        if update_hash:
            self.mutate_report('output_sha256', hashlib.sha256(self.records.read_bytes()).hexdigest())

    def assert_rejected(self):
        with self.assertRaises((ValueError, OSError, sqlite3.Error)):
            self.load()
        self.assertFalse(self.database.exists())
        self.assertFalse(list(self.root.glob('.evidence-*')))

    def test_schema_referential_integrity_and_unique_ids(self):
        self.load()
        with database_connection(self.database) as db:
            db.execute('PRAGMA foreign_keys=ON')
            self.assertEqual(db.execute('PRAGMA foreign_key_check').fetchall(), [])
            self.assertEqual(db.execute('PRAGMA integrity_check').fetchone(), ('ok',))
            self.assertEqual(db.execute('SELECT count(*),count(distinct row_id) FROM occurrence').fetchone(), (4, 4))
            with self.assertRaises(sqlite3.IntegrityError):
                db.execute("INSERT INTO original_field VALUES ('missing',1,'')")
            with self.assertRaises(sqlite3.IntegrityError):
                db.execute('INSERT INTO occurrence SELECT * FROM occurrence LIMIT 1')

    def test_exact_reconstruction_fields_empty_order_and_raw(self):
        before = self.source.read_bytes()
        self.load()
        rows = [json.loads(line) for line in self.records.read_text(encoding='utf-8').splitlines()]
        for row in rows:
            self.assertEqual(evidence.inspect_database(self.database, 'record', row['row_id']), row)
        with database_connection(self.database) as db:
            reconstructed = dict(db.execute('SELECT source_line,raw_text||line_ending FROM occurrence'))
            reconstructed.update(db.execute('SELECT source_line,line_ending FROM blank_line'))
        self.assertEqual(''.join(reconstructed[i] for i in sorted(reconstructed)).encode('utf-8'), before)
        self.assertEqual(self.source.read_bytes(), before)

    def test_quality_all_properties_preserved(self):
        self.load()
        self.assertEqual(evidence.inspect_database(self.database, 'quality'), self.report())

    def test_multiplicity_and_no_short_alignment(self):
        self.load()
        self.assertEqual(evidence.inspect_database(self.database, 'multiplicity'),
                         {'duplicate_groups': 1, 'duplicate_excess_records': 1, 'duplicate_involved_records': 2})
        with database_connection(self.database) as db:
            row_id = db.execute('SELECT row_id FROM occurrence WHERE original_field_count=11').fetchone()[0]
        short = evidence.inspect_database(self.database, 'record', row_id)
        self.assertEqual(len(short['original_fields']), 11)
        self.assertIsNone(short['positional_fields_13'])

    def test_idempotence_no_database_byte_changes(self):
        self.assertEqual(self.load()['status'], 'created')
        before = self.database.read_bytes()
        self.assertEqual(self.load()['status'], 'unchanged')
        self.assertEqual(self.database.read_bytes(), before)

    def test_logical_equality_between_independent_loads(self):
        self.load()
        other = self.root / 'other.sqlite'
        self.load(other)
        with database_connection(self.database) as a, database_connection(other) as b:
            self.assertEqual(list(a.iterdump()), list(b.iterdump()))

    def test_missing_report(self):
        self.quality.unlink()
        self.assert_rejected()

    def test_report_version_incomplete_and_all_metadata_mutations(self):
        original = self.quality.read_bytes()
        report = self.report()
        for key, value in report.items():
            with self.subTest(key=key):
                self.quality.write_bytes(original)
                self.mutate_report(key, 'tampered' if type(value) is not str else value + 'tampered')
                self.assert_rejected()

    def test_bad_records_hash(self):
        self.records.write_bytes(self.records.read_bytes() + b'\n')
        self.assert_rejected()

    def test_field_mutation_detected_even_with_updated_records_hash(self):
        self.mutate_rows(lambda rows: rows[0]['original_fields'].__setitem__(0, 'changed'))
        self.assert_rejected()

    def test_coherent_raw_mutation_detected_by_source_hash(self):
        def change(rows):
            row = rows[0]
            row['raw_text'] = row['raw_text'].replace('001', '002')
            row['original_fields'][0] = '002'
            row['positional_fields_13']['field_01'] = '002'
        self.mutate_rows(change)
        self.assert_rejected()

    def test_missing_duplicate_and_reordered_rows(self):
        original_records, original_report = self.records.read_bytes(), self.quality.read_bytes()
        for change in [lambda rows: rows.pop(), lambda rows: rows.append(rows[0]), lambda rows: rows.reverse()]:
            with self.subTest(change=change):
                self.records.write_bytes(original_records)
                self.quality.write_bytes(original_report)
                self.mutate_rows(change)
                self.assert_rejected()

    def test_duplicate_json_keys_rejected(self):
        self.quality.write_text('{"pipeline_version":"1","pipeline_version":"1"}', encoding='utf-8')
        self.assert_rejected()

    def test_invalid_record_csv_and_unexpected_width_preserved(self):
        # v1 conserva CSV parseable con anchura inesperada e invalid_csv recuperable.
        other = self.root / 'raw/malformed.csv'
        other.write_text('"a"x,b\n', encoding='utf-8')
        normalize(other, self.root / 'malformed-v1')
        evidence.load(self.root / 'malformed-v1/records.jsonl', self.root / 'malformed-v1/quality.json', self.database)
        row = json.loads((self.root / 'malformed-v1/records.jsonl').read_text(encoding='utf-8'))
        self.assertEqual(evidence.inspect_database(self.database, 'record', row['row_id']), row)

    def test_summary_supports_mixed_parseable_and_invalid_csv(self):
        source = self.root / 'raw/mixed.csv'
        source.write_bytes(b'"a"x,b\na,b\n')
        directory = self.root / 'mixed-v1'
        normalize(source, directory)
        evidence.load(directory / 'records.jsonl', directory / 'quality.json', self.database)
        summary = evidence.inspect_database(self.database)
        self.assertEqual(summary['widths'], {'unparseable': 1, '2': 1})
        self.assertEqual(json.loads(evidence.canonical(summary)), summary)

    def test_transaction_write_failure_leaves_no_destination(self):
        populate = evidence._populate
        def fail(db, *args):
            populate(db, *args)
            raise OSError('simulated disk failure before acceptance')
        with patch.object(evidence, '_populate', side_effect=fail):
            self.assert_rejected()

    def test_failure_after_first_record_rolls_back_partial_load(self):
        validate = evidence._validate_record
        calls = 0
        def fail(*args):
            nonlocal calls
            calls += 1
            if calls == 2:
                raise OSError('simulated failure after first insert')
            return validate(*args)
        with patch.object(evidence, '_validate_record', side_effect=fail):
            self.assert_rejected()
        self.assertEqual(calls, 2)

    def test_read_permission_failure_is_closed(self):
        with patch.object(evidence, 'digest', side_effect=PermissionError('simulated')):
            self.assert_rejected()

    def test_empty_and_only_blank_source(self):
        for index, text in enumerate(['', '\n\r\n']):
            with self.subTest(text=text):
                source = self.root / 'raw' / f'empty{index}.csv'
                source.write_bytes(text.encode('utf-8'))
                output = self.root / f'empty{index}-v1'
                normalize(source, output)
                database = self.root / f'empty{index}.db'
                evidence.load(output / 'records.jsonl', output / 'quality.json', database)
                self.assertEqual(evidence.inspect_database(database)['occurrences'], 0)

    def test_publication_failure_leaves_no_destination(self):
        with patch.object(evidence.os, 'link', side_effect=PermissionError('simulated')):
            self.assert_rejected()

    def test_failed_repeat_preserves_existing_database(self):
        self.load()
        before = self.database.read_bytes()
        self.mutate_report('records_written', 999)
        with self.assertRaises(ValueError):
            self.load()
        self.assertEqual(self.database.read_bytes(), before)

    def test_database_tampering_detected_without_overwrite(self):
        self.load()
        with database_connection(self.database) as db:
            db.execute("UPDATE original_field SET value='tampered' WHERE position=1")
        before = self.database.read_bytes()
        with self.assertRaises(ValueError):
            self.load()
        self.assertEqual(self.database.read_bytes(), before)

    def test_unrelated_existing_file_untouched(self):
        self.database.write_bytes(b'not sqlite')
        with self.assertRaises(sqlite3.DatabaseError):
            self.load()
        self.assertEqual(self.database.read_bytes(), b'not sqlite')

    def test_input_output_collision_and_protected_destination(self):
        for target in [self.records, ROOT / 'data/raw/forbidden.sqlite', ROOT / 'data/processed/forbidden.sqlite']:
            with self.subTest(target=target), self.assertRaises(ValueError):
                self.load(target)

    def test_inputs_changed_during_load_rejected(self):
        populate = evidence._populate
        def change(db, *args):
            populate(db, *args)
            self.quality.write_bytes(self.quality.read_bytes() + b' ')
        with patch.object(evidence, '_populate', side_effect=change):
            self.assert_rejected()

    def test_cli_success_queries_idempotence_and_exit_codes(self):
        base = [sys.executable, '-B', '-X', 'utf8', str(ROOT / 'src/evidence_sqlite.py')]
        load = base + ['load', '--records', str(self.records), '--quality', str(self.quality), '--database', str(self.database)]
        for state in ['created', 'unchanged']:
            run = subprocess.run(load, capture_output=True, text=True, encoding='utf-8')
            self.assertEqual(run.returncode, 0, run.stderr)
            self.assertEqual(json.loads(run.stdout)['status'], state)
        for query in ['summary', 'quality', 'multiplicity']:
            run = subprocess.run(base + ['query', '--database', str(self.database), '--query', query], capture_output=True)
            self.assertEqual(run.returncode, 0, run.stderr)
        for args, expected in [([], 2), (['load'], 2), (['query', '--database', str(self.root / 'missing.db')], 1),
                               (['query', '--database', str(self.database), '--query', 'record', '--row-id', 'missing'], 1)]:
            self.assertEqual(subprocess.run(base + args, capture_output=True).returncode, expected)


class EvidenceRealIntegrationTests(unittest.TestCase):
    def test_official_files_full_roundtrip_and_reproducibility(self):
        directory = ROOT / 'data/processed/normalization-v1'
        records, quality = directory / 'records.jsonl', directory / 'quality.json'
        self.assertTrue(records.is_file() and quality.is_file(), 'Integración exige archivos oficiales locales; no se omite.')
        protected = [ROOT / 'data/raw/jewelry.csv', records, quality, ROOT / 'src/normalize_jewelry.py']
        before = {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in protected}
        with tempfile.TemporaryDirectory() as folder:
            a, b = Path(folder) / 'a.sqlite', Path(folder) / 'b.sqlite'
            evidence.load(records, quality, a)
            evidence.load(records, quality, b)
            self.assertEqual(evidence.load(records, quality, a)['status'], 'unchanged')
            # Oráculo SQL/JSON independiente, sin usar consultas/helpers del cargador.
            with database_connection(a) as db, database_connection(b) as other:
                self.assertEqual(db.execute('SELECT COUNT(*) FROM occurrence').fetchone(), (95911,))
                self.assertEqual(dict(db.execute('SELECT original_field_count,COUNT(*) FROM occurrence GROUP BY original_field_count')), {11: 5352, 13: 90559})
                self.assertEqual(db.execute('SELECT SUM(n-1) FROM (SELECT COUNT(*) n FROM occurrence GROUP BY raw_text)').fetchone(), (2589,))
                self.assertEqual(db.execute('SELECT COUNT(*) FROM original_field').fetchone(), (1236139,))
                with records.open(encoding='utf-8') as incoming:
                    for text, row in zip(incoming, db.execute('SELECT row_id,source_line,original_field_count,validation_status,raw_text,line_ending FROM occurrence ORDER BY source_line'), strict=True):
                        expected = json.loads(text)
                        self.assertEqual(tuple(expected[k] for k in ['row_id','source_line','original_field_count','validation_status','raw_text','line_ending']), row)
                        fields = [v for (v,) in db.execute('SELECT value FROM original_field WHERE row_id=? ORDER BY position', (row[0],))]
                        self.assertEqual(fields, expected['original_fields'])
                self.assertEqual({k: json.loads(v) for k,v in db.execute('SELECT property,value_json FROM quality_result')}, json.loads(quality.read_text(encoding='utf-8')))
                for table, order in [('source_file','source_sha256'),('import_manifest','schema_version'),('occurrence','source_line'),('original_field','row_id,position'),('blank_line','source_line'),('quality_result','property')]:
                    for x,y in zip(db.execute(f'SELECT * FROM {table} ORDER BY {order}'), other.execute(f'SELECT * FROM {table} ORDER BY {order}'), strict=True):
                        self.assertEqual(x,y)
                self.assertEqual(db.execute('PRAGMA integrity_check').fetchone(), ('ok',))
                self.assertEqual(db.execute('PRAGMA foreign_key_check').fetchall(), [])
        self.assertEqual(before, {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in protected})


if __name__ == '__main__':
    unittest.main()
