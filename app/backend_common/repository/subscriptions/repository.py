import json
from typing import Optional
from sanic.log import logger

from app.backend_common.models.dao.postgres.subscriptions import Subscriptions
from app.backend_common.models.dto.subscriptions_dto import SubscriptionData, SubscriptionDTO
from app.backend_common.repository.db import DB


class SubscriptionsRepository:
    @classmethod
    async def get_by_user_team_id(cls, user_team_id: int) -> Optional[SubscriptionDTO]:
        try:
            subscription = await DB.by_filters(
                model_name=Subscriptions,
                where_clause={"user_team_id": user_team_id},
                fetch_one=True,
            )
            if not subscription:
                return None
            return SubscriptionDTO(**subscription)
        except Exception as ex:
            logger.error(f"Error occurred while getting subscription by user team id {user_team_id} from DB, ex: {ex}")
            raise ex

    @classmethod
    async def db_insert(cls, subscription_data: SubscriptionData) -> SubscriptionDTO:
        try:
            subscription = await DB.insert_row(Subscriptions, subscription_data.model_dump(mode="json"))
            return SubscriptionDTO.model_validate_json(
                json.dumps(
                    dict(
                        id=subscription.id,
                        plan_id=subscription.plan_id,
                        user_team_id=subscription.user_team_id,
                        current_status=subscription.current_status,
                        start_date=subscription.start_date.isoformat(),
                        end_date=subscription.end_date.isoformat(),
                        created_at=subscription.created_at.isoformat(),
                        updated_at=subscription.updated_at.isoformat(),
                    )
                )
            )
        except Exception as ex:
            logger.error(f"Error occurred while inserting subscription {subscription_data} in DB, ex: {ex}")
            raise ex
