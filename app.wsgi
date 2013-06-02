from gitfile.rest_service import create_app
from os.path import abspath, dirname
import os

GIT_DIR = abspath(dirname(__file__))
PORT = int(os.environ.get('PORT', 5000))


if __name__ == '__main__':
    from werkzeug.serving import run_simple
    app = create_app(GIT_DIR)
    run_simple('', PORT, app, use_debugger=True, use_reloader=True)
