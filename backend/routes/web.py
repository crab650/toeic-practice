from flask import Blueprint, send_from_directory

from ..config import BASE_DIR


web_bp = Blueprint('web', __name__)


@web_bp.route('/')
def index():
    return send_from_directory(BASE_DIR, 'index.html')
