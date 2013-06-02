gitfile - Git as a versioned file system and its RESTful interface
==================================================================

gitfile is a wrapper to Git and allows to edit files without checking out a repository. This library is in an alpha state.

Features
--------

* Create/Update/Delete files
* Create/Delete branches
* Create/Delete tags
* RESTful interface

Dependencies
------------

* `libgit2 <http://libgit2.github.com/>`_
* `pygit2 <http://github.com/libgit2/pygit2>`_
* Werkzeug

Install
-------

::

  $ virtualenv env --no-site-packages
  $ env/bin/pip install -r requirements.txt -r requirements-test.txt
  $ env/bin/nosetests tests
  $ env/bin/python app.wsgi

Example API usage
-----------------

::

  from gitfile.git import Git
  
  git = Git('/path/to/gitdir')
  
  blob_sha1 = git.create_blob('blah')
  commit_sha1 = git.create_entry('master',
                                 '/new_file.txt',
                                 blob_sha1,
                                 author_name='foo',
                                 author_email='foo@example.com',
                                 comment='adding new_file.txt')

Example RESTful JSON API usage
------------------------------

You can run a simple web server with the attached wsgi file. ::

  $ env/bin/python app.wsgi

To get a list of branches ::

  $ curl -is http://localhost:5000/test.git/branches
  HTTP/1.0 200 OK
  Content-Type: application/json
  Content-Length: 162
  Server: Werkzeug/0.8.3 Python/2.7.3
  Date: Thu, 03 Jan 2013 07:30:14 GMT

  {
      "error": false,
      "message": null,
      "result": {
          "entries": {
              "master": "7769894b4941d8419f24bcead6efbdf11e483b36"
          }
      }
  }

To create a new blob object ::

  $ curl -is -X POST -H 'Content-Type: text/plain' -d "test" http://localhost:5000/test.git/blobs
  HTTP/1.0 201 CREATED
  Content-Type: application/json
  Content-Length: 155
  Server: Werkzeug/0.8.3 Python/2.7.3
  Date: Thu, 03 Jan 2013 07:32:16 GMT

  {
      "error": false,
      "message": "A resource created successfully.",
      "result": {
          "sha1": "30d74d258442c7c65512eafab474568dd706c430"
      }
  }

To add a new file in the master branch ::

  $ curl -is -X POST -H 'Content-Type: application/json' -d '{"sha1":"30d74d258442c7c65512eafab474568dd706c430","author_name":"foo","author_email":"foo@example.com"}' http://localhost:5000/test.git/branches/master/new_file.txt
  HTTP/1.0 201 CREATED
  Content-Type: application/json
  Content-Length: 91
  Server: Werkzeug/0.8.3 Python/2.7.3
  Date: Thu, 03 Jan 2013 07:37:35 GMT

  {
      "error": false,
      "message": "A resource created successfully.",
      "result": {}
  }

To get a list of files in the root directory in the master branch ::

  $ curl -is http://localhost:5000/test.git/branches/master
  HTTP/1.0 200 OK
  Content-Type: application/json
  Content-Length: 672
  Server: Werkzeug/0.8.3 Python/2.7.3
  Date: Thu, 03 Jan 2013 07:38:05 GMT

  {
      "error": false,
      "message": null,
      "result": {
          "entries": [
              {
                  "mode": "0100644",
                  "name": ".git-placeholder",
                  "sha1": "e69de29bb2d1d6434b8b29ae775ad8c2e48c5391",
                  "size": 0,
                  "type": "blob"
              },
              {
                  "mode": "0100644",
                  "name": "new_file.txt",
                  "sha1": "30d74d258442c7c65512eafab474568dd706c430",
                  "size": 4,
                  "type": "blob"
              }
          ],
          "name": "master",
          "sha1": "04f2c15b084af23a1120516bf6ea22e58090665a",
          "type": "branch"
      }
  }

        


