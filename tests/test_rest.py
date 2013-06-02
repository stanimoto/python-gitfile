import unittest
import testutil
import os
import json
from werkzeug.test import Client
from werkzeug.wrappers import BaseResponse
from gitfile.git import *
from gitfile.utils import *
from gitfile.rest_service import create_app


class RESTServiceTest(unittest.TestCase):

    def setUp(self):
        testutil.cleanup()
        testutil.init_repo('foo.git')

        git = Git(os.path.join(testutil.GIT_DIR, 'foo.git'))
        testutil.create_empty_branch(git.repo)
        self.git = git

        app = create_app(testutil.GIT_DIR)
        self.client = Client(app, BaseResponse)

    def tearDown(self):
        pass

    def test_create_app(self):
        self.assertRaises(Exception,
                          create_app,
                          os.path.join(testutil.GIT_DIR, 'blah'))
        self.assertTrue(create_app(testutil.GIT_DIR))

    def test_find_git_dir(self):
        testutil.init_repo('bar.git')
        testutil.init_repo('baz')
        app = create_app(testutil.GIT_DIR)

        self.assertTrue(app.find_git_dir('bar'))
        self.assertTrue(app.find_git_dir('bar.git'))
        self.assertTrue(app.find_git_dir('baz'))
        self.assertFalse(app.find_git_dir('baz.git'))

        res = self.client.get('/bar/branches')
        self.assertEqual(res.status_code, 200,
                         'repository is accessible w/o ".git"')
        res = self.client.get('/bar.git/branches')
        self.assertEqual(res.status_code, 200,
                         'repository is accessible w/ ".git"')

        res = self.client.get('/baz/branches')
        self.assertEqual(res.status_code, 200,
                         'repository is accessible w/o ".git"')
        res = self.client.get('/baz.git/branches')
        self.assertEqual(res.status_code, 404,
                         'repository is not accessible w/ unnecessary ext')

    def test_blob(self):
        content = 'test_blob'
        res = self.client.post('/foo/blobs', data=content)
        self.assertEqual(res.status_code, 201,
                         'object created')
        sha1 = json.loads(res.data)['result']['sha1']
        res = self.client.get('/foo/blobs/%s' % sha1)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data, content, 'correct object fetched')

        res = self.client.get('/foo/blobs/' + '1' * 40)
        self.assertEqual(res.status_code, 404, 'object not found')

    def test_branch(self):
        res = self.client.get('/foo/branches')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(json.loads(res.data)['result']['entries'].keys(),
                         ['master'],
                         'master branch is there')

        res = self.client.get('/foo/branches/master')
        self.assertEqual(res.status_code, 200)
        entries = json.loads(res.data)['result']['entries']
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]['name'], '.git-placeholder')

        # create a blob object
        content = 'test_branch'
        res = self.client.post('/foo/blobs', data=content)
        sha1 = json.loads(res.data)['result']['sha1']

        res = self.client.post('/foo/branches/master/file1',
                               data=json.dumps({
                                   'sha1': sha1,
                                   'author_name': 'foo',
                                   'author_email': 'foo@example.com',
                               }))
        self.assertEqual(res.status_code, 201, 'file created')

        # check entries in the root dir
        res = self.client.get('/foo/branches/master')
        entries = json.loads(res.data)['result']['entries']
        self.assertEqual(sorted(map((lambda x: x['name']), entries)),
                         ['.git-placeholder', 'file1'])

        # test update
        content = 'test_branch 2'
        res = self.client.post('/foo/blobs', data=content)
        sha1 = json.loads(res.data)['result']['sha1']

        res = self.client.put('/foo/branches/master/file1',
                              data=json.dumps({
                                  'sha1': sha1,
                                  'author_name': 'foo',
                                  'author_email': 'foo@example.com',
                              }))
        self.assertEqual(res.status_code, 200, 'file updated')

        res = self.client.post('/foo/branches/master/dir1/file2',
                               data=json.dumps({
                                   'sha1': sha1,
                                   'author_name': 'foo',
                                   'author_email': 'foo@example.com',
                               }))
        self.assertEqual(res.status_code, 201, 'file created')

        # check entries in the root dir
        res = self.client.get('/foo/branches/master')
        entries = json.loads(res.data)['result']['entries']
        self.assertEqual(sorted(map((lambda x: x['name']), entries)),
                         ['.git-placeholder', 'dir1', 'file1'])

        res = self.client.get('/foo/branches/master/dir1')
        entries = json.loads(res.data)['result']['entries']
        self.assertEqual(sorted(map((lambda x: x['name']), entries)),
                         ['file2'])

        # delete file
        res = self.client.delete('/foo/branches/master/file1',
                                 data=json.dumps({
                                     'author_name': 'foo',
                                     'author_email': 'foo@example.com',
                                 }))
        self.assertEqual(res.status_code, 200, 'file deleted')
        res = self.client.get('/foo/branches/master/file1')
        self.assertEqual(res.status_code, 404, 'file is gone')
        res = self.client.get('/foo/branches/master')
        entries = json.loads(res.data)['result']['entries']
        self.assertEqual(sorted(map((lambda x: x['name']), entries)),
                         ['.git-placeholder', 'dir1'])

        # create branch
        res = self.client.get('/foo/branches/master')
        head = json.loads(res.data)['result']['sha1']
        res = self.client.post('/foo/branches/branch1',
                               data=json.dumps({'target': head}))
        self.assertEqual(res.status_code, 201, 'branch created')

        # TODO: branch with slash
        #res = self.client.post('/foo/branches/feature%2Ffoo',
        #                       data=json.dumps({'target': head}))
        #self.assertEqual(res.status_code, 201, 'branch created')

        # create file in new branch
        content = '/foo/branches/branch1/dir2/file3'
        res = self.client.post('/foo/blobs', data=content)
        sha1 = json.loads(res.data)['result']['sha1']

        res = self.client.post('/foo/branches/branch1/dir2/file3',
                               data=json.dumps({
                                   'sha1': sha1,
                                   'author_name': 'foo',
                                   'author_email': 'foo@example.com',
                               }))
        self.assertEqual(res.status_code, 201, 'file created')

        res = self.client.get('/foo/branches/branch1/dir2/file3')
        self.assertEqual(res.status_code, 200)
        res = self.client.get('/foo/branches/master/dir2/file3')
        self.assertEqual(res.status_code, 404, 'not on master')

        # delete branch
        res = self.client.delete('/foo/branches/branch1')
        self.assertEqual(res.status_code, 200, 'branch deleted')
        res = self.client.get('/foo/branches/branch1')
        self.assertEqual(res.status_code, 404)

    def test_tag(self):
        res = self.client.get('/foo/tags')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(json.loads(res.data)['result']['entries'].keys(),
                         [],
                         'no tags yet')

        res = self.client.get('/foo/branches/master')
        head = json.loads(res.data)['result']['sha1']

        # create tag
        res = self.client.post('/foo/tags/tag1',
                               data=json.dumps({'target': head}))
        self.assertEqual(res.status_code, 201, 'tag created')

        res = self.client.get('/foo/tags/tag1/.git-placeholder')
        self.assertEqual(res.status_code, 200)

        res = self.client.get('/foo/tags')
        self.assertEqual(json.loads(res.data)['result']['entries'].keys(),
                         ['tag1'])

        # create file in branch
        content = 'test_tag'
        res = self.client.post('/foo/blobs', data=content)
        sha1 = json.loads(res.data)['result']['sha1']

        res = self.client.post('/foo/branches/master/file1',
                               data=json.dumps({
                                   'sha1': sha1,
                                   'author_name': 'foo',
                                   'author_email': 'foo@example.com',
                               }))
        self.assertEqual(res.status_code, 201, 'file created')
        res = self.client.get('/foo/branches/master')
        head = json.loads(res.data)['result']['sha1']

        # create another tag
        res = self.client.post('/foo/tags/tag2',
                               data=json.dumps({'target': head}))
        self.assertEqual(res.status_code, 201, 'tag created')

        res = self.client.get('/foo/tags')
        self.assertEqual(json.loads(res.data)['result']['entries'].keys(),
                         ['tag1', 'tag2'])

        res = self.client.get('/foo/tags/tag1/file1')
        self.assertEqual(res.status_code, 404)
        res = self.client.get('/foo/tags/tag2/file1')
        self.assertEqual(res.status_code, 200)

        # delete tag
        res = self.client.delete('/foo/tags/tag1')
        self.assertEqual(res.status_code, 200, 'tag deleted')

        res = self.client.get('/foo/tags')
        self.assertEqual(json.loads(res.data)['result']['entries'].keys(),
                         ['tag2'])

    def test_commit(self):
        # update 'file1' twice
        contents = ('foo', 'bar')
        commits = []
        for content in contents:
            res = self.client.post('/foo/blobs', data=content)
            sha1 = json.loads(res.data)['result']['sha1']
            res = self.client.post(
                '/foo/branches/master/file1',
                data=json.dumps({
                    'sha1': sha1,
                    'author_name': 'foo',
                    'author_email': 'foo@example.com',
                })
            )
            res = self.client.get('/foo/branches/master')
            commit = json.loads(res.data)['result']['sha1']
            commits.append(commit)

        for i, commit in enumerate(commits):
            res = self.client.get('/foo/commits/%s/file1' % commit)
            sha1 = json.loads(res.data)['result']['sha1']
            res = self.client.get('/foo/blobs/%s' % sha1)
            self.assertEqual(res.status_code, 200)
            self.assertEqual(res.data, contents[i], 'correct object fetched')
