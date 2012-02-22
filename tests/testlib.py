import random
import string

def randstr(l=None, chars=string.ascii_letters+string.digits):
    l = l or random.randint(1, 100)
    return ''.join(random.choice(chars) for i in xrange(l))


randint = random.randint


def randdict(l=None):
    i = l or random.randint(1, 100)
    d = {}
    for i in xrange(i):
        d[randstr()] = randstr()
    return d
