import io
import logging

from flask import Blueprint, render_template, request, redirect, url_for, flash
from werkzeug.utils import secure_filename
from PIL import Image

from image_gallery.utils import s3_client

main_bp = Blueprint("main", __name__)
LOG = logging.getLogger()


@main_bp.route("/")
def index():
    try:
        images = s3_client.list_images()
    except Exception as e:
        flash(f"Error loading images: {str(e)}", "error")
        images = []

    return render_template("index.html", images=images)


@main_bp.route("/upload", methods=["POST"])
def upload_file():
    if request.headers.get('X-Forwarded-For'):
        client_ip = request.headers.get('X-Forwarded-For').split(',')[0]
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


@main_bp.route("/health")
def health():
    return {"status": "ok", "service": "Image Gallery"}
