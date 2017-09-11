from setuptools import setup
import urlfetch
import re
import os
import sys

setup(
    name="urlfetch",
    version=urlfetch.__version__,
    author=re.sub(r'\s+<.*', r'', urlfetch.__author__),
    author_email=re.sub(r'(^.*<)|(>.*$)', r'', urlfetch.__author__),
    url=urlfetch.__url__,
    description="An easy to use HTTP client",
    long_description=open('README.rst').read(),
    license="BSD",
    keywords="httpclient urlfetch",
    py_modules=['urlfetch'],
    data_files=[('', ['urlfetch.useragents.list'])],
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: POSIX',
        'Operating System :: POSIX :: Linux',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ],
    test_suite='tests.testall',
    tests_require=['bottle', 'gunicorn'],
)
