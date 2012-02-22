import unittest
import os
import sys


tests = [i[:-3] for i in os.listdir(os.path.dirname(os.path.abspath(__file__))) 
        if i.startswith('test_') and i.endswith('.py')]

suite = unittest.defaultTestLoader.loadTestsFromNames(tests)
result = unittest.TextTestRunner(verbosity=2).run(suite)


sys.exit(1 if result.errors or result.failures else 0)
