from typing import Dict
from typing import Any
from app.backend_common.service_clients.aws.aws_client_manager import AWSClientManager
from types_aiobotocore_s3.client import S3Client

from app.backend_common.service_clients.aws.dataclasses.aws_client_manager import AWSConnectionParams


class AWSS3ServiceClient:
    # constructor
    def __init__(self, bucket_name: str, region_name: str):
        self.region_name = region_name
        self.bucket_name = bucket_name
        self.aws_service_name = "s3"

        self.aws_client_manager = AWSClientManager(
            aws_service_name=self.aws_service_name,
            region_name=self.region_name,
            aws_connection_params=AWSConnectionParams(
                endpoint_url="http://localhost:4566",
                aws_access_key_id="DUMMY_ACCESS_KEY_ID",
                aws_secret_access_key="DUMMY_SECRET_ACCESS_KEY",
            ),
        )

    async def create_presigned_post_url(
        self, object_name: str, content_type: str, expiry: int, s3_key: str, min_bytes: int, max_bytes: int
    ) -> Dict[str, Any]:
        """
        Generate a presigned URL to share an S3 object
        """
        s3_client: S3Client = await self.aws_client_manager.get_client()  # type: ignore
        fields = {"Content-Type": content_type, "acl": "private", "key": s3_key}
        response = await s3_client.generate_presigned_post(
            Bucket=self.bucket_name,
            Key=s3_key,
            Fields=fields,
            Conditions=[
                {"Content-Type": content_type},
                ["content-length-range", min_bytes, max_bytes],
                {"acl": "private"},
                ["starts-with", "$key", s3_key],
            ],
            ExpiresIn=expiry,
        )
        return response

    async def create_presigned_get_url(self, s3_key: str, expiry: int) -> str:
        """
        Generate a presigned URL to share an S3 object
        """
        s3_client: S3Client = await self.aws_client_manager.get_client()  # type: ignore
        response = await s3_client.generate_presigned_url(
            ClientMethod="get_object",
            Params={"Bucket": self.bucket_name, "Key": s3_key},
            ExpiresIn=expiry,
        )
        return response

    async def get_object(self, object_name: str) -> bytes:
        s3_client: S3Client = await self.aws_client_manager.get_client()  # type: ignore
        response = await s3_client.get_object(Bucket=self.bucket_name, Key=object_name)
        async with response["Body"] as stream:  # type: ignore
            return await stream.read()  # type: ignore
