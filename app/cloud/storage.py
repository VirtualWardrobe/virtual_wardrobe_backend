from typing import Optional

from env import env


def _storage_module():
    if env.CLOUD_PROVIDER == "GCP":
        from app.cloud.gcp import storage as storage_module
    elif env.CLOUD_PROVIDER == "AWS":
        from app.cloud.aws import storage as storage_module
    else:
        raise ValueError("VW_CLOUD_PROVIDER must be either 'GCP' or 'AWS'")
    return storage_module


def get_media_bucket() -> str:
    return env.get_media_bucket()


async def upload_file(
    file: bytes,
    bucket_name: str,
    folder_name: Optional[str] = None,
    content_type: Optional[str] = None,
    filename: Optional[str] = None,
) -> str:
    storage_module = _storage_module()
    if env.CLOUD_PROVIDER == "GCP":
        return await storage_module.upload_file_to_gcs(
            file=file,
            bucket_name=bucket_name,
            folder_name=folder_name,
            content_type=content_type,
            filename=filename,
        )
    return await storage_module.upload_file_to_s3(
        file=file,
        bucket_name=bucket_name,
        folder_name=folder_name,
        content_type=content_type,
        filename=filename,
    )


async def delete_file(file_url: str, bucket_name: str) -> dict:
    storage_module = _storage_module()
    if env.CLOUD_PROVIDER == "GCP":
        return await storage_module.delete_file_from_gcs(
            file_url=file_url, bucket_name=bucket_name
        )
    return await storage_module.delete_file_from_s3(
        file_url=file_url, bucket_name=bucket_name
    )
