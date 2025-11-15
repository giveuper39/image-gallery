import io
import logging
import os

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_httpauth import HTTPBasicAuth
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from PIL import Image

from image_gallery.utils import s3_client, auth_manager

main_bp = Blueprint("main", __name__)
LOG = logging.getLogger()
auth = HTTPBasicAuth()
users = {"admin": generate_password_hash(os.getenv("ADMIN_PASSWORD"))}


@main_bp.route("/")
def index():
    try:
        images = s3_client.list_images()
    except Exception as e:
        flash(f"Error loading images: {str(e)}", "error")
        images = []

    return render_template("index.html", images=images,
                           upload_auth_enabled=auth_manager.is_upload_auth_enabled())


@auth.verify_password
def verify_password(username, password):
    if username in users and check_password_hash(users[username], password):
        return username


@main_bp.route("/upload", methods=["POST"])
def upload_file():
    if auth_manager.is_upload_auth_enabled():
        auth_header = request.authorization
        valid_credentials = (
                auth_header
                and auth_header.type == "basic"
                and verify_password(auth_header.username, auth_header.password)
        )

        if not valid_credentials:
            return (
                "Login required for upload",
                401,
                {"WWW-Authenticate": 'Basic realm="Authentication Required"'}
            )

    if request.headers.get("X-Forwarded-For"):
        client_ip = request.headers.get("X-Forwarded-For").split(",")[0]
    else:
        client_ip = request.remote_addr

    if "file" not in request.files:
        flash("No file selected", "error")
        return redirect(url_for("main.index"))

    file = request.files["file"]
    if file.filename == "":
        flash("No file selected", "error")
        return redirect(url_for("main.index"))

    if file and s3_client.allowed_file(file.filename):
        image = Image.open(file.stream)

        if image.mode in ("RGBA", "P"):
            image = image.convert("RGB")

        if image.width > 1200:
            ratio = 1200 / image.width
            new_size = (1200, int(image.height * ratio))
            image = image.resize(new_size, Image.Resampling.LANCZOS)

        output = io.BytesIO()
        image.save(output, format="JPEG", quality=85, optimize=True)
        file_data = output.getvalue()
        filename = secure_filename(file.filename)

        s3_client.upload_to_s3(file_data, filename, client_ip)
        flash(f"Uploaded {filename}", "success")
        LOG.info("Uploaded %s from %s", filename, client_ip)

    else:
        flash("Invalid file type. Allowed: PNG, JPG, JPEG, GIF, WEBP", "error")

    return redirect(url_for("main.index"))


@main_bp.route("/admin", methods=["GET", "POST"])
@auth.login_required
def admin_panel():
    if request.method == "POST":
        new_status = request.form.get("upload_auth") == "enable"
        auth_manager.set_auth_status(new_status)
        flash(
            f"🔒 Upload authorization {'enabled' if new_status else 'disabled'}",
            "success",
        )

    current_status = auth_manager.get_auth_status()
    upload_count = len(s3_client.list_images())

    return render_template(
        "admin.html", auth_enabled=current_status, upload_count=upload_count
    )


@main_bp.route("/health")
def health():
    return {"status": "ok", "service": "Image Gallery"}
