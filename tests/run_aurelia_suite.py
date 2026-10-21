"""Suite de la línea sintética: no necesita datasets reales ni red."""
import sys
import unittest
from test_aurelia_dw import AureliaTests


if __name__ == '__main__':
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(AureliaTests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    print(f'AURELIA_QA tests={result.testsRun} failures={len(result.failures)} errors={len(result.errors)} skipped={len(result.skipped)}')
    sys.exit(0 if result.wasSuccessful() and not result.skipped else 1)
