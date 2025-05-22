from typing import Optional
from app.backend_common.service_clients.aws.aws_client import AWSClient
from deputydev_core.utils.config_manager import ConfigManager
from aiobotocore.session import get_session 

class AWSS3ServiceClient:
    def __init__(self):
        self.aws_service_name = ConfigManager.configs['AWS_S3_BUCKET']['AWS_SERVICE_NAME']
        self.region_name = ConfigManager.configs['AWS_S3_BUCKET']['AWS_REGION']
        self.bucket_name = ConfigManager.configs['AWS_S3_BUCKET']['AWS_BUCKET_NAME']
        self.aws_secret_access_key = ConfigManager.configs['AWS_S3_BUCKET']['AWS_SECRET_ACCESS_KEY']
        self.aws_access_key_id = ConfigManager.configs['AWS_S3_BUCKET']['AWS_ACCESS_KEY_ID']
        self.expiration = ConfigManager.configs['AWS_S3_BUCKET']['EXPIRATION']
        self.file_min_size = ConfigManager.configs['AWS_S3_BUCKET']['FILE_MIN_SIZE']
        self.file_max_size = ConfigManager.configs['AWS_S3_BUCKET']['FILE_MAX_SIZE']

    async def create_client(self):
        session = get_session()
        try:
            client = session.create_client(
                self.aws_service_name,
                region_name=self.region_name,
                aws_secret_access_key=self.aws_secret_access_key,
                aws_access_key_id=self.aws_access_key_id,
            )
            return client
        except Exception as e:
                raise Exception(f"Failed to create S3 client: {e}")

    async def create_presigned_post_url(self, object_name: str, content_type: str, expiration: int = 600) -> str:

        if content_type not in ["image/jpeg", "image/jpg", "image/png", "image/webp"]:
            raise ValueError("Invalid content type. Allowed: jpeg, jpg, png, webp")
        
        region_name = "ap-south-1"
        aws_access_key_id="test"
        aws_secret_access_key = "test"
        endpoint_url="http://localhost:4566"


        try:
            s3_client = await self.create_client()
            s3_client = await AWSClient.create_client(
                aws_service_name="s3",
                region_name=region_name,
                aws_secret_access_key=aws_secret_access_key,
                aws_access_key_id=aws_access_key_id,
                endpoint_url=endpoint_url,
            )

            async with s3_client as s3:
                conditions = [
                {"Content-Type": content_type},
                ["content-length-range", self.file_min_size, self.file_max_size],  # Max 5MB
                {"acl": "private"},
                ["starts-with", "$key", object_name]
                ]

                fields = {
                    "Content-Type": content_type,
                    "acl": "private",
                    "key": object_name
                }

                post_url = await s3.generate_presigned_post(
                    Bucket=self.bucket_name,
                    Key=object_name,
                    Fields=fields,
                    Conditions=conditions,
                    ExpiresIn=expiration
                )

                get_url = await s3.generate_presigned_url(
                    ClientMethod='get_object',
                    Params={
                        'Bucket': self.bucket_name,
                        'Key': object_name
                    },
                    ExpiresIn=expiration
                )

                post_url["post_url"] = post_url.pop("url")
                post_url["get_url"] = get_url 

                return post_url
            
        except Exception as e:
            raise Exception(f"Failed to generate presigned URL: {e}")



    async def create_presigned_get_url(
        self,
        object_name: str,
        expiration: int = 600
    ) -> str:
        region_name = "ap-south-1"
        aws_access_key_id="test"
        aws_secret_access_key = "test"
        endpoint_url="http://localhost:4566"

        try:
            # s3_client = await self.create_client()
            s3_client = await AWSClient.create_client(aws_service_name="s3",
                                                      region_name=region_name,
                                                      aws_secret_access_key=aws_secret_access_key,
                                                      aws_access_key_id=aws_access_key_id,
                                                      endpoint_url=endpoint_url,)
            async with s3_client as s3:
                response = await s3.generate_presigned_url(
                    ClientMethod='get_object',
                    Params={
                        'Bucket': self.bucket_name,
                        'Key': object_name
                    },
                    ExpiresIn=expiration
                )
                return response
        except Exception as e:
            raise Exception(f"Failed to generate presigned GET URL: {e}")
        


    async def get_file(self, object_name: str) -> Optional[bytes]:
        region_name = "ap-south-1"
        aws_access_key_id="test"
        aws_secret_access_key = "test"
        endpoint_url="http://localhost:4566"

        try:
            # s3_client = await self.create_client()
            s3_client = await AWSClient.create_client(aws_service_name="s3",
                                                      region_name=region_name,
                                                      aws_secret_access_key=aws_secret_access_key,
                                                      aws_access_key_id=aws_access_key_id,
                                                      endpoint_url=endpoint_url,)
            async with s3_client as s3:
                response = await s3.get_object(
                    Bucket=self.bucket_name,
                    Key=object_name
                )
                async with response["Body"] as stream:
                    return await stream.read()
        except Exception as e:
            raise Exception(f"Failed to get file: {e}")