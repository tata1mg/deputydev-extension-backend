import datetime
from typing import ClassVar, Dict, Optional, cast

from botocore.signers import CloudFrontSigner
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey


class AWSCloudFrontServiceClient:
    _signers: ClassVar[Dict[str, CloudFrontSigner]] = {}

    def __init__(
        self,
        distribution_url: str,
        key_pair_id: str,
        private_key_str: str,
        default_expiry: int = 1800,  # seconds
    ) -> None:
        self.distribution_url = distribution_url
        self.key_pair_id = key_pair_id
        self.private_key_str = private_key_str
        self.default_expiry = default_expiry

        if self.key_pair_id not in self._signers:
            self._signers[self.key_pair_id] = self._create_signer()

        self.signer = self._signers[self.key_pair_id]

    def _create_signer(self) -> CloudFrontSigner:
        """Create a CloudFront signer with the private key"""
        private_key = cast(
            RSAPrivateKey,
            serialization.load_pem_private_key(
                self.private_key_str.encode("utf-8"),
                password=None,
            ),
        )

        def rsa_signer(message: bytes) -> bytes:
            return private_key.sign(message, padding.PKCS1v15(), hashes.SHA1())

        return CloudFrontSigner(self.key_pair_id, rsa_signer)

    async def generate_signed_url(self, s3_key: str, expiry: Optional[int] = None) -> str:
        """
        Generate a signed CloudFront URL for the given S3 key

        Args:
            s3_key: The S3 key/path for the file
            expiry: Expiry time in seconds (defaults to configured value)

        Returns:
            Signed CloudFront URL
        """
        if expiry is None:
            expiry = self.default_expiry

        # Construct the CloudFront URL
        cloudfront_url = f"{self.distribution_url.rstrip('/')}/{s3_key.lstrip('/')}"

        # Set expiration time
        expires = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(seconds=expiry)

        # Generate signed URL
        signed_url = self.signer.generate_presigned_url(cloudfront_url, date_less_than=expires)

        return signed_url
