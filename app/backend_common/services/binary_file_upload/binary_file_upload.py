from app.backend_common.service_clients.aws.services.s3 import AWSS3ServiceClient
from deputydev_core.utils.config_manager import ConfigManager

class BinaryFileUpload:
    s3_client = AWSS3ServiceClient(
        bucket_name=ConfigManager.configs["AWS_S3_BUCKET"]["AWS_BUCKET_NAME"],
        region_name=ConfigManager.configs["AWS_S3_BUCKET"]["AWS_REGION"],
    )

    PRESIGNED_URL_EXPIRY = ConfigManager.configs["BINARY_UPLOAD"]["PRESIGNED_URL_EXPIRY"]

    @classmethod
    async def get_presigned_urls_for_upload(cls, s3_key: str) -> str:
        """
        Generate presigned URLs for uploading binary, to be given to the client
        """
        presigned_post_url = await cls.s3_client.create_presigned_put_url(expiry=cls.PRESIGNED_URL_EXPIRY, s3_key=s3_key)
        return presigned_post_url