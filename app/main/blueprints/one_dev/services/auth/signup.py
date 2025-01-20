

from torpedo.exceptions import BadRequestException
from app.main.blueprints.deputy_dev.constants.onboarding import UserRoles
from app.main.blueprints.deputy_dev.models.dao.postgres.user_teams import UserTeams
from app.main.blueprints.deputy_dev.models.request.onboarding import SignUpRequest
from app.main.blueprints.deputy_dev.services.workspace.onboarding_manager import OnboardingManager
from app.main.blueprints.one_dev.constants.constants import TATA_1MG, TRAYA
from app.common.exception.exception import SignUpError

class SignUp:
    @classmethod
    async def signup(cls, headers):
        email = headers.get("X-User-Email")
        email_verification = cls.verify_email(email)
        if "error" in email_verification:
            raise BadRequestException(email_verification["error"])
        else:
            # good, continue signup and onboard user with his personal team
            try:
                user_id = await OnboardingManager.signup(payload=SignUpRequest(
                    username=headers.get("X-User-Name"),
                    email=email,
                    org_name=email_verification["org_name"],
                ))

                await UserTeams.create(
                    user_id=user_id,
                    team_id=email_verification["team_id"],
                    role=UserRoles.ADMIN.value,
                    is_owner=True,
                    is_billable=True,
                )
                return {
                    "success": True
                }
            except SignUpError as e:
                return {
                    "success": True,
                    "message": str(e)
                }
            except Exception as e:
                raise BadRequestException(str(e))


    @classmethod
    def verify_email(cls, email):
        domain = email.split("@")[1]
        if domain == TATA_1MG["domain"]:
            return {
                "team_id": TATA_1MG["team_id"],
                "org_name": TATA_1MG["org_name"],
            }
        elif domain == TRAYA["domain"]:
            return {
                "team_id": TRAYA["team_id"],
                "org_name": TRAYA["org_name"],
            }
        else:
            return {
                "team_id": None,
                "org_name": None,
                "error": "Invalid domain"
            }