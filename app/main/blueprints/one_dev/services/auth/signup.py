from typing import Any, Dict, Optional

from deputydev_core.utils.constants.enums import Clients
from torpedo import CONFIG

from app.backend_common.constants.onboarding import UserRoles
from app.backend_common.exception.exception import SignUpError
from app.backend_common.models.dao.postgres.user_teams import UserTeams
from app.backend_common.models.request.onboarding import SignUpRequest
from app.backend_common.services.workspace.onboarding_manager import OnboardingManager


class SignUp:
    @classmethod
    async def signup(cls, headers: Dict[str, Any]) -> Dict[str, Any]:
        external_auth_client = headers.get("X-External-Auth-Client")
        email = headers.get("X-User-Email")
        email_verification = cls.get_team_info_from_email(email, external_auth_client)
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
                    role=UserRoles.MEMBER.value,
                    is_owner=False,
                    is_billable=False,
                )
                return {"success": True}
            except SignUpError:
                # user already exists
                return {"success": True, "is_user_exist": True}
            except Exception as e:
                raise Exception(str(e))

    @classmethod
    def get_team_info_from_email(cls, email: str, external_auth_client: Optional[str] = None) -> Dict[str, Any]:
        domain = email.split("@")[1]
        if external_auth_client:
            if Clients(external_auth_client) == Clients.VSCODE_EXT:
                if domain == CONFIG.config["ORG_INFO"]["TATA_1MG"]["domain"]:
                    return {
                        "team_id": CONFIG.config["ORG_INFO"]["TATA_1MG"]["team_id"],
                        "org_name": CONFIG.config["ORG_INFO"]["TATA_1MG"]["org_name"],
                    }
                elif domain == CONFIG.config["ORG_INFO"]["TBO"]["domain"]:
                    return {
                        "team_id": CONFIG.config["ORG_INFO"]["TBO"]["team_id"],
                        "org_name": CONFIG.config["ORG_INFO"]["TBO"]["org_name"],
                    }
                elif domain == CONFIG.config["ORG_INFO"]["CARATLANE"]["domain"]:
                    return {
                        "team_id": CONFIG.config["ORG_INFO"]["CARATLANE"]["team_id"],
                        "org_name": CONFIG.config["ORG_INFO"]["CARATLANE"]["org_name"],
                    }
                elif domain == CONFIG.config["ORG_INFO"]["HSV_DIGITAL"]["domain"]:
                    return {
                        "team_id": CONFIG.config["ORG_INFO"]["HSV_DIGITAL"]["team_id"],
                        "org_name": CONFIG.config["ORG_INFO"]["HSV_DIGITAL"]["org_name"],
                    }
                else:
                    if email in CONFIG.config["ALLOWED_EMAILS"]:
                        return {
                            "team_id": CONFIG.config["ORG_INFO"]["DEPUTYDEV_PRIVATE"]["team_id"],
                            "org_name": CONFIG.config["ORG_INFO"]["DEPUTYDEV_PRIVATE"]["org_name"],
                        }
                    else:
                        return {"team_id": None, "org_name": None, "error": "Invalid domain"}
        if domain == CONFIG.config["ORG_INFO"]["TATA_1MG"]["domain"]:
            return {
                "team_id": CONFIG.config["ORG_INFO"]["TATA_1MG"]["team_id"],
                "org_name": CONFIG.config["ORG_INFO"]["TATA_1MG"]["org_name"],
            }
        elif domain == CONFIG.config["ORG_INFO"]["TRAYA"]["domain"]:
            return {
                "team_id": CONFIG.config["ORG_INFO"]["TRAYA"]["team_id"],
                "org_name": CONFIG.config["ORG_INFO"]["TRAYA"]["org_name"],
            }
        elif domain == CONFIG.config["ORG_INFO"]["5CNETWORK"]["domain"]:
            return {
                "team_id": CONFIG.config["ORG_INFO"]["5CNETWORK"]["team_id"],
                "org_name": CONFIG.config["ORG_INFO"]["5CNETWORK"]["org_name"],
            }
        elif domain == CONFIG.config["ORG_INFO"]["TBO"]["domain"]:
            return {
                "team_id": CONFIG.config["ORG_INFO"]["TBO"]["team_id"],
                "org_name": CONFIG.config["ORG_INFO"]["TBO"]["org_name"],
            }
        elif domain == CONFIG.config["ORG_INFO"]["CARATLANE"]["domain"]:
            return {
                "team_id": CONFIG.config["ORG_INFO"]["CARATLANE"]["team_id"],
                "org_name": CONFIG.config["ORG_INFO"]["CARATLANE"]["org_name"],
            }
        elif domain == CONFIG.config["ORG_INFO"]["HSV_DIGITAL"]["domain"]:
            return {
                "team_id": CONFIG.config["ORG_INFO"]["HSV_DIGITAL"]["team_id"],
                "org_name": CONFIG.config["ORG_INFO"]["HSV_DIGITAL"]["org_name"],
            }
        else:
            if email in CONFIG.config["ALLOWED_EMAILS"]:
                return {
                    "team_id": CONFIG.config["ORG_INFO"]["DEPUTYDEV_PRIVATE"]["team_id"],
                    "org_name": CONFIG.config["ORG_INFO"]["DEPUTYDEV_PRIVATE"]["org_name"],
                }
            else:
                return {"team_id": None, "org_name": None, "error": "Invalid domain"}
