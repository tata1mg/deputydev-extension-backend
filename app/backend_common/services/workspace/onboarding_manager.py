from __future__ import annotations

import uuid

from tortoise.exceptions import DoesNotExist
from tortoise.transactions import in_transaction

from app.backend_common.models.dao.postgres import Teams, Users, UserTeams
from app.backend_common.models.request.onboarding import SignUpRequest
from app.common.constants.onboarding import UserRoles
from app.common.exception.exception import SignUpError


class OnboardingManager:
    """Organisation onboarding & SCM accounts management."""

    # ---------------------------------- signup ---------------------------------- #

    @classmethod
    async def signup(cls, payload: SignUpRequest):
        try:
            await Users.get(email=payload.email)
        except DoesNotExist:
            # good, continue signup
            pass
        else:
            raise SignUpError("User already exists")

        async with in_transaction(connection_name="default"):
            user = Users(
                name=payload.username,
                email=payload.email,
                org_name=payload.org_name,
            )
            await user.save()

            team = Teams(name=cls.__generate_team_name(payload.username))
            await team.save()

            await UserTeams.create(
                user_id=user.id,
                team_id=team.id,
                role=UserRoles.ADMIN.value,
                is_owner=True,
                is_billable=True,
            )
            return user.id

    @staticmethod
    def __generate_team_name(username: str) -> str:
        return f"{username.lower()}-team-{uuid.uuid4().hex}"
