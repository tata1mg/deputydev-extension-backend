from typing import Any, Dict

from app.backend_common.models.dao.postgres.user_teams import UserTeams
from app.backend_common.models.request.onboarding import SignUpRequest
from app.backend_common.services.workspace.onboarding_manager import OnboardingManager
from app.common.constants.onboarding import UserRoles
from app.common.exception.exception import SignUpError
from app.common.utils.config_manager import ConfigManager


class SignUp:
    @classmethod
    async def signup(cls, headers: Dict[str, Any]) -> Dict[str, Any]:
        email = headers.get("X-User-Email")
        email_verification = cls.verify_email(email)
        if "error" in email_verification:
            return {"success": False, "error": email_verification["error"]}
        else:
            # good, continue signup and onboard user with his personal team
            try:
                user_id = await OnboardingManager.signup(
                    payload=SignUpRequest(
                        username=headers.get("X-User-Name"),
                        email=email,
                        org_name=email_verification["org_name"],
                    )
                )

                await UserTeams.create(
                    user_id=user_id,
                    team_id=email_verification["team_id"],
                    role=UserRoles.ADMIN.value,
                    is_owner=True,
                    is_billable=True,
                )
                return {"success": True}
            except SignUpError:
                # user already exists
                return {"success": True, "is_user_exist": True}
            except Exception as e:
                raise Exception(str(e))

    @classmethod
    def verify_email(cls, email: str) -> Dict[str, Any]:
        domain = email.split("@")[1]
        if domain == ConfigManager.config["ORG_INFO"]["TATA_1MG"]["domain"]:
            return {
                "team_id": ConfigManager.config["ORG_INFO"]["TATA_1MG"]["team_id"],
                "org_name": ConfigManager.config["ORG_INFO"]["TATA_1MG"]["org_name"],
            }
        elif domain == ConfigManager.config["ORG_INFO"]["TRAYA"]["domain"]:
            return {
                "team_id": ConfigManager.config["ORG_INFO"]["TRAYA"]["team_id"],
                "org_name": ConfigManager.config["ORG_INFO"]["TRAYA"]["org_name"],
            }
        else:
            return {"team_id": None, "org_name": None, "error": "Invalid domain"}
