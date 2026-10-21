"""Suite propia de ajustes v2; ejecutar también las suites históricas."""
import sys
import unittest
from test_aurelia_v2 import AdjustmentTests

if __name__=='__main__':
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(AdjustmentTests))
    print(f'AURELIA_V2_QA tests={result.testsRun} failures={len(result.failures)} errors={len(result.errors)} skipped={len(result.skipped)}')
    sys.exit(0 if result.wasSuccessful() and not result.skipped else 1)
