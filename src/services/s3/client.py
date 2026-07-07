import aioboto3
from botocore.config import Config

from config import settings
from contextlib import asynccontextmanager


class S3Client:
    def __init__(self):
        self.endpoint_url = settings.S3_ENDPOINT_URL
        self.bucket = settings.S3_BUCKET_NAME
        self.access_key = settings.S3_ACCESS_KEY
        self.secret_key = settings.S3_SECRET_KEY
        self.force_path_style = settings.S3_FORCE_PATH_STYLE
        self.region = settings.S3_REGION
        self.session = aioboto3.Session()

    @asynccontextmanager
    async def _client(self):
        async with self.session.client(
            "s3",
            endpoint_url=self.endpoint_url,
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
            region_name=self.region,
            config=Config(
                signature_version="s3v4",
                s3={"addressing_style": "path" if self.force_path_style else "virtual"},
            ),
        ) as client:
            yield client

    async def generate_upload_url(
        self,
        object_key: str,
        content_type: str,
        expires_in: int = settings.S3_LINK_EXPIRE_MINUTES * 60,
    ) -> str:
        async with self._client() as s3:
            url = await s3.generate_presigned_url(
                ClientMethod="put_object",
                Params={
                    "Bucket": self.bucket,
                    "Key": object_key,
                    "ContentType": content_type,
                },
                ExpiresIn=expires_in,
                HttpMethod="PUT",
            )
            return url

    async def generate_download_url(
        self,
        object_key: str,
        expires_in: int = settings.S3_LINK_EXPIRE_MINUTES * 60,
    ) -> str:
        async with self._client() as s3:
            url = await s3.generate_presigned_url(
                ClientMethod="get_object",
                Params={
                    "Bucket": self.bucket,
                    "Key": object_key,
                },
                ExpiresIn=expires_in,
                HttpMethod="GET",
            )
            return url

    async def delete_object(self, object_key: str):
        async with self._client() as s3:
            await s3.delete_object(
                Bucket=self.bucket,
                Key=object_key,
            )

    async def object_exists(self, object_key: str) -> bool:
        async with self._client() as s3:
            try:
                await s3.head_object(Bucket=self.bucket, Key=object_key)
                return True
            except Exception:
                return False
