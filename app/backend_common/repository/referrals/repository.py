from sanic.log import logger

from app.backend_common.models.dao.postgres.referrals import Referrals
from app.backend_common.models.dto.referrals_dto import ReferralData, ReferralDTO
from app.backend_common.repository.db import DB


class ReferralsRepository:
    @classmethod
    async def get_or_insert(cls, referral_data: ReferralData) -> ReferralDTO:
        try:
            existing_referral = await DB.by_filters(
                model_name=Referrals,
                where_clause={
                    "referral_code_id": referral_data.referral_code_id,
                    "referree_id": referral_data.referree_id,
                },
            )
            if existing_referral:
                return ReferralDTO(**existing_referral)
            referral = await DB.insert_row(Referrals, referral_data.model_dump(mode="json"))
            return ReferralDTO(**referral)
        except Exception as ex:
            logger.error(f"Error occurred while inserting referral in DB, ex: {ex}")
            raise ex
