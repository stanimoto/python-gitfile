from pygit2 import Repository, Signature
import re
from gitfile.exceptions import InvalidParamException
from gitfile.utils import *

DEFAULT_MODE_BLOB = 0o0100644
DEFAULT_MODE_TREE = 0o0040000


class Git(object):
    r"""
    Interact with a git repository.
    """

    def __init__(self, gitdir):
        r"""
        Take a path to the git repository. Other methods interact with
        this git repository.
        """
        self.repo = Repository(gitdir)

    def branches(self):
        r"""
        Return the list of a branch name and its last commit id.
        """
        return self._refs('heads')

    def tags(self):
        r"""
        Return the list of a tag name and its last commit id.
        """
        return self._refs('tags')

    def _refs(self, type):
        refs = {}
        pattern = re.compile(r'refs/%s/(.*)$' % type)
        for ref in self.repo.listall_references():
            m = pattern.match(ref)
            if m:
                reference = self.repo.lookup_reference(ref)
                refs[m.group(1)] = reference.hex
        return refs

    def create_branch(self, name, target):
        r"""
        Create new branch.
        """
        if not is_valid_value(name):
            raise InvalidParamException("name is required")
        if not is_valid_hex(target):
            raise InvalidParamException("target is required")

        target = sha_hex2bin(target)
        try:
            self.repo.create_reference('refs/heads/%s' % name, target)
        except Exception, e:
            raise InvalidParamException(str(e))

        return True

    def delete_branch(self, name):
        r"""
        Delete the branch for the given name.
        """
        if not is_valid_value(name):
            raise InvalidParamException("name is required")

        try:
            ref = self.repo.lookup_reference('refs/heads/%s' % name)
            ref.delete()
        except Exception, e:
            raise InvalidParamException(str(e))

        return True

    def create_content(self, content):
        r"""
        Create a new blob object and return the sha1 hex.
        """
        if content is None:
            raise InvalidParamException('content is required')

        oid = self.repo.create_blob(content)
        blob = self.repo[oid]
        return blob.hex

    def get_content(self, hex):
        r"""
        Return the raw content of the blob object for the given sha1.
        """
        if not is_valid_hex(hex):
            raise InvalidParamException('hex is required')
        try:
            obj = self.repo[sha_hex2bin(hex)]
        except KeyError, e:
            return None

        if obj.type != GIT_OBJ_BLOB:
            return None

        return obj.read_raw()

    def find_entry(self, path, branch=None, tag=None, commit=None):
        r"""
        Return the entry for the given path and on the given
        branch/tag.
        """
        if branch:
            entry = tree = self.branch_tree(branch)
        elif tag:
            entry = tree = self.tag_tree(tag)
        elif commit:
            entry = tree = self.commit_tree(commit)
        else:
            raise InvalidParamException('branch or tag is required')

        for filename in path.split('/'):
            if filename == '':
                continue
            entry = None
            for tree_entry in tree:
                if tree_entry.name == filename:
                    entry = tree_entry
                    break
            if entry is None:
                return None
            tree = entry.to_object()

        return entry

    def create_entry(self, branch, path, sha1, mode=None,
                     author_name='', author_email='', comment=''):
        r"""
        Create a new file at the given path and return the commit id.
        """
        if not is_valid_hex(sha1):
            raise InvalidParamException("sha1 is invalid")

        try:
            obj = self.repo[sha_hex2bin(sha1)]
        except KeyError, e:
            raise InvalidParamException(
                "No blob found for the given id: " + sha1)

        branch_tree = self.branch_tree(branch)
        committer = Signature(author_name, author_email)

        dirname, filename = parse_path(path)
        dirs = make_dir_paths(dirname)

        new_tree_oid = None
        new_tree_hex = None
        for dir_path in dirs:
            dir_tree = []
            if dir_path == '/':
                dir_tree = branch_tree
            else:
                entry = self.find_entry(dir_path, branch=branch)
                if entry:
                    dir_tree = entry.to_object()

            new_entry = None
            old_entry = None
            for e in dir_tree:
                if e.name == filename:
                    old_entry = e
                    break

            if new_tree_oid:
                new_entry = {
                    'name': filename,
                    'filemode': getattr(old_entry, 'filemode',
                                        DEFAULT_MODE_TREE),
                    'oid': new_tree_oid,
                }
            else:
                if mode is None:
                    if obj.type == GIT_OBJ_BLOB:
                        mode = DEFAULT_MODE_BLOB
                    elif obj.type == GIT_OBJ_TREE:
                        mode = DEFAULT_MODE_TREE

                new_entry = {
                    'name': filename,
                    'filemode': mode,
                    'oid': sha_hex2bin(sha1),
                }

            tb = self.repo.TreeBuilder()

            if old_entry:
                for e in dir_tree:
                    if e.name == old_entry.name:
                        tb.insert(new_entry['name'],
                                  new_entry['oid'],
                                  new_entry['filemode'])
                    else:
                        tb.insert(e.name, e.oid, e.filemode)
            else:
                entries = [new_entry]
                for e in dir_tree:
                    entries.append({
                        'name': e.name,
                        'oid': e.oid,
                        'filemode': e.filemode,
                    })
                for e in sorted(entries, key=lambda x: x['name']):
                    tb.insert(e['name'], e['oid'], e['filemode'])

            new_tree_oid = tb.write()
            new_tree_hex = self.repo[new_tree_oid].hex
            # the last element is always an empty string
            filename = dir_path.split('/')[-2]

        parent = self.repo.lookup_reference('refs/heads/%s' % branch)
        commit = self.repo.create_commit(
            'refs/heads/%s' % (branch),
            committer,
            committer,
            comment,
            new_tree_oid,
            [parent.oid],
        )
        return self.repo[commit].hex

    def update_entry(self, branch, path, sha1, mode=None,
                     author_name='', author_email='', comment=''):
        r"""
        Update the file at the given path and return the commit id.
        """
        if not is_valid_hex(sha1):
            raise InvalidParamException("sha1 is invalid")

        try:
            self.repo[sha_hex2bin(sha1)]
        except KeyError, e:
            raise InvalidParamException("sha1 is invalid")

        branch_tree = self.branch_tree(branch)
        committer = Signature(author_name, author_email)

        dirname, filename = parse_path(path)
        dirs = make_dir_paths(dirname)

        new_tree_oid = None
        new_tree_hex = None
        for dir_path in dirs:
            dir_tree = branch_tree if dir_path == '/' \
                else self.find_entry(dir_path, branch=branch).to_object()

            new_entry = None
            old_entry = None
            for e in dir_tree:
                if e.name == filename:
                    old_entry = e
                    break

            if not old_entry:
                raise InvalidParamException(
                    'no entry for the given path')

            if new_tree_oid:
                new_entry = {
                    'name': filename,
                    'filemode': old_entry.filemode,
                    'oid': new_tree_oid,
                }
            else:
                new_entry = {
                    'name': filename,
                    'filemode': mode if mode else old_entry.filemode,
                    'oid': sha_hex2bin(sha1) if sha1 else old_entry.oid,
                }

            tb = self.repo.TreeBuilder()

            for e in dir_tree:
                if e.name == new_entry['name']:
                    tb.insert(new_entry['name'],
                              new_entry['oid'],
                              new_entry['filemode'])
                else:
                    tb.insert(e.name, e.oid, e.filemode)

            new_tree_oid = tb.write()
            new_tree_hex = self.repo[new_tree_oid].hex
            # the last element is an empty string
            filename = dir_path.split('/')[-2]

        parent = self.repo.lookup_reference('refs/heads/%s' % branch)
        commit = self.repo.create_commit(
            'refs/heads/%s' % (branch),
            committer,
            committer,
            comment,
            new_tree_oid,
            [parent.oid],
        )
        return self.repo[commit].hex

    def delete_entry(self, branch, path,
                     author_name='', author_email='', comment=''):
        r"""
        Delete the file for the given path and return the commit id.
        """
        branch_tree = self.branch_tree(branch)
        committer = Signature(author_name, author_email)

        dirname, filename = parse_path(path)
        dirs = make_dir_paths(dirname)

        new_tree_oid = None
        new_tree_hex = None
        for dir_path in dirs:
            dir_tree = branch_tree if dir_path == '/' \
                else self.find_entry(dir_path, branch=branch).to_object()

            new_entry = None
            old_entry = None
            for e in dir_tree:
                if e.name == filename:
                    old_entry = e
                    break

            if not old_entry:
                raise InvalidParamException(
                    'no entry for the given path')

            if new_tree_oid:
                new_entry = {
                    'name': filename,
                    'filemode': old_entry.filemode,
                    'oid': new_tree_oid,
                }

            tb = self.repo.TreeBuilder()

            for e in dir_tree:
                if e.name == filename:
                    if new_entry:
                        tb.insert(new_entry['name'],
                                  new_entry['oid'],
                                  new_entry['filemode'])
                else:
                    tb.insert(e.name, e.oid, e.filemode)

            new_tree_oid = tb.write()
            new_tree_hex = self.repo[new_tree_oid].hex
            # the last element is an empty string
            filename = dir_path.split('/')[-2]

        parent = self.repo.lookup_reference('refs/heads/%s' % branch)
        commit = self.repo.create_commit(
            'refs/heads/%s' % (branch),
            committer,
            committer,
            comment,
            new_tree_oid,
            [parent.oid],
        )
        return self.repo[commit].hex

    def create_tag(self, name, target):
        r"""
        Create a new tag.
        """
        if not is_valid_value(name):
            raise InvalidParamException("name is required")
        if not is_valid_hex(target):
            raise InvalidParamException("target is invalid")

        target = sha_hex2bin(target)
        try:
            self.repo.create_reference('refs/tags/%s' % name, target)
        except Exception, e:
            raise InvalidParamException(str(e))

        return True

    def delete_tag(self, name):
        r"""
        Delete the tag for the given name.
        """
        if not is_valid_value(name):
            raise InvalidParamException("name is required")

        try:
            ref = self.repo.lookup_reference('refs/tags/%s' % name)
            ref.delete()
        except Exception, e:
            raise InvalidParamException(str(e))

        return True

    def branch_tree(self, name):
        r"""
        Return the root node of the branch.
        """
        try:
            ref = self.repo.lookup_reference('refs/heads/%s' % name)
        except Exception, e:
            raise InvalidParamException(str(e))
        commit = self.repo[ref.oid]
        return commit.tree

    def tag_tree(self, name):
        r"""
        Return the root node of the tag.
        """
        try:
            ref = self.repo.lookup_reference('refs/tags/%s' % name)
        except Exception, e:
            raise InvalidParamException(str(e))
        tag = self.repo[ref.oid]
        return tag.tree

    def commit_tree(self, hex_):
        r"""
        Return the root node of the commit.
        """
        if not is_valid_hex(hex_):
            raise InvalidParamException('hex is required')
        commit = self.repo[sha_hex2bin(hex_)]
        return commit.tree
