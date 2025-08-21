from __future__ import annotations

import uuid
from typing import Optional

from tortoise.exceptions import DoesNotExist
from tortoise.transactions import in_transaction

from app.backend_common.exception.exception import SignUpError, TeamNotFound
from app.backend_common.models.dao.postgres import Teams, Users, UserTeams
from app.main.blueprints.deputy_dev.constants.onboarding import UserRoles
from app.main.blueprints.deputy_dev.models.request import (
    OnboardingRequest,
    SignUpRequest,
)

from ..integration import Integration, get_integration


class OnboardingManager:
    """Organisation onboarding & SCM accounts management."""

    # ---------------------------------- signup ---------------------------------- #

    @classmethod
    async def signup(cls, payload: SignUpRequest) -> Optional[int]:
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

    # ---------------------------------- onboard --------------------------------- #

    @classmethod
    async def onboard(cls, payload: OnboardingRequest) -> None:
        try:
            _ = await Teams.get(id=payload.team_id)  # check if team exists
        except DoesNotExist as exc:
            raise TeamNotFound(f"Team with id {payload.team_id} not found") from exc

        integration: Integration = get_integration(payload.integration_client)()
        await integration.integrate(payload=payload)
