import unittest
import os
import sys
import time
import signal

here = os.path.dirname(os.path.abspath(__file__))
sys.path.append(here)
bottlepid = os.spawnlp(os.P_NOWAIT, "python", "python", os.path.join(here, "server.py"), "quiet")
time.sleep(1)

tests = [i[:-3] for i in os.listdir(here) 
        if i.startswith('test_') and i.endswith('.py')]
suite = unittest.defaultTestLoader.loadTestsFromNames(tests)

try:
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    sys.exit(1 if result.errors or result.failures else 0)
except:
    raise
finally:
    os.kill(bottlepid, signal.SIGTERM)
