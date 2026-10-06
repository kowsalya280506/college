import sys
import os

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest

def main():
    print("Discovering tests...", flush=True)
    loader = unittest.TestLoader()
    suite = loader.discover(os.path.dirname(__file__), pattern="test_*.py")
    print(f"Discovered {suite.countTestCases()} test cases. Running...", flush=True)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    print(f"\nSummary: Ran {result.testsRun} tests. Failures={len(result.failures)}, Errors={len(result.errors)}", flush=True)
    if not result.wasSuccessful():
        sys.exit(1)
    print("ALL 16+ TESTS PASSED SUCCESSFULLY!", flush=True)

if __name__ == "__main__":
    main()
