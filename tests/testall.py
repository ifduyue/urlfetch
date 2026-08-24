#!/usr/bin/env python
import multiprocessing
import os
import sys
import time
import unittest

here = os.path.dirname(os.path.abspath(__file__))
parent = os.path.dirname(here)
sys.path.append(parent)
sys.path.append(here)


def main():
    import server

    try:
        multiprocessing.set_start_method("fork")
    except RuntimeError:
        pass

    p = multiprocessing.Process(target=server.run)
    p.start()
    time.sleep(1)

    tests = [
        i[:-3]
        for i in os.listdir(here)
        if i.startswith("test_") and i.endswith(".py")
    ]
    suite = unittest.defaultTestLoader.loadTestsFromNames(tests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    p.terminate()
    sys.exit(1 if result.errors or result.failures else 0)


if __name__ == "__main__":
    main()
