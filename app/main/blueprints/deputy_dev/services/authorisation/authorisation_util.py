import hashlib
import hmac


def validate_bitbucket_request(auth_token: str, payload: str, secret: str) -> bool:
    hash_object = hmac.new(
        secret.encode("utf-8"),
        msg=payload.encode("utf-8"),
        digestmod=hashlib.sha256,
    )
    calculated_signature = "sha256=" + hash_object.hexdigest()
    return hmac.compare_digest(calculated_signature, auth_token)
