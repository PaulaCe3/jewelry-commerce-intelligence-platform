"""Aceptación autónoma local del pipeline sintético y su consumo."""
import sys
import unittest
from test_aurelia_pipeline import PipelineTests

if __name__=='__main__':
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(PipelineTests))
    print(f'AURELIA_PIPELINE_QA tests={result.testsRun} failures={len(result.failures)} errors={len(result.errors)} skipped={len(result.skipped)}')
    sys.exit(0 if result.wasSuccessful() and not result.skipped else 1)
