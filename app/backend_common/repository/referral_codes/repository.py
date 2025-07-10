from typing import Optional

from sanic.log import logger

from app.backend_common.models.dao.postgres.referral_codes import ReferralCodes
from app.backend_common.models.dto.referral_codes_dto import ReferralCodeDTO
from app.backend_common.repository.db import DB


class ReferralCodesRepository:
    @classmethod
    async def get_by_code(cls, referral_code: str) -> Optional[ReferralCodeDTO]:
        try:
            referral_code = await DB.by_filters(
                model_name=ReferralCodes,
                where_clause={"referral_code": referral_code},
                fetch_one=True,
            )
            if not referral_code:
                return None
            return ReferralCodeDTO(**referral_code)
        except Exception as ex:
            logger.error(f"Not able to get referral code details from db {referral_code} exception {ex}")
            raise ex

    @classmethod
    async def db_update(cls, referral_code_payload: ReferralCodeDTO) -> Optional[ReferralCodeDTO]:
        try:
            referral_code = await DB.update_by_filters(
                row=None,
                model_name=ReferralCodes,
                payload={"usage_limit": referral_code_payload.usage_limit},
                where_clause={"id": referral_code_payload.id},
            )
            if not referral_code:
                return None
            return ReferralCodeDTO(**referral_code)
        except Exception as ex:
            logger.error(f"Not able to update referral code details in db {referral_code_payload} exception {ex}")
            raise ex
