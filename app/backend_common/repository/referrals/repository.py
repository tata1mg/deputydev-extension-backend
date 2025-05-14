import json
from app.backend_common.models.dto.referrals_dto import ReferralData, ReferralDTO
from app.backend_common.repository.db import DB
from app.backend_common.models.dao.postgres.referrals import Referrals
from sanic.log import logger

class ReferralsRepository:
    @classmethod
    async def get_or_insert(cls, referral_data: ReferralData) -> ReferralDTO:
        try:
            existing_referral = await DB.by_filters(
                model_name=Referrals,
                where_clause={
                    "referral_code_id": referral_data.referral_code_id,
                    "referree_id": referral_data.referree_id
                }
            )
            if existing_referral:
                return ReferralDTO.model_validate_json(
                    json_data=json.dumps(
                        dict(
                            id=existing_referral.id,
                            referral_code_id=existing_referral.referral_code_id,
                            referree_id=existing_referral.referree_id,
                            created_at=existing_referral.created_at.isoformat(),
                            updated_at=existing_referral.updated_at.isoformat(),
                        )
                    )
                )
            referral = await DB.insert_row(Referrals, referral_data.model_dump(mode="json"))
            return ReferralDTO.model_validate_json(
                json_data=json.dumps(
                    dict(
                        id=referral.id,
                        referral_code_id=referral.referral_code_id,
                        referree_id=referral.referree_id,
                        created_at=referral.created_at.isoformat(),
                        updated_at=referral.updated_at.isoformat(),
                    )
                )
            )
        except Exception as ex:
            logger.error(f"Error occurred while inserting referral in DB, ex: {ex}")
            raise ex