import os

from backend import create_app
from backend.config import DEFAULT_HOST, DEFAULT_PORT


app = create_app()


if __name__ == '__main__':
    host = os.environ.get('APP_HOST', DEFAULT_HOST)
    port = int(os.environ.get('APP_PORT', DEFAULT_PORT))
    debug = os.environ.get('FLASK_DEBUG', '').lower() in {'1', 'true', 'yes', 'on'}
    app.run(host=host, port=port, debug=debug)
