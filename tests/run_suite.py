"""Entrada explícita de QA: una suite parcial nunca representa aprobación total."""
import argparse
import sys
import unittest

from test_normalize_jewelry import NormalizationTests, LocalDatasetIntegrationTests
from test_qa_unit import QAUnitTests
from test_cli_integration import CLIIntegrationTests


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    group=parser.add_mutually_exclusive_group()
    group.add_argument('--unit-only',action='store_true')
    group.add_argument('--integration-only',action='store_true')
    args=parser.parse_args()
    units=[NormalizationTests,QAUnitTests]
    integrations=[CLIIntegrationTests,LocalDatasetIntegrationTests]
    selected=units if args.unit_only else integrations if args.integration_only else units+integrations
    scope='UNIT ONLY - NO FULL APPROVAL' if args.unit_only else 'INTEGRATION ONLY' if args.integration_only else 'FULL SUITE - REAL DATA REQUIRED'
    print(scope,flush=True)
    suite=unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromTestCase(case) for case in selected)
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    print(f'QA_RESULT tests={result.testsRun} failures={len(result.failures)} errors={len(result.errors)} skipped={len(result.skipped)}',flush=True)
    return 0 if result.wasSuccessful() and not result.skipped else 1


if __name__=='__main__': sys.exit(main())
