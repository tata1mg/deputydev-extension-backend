from typing import Optional

from sanic.log import logger

from app.backend_common.models.dao.postgres.subscription_plans import SubscriptionPlans
from app.backend_common.models.dto.subscription_plans_dto import SubscriptionPlanDTO
from app.backend_common.repository.db import DB


class SubscriptionPlansRepository:
    @classmethod
    async def get_subscription_plan(cls, plan: str) -> Optional[SubscriptionPlanDTO]:
        try:
            subscription_plan = await DB.by_filters(
                model_name=SubscriptionPlans,
                where_clause={"plan_type": plan},
                fetch_one=True,
            )
            if not subscription_plan:
                return None
            return SubscriptionPlanDTO(**subscription_plan)
        except Exception as ex:
            logger.error(f"Error occurred while getting subscription plan {plan} from DB, ex: {ex}")
            raise ex
