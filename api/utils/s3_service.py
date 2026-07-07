import os
import uuid
import logging
import boto3
from botocore.client import Config
from fastapi import UploadFile
from django.conf import settings

logger = logging.getLogger("django")

class S3Service:
    @staticmethod
    def get_s3_client():
        """
        Creates and returns a boto3 S3 client configured for Supabase Storage.
        """
        return boto3.client(
            's3',
            endpoint_url=settings.SUPABASE_S3_ENDPOINT_URL,
            aws_access_key_id=settings.SUPABASE_S3_ACCESS_KEY_ID,
            aws_secret_access_key=settings.SUPABASE_S3_SECRET_ACCESS_KEY,
            region_name=settings.SUPABASE_S3_REGION,
            config=Config(signature_version='s3v4')
        )

    @classmethod
    async def upload_file(cls, file: UploadFile, folder: str = "products") -> dict:
        """
        Uploads an image file to S3-compatible Supabase Storage.
        Returns a dict containing the file key, the S3 URL, and the public Supabase URL.
        """
        s3_client = cls.get_s3_client()
        bucket_name = settings.SUPABASE_S3_BUCKET_NAME

        # Generate a unique key for the file
        ext = os.path.splitext(file.filename)[1].lower()
        unique_filename = f"{uuid.uuid4()}{ext}"
        key = f"{folder}/{unique_filename}" if folder else unique_filename

        content = await file.read()

        try:
            # Upload object to bucket
            s3_client.put_object(
                Bucket=bucket_name,
                Key=key,
                Body=content,
                ContentType=file.content_type
            )

            # Generate default S3 URL
            s3_url = f"{settings.SUPABASE_S3_ENDPOINT_URL}/{bucket_name}/{key}"

            # Generate Supabase Public URL:
            # Format: https://<project-ref>.supabase.co/storage/v1/object/public/<bucket-name>/<key>
            project_ref = ""
            endpoint_host = settings.SUPABASE_S3_ENDPOINT_URL.split("://")[1]
            if ".storage.supabase.co" in endpoint_host:
                project_ref = endpoint_host.split(".storage.supabase.co")[0]
            # https://rmjipqwaimxoyqownkyg.storage.supabase.co/storage/v1/s3
            if project_ref:
                public_url = f"https://{project_ref}.supabase.co/storage/v1/object/public/{bucket_name}/{key}"
            else:
                public_url = s3_url

            return {
                "file_key": key,
                "s3_url": s3_url,
                "public_url": public_url
            }
        except Exception as e:
            logger.error(f"S3 upload error: {str(e)}")
            raise e
        finally:
            # Reset file pointer for any future reads
            await file.seek(0)
