import unittest
import gitfile
import os
import testutil
from gitfile.git import *
from gitfile.exceptions import *
from gitfile.utils import *


class ApiTest(unittest.TestCase):

    def setUp(self):
        testutil.cleanup()
        testutil.init_repo('foo.git')

        git = Git(os.path.join(testutil.GIT_DIR, 'foo.git'))
        self.assertEqual(git.branches(), {}, 'no branches yet')

        testutil.create_empty_branch(git.repo)

        self.git = Git(os.path.join(testutil.GIT_DIR, 'foo.git'))

    def tearDown(self):
        pass

    def test_init(self):
        self.assertTrue(isinstance(self.git, Git), 'create git instance')

    def test_branches(self):
        self.assertEqual(self.git.branches().keys(), ['master'],
                         'master branch')

    def test_create_branch(self):
        self.assertRaises(InvalidParamException,
                          self.git.create_branch, None, None)

        self.assertRaises(InvalidParamException,
                          self.git.create_branch, 'branch1', None)

        self.assertRaises(InvalidParamException,
                          self.git.create_branch, 'branch1',
                          '1' * 40)

        branches = self.git.branches()
        self.assertRaises(InvalidParamException,
                          self.git.create_branch, 'master', branches['master'])

        self.assertTrue(self.git.create_branch('branch1', branches['master']))
        self.assertEqual(sorted(self.git.branches().keys()),
                         ['branch1', 'master'],
                         'branch1 created')

        self.assertTrue(self.git.create_branch('branch2', branches['master']))
        self.assertEqual(sorted(self.git.branches().keys()),
                         ['branch1', 'branch2', 'master'],
                         'branch2 created')

        # branch with slash
        self.assertTrue(self.git.create_branch('foo/bar', branches['master']))
        self.assertTrue('foo/bar' in self.git.branches().keys())

    def test_delete_branch(self):
        branches = self.git.branches()
        self.assertTrue(self.git.create_branch('branch1', branches['master']))
        self.assertEqual(sorted(self.git.branches().keys()),
                         ['branch1', 'master'],
                         'branch1 created')

        self.assertRaises(InvalidParamException,
                          self.git.delete_branch, None)

        self.assertRaises(InvalidParamException,
                          self.git.delete_branch, 'foo')

        self.assertTrue(self.git.delete_branch('branch1'))
        self.assertEqual(sorted(self.git.branches().keys()),
                         ['master'])

        self.assertTrue(self.git.delete_branch('master'))

    def test_create_content(self):
        self.assertRaises(InvalidParamException,
                          self.git.create_content, None)

        content = 'foo'
        hex = self.git.create_content(content)
        self.assertTrue(hex)
        self.assertEqual(self.git.create_content(content), hex)

    def test_get_content(self):
        self.assertRaises(InvalidParamException,
                          self.git.get_content, None)

        self.assertRaises(InvalidParamException,
                          self.git.get_content, 'a')

        content = 'foo'
        hex = self.git.create_content(content)
        self.assertTrue(hex)
        self.assertEqual(self.git.get_content(hex), content)

        self.assertEqual(self.git.get_content('a' * 40), None)

    def test_find_entry(self):
        self.assertTrue(self.git.find_entry('/', branch='master'))
        self.assertTrue(self.git.find_entry('/.git-placeholder',
                        branch='master'))
        self.assertFalse(self.git.find_entry('/foo', branch='master'))

        self.assertRaises(InvalidParamException,
                          self.git.find_entry, '/', branch='abc')

    def test_create_entry(self):
        paths = ['/foo.txt', '/foo/bar.txt', '/foo/bar/baz.txt']
        for path in paths:
            hex = self.git.create_content('blah')
            self.assertFalse(self.git.find_entry(path, branch='master'),
                             'path does not exist yet')
            commit_hex = self.git.create_entry('master',
                                               path,
                                               hex,
                                               author_name='foo',
                                               author_email='foo@example.com')
            self.assertTrue(commit_hex, 'path exists now')
            self.assertTrue(self.git.repo[sha_hex2bin(commit_hex)])

            entry = self.git.find_entry(path, branch='master')
            self.assertEqual(self.git.get_content(entry.hex), 'blah')
            self.assertEqual(entry_to_dict(entry),
                             {'name': entry.name,
                              'sha1': entry.hex,
                              'mode': oct(entry.filemode),
                              'type': 'blob',
                              'size': len('blah')})

        entry = self.git.find_entry('/foo', branch='master')
        self.assertEqual(entry_to_dict(entry),
                         {'name': 'foo',
                          'sha1': entry.hex,
                          'mode': oct(entry.filemode),
                          'type': 'tree'})

        path = '/test.txt'
        hex = self.git.create_content('blah')

        self.assertRaises(InvalidParamException,
                          self.git.create_entry, 'abc', path, hex)
        self.assertRaises(InvalidParamException,
                          self.git.create_entry, 'abc', path, 'a')

        hex = self.git.create_content('blah')
        for path in ['foo', 'bar', 'baz']:
            self.git.create_entry('master',
                                  '/dir1/' + path,
                                  hex,
                                  author_name='foo',
                                  author_email='foo@example.com')
        for path in ['foo', 'bar', 'baz']:
            entry = self.git.find_entry('/dir1/' + path, branch='master')
            self.assertTrue(entry, "%s exists" % path)

    def test_update_entry(self):
        path = '/test_update_entry.txt'
        content = 'test for update_entry'
        hex = self.git.create_content(content)
        content_new = 'test for update_entry (new)'
        hex_new = self.git.create_content(content_new)

        self.assertRaises(InvalidParamException,
                          self.git.update_entry, 'abc', path, hex)
        self.assertRaises(InvalidParamException,
                          self.git.update_entry, 'master', path, 'a')
        self.assertRaises(InvalidParamException,
                          self.git.update_entry, 'master', path, hex,
                          author_name='foo', author_email='foo@example.com')

        self.assertTrue(self.git.create_entry('master', path, hex,
                                              author_name='foo',
                                              author_email='foo@example.com'))
        self.assertEqual(self.git.find_entry(path, branch='master').hex, hex)

        self.assertTrue(self.git.update_entry('master', path, hex_new,
                                              author_name='foo',
                                              author_email='foo@example.com'))
        self.assertEqual(self.git.find_entry(path, branch='master').hex,
                         hex_new)

    def test_delete_entry(self):
        path = '/test_delete_entry.txt'
        content = 'test for delete_entry'
        hex = self.git.create_content(content)

        self.assertRaises(InvalidParamException,
                          self.git.delete_entry, 'abc', path,
                          author_name='foo',
                          author_email='foo@example.com')
        self.assertRaises(InvalidParamException,
                          self.git.delete_entry, 'master', path,
                          author_name='foo',
                          author_email='foo@example.com')

        self.assertTrue(self.git.create_entry('master', path, hex,
                                              author_name='foo',
                                              author_email='foo@example.com'))
        self.assertEqual(self.git.find_entry(path, branch='master').hex, hex)

        self.assertTrue(self.git.delete_entry('master', path,
                                              author_name='foo',
                                              author_email='foo@example.com'))
        self.assertFalse(self.git.find_entry(path, branch='master'))

    def test_tags(self):
        path = '/text_create_tag.txt'
        content = 'test for create_tag'
        hex = self.git.create_content(content)
        hex_new = self.git.create_content(content + ' (new)')

        target = self.git.create_entry('master', path, hex,
                                       author_name='foo',
                                       author_email='foo@example.com')
        self.assertTrue(target)

        self.assertRaises(InvalidParamException,
                          self.git.create_tag, '', None)
        self.assertRaises(InvalidParamException,
                          self.git.create_tag, 'tag1', None)

        self.assertTrue(self.git.create_tag('tag1', target))

        target = self.git.update_entry('master', path, hex_new,
                                       author_name='foo',
                                       author_email='foo@example.com')
        self.assertTrue(target)

        self.assertTrue(self.git.create_tag('tag2', target))

        self.assertEqual(self.git.find_entry(path, tag='tag1').hex, hex)
        self.assertEqual(self.git.find_entry(path, tag='tag2').hex, hex_new)

        self.assertEqual(self.git.tags().keys(), ['tag1', 'tag2'])

        for tag in [None, '']:
            self.assertRaises(InvalidParamException,
                              self.git.delete_tag, tag)

        self.assertRaises(InvalidParamException,
                          self.git.delete_tag, 'tag100')

        self.assertTrue(self.git.delete_tag('tag1'))
        self.assertEqual(self.git.tags().keys(), ['tag2'])
        self.assertTrue(self.git.delete_tag('tag2'))
        self.assertEqual(self.git.tags().keys(), [])

if __name__ == '__main__':
    unittest.main()
