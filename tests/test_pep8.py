from os.path import abspath, join, dirname
import unittest
import pep8

BASE_DIR = abspath(join(dirname(__file__), '..'))
TEST_DIRS = ['gitfile', 'tests']


class TestPep8(unittest.TestCase):

    def setUp(self):
        paths = []
        for dir in TEST_DIRS:
            paths.append(join(BASE_DIR, dir))
        self.paths = paths

    def tearDown(self):
        pass

    def test_pep8(self):
        pep8style = pep8.StyleGuide()
        report = pep8style.check_files(paths=self.paths)
        if report.total_errors:
            self.fail("Found %s pep8 errors" % report.total_errors)

if __name__ == '__main__':
    unittest.main()
