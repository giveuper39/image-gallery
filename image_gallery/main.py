from image_gallery.routes import main_bp
from flask import Flask

import os
import logging


def create_app():
    base_dir = os.path.abspath(os.path.dirname(__file__))
    template_dir = os.path.join(base_dir, "..", "templates")

    app = Flask(__name__, template_folder=template_dir, static_folder="../static")

    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret-key")
    app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16 MB

    required_vars = [
        "AWS_ACCESS_KEY_ID",
        "AWS_SECRET_ACCESS_KEY",
        "S3_BUCKET_NAME",
        "S3_ENDPOINT_URL",
    ]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        print(f"WARNING: Missing environment variables: {missing_vars}")

    app.register_blueprint(main_bp)

    return app


app = create_app()
logging.basicConfig(level=logging.INFO)

LOG = logging.getLogger(__name__)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
