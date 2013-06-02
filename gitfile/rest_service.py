from werkzeug.wrappers import Request, Response
import werkzeug.exceptions as ex
import os
import json
from gitfile.git import *
from gitfile.rest_handler import *


class RESTService(object):

    def __init__(self, base_path):
        if not base_path:
            raise Exception('base_path is required')
        if not os.path.isdir(base_path):
            raise Exception('base_path is not a directory')
        self.base_path = base_path

    def __call__(self, environ, start_response):
        return self.wsgi_app(environ, start_response)

    def wsgi_app(self, environ, start_response):
        request = Request(environ)
        response = self.dispatch_request(request)
        return response(environ, start_response)

    def dispatch_request(self, request):
        repo, noun, path = self._split_path(request.path)

        try:
            if not repo:
                raise ex.NotFound('repository is not specified')

            if not noun:
                raise ex.NotFound('noun is not specified')

            gitdir = self.find_git_dir(repo)
            if not gitdir:
                raise ex.NotFound('No such repository')

            git = Git(gitdir)
            content = RESTHandler.get_noun_handler(git, request, noun).\
                handle(path)

            status = {
                'GET': [200, None],
                'HEAD': [200, None],
                'POST': [201, 'A resource created successfully.'],
                'PUT': [200, 'A resource updated successfully.'],
                'DELETE': [200, 'A resource deleted successfully.'],
            }[request.method]

            content_type = 'application/json'
            if noun.lower() == 'blobs' and (request.method in ['GET', 'HEAD']):
                content_type = 'application/octet-stream'

            if type(content).__name__ == 'dict':
                body = json.dumps({'error': False,
                                   'message': status[1],
                                   'result': content},
                                  sort_keys=True,
                                  indent=4)
            else:
                body = content
            response = Response(body, status=status[0], mimetype=content_type)
        except ex.HTTPException, e:
            return self.error_response(e)
        except ValueError, e:
            return self.error_response(ex.BadRequest(str(e)))
        except Exception, e:
            return self.error_response(ex.InternalServerError(str(e)))

        return response

    def error_response(self, error):
        body = json.dumps({
            'error': True,
            'message': getattr(error, 'description', 'Unknown error'),
        }, sort_keys=True, indent=4)
        return Response(body, status=error.code, mimetype='application/json')

    def find_git_dir(self, repo):
        path = os.path.join(self.base_path, repo)
        for dir in [path, path + '.git']:
            if os.path.isdir(dir):
                return dir
        return

    def _split_path(self, path):
        segments = path.rstrip('/').split('/')

        try:
            repo = segments[1]
        except:
            repo = None
        try:
            noun = segments[2]
        except:
            noun = None
        rest = segments[3:]

        return repo, noun, rest


def create_app(base_path):
    app = RESTService(base_path=base_path)
    return app
