"""
Run the complete test suite.

Pyro - Python Remote Objects.  Copyright by Irmen de Jong.
irmen@razorvine.net - http://www.razorvine.net/python/Pyro
"""

import unittest
import sys, os
try:
    import coverage
except ImportError:
    class CoverageDummy(object):
        def start(self): pass
        def stop(self): pass
        def report(self, *args, **kwargs): pass
    coverage=CoverageDummy()
    print("No coverage info available")

sys.path.insert(0,"../src")    # add Pyro source directory
sys.path.insert(1,"PyroTests")

if __name__=="__main__":
    # add test modules here
    modules=[module[:-3] for module in os.listdir("PyroTests") if module.endswith(".py") and not module.startswith("__")]
     
    print("gathering testcases from %s" % modules)

    coverage.start()
     
    suite=unittest.TestSuite()
    for module in modules:
        m=__import__("PyroTests."+module)
        m=getattr(m,module)
        testcases = unittest.defaultTestLoader.loadTestsFromModule(m)
        suite.addTest(testcases)

    print("\nRUNNING UNIT TESTS...")
    unittest.TextTestRunner(verbosity=1).run(suite)

    coverage.stop()
    print("")
    coverage.report(show_missing=False, omit_prefixes=["PyroTests"])
    
    print("\nRUNNING PYFLAKE CODE CHECKS...")
    import run_syntaxcheck
    run_syntaxcheck.main(["flakes"])
