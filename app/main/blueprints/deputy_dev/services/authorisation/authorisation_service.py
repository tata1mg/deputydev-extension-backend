from torpedo.exceptions import BadRequestException

from app.main.blueprints.deputy_dev.services.authorisation.authorisation_util import (
    validate_bitbucket_request,
)


class AuthorisationService:
    @classmethod
    def authorize_pr_service_request(cls, request_auth_token: str, payload: str, secret: str) -> bool:
        # not getting used currently
        if validate_bitbucket_request(request_auth_token, payload, secret):
            return True
        else:
            raise BadRequestException("Unauthorised Request")
