from gitfile.rest_service import create_app
from os.path import abspath, dirname

GIT_DIR = abspath(dirname(__file__))


if __name__ == '__main__':
    from werkzeug.serving import run_simple
    app = create_app(GIT_DIR)
    run_simple('', 5000, app, use_debugger=True, use_reloader=True)
