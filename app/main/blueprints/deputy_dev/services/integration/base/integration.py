from abc import ABC, abstractmethod

from tortoise.exceptions import DoesNotExist

from app.backend_common.exception.exception import OnboardingError
from app.main.blueprints.deputy_dev.models.dao.postgres import Integrations
from app.main.blueprints.deputy_dev.models.request import OnboardingRequest


class Integration(ABC):
    """Each integration must inherit this abstract class."""

    @abstractmethod
    async def integrate(self, payload: OnboardingRequest) -> None:
        """
        Each integration must overload this with integration steps,
        including creating datastore entries and other required setup.
        """

    async def get_integration(self, team_id: int, client: str) -> Integrations:
        try:
            integration_row = await Integrations.get(team_id=team_id, client=client)

            if integration_row.is_connected:
                raise OnboardingError("Integration already onboarded")

        except DoesNotExist:
            integration_row = Integrations(
                team_id=team_id,
                client=client,
                is_connected=False,
            )
            await integration_row.save()

        return integration_row

    async def mark_connected(self, integration_row: Integrations) -> None:
        await Integrations.filter(id=integration_row.id).update(is_connected=True)
