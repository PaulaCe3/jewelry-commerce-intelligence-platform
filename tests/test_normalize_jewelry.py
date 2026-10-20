import csv
from collections import Counter
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from normalize_jewelry import normalize, sha256, ROOT, AUDITED_SHA256


def csv_line(values):
    stream = io.StringIO(newline='')
    csv.writer(stream, lineterminator='\n').writerow(values)
    return stream.getvalue()


class NormalizationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.source = self.root / 'raw' / 'fixture.csv'
        self.source.parent.mkdir()
        self.output = self.root / 'processed' / 'run'

    def write(self, text):
        self.source.write_bytes(text.encode('utf-8'))

    def records(self, directory=None):
        return [json.loads(line) for line in ((directory or self.output) / 'records.jsonl').read_text(encoding='utf-8').splitlines()]

    def test_conservation_text_duplicates_and_traceability(self):
        long = ['0001', '9999999999999999999', '', '1', '', '', '0', '0.00', '001', '', '', '', '']
        short = ['x'] * 11
        self.write('\n' + csv_line(long) + csv_line(short) + csv_line(long))
        before = self.source.read_bytes()
        report = normalize(self.source, self.output)
        rows = self.records()
        self.assertEqual(len(rows), 3)
        self.assertEqual([r['source_line'] for r in rows], [2, 3, 4])
        self.assertEqual(len({r['row_id'] for r in rows}), 3)
        self.assertEqual(rows[0]['original_fields'], long)
        self.assertEqual(rows[0]['original_fields'], rows[2]['original_fields'])
        self.assertEqual(rows[0]['row_id'], f'{sha256(self.source)}:2')
        self.assertEqual(report['field_count_distribution'], {'13': 2, '11': 1})
        self.assertEqual(report['duplicate_excess_records'], 1)
        self.assertEqual(report['duplicate_involved_records'], 2)
        self.assertEqual(report['source_sha256_before'], report['source_sha256_after'])
        self.assertEqual(self.source.read_bytes(), before)

    def test_alignment_is_only_positional_for_13_and_never_for_11(self):
        long = [f'position {i}' for i in range(1, 14)]
        short = ['a', 'b', 'c', '1', '', '0.00', '0001', '', '', '', '']
        self.write(csv_line(long) + csv_line(short))
        report = normalize(self.source, self.output)
        a, b = self.records()
        self.assertEqual(a['positional_fields_13'], {f'field_{i:02d}': value for i, value in enumerate(long, 1)})
        self.assertIsNone(b['positional_fields_13'])
        self.assertEqual(b['original_fields'], short)
        self.assertEqual(b['validation_status'], 'pending_schema_11')
        self.assertEqual(report['pending_schema_records'], 1)

    def test_invalid_width_and_csv_are_preserved(self):
        self.write('a,b\n"closed"extra,x\n' + csv_line(['ok'] * 13))
        report = normalize(self.source, self.output)
        rows = self.records()
        self.assertEqual([r['validation_status'] for r in rows], ['invalid_field_count', 'invalid_csv', 'structural_13_semantics_unverified'])
        self.assertEqual(rows[0]['original_fields'], ['a', 'b'])
        self.assertIsNone(rows[1]['original_fields'])
        self.assertEqual(rows[1]['raw_text'], '"closed"extra,x')
        self.assertEqual(report['invalid_records'], 2)

    def test_bytes_reconstruct_with_blanks_crlf_unicode_and_no_final_newline(self):
        self.write('\r\n' + csv_line(['á,ñ', '"', ''] + ['x'] * 10).replace('\n', '\r\n') + '\nend')
        report = normalize(self.source, self.output)
        lines = {r['source_line']: (r['raw_text'] + r['line_ending']).encode('utf-8') for r in self.records()}
        lines.update({r['source_line']: r['line_ending'].encode() for r in report['blank_lines']})
        self.assertEqual(b''.join(lines[n] for n in sorted(lines)), self.source.read_bytes())

    def test_reproducible_output_in_independent_directories(self):
        self.write(csv_line([''] * 13) + csv_line(['0'] * 11))
        other = self.root / 'processed' / 'second'
        normalize(self.source, self.output)
        normalize(self.source, other)
        for name in ['records.jsonl', 'quality.json']:
            self.assertEqual((self.output / name).read_bytes(), (other / name).read_bytes())

    def test_existing_destination_never_overwritten(self):
        self.write(csv_line(['x'] * 13))
        self.output.mkdir(parents=True)
        marker = self.output / 'records.jsonl'
        marker.write_text('keep', encoding='utf-8')
        with self.assertRaises(FileExistsError):
            normalize(self.source, self.output)
        self.assertEqual(marker.read_text(), 'keep')

    def test_destination_cannot_write_to_source_directory(self):
        self.write('x')
        with self.assertRaises(ValueError):
            normalize(self.source, self.source.parent / 'run')

    def test_unknown_encoding_fails_without_complete_report(self):
        self.source.write_bytes(b'\xff\n')
        with self.assertRaises(UnicodeDecodeError):
            normalize(self.source, self.output)
        self.assertFalse((self.output / 'quality.json').exists())

    def test_changed_source_hash_fails_without_complete_report(self):
        self.write(csv_line(['x'] * 13))
        with patch('normalize_jewelry.sha256', side_effect=['a' * 64, 'b' * 64]):
            with self.assertRaises(RuntimeError):
                normalize(self.source, self.output)
        self.assertFalse((self.output / 'quality.json').exists())

    def test_audit_guard_rejects_other_input_before_writing(self):
        self.write(csv_line(['x'] * 13))
        with self.assertRaises(ValueError):
            normalize(self.source, self.output, check_audit=True)
        self.assertFalse(self.output.exists())

    def test_empty_file_is_explicitly_empty(self):
        self.write('')
        report = normalize(self.source, self.output)
        self.assertEqual(report['records_written'], 0)
        self.assertEqual(report['physical_lines'], 0)
        self.assertEqual(self.records(), [])

    def test_multiline_csv_rejected_without_complete_report(self):
        self.write('"first\nsecond",x\n')
        before = self.source.read_bytes()
        with self.assertRaises(ValueError):
            normalize(self.source, self.output)
        self.assertFalse((self.output / 'quality.json').exists())
        self.assertEqual(self.source.read_bytes(), before)


class LocalDatasetIntegrationTests(unittest.TestCase):
    def test_audited_dataset_conservation_and_reproducibility(self):
        source = ROOT / 'data/raw/jewelry.csv'
        self.assertTrue(source.is_file(), 'Integración obligatoria: falta data/raw/jewelry.csv; no se aprueba la suite completa.')
        with tempfile.TemporaryDirectory() as temporary:
            first, second = Path(temporary) / 'first', Path(temporary) / 'second'
            report = normalize(source, first, check_audit=True)
            normalize(source, second, check_audit=True)
            for name in ['records.jsonl', 'quality.json']:
                self.assertEqual(sha256(first / name), sha256(second / name))
            self.assertEqual(report['records_written'], 95911)
            self.assertEqual(report['field_count_distribution'], {'13': 90559, '11': 5352})
            self.assertEqual(report['duplicate_excess_records'], 2589)
            self.assertEqual(report['duplicate_groups'], 2298)
            self.assertEqual(report['pending_schema_records'], 5352)
            self.assertEqual(report['invalid_records'], 0)
            self.assertEqual(sha256(source), AUDITED_SHA256)
            ids, contents, count = set(), Counter(), 0
            blank = {r['source_line']: r['line_ending'] for r in report['blank_lines']}
            with source.open('rb') as original, (first / 'records.jsonl').open(encoding='utf-8') as result:
                for line_number, binary in enumerate(original, 1):
                    if line_number in blank:
                        self.assertEqual(binary, blank[line_number].encode())
                        continue
                    row = json.loads(next(result))
                    self.assertEqual(row['source_line'], line_number)
                    self.assertEqual((row['raw_text'] + row['line_ending']).encode('utf-8'), binary)
                    self.assertEqual(row['original_fields'], next(csv.reader([binary.decode('utf-8')], strict=True)))
                    self.assertNotIn(row['row_id'], ids)
                    ids.add(row['row_id'])
                    contents[row['raw_text']] += 1
                    if row['original_field_count'] == 11:
                        self.assertIsNone(row['positional_fields_13'])
                    count += 1
                self.assertEqual(result.read(), '')
            self.assertEqual(count, 95911)
            self.assertEqual(sum(v - 1 for v in contents.values()), 2589)


if __name__ == '__main__':
    unittest.main()
