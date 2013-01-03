import unittest
from gitfile.git import *
from gitfile.utils import *


class UtilsTest(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_make_dir_paths(self):
        t = {
            '/': ['/'],
            '/foo/': ['/foo/', '/'],
            '/foo/bar/': ['/foo/bar/', '/foo/', '/'],
        }
        for i, o in t.iteritems():
            self.assertEqual(make_dir_paths(i), o)

    def test_parse_path(self):
        t = {
            '': ['/', ''],
            '/foo': ['/', 'foo'],
            'foo': ['/', 'foo'],
            'foo/bar': ['/foo/', 'bar'],
            '/foo/bar/': ['/foo/', 'bar'],
            '/foo/bar.jpg': ['/foo/', 'bar.jpg'],
            '/foo/bar/baz': ['/foo/bar/', 'baz'],
        }
        for i, o in t.iteritems():
            self.assertEqual(list(parse_path(i)), o)
