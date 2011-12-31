from setuptools import setup
import urlfetch
import re

setup(
    name = "urlfetch",
    version = urlfetch.__version__,
    author = re.sub(r'\s+<.*', r'', urlfetch.__author__),
    author_email = re.sub(r'(^.*<)|(>.*$)', r'', urlfetch.__author__),
    url = urlfetch.__url__,
    description = ("An easy to use HTTP client based on httplib"),
    long_description = open('README.rst').read(),
    license = "BSD",
    keywords = "http urlfetch",
    packages = [
        'urlfetch',
    ],
    classifiers = [
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: BSD License',
        'Operating System :: POSIX',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ],
)

