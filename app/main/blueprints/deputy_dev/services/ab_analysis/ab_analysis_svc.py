from typing import Any, Dict, List

import pandas as pd
from sanic.log import logger

from app.backend_common.repository.db import DB
from app.backend_common.utils.sanic_wrapper.exceptions import BadRequestException
from app.main.blueprints.deputy_dev.constants.ab_analysis_constants import (
    AbAnalysisDates,
    AbAnalysisPhases,
    AbAnalysisQueries,
)


class AbAnalysisFetchingData:
    """Fetching AbAnalysis Data"""

    # Method for the conversion of list of dicts to CSV
    @classmethod
    def convert_to_csv(cls, data: List[Dict[str, Any]]) -> str:
        df = pd.DataFrame(data)
        csv_data = df.to_csv(index=False)
        return csv_data

    @classmethod
    async def get_ab_analysis_data(cls, query_params: Dict[str, Any]) -> str:
        query_phase = query_params.get("query_phase")
        ab_analysis_time = query_params.get("ab_analysis_time")
        try:
            if ab_analysis_time == "approval":
                if query_phase == AbAnalysisPhases.ab_analysis_phase1.value:
                    query = AbAnalysisQueries.approval_query.value.format(
                        date_condition=AbAnalysisDates.date_condition_phase1.value
                    )
                elif query_phase == AbAnalysisPhases.ab_analysis_phase2.value:
                    query = AbAnalysisQueries.approval_query.value.format(
                        date_condition=AbAnalysisDates.date_condition_phase2.value
                    )
                elif query_phase == AbAnalysisPhases.ab_analysis_phase_overall.value:
                    query = AbAnalysisQueries.approval_query.value.format(
                        date_condition=AbAnalysisDates.date_condition_phase_overall.value
                    )
                else:
                    raise BadRequestException("invalid Query Phase Input !!!")
            elif ab_analysis_time == "merge":
                if query_phase == AbAnalysisPhases.ab_analysis_phase1.value:
                    query = AbAnalysisQueries.merge_query.value.format(
                        date_condition=AbAnalysisDates.date_condition_phase1.value
                    )
                elif query_phase == AbAnalysisPhases.ab_analysis_phase2.value:
                    query = AbAnalysisQueries.merge_query.value.format(
                        date_condition=AbAnalysisDates.date_condition_phase2.value
                    )
                elif query_phase == AbAnalysisPhases.ab_analysis_phase_overall.value:
                    query = AbAnalysisQueries.merge_query.value.format(
                        date_condition=AbAnalysisDates.date_condition_phase_overall.value
                    )
                else:
                    raise BadRequestException("invalid Query Phase Input !!!")
            else:
                raise BadRequestException("Invalid ab analysis time input")

            data = await DB.raw_sql(query)
            csv_data = cls.convert_to_csv(data)
            return csv_data

        except Exception as ex:  # noqa: BLE001
            logger.error("Get ab analysis data failed !!!")
            raise BadRequestException(f"Invalid Ab analysis data request with error {ex}")
