import json

AUTH_CONFIG_FILE = "auth_config.json"


def get_auth_status():
    try:
        with open(AUTH_CONFIG_FILE, "r") as f:
            config = json.load(f)
            return config.get("upload_auth_enabled", True)
    except FileNotFoundError:
        set_auth_status(True)
        return True


def set_auth_status(enabled):
    config = {"upload_auth_enabled": enabled}
    with open(AUTH_CONFIG_FILE, "w") as f:
        json.dump(config, f)


def is_upload_auth_enabled():
    return get_auth_status()
