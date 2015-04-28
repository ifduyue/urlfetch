#!/usr/bin/env python
import unittest
import os
import sys
import time
import signal
import multiprocessing

here = os.path.dirname(os.path.abspath(__file__))
sys.path.append(here)

import server


p = multiprocessing.Process(target=server.run)
p.start()

# waiting for the http server to be ready
time.sleep(1)

tests = [i[:-3] for i in os.listdir(here)
                if i.startswith('test_') and i.endswith('.py')]
suite = unittest.defaultTestLoader.loadTestsFromNames(tests)
additional_tests = lambda: suite
result = unittest.TextTestRunner(verbosity=2).run(suite)

p.terminate()

sys.exit(1 if result.errors or result.failures else 0)
