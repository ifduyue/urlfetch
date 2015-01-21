#!/usr/bin/env python
import unittest
import os
import sys
import time
import signal
import atexit

here = os.path.dirname(os.path.abspath(__file__))
sys.path.append(here)

pid = os.spawnlp(os.P_NOWAIT, "gunicorn", *("gunicorn --pythonpath tests -w 4 --log-level warning -b 0:8800 server:app".split()))
time.sleep(1)

@atexit.register
def clean_gunicorn():
    os.kill(pid, signal.SIGTERM)

tests = [i[:-3] for i in os.listdir(here)
        if i.startswith('test_') and i.endswith('.py')]
suite = unittest.defaultTestLoader.loadTestsFromNames(tests)
additional_tests = lambda: suite

if __name__ == '__main__':
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    sys.exit(1 if result.errors or result.failures else 0)
