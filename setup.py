from setuptools import setup
from gitfile import __version__ as version


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
    dependency_links=[],
    install_requires=[
        'pygit2',
        'Werkzeug',
    ],
    tests_require=['unittest2', 'nose', 'pep8'],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.6',
        'License :: OSI Approved :: BSD License',
    ],
)
