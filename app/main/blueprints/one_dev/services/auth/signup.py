import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional, Tuple

from deputydev_core.utils.constants.enums import Clients
from torpedo import CONFIG
from tortoise.exceptions import DoesNotExist
from tortoise.transactions import in_transaction

from app.backend_common.constants.onboarding import SubscriptionStatus, UserRoles
from app.backend_common.exception.exception import SignUpError
from app.backend_common.models.dao.postgres import Teams, Users
from app.backend_common.models.dao.postgres.referral_codes import ReferralCodes
from app.backend_common.models.dao.postgres.referrals import Referrals
from app.backend_common.models.dao.postgres.subscription_plans import SubscriptionPlans
from app.backend_common.models.dao.postgres.subscriptions import Subscriptions
from app.backend_common.models.dao.postgres.user_teams import UserTeams
from app.backend_common.models.dto.referral_codes_dto import ReferralCodeDTO
from app.backend_common.models.request.onboarding import SignUpRequest
from app.backend_common.repository.referral_codes.repository import ReferralCodesRepository
from app.backend_common.repository.user_teams.user_team_repository import UserTeamRepository
from app.backend_common.repository.users.user_repository import UserRepository


class SignUp:
    @classmethod
    async def signup(cls, headers: Dict[str, Any]) -> Dict[str, Any]:
        try:
            referral_code = headers.get("X-Referral-Code")
            external_auth_client = headers.get("X-External-Auth-Client")
            email = headers.get("X-User-Email")
            username = headers.get("X-User-Name")
            if referral_code:
                is_valid, referral_code_data = await cls.validate_referral_code(referral_code)
                if is_valid:
                    signup_payload = SignUpRequest(
                        username=username, email=email, org_name=f"{username}'s Organisation"
                    )
                    await cls.signup_and_subscribe(signup_payload, referral_code_data=referral_code_data)
                    return {"success": True}
                else:
                    return {"success": False, "error": "Invalid/Expired referral code"}
            else:
                email_verification = await cls.get_team_info_from_email(email, external_auth_client)
                if "error" in email_verification:
                    return {"success": False, "error": email_verification["error"]}
                signup_payload = SignUpRequest(username=username, email=email, org_name=email_verification["org_name"])
                await cls.signup_and_subscribe(signup_payload, email_verification=email_verification)
                return {"success": True}
        except SignUpError:
            # user already exists
            return {"success": True, "is_user_exist": True}

    @classmethod
    async def signup_and_subscribe(
        cls,
        signup_payload: SignUpRequest,
        referral_code_data: Optional[ReferralCodeDTO] = None,
        email_verification: Optional[Dict[str, Any]] = None,
    ) -> None:
        async with in_transaction(connection_name="default"):
            try:
                user = await Users.get(email=signup_payload.email)
            except DoesNotExist:
                # good, continue signup
                user = Users(
                    name=signup_payload.username,
                    email=signup_payload.email,
                    org_name=signup_payload.org_name,
                )
                await user.save()

                personal_team = Teams(name=cls.__generate_personal_team_name(signup_payload.username))
                await personal_team.save()

                personal_user_team = await UserTeams.create(
                    user_id=user.id,
                    team_id=personal_team.id,
                    role=UserRoles.ADMIN.value,
                    is_owner=True,
                    is_billable=True,
                )

                user_team_id = personal_user_team.id

                # Only for domain or allowed emails based onboarding
                if not referral_code_data and email_verification:
                    user_team = await UserTeams.create(
                        user_id=user.id,
                        team_id=email_verification["team_id"],
                        role=UserRoles.MEMBER.value,
                        is_owner=False,
                        is_billable=False,
                    )
                    user_team_id = user_team.id

                if referral_code_data:
                    # create referral
                    await Referrals.get_or_create(
                        defaults={"referral_code_id": referral_code_data.id, "referree_id": personal_user_team.id},
                        referral_code_id=referral_code_data.id,
                        referree_id=personal_user_team.id,
                    )

                subscription_plan = await SubscriptionPlans.get(plan_type="PRO")

                end_date = None
                if referral_code_data:
                    end_date = datetime.now() + timedelta(
                        hours=referral_code_data.benefits.subscription_expiry_timedelta
                    )

                subscription = Subscriptions(
                    plan_id=subscription_plan.id,
                    user_team_id=user_team_id,
                    current_status=SubscriptionStatus.ACTIVE.value,
                    start_date=datetime.now(),
                    end_date=end_date,
                )

                await subscription.save()

                if referral_code_data:
                    await ReferralCodes.update_or_create(
                        defaults={"current_limit_left": referral_code_data.current_limit_left - 1},
                        id=referral_code_data.id,
                    )
            else:
                raise SignUpError("User already exists")

    @classmethod
    async def get_team_info_from_email(cls, email: str, external_auth_client: Optional[str] = None) -> Dict[str, Any]:
        domain = email.split("@")[1]
        if external_auth_client:
            if Clients(external_auth_client) == Clients.VSCODE_EXT:
                if domain == CONFIG.config["ORG_INFO"]["TATA_1MG"]["domain"]:
                    return {
                        "team_id": CONFIG.config["ORG_INFO"]["TATA_1MG"]["team_id"],
                        "org_name": CONFIG.config["ORG_INFO"]["TATA_1MG"]["org_name"],
                    }

        if domain == CONFIG.config["ORG_INFO"]["TATA_1MG"]["domain"]:
            return {
                "team_id": CONFIG.config["ORG_INFO"]["TATA_1MG"]["team_id"],
                "org_name": CONFIG.config["ORG_INFO"]["TATA_1MG"]["org_name"],
            }

        elif email in CONFIG.config["ALLOWED_EMAILS"]:
            return {
                "team_id": CONFIG.config["ORG_INFO"]["DEPUTYDEV_PRIVATE"]["team_id"],
                "org_name": CONFIG.config["ORG_INFO"]["DEPUTYDEV_PRIVATE"]["org_name"],
            }
        else:
            return await cls.get_personal_team_info_from_email(email)

    @classmethod
    async def validate_referral_code(cls, referral_code: str) -> Tuple[bool, Optional[ReferralCodeDTO]]:
        referral_code_data: Optional[ReferralCodeDTO] = await ReferralCodesRepository.get_by_code(referral_code)
        if (
            not referral_code_data
            or referral_code_data.expiration_date < datetime.now(tz=timezone.utc)
            or referral_code_data.current_limit_left == 0
        ):
            return False, None
        return True, referral_code_data

    @classmethod
    async def get_personal_team_info_from_email(cls, email: str) -> Dict[str, Any]:
        user_info = await UserRepository.db_get({"email": email}, fetch_one=True)
        if not user_info:
            return {"team_id": None, "org_name": None, "error": "User not found"}
        user_team_info = await UserTeamRepository.db_get(
            {"user_id": user_info.id, "role": UserRoles.ADMIN.value}, fetch_one=True
        )
        if not user_team_info:
            return {"team_id": None, "org_name": None, "error": "User personal team not found"}
        return {"team_id": user_team_info.team_id, "org_name": user_info.org_name}

    @staticmethod
    def __generate_personal_team_name(username: str) -> str:
        return f"{username.lower()}-team-{uuid.uuid4().hex}"
