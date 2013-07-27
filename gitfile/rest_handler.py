from gitfile.git import *
from gitfile.utils import *
from gitfile.exceptions import *
import werkzeug.exceptions as ex
import json


class RESTHandler(object):
    @classmethod
    def get_noun_handler(self, git, request, noun):
        try:
            noun_class = globals()[noun.capitalize()]
        except KeyError:
            raise ex.NotFound('Unsupported noun: %s' %
                              noun.capitalize())
        return noun_class(git, request)


class NounHandler(object):
    def __init__(self, git, request):
        self.git = git
        self.request = request

    def handle(self, path):
        branch_or_tag_or_sha1 = path.pop(0) if len(path) else None
        method_name = 'handle_' + self.request.method.lower()
        if len(path):
            method_name = method_name + '_file'

        try:
            method = getattr(self, method_name)
        except AttributeError:
            raise ex.NotFound('Unsupported operation')

        return method(branch_or_tag_or_sha1, path)


class Blobs(NounHandler):
    def handle_get(self, sha1, *args):
        content = self.git.get_content(sha1)
        if content is None:
            raise ex.NotFound('No blob found for the given id: ' + sha1)
        return content

    def handle_post(self, *args):
        sha1 = self.git.create_content(self.request.data)
        return {'sha1': sha1}


class Branches(NounHandler):
    def handle_get_branches(self):
        branches = self.git.branches()
        return {'entries': branches}

    def handle_get(self, branch, paths):
        if branch is None:
            return self.handle_get_branches()

        branches = self.git.branches()
        try:
            sha1 = branches[branch]
        except KeyError:
            raise ex.NotFound('No branch found for the given name: ' + branch)

        branch_tree = self.git.branch_tree(branch)
        return {
            'name': branch,
            'type': 'branch',
            'sha1': sha1,
            'entries': [entry_to_dict(x, self.git.repo) for x in branch_tree],
        }

    def handle_post(self, branch, paths):
        param = json.loads(self.request.data)

        branches = self.git.branches()
        if branch in branches:
            raise ex.Conflict("'%s' branch already exists." % branch)

        self.git.create_branch(branch, param.get('target'))
        return {}

    def handle_delete(self, branch, paths):
        self.git.delete_branch(branch)
        return {}

    def handle_get_file(self, branch, paths):
        entry = self.git.find_entry('/'.join(paths), branch=branch)
        if entry:
            d = entry_to_dict(entry, self.git.repo)
            if d['type'] == 'tree':
                entries = [
                    entry_to_dict(x, self.git.repo)
                    for x in self.git.repo[entry.oid]
                ]
                d['entries'] = entries
            return d
        else:
            raise ex.NotFound('File does not exist in %s branch' % branch)

    def handle_post_file(self, branch, paths):
        param = json.loads(self.request.data)
        commit_hex = self.git.create_entry(
            branch,
            '/'.join(paths),
            param.get('sha1'),
            mode=getattr(param, 'mode', None),
            author_name=param.get('author_name'),
            author_email=param.get('author_email'),
            comment=getattr(param, 'comment', ''))
        return {}

    def handle_put_file(self, branch, paths):
        param = json.loads(self.request.data)
        commit_hex = self.git.update_entry(
            branch,
            '/'.join(paths),
            param.get('sha1'),
            mode=getattr(param, 'mode', None),
            author_name=param.get('author_name'),
            author_email=param.get('author_email'),
            comment=getattr(param, 'comment', ''))
        return {}

    def handle_delete_file(self, branch, paths):
        param = json.loads(self.request.data)
        commit_hex = self.git.delete_entry(
            branch,
            '/'.join(paths),
            author_name=param.get('author_name'),
            author_email=param.get('author_email'),
            comment=getattr(param, 'comment', ''))
        return {}


class Tags(NounHandler):
    def handle_get_tags(self):
        tags = self.git.tags()
        return {'entries': tags}

    def handle_get(self, tag, paths):
        if tag is None:
            return self.handle_get_tags()

        tags = self.git.tags()
        try:
            sha1 = tags[tag]
        except KeyError:
            raise ex.NotFound('No tag found for the given name: ' + tag)

        tag_tree = self.git.tag_tree(tag)
        return {
            'name': tag,
            'type': 'tag',
            'sha1': sha1,
            'entries': [
                entry_to_dict(x, self.git.repo) for x in tag_tree
            ],
        }

    def handle_post(self, tag, paths):
        param = json.loads(self.request.data)

        tags = self.git.tags()
        if tag in tags:
            raise ex.Conflict("'%s' tag already exists." % tag)

        self.git.create_tag(tag, param.get('target'))
        return {}

    def handle_delete(self, tag, paths):
        self.git.delete_tag(tag)
        return {}

    def handle_get_file(self, tag, paths):
        entry = self.git.find_entry('/'.join(paths), tag=tag)
        if entry:
            d = entry_to_dict(entry, self.git.repo)
            if d['type'] == 'tree':
                entries = [
                    entry_to_dict(x, self.git.repo)
                    for x in self.git.repo[entry.oid]
                ]
                d['entries'] = entries
            return d
        else:
            raise ex.NotFound('File does not exist in %s tag' % tag)


class Commits(NounHandler):
    def handle_get(self, sha1, paths):
        commit_tree = self.git.commit_tree(sha1)
        return {
            'name': sha1,
            'type': 'commit',
            'sha1': sha1,
            'entries': [entry_to_dict(x, self.git.repo) for x in commit_tree],
        }

    def handle_get_file(self, sha1, paths):
        entry = self.git.find_entry('/'.join(paths), commit=sha1)
        if entry:
            d = entry_to_dict(entry, self.git.repo)
            if d['type'] == 'tree':
                entries = [
                    entry_to_dict(x, self.git.repo)
                    for x in self.git.repo[entry.oid]
                ]
                d['entries'] = entries
            return d
        else:
            raise ex.NotFound('File does not exist in %s commit' % sha1)
