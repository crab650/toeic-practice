from flask import Blueprint, jsonify, request

from ..config import (
    DEFAULT_GEMINI_MODEL, DEFAULT_PLATFORM_BASE_URL, get_config,
    get_config_file_data, get_platform_token, save_config, save_platform_token,
    normalize_platform_base_url,
)


settings_bp = Blueprint('settings', __name__)


@settings_bp.route('/api/settings/config', methods=['GET', 'POST'])
def handle_config():
    if request.method == 'POST':
        data = request.get_json() or {}
        api_key = data.get('gemini_api_key', '').strip()
        gemini_model = data.get('gemini_model', '').strip() or DEFAULT_GEMINI_MODEL
        platform_base_url = normalize_platform_base_url(data.get('platform_base_url', ''))
        platform_token = data.get('platform_token', '').strip()

        config = get_config_file_data()
        if api_key:
            config['gemini_api_key'] = api_key
        config['gemini_model'] = gemini_model
        if platform_base_url:
            config['platform_base_url'] = platform_base_url
        save_config(config)
        token_saved = None
        if platform_token:
            token_saved = save_platform_token(platform_token)
        if token_saved is False:
            return jsonify({"error": "無法寫入 Windows Credential Manager；開發時可改用 LEARNING_PLATFORM_TOKEN 環境變數。"}), 500
        return jsonify({"success": True, "gemini_model": gemini_model})

    config = get_config()
    api_key = config.get('gemini_api_key', '')
    gemini_model = config.get('gemini_model', DEFAULT_GEMINI_MODEL)
    platform_token, token_source = get_platform_token()
    return jsonify({
        "gemini_api_key_set": bool(api_key),
        "gemini_api_key_masked": (api_key[:4] + "..." + api_key[-4:]) if len(api_key) > 8 else "",
        "gemini_model": gemini_model,
        "default_gemini_model": DEFAULT_GEMINI_MODEL,
        "platform_base_url": config.get('platform_base_url', DEFAULT_PLATFORM_BASE_URL),
        "platform_token_set": bool(platform_token),
        "platform_token_source": token_source,
    })
