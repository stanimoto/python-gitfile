import os
from os.path import abspath, join, dirname
import shutil
from pygit2 import *
from gitfile.utils import *

GIT_DIR = abspath(join(dirname(__file__), 'gitdir'))


def init_repo(name):
    try:
        os.makedirs(GIT_DIR)
    except:
        pass
    init_repository(join(GIT_DIR, name), True)


def cleanup():
    shutil.rmtree(GIT_DIR, True)


def create_empty_branch(repo):
    hex = repo.create_blob("")
    tb = repo.TreeBuilder()
    tb.insert('.git-placeholder', hex, 0o0100644)
    tree = tb.write()
    committer = Signature('Foo', 'foo@example.com')
    commit = repo.create_commit(
        'refs/heads/master',
        committer,
        committer,
        'create branch',
        tree,
        [],
    )
    return commit
