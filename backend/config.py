import json
import os
import sys
import ctypes
from ctypes import wintypes
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE = BASE_DIR / 'trainer.db'
CONFIG_FILE = BASE_DIR / 'config.json'
CACHE_DIR = BASE_DIR / 'audio_cache'

DEFAULT_HOST = '127.0.0.1'
DEFAULT_PORT = 8000
DEFAULT_GEMINI_MODEL = 'gemini-3.1-flash-lite'
DEFAULT_PLATFORM_BASE_URL = 'http://127.0.0.1:5050'
PLATFORM_CREDENTIAL_TARGET = 'SmartEnglishTrainer/learning-platform-token'
PLATFORM_API_SUFFIXES = ('/api/v1/study/practice-logs', '/api/v1/auth/me')


class _CREDENTIALW(ctypes.Structure):
    _fields_ = [
        ('Flags', wintypes.DWORD), ('Type', wintypes.DWORD),
        ('TargetName', wintypes.LPWSTR), ('Comment', wintypes.LPWSTR),
        ('LastWritten', wintypes.FILETIME), ('CredentialBlobSize', wintypes.DWORD),
        ('CredentialBlob', ctypes.POINTER(ctypes.c_ubyte)), ('Persist', wintypes.DWORD),
        ('AttributeCount', wintypes.DWORD), ('Attributes', ctypes.c_void_p),
        ('TargetAlias', wintypes.LPWSTR), ('UserName', wintypes.LPWSTR),
    ]


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

    config['platform_base_url'] = os.environ.get(
        'LEARNING_PLATFORM_BASE_URL',
        config.get('platform_base_url', DEFAULT_PLATFORM_BASE_URL),
    ).strip().rstrip('/')
    for suffix in PLATFORM_API_SUFFIXES:
        if config['platform_base_url'].endswith(suffix):
            config['platform_base_url'] = config['platform_base_url'][:-len(suffix)].rstrip('/')
            break

    return config


def normalize_platform_base_url(value):
    value = (value or '').strip().rstrip('/')
    for suffix in PLATFORM_API_SUFFIXES:
        if value.endswith(suffix):
            return value[:-len(suffix)].rstrip('/')
    return value


def get_platform_token():
    """Read the platform token without ever placing it in config.json."""
    env_token = os.environ.get('LEARNING_PLATFORM_TOKEN', '').strip()
    if env_token:
        return env_token, 'environment'
    if sys.platform != 'win32':
        return '', 'none'
    credential_ptr = ctypes.POINTER(_CREDENTIALW)()
    try:
        advapi32 = ctypes.WinDLL('Advapi32.dll')
        advapi32.CredReadW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD, ctypes.POINTER(ctypes.POINTER(_CREDENTIALW))]
        advapi32.CredReadW.restype = wintypes.BOOL
        advapi32.CredFree.argtypes = [ctypes.c_void_p]
        if not advapi32.CredReadW(PLATFORM_CREDENTIAL_TARGET, 1, 0, ctypes.byref(credential_ptr)):
            return '', 'none'
        credential = credential_ptr.contents
        blob = ctypes.string_at(credential.CredentialBlob, credential.CredentialBlobSize)
        token = blob.decode('utf-16-le').strip()
        return token, 'credential_manager' if token else 'none'
    except Exception:
        return '', 'none'
    finally:
        if credential_ptr:
            ctypes.WinDLL('Advapi32.dll').CredFree(credential_ptr)


def save_platform_token(token):
    if sys.platform != 'win32':
        return False
    try:
        advapi32 = ctypes.WinDLL('Advapi32.dll')
        advapi32.CredDeleteW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD]
        advapi32.CredDeleteW.restype = wintypes.BOOL
        advapi32.CredWriteW.argtypes = [ctypes.POINTER(_CREDENTIALW), wintypes.DWORD]
        advapi32.CredWriteW.restype = wintypes.BOOL
        if not token:
            return bool(advapi32.CredDeleteW(PLATFORM_CREDENTIAL_TARGET, 1, 0))
        blob = token.encode('utf-16-le')
        blob_buffer = (ctypes.c_ubyte * len(blob)).from_buffer_copy(blob)
        credential = _CREDENTIALW()
        credential.Type = 1  # CRED_TYPE_GENERIC
        credential.TargetName = PLATFORM_CREDENTIAL_TARGET
        credential.CredentialBlobSize = len(blob)
        credential.CredentialBlob = ctypes.cast(blob_buffer, ctypes.POINTER(ctypes.c_ubyte))
        credential.Persist = 2  # CRED_PERSIST_LOCAL_MACHINE
        credential.UserName = 'Smart English Trainer'
        return bool(advapi32.CredWriteW(ctypes.byref(credential), 0))
    except Exception:
        return False


def save_config(config_data):
    try:
        with CONFIG_FILE.open('w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=2)
    except Exception as e:
        print(f"Error saving config: {e}")
