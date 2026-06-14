from flask import Blueprint, jsonify, request

from ..config import DEFAULT_GEMINI_MODEL, get_config, get_config_file_data, save_config


settings_bp = Blueprint('settings', __name__)


@settings_bp.route('/api/settings/config', methods=['GET', 'POST'])
def handle_config():
    if request.method == 'POST':
        data = request.get_json() or {}
        api_key = data.get('gemini_api_key', '').strip()
        gemini_model = data.get('gemini_model', '').strip() or DEFAULT_GEMINI_MODEL

        config = get_config_file_data()
        if api_key:
            config['gemini_api_key'] = api_key
        config['gemini_model'] = gemini_model
        save_config(config)
        return jsonify({"success": True, "gemini_model": gemini_model})

    config = get_config()
    api_key = config.get('gemini_api_key', '')
    gemini_model = config.get('gemini_model', DEFAULT_GEMINI_MODEL)
    return jsonify({
        "gemini_api_key_set": bool(api_key),
        "gemini_api_key_masked": (api_key[:4] + "..." + api_key[-4:]) if len(api_key) > 8 else "",
        "gemini_model": gemini_model,
        "default_gemini_model": DEFAULT_GEMINI_MODEL,
    })
