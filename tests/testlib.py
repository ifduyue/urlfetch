import random
import string
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def randstr(l=None, chars=string.ascii_letters+string.digits):
    l = l or random.randint(1, 100)
    return ''.join(random.choice(chars) for i in range(l))


randint = random.randint


def randdict(l=None):
    i = l or random.randint(1, 100)
    d = {}
    for i in range(i):
        d[randstr()] = randstr()
    return d


py3k = (sys.version_info[0] == 3)
