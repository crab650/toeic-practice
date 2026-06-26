from flask import Flask

from .config import BASE_DIR
from .db import init_db
from .routes.pet import pet_bp
from .routes.settings import settings_bp
from .routes.toeic_part2 import toeic_part2_bp
from .routes.toeic_part5 import toeic_part5_bp
from .routes.units import units_bp
from .routes.web import web_bp


def create_app():
    app = Flask(__name__, static_folder=str(BASE_DIR), static_url_path='')
    init_db()
    app.register_blueprint(web_bp)
    app.register_blueprint(units_bp)
    app.register_blueprint(pet_bp)
    app.register_blueprint(settings_bp)
    app.register_blueprint(toeic_part5_bp)
    app.register_blueprint(toeic_part2_bp)
    return app
