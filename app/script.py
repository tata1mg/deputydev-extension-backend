from app.main.blueprints.deputy_dev.services.pr.backfill_data_manager import (
    BackfillManager,
)
import asyncio

query_params = {"start": 14695, "end": 15000, "type": "pr_state_pullrequest_update"}
asyncio.run(BackfillManager().backfill_pr_approval_time(query_params))
BackfillManager().backfill_pr_approval_time(query_params)
