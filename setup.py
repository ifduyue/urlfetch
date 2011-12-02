from setuptools import setup

setup(
    name = "urlfetch",
    version = '0.1',
    author = "Yue Du",
    author_email = "lyxint@gmail.com",
    description = ("An easy to use HTTP client based on httplib"),
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

