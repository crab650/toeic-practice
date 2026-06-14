import json
import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE = BASE_DIR / 'trainer.db'
CONFIG_FILE = BASE_DIR / 'config.json'
CACHE_DIR = BASE_DIR / 'audio_cache'

DEFAULT_HOST = '127.0.0.1'
DEFAULT_PORT = 8000
DEFAULT_GEMINI_MODEL = 'gemini-3.1-flash-lite'


def get_config_file_data():
    if not CONFIG_FILE.exists():
        return {}
    try:
        with CONFIG_FILE.open('r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}


def get_config():
    config = get_config_file_data()

    env_api_key = os.environ.get('GEMINI_API_KEY', '').strip()
    if env_api_key:
        config['gemini_api_key'] = env_api_key

    env_model = os.environ.get('GEMINI_MODEL', '').strip()
    if env_model:
        config['gemini_model'] = env_model
    elif not config.get('gemini_model'):
        config['gemini_model'] = DEFAULT_GEMINI_MODEL

    return config


def save_config(config_data):
    try:
        with CONFIG_FILE.open('w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=2)
    except Exception as e:
        print(f"Error saving config: {e}")
