import errno
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
import normalize_jewelry as pipeline
from independent_checks import validate_output, digest_file
from test_normalize_jewelry import csv_line


class QAUnitTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='plathel-qa-unit-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / 'input' / 'fixture.csv'
        self.source.parent.mkdir()
        self.output = self.root / 'out'
        self.source.write_text('\n' + csv_line(['000', 'ñ,"'] + ['x']*11)*2 + csv_line(['']*11), encoding='utf-8', newline='')

    def test_all_report_fields_independently_verified(self):
        pipeline.normalize(self.source, self.output)
        validate_output(self.source, self.output, audit_checked=False)

    def test_each_report_field_mutation_is_detected(self):
        pipeline.normalize(self.source, self.output)
        path = self.output / 'quality.json'
        original = json.loads(path.read_text(encoding='utf-8'))
        for key, value in original.items():
            with self.subTest(field=key):
                changed = dict(original)
                changed[key] = (not value if isinstance(value, bool) else value+1 if isinstance(value,int)
                                else 'MUTATED')
                path.write_text(json.dumps(changed), encoding='utf-8')
                with self.assertRaises(AssertionError):
                    validate_output(self.source, self.output, audit_checked=False)
        path.write_text(json.dumps(original), encoding='utf-8')
        validate_output(self.source, self.output, audit_checked=False)

    def test_each_record_field_mutation_is_detected_even_with_updated_output_hash(self):
        pipeline.normalize(self.source, self.output)
        path = self.output / 'records.jsonl'
        original = path.read_text(encoding='utf-8').splitlines()
        row = json.loads(original[0])
        report_path = self.output / 'quality.json'
        report = json.loads(report_path.read_text(encoding='utf-8'))
        for key in row:
            with self.subTest(field=key):
                changed = dict(row)
                changed[key] = 'MUTATED'
                path.write_text('\n'.join([json.dumps(changed)] + original[1:])+'\n', encoding='utf-8')
                report['output_sha256'] = digest_file(path)
                report_path.write_text(json.dumps(report), encoding='utf-8')
                with self.assertRaises(AssertionError):
                    validate_output(self.source, self.output, audit_checked=False)

    def test_missing_extra_reordered_and_deduplicated_rows_are_detected(self):
        pipeline.normalize(self.source, self.output)
        path = self.output / 'records.jsonl'
        lines = path.read_text(encoding='utf-8').splitlines()
        for mutated in [lines[1:], lines+lines[:1], list(reversed(lines)), [lines[0], lines[-1]]]:
            with self.subTest(size=len(mutated)):
                path.write_text('\n'.join(mutated)+'\n', encoding='utf-8')
                with self.assertRaises(AssertionError):
                    validate_output(self.source, self.output, audit_checked=False)

    def test_bom_and_isolated_cr_rejected_without_changing_source(self):
        for index, binary in enumerate([b'\xef\xbb\xbf'+b'x,'*12+b'x\n', b'x\ry\n', b'x\r']):
            with self.subTest(binary=index):
                self.source.write_bytes(binary)
                dest = self.root / f'bad-{index}'
                with self.assertRaises(ValueError):
                    pipeline.normalize(self.source, dest)
                self.assertFalse((dest/'quality.json').exists())
                self.assertEqual(self.source.read_bytes(), binary)

    def test_quoted_commas_escaped_quotes_and_mixed_supported_endings(self):
        self.source.write_bytes((csv_line(['a,b', '"quoted"', '  x  ']+['']*10).replace('\n','\r\n') +
                                 '\n'+csv_line(['']*11).rstrip('\n')).encode())
        pipeline.normalize(self.source, self.output)
        validate_output(self.source, self.output, audit_checked=False)

    def test_long_field_boundary_and_global_csv_limit_restored(self):
        import csv
        previous = csv.field_size_limit()
        for length in [131072, 131073]:
            with self.subTest(length=length):
                self.source.write_text(csv_line(['x'*length]+['']*12), encoding='utf-8')
                destination = self.root / f'long-{length}'
                if length == 131072:
                    pipeline.normalize(self.source, destination)
                    validate_output(self.source, destination, audit_checked=False)
                else:
                    with self.assertRaises(ValueError):
                        pipeline.normalize(self.source, destination)
                    self.assertFalse((destination/'quality.json').exists())
                self.assertEqual(csv.field_size_limit(), previous)

    def test_multiline_with_plausible_13_field_continuation_is_rejected(self):
        self.source.write_text('"start\n' + csv_line(['end"']+['x']*12), encoding='utf-8')
        with self.assertRaises(ValueError):
            pipeline.normalize(self.source, self.output)
        self.assertFalse((self.output/'quality.json').exists())

    def test_unexpected_widths_are_preserved_and_counted(self):
        self.source.write_text(''.join(csv_line(['x']*n) for n in [1,2,10,12,14,20]), encoding='utf-8')
        pipeline.normalize(self.source, self.output)
        report = validate_output(self.source, self.output, audit_checked=False)
        self.assertEqual(report['invalid_records'], 6)
        self.assertEqual(report['records_written'], 6)

    def test_source_and_destination_permission_failures(self):
        original_open = Path.open
        def deny_read(path, *args, **kwargs):
            if path == self.source:
                raise PermissionError(errno.EACCES, 'simulated read denied')
            return original_open(path, *args, **kwargs)
        with patch.object(Path, 'open', deny_read):
            with self.assertRaises(PermissionError):
                pipeline.normalize(self.source, self.output)
        with patch.object(Path, 'mkdir', side_effect=PermissionError(errno.EACCES, 'simulated mkdir denied')):
            with self.assertRaises(PermissionError):
                pipeline.normalize(self.source, self.output)
        self.assertFalse(self.output.exists())

    def test_partial_record_and_report_writes_never_publish_complete_marker(self):
        original_open = Path.open
        for index, target in enumerate(['records.jsonl', '.quality.json.partial']):
            destination = self.root / f'fault-{index}'
            class PartialWriter:
                def __init__(self, stream): self.stream = stream
                def __enter__(self): return self
                def __exit__(self, *args): return self.stream.__exit__(*args)
                def write(self, value):
                    self.stream.write(value[:len(value)//2])
                    raise OSError(errno.ENOSPC, 'simulated disk full after partial write')
            def fail_write(path, *args, **kwargs):
                stream = original_open(path, *args, **kwargs)
                return PartialWriter(stream) if path.name == target and args and args[0] == 'x' else stream
            before = digest_file(self.source)
            with self.subTest(target=target), patch.object(Path, 'open', fail_write):
                with self.assertRaises(OSError):
                    pipeline.normalize(self.source, destination)
            self.assertFalse((destination/'quality.json').exists())
            self.assertEqual(digest_file(self.source), before)
            self.assertTrue(any(destination.iterdir()))
            with self.assertRaises(FileExistsError):
                pipeline.normalize(self.source, destination)

    def test_report_fsync_and_publication_failures_do_not_publish_marker(self):
        for index, attribute in enumerate(['fsync', 'link']):
            destination = self.root / f'publication-{index}'
            with self.subTest(stage=attribute), patch.object(pipeline.os, attribute, side_effect=OSError(errno.EIO,'simulated I/O failure')):
                with self.assertRaises(OSError):
                    pipeline.normalize(self.source, destination)
            self.assertFalse((destination/'quality.json').exists())

    def test_report_flush_and_record_close_failures_do_not_publish_marker(self):
        original_open = Path.open
        for index, stage in enumerate(['flush', 'close']):
            destination = self.root / f'buffered-{index}'
            target = '.quality.json.partial' if stage == 'flush' else 'records.jsonl'
            class BufferedFailure:
                def __init__(self, stream): self.stream = stream
                def __enter__(self): return self
                def __getattr__(self, name): return getattr(self.stream, name)
                def flush(self): raise OSError(errno.EIO, 'simulated flush error')
                def __exit__(self, *args):
                    self.stream.__exit__(*args)
                    if stage == 'close': raise OSError(errno.EIO, 'simulated close error')
            def fail_buffer(path, *args, **kwargs):
                stream = original_open(path, *args, **kwargs)
                return BufferedFailure(stream) if path.name == target and args and args[0] == 'x' else stream
            with self.subTest(stage=stage), patch.object(Path, 'open', fail_buffer):
                with self.assertRaises(OSError):
                    pipeline.normalize(self.source, destination)
            self.assertFalse((destination/'quality.json').exists())

    def test_actual_fixture_change_during_run_is_detected(self):
        original_encode = pipeline.encode_json
        mutated = False
        def mutate_fixture(value):
            nonlocal mutated
            if not mutated:
                with self.source.open('ab') as stream: stream.write(b'changed\n')
                mutated = True
            return original_encode(value)
        with patch.object(pipeline, 'encode_json', mutate_fixture):
            with self.assertRaisesRegex(RuntimeError, 'original cambi'):
                pipeline.normalize(self.source, self.output)
        self.assertFalse((self.output/'quality.json').exists())

    def test_audit_count_guard_cannot_accept_wrong_counts(self):
        with patch.object(pipeline, 'AUDITED_SHA256', digest_file(self.source)):
            with self.assertRaisesRegex(RuntimeError, 'conteos auditados'):
                pipeline.normalize(self.source, self.output, check_audit=True)
        self.assertFalse((self.output/'quality.json').exists())

    def test_report_publication_is_exclusive(self):
        original_link = pipeline.os.link
        def collision(src, dst):
            Path(dst).write_text('external marker', encoding='utf-8')
            return original_link(src, dst)
        with patch.object(pipeline.os, 'link', collision):
            with self.assertRaises(FileExistsError):
                pipeline.normalize(self.source, self.output)
        self.assertEqual((self.output/'quality.json').read_text(), 'external marker')

    def test_integration_missing_dataset_is_failure_not_skip(self):
        import test_normalize_jewelry as original
        result = unittest.TestResult()
        with patch.object(original, 'ROOT', self.root):
            original.LocalDatasetIntegrationTests('test_audited_dataset_conservation_and_reproducibility').run(result)
        self.assertEqual(len(result.failures), 1)
        self.assertEqual(result.skipped, [])


if __name__ == '__main__':
    unittest.main()
