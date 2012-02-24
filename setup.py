from setuptools import setup
import urlfetch
import re

setup(
    name = "urlfetch",
    version = urlfetch.__version__,
    author = re.sub(r'\s+<.*', r'', urlfetch.__author__),
    author_email = re.sub(r'(^.*<)|(>.*$)', r'', urlfetch.__author__),
    url = urlfetch.__url__,
    description = ("An easy to use HTTP client"),
    long_description = open('README.rst').read(),
    license = "BSD",
    keywords = "httpclient urlfetch",
    packages = [
        'urlfetch',
    ],
    classifiers = [
        'Development Status :: 4 - Beta',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: POSIX',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ],
    include_package_data = True,
)

