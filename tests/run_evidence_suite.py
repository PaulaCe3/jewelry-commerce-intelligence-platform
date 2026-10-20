"""Runner de evidencia SQLite; integración real obligatoria salvo --unit-only."""
import argparse
import sys
import unittest
from test_evidence_sqlite import EvidenceUnitTests, EvidenceRealIntegrationTests


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--unit-only', action='store_true')
    args = parser.parse_args()
    classes = [EvidenceUnitTests] if args.unit_only else [EvidenceUnitTests, EvidenceRealIntegrationTests]
    print('UNIT ONLY - NO FULL APPROVAL' if args.unit_only else 'FULL EVIDENCE SUITE - REAL DATA REQUIRED', flush=True)
    suite = unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromTestCase(case) for case in classes)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    print(f'EVIDENCE_QA tests={result.testsRun} failures={len(result.failures)} errors={len(result.errors)} skipped={len(result.skipped)}', flush=True)
    return 0 if result.wasSuccessful() and not result.skipped else 1


if __name__ == '__main__':
    sys.exit(main())
