from setuptools import setup
from gitfile import __version__ as version


# Set "LIBGIT2" env var to refer to your own libgit2 build
setup(
    name='GitFile',
    version=version,
    author='Satoshi Tanimoto',
    author_email='tanimoto.satoshi@gmail.com',
    description='gitfile is a wrapper to Git and allows to edit files without checking out a repository.',
    long_description=open('README.rst').read(),
    url='http://github.com/stanimoto/python-gitfile',
    packages=['gitfile'],
    license='BSD',
    dependency_links=[
        #'http://github.com/libgit2/libgit2/tarball/development',
        'http://github.com/libgit2/pygit2/tarball/master#egg=pygit2',
    ],
    install_requires=[
        'pygit2',
        'Werkzeug',
        'simplejson',
    ],
    tests_require=['nose', 'unittest2', 'pep8'],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.6',
        'License :: OSI Approved :: BSD License',
    ],
)
