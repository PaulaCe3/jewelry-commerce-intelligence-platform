import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

from independent_checks import validate_output, digest_file
from test_normalize_jewelry import csv_line

PROJECT = Path(__file__).resolve().parents[1]


class CLIIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='plathel-cli-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root/'src').mkdir()
        (self.root/'data/raw').mkdir(parents=True)
        (self.root/'data/processed').mkdir()
        self.script = self.root/'src/normalize_jewelry.py'
        shutil.copyfile(PROJECT/'src/normalize_jewelry.py', self.script)
        self.source = self.root/'data/raw/jewelry.csv'
        self.source.write_text('\n'+csv_line(['000']*13)*2+csv_line(['']*11), encoding='utf-8')
        self.output = self.root/'data/processed/run'

    def cli(self, *args):
        return subprocess.run([sys.executable,'-X','utf8','-B',str(self.script),*map(str,args)], cwd=self.root,
                              capture_output=True, text=True, encoding='utf-8', timeout=120)

    def test_success_exit_stdout_report_and_source_protection(self):
        before = digest_file(self.source)
        result = self.cli('--output-dir',self.output)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual(result.stderr,'')
        report = validate_output(self.source,self.output,audit_checked=False)
        self.assertEqual(json.loads(result.stdout),report)
        self.assertEqual(digest_file(self.source),before)

    def test_missing_unknown_and_invalid_path_arguments_exit_2(self):
        for args in [[],['--unknown'],['--output-dir'],['--output-dir',self.root/'outside'],
                     ['--output-dir',self.source.parent/'child'],['--output-dir',self.source]]:
            with self.subTest(args=list(map(str,args))):
                result=self.cli(*args)
                self.assertEqual(result.returncode,2)
                self.assertIn('error:',result.stderr)
                self.assertEqual(result.stdout,'')
        self.assertTrue(self.source.is_file())

    def test_help_exit_0_without_writing(self):
        result=self.cli('--help')
        self.assertEqual(result.returncode,0)
        self.assertIn('--check-audit',result.stdout)
        self.assertFalse(self.output.exists())

    def test_existing_destination_exit_1_and_unchanged(self):
        self.output.mkdir()
        marker=self.output/'records.jsonl'
        marker.write_bytes(b'keep')
        result=self.cli('--output-dir',self.output)
        self.assertEqual(result.returncode,1)
        self.assertIn('Error:',result.stderr)
        self.assertEqual(marker.read_bytes(),b'keep')

    def test_audit_hash_rejection_exit_1_without_output(self):
        result=self.cli('--check-audit','--output-dir',self.output)
        self.assertEqual(result.returncode,1)
        self.assertIn('SHA-256',result.stderr)
        self.assertFalse(self.output.exists())

    def test_missing_source_exit_1_without_output(self):
        self.source.unlink()  # Only this test's synthetic fixture.
        result=self.cli('--output-dir',self.output)
        self.assertEqual(result.returncode,1)
        self.assertFalse(self.output.exists())

    def test_unsupported_format_exit_1_and_partial_not_reusable(self):
        self.source.write_bytes(b'\xef\xbb\xbfx\n')
        before=digest_file(self.source)
        result=self.cli('--output-dir',self.output)
        self.assertEqual(result.returncode,1)
        self.assertFalse((self.output/'quality.json').exists())
        self.assertEqual(digest_file(self.source),before)
        self.assertEqual(self.cli('--output-dir',self.output).returncode,1)

    def test_simulated_permission_and_publish_failure_exit_1(self):
        for index, mode in enumerate(['deny','publish']):
            dest=self.root/f'data/processed/fail-{index}'
            # Injection only in a fresh subprocess; official source is untouched.
            program = (
                'import sys; from pathlib import Path; from unittest.mock import patch; '
                f'sys.path.insert(0,{str(self.root/"src")!r}); import normalize_jewelry as m; '
                f'sys.argv=["normalize_jewelry.py","--output-dir",{str(dest)!r}]; '
                + ('\nwith patch.object(Path,"mkdir",side_effect=PermissionError("simulated denied")): m.main()'
                   if mode=='deny' else '\nwith patch.object(m.os,"link",side_effect=OSError("simulated publication failure")): m.main()')
            )
            result=subprocess.run([sys.executable,'-X','utf8','-B','-c',program],cwd=self.root,
                                  capture_output=True,text=True,encoding='utf-8',timeout=120)
            self.assertEqual(result.returncode,1,result.stderr)
            self.assertIn('Error:',result.stderr)
            self.assertNotIn('Traceback',result.stderr)
            self.assertFalse((dest/'quality.json').exists())

    def test_real_dataset_cli_twice_matches_official_and_all_metadata(self):
        real=PROJECT/'data/raw/jewelry.csv'
        self.assertTrue(real.is_file(),'Integración real obligatoria: falta dataset')
        official=PROJECT/'data/processed/normalization-v1'
        self.assertTrue((official/'quality.json').is_file(),'Falta baseline oficial')
        protected=[real,official/'records.jsonl',official/'quality.json']
        before={str(p):digest_file(p) for p in protected}
        shutil.copyfile(real,self.source)
        for dest in [self.output,self.root/'data/processed/second']:
            result=self.cli('--check-audit','--output-dir',dest)
            self.assertEqual(result.returncode,0,result.stderr)
            expected=validate_output(self.source,dest,audit_checked=True)
            self.assertEqual(json.loads(result.stdout),expected)
            for name in ['records.jsonl','quality.json']:
                # Compare bytes independently, not pipeline hashes alone.
                with (dest/name).open('rb') as a,(official/name).open('rb') as b:
                    while True:
                        x,y=a.read(1048576),b.read(1048576)
                        self.assertEqual(x,y)
                        if not x: break
        validate_output(real,official,audit_checked=True)
        self.assertEqual(before,{str(p):digest_file(p) for p in protected})


if __name__=='__main__': unittest.main()
