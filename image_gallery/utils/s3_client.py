import logging
import os
from typing import List, Dict

import boto3
from botocore.client import Config

LOG = logging.getLogger(__name__)


def get_s3_client():
    session = boto3.session.Session()
    return session.client(
        "s3",
        endpoint_url=os.getenv("S3_ENDPOINT_URL"),
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        region_name="ru-msk",
        config=Config(
            signature_version="s3v4",
            s3={"addressing_style": "path"},
            user_agent_extra="",
            request_checksum_calculation="when_required",
            response_checksum_validation="when_required"
        )
    )


def upload_to_s3(file_data: bytes, filename: str, ip: str):
    s3 = get_s3_client()
    bucket_name = os.getenv("S3_BUCKET_NAME")
    s3.put_object(
        Bucket=bucket_name,
        Key=filename,
        Body=file_data,
        Metadata={"ip": ip}
    )


def list_images() -> List[Dict]:
    s3 = get_s3_client()
    bucket_name = os.getenv("S3_BUCKET_NAME")
    images = []
    try:
        response = s3.list_objects_v2(Bucket=bucket_name)
        if "Contents" in response:
            for item in response["Contents"]:
                head_response = s3.head_object(
                    Bucket=bucket_name,
                    Key=item["Key"]
                )
                uploader_ip = head_response.get("Metadata", {}
                                                ).get("Ip", "Unknown")

                url = s3.generate_presigned_url(
                    "get_object",
                    Params={"Bucket": bucket_name, "Key": item["Key"]},
                    ExpiresIn=3600,
                )
                images.append(
                    {
                        "name": item["Key"],
                        "url": url,
                        "size": item["Size"],
                        "date":
                            item["LastModified"].strftime("%Y-%m-%d %H:%M:%S"),
                        "ip": uploader_ip
                    }
                )
    except Exception as e:
        raise Exception(f"S3 list error: {str(e)}")

    return images


def allowed_file(filename: str) -> bool:
    allowed_extensions = {"png", "jpg", "jpeg", "gif", "webp"}
    return ("." in filename and filename.rsplit(".", 1)[1].lower()
            in allowed_extensions)
