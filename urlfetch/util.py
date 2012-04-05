from __future__ import absolute_import
import sys

if sys.version_info >= (3, 0):
    py3k = True
    unicode = str
else:
    py3k = False

def mb_code(s, coding=None):
    if isinstance(s, unicode):
        return s if coding is None else s.encode(coding)
    for c in ('utf-8', 'gb2312', 'gbk', 'gb18030', 'big5'):
        try:
            s = s.decode(c, errors='replace')
            return s if coding is None else s.encode(coding, errors='replace')
        except: pass
    return s