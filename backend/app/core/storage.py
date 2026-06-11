from typing import BinaryIO

import boto3

from app.core.config import get_settings


def _client():
    settings = get_settings()
    return boto3.client(
        "s3",
        endpoint_url=settings.minio_endpoint,
        aws_access_key_id=settings.minio_access_key,
        aws_secret_access_key=settings.minio_secret_key,
    )


def upload_file(file_obj: BinaryIO, key: str, content_type: str) -> None:
    settings = get_settings()
    _client().upload_fileobj(
        file_obj,
        settings.minio_bucket,
        key,
        ExtraArgs={"ContentType": content_type},
    )


def delete_file(key: str) -> None:
    settings = get_settings()
    _client().delete_object(Bucket=settings.minio_bucket, Key=key)


def get_presigned_url(key: str, expires_seconds: int = 3600) -> str:
    settings = get_settings()
    return _client().generate_presigned_url(
        "get_object",
        Params={"Bucket": settings.minio_bucket, "Key": key},
        ExpiresIn=expires_seconds,
    )
