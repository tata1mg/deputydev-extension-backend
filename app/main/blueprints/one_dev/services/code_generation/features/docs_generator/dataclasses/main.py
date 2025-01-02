from typing import Optional

from app.main.blueprints.one_dev.services.code_generation.dataclasses.main import (
    PRConfig,
)
from app.main.blueprints.one_dev.services.code_generation.features.dataclass.main import (
    BaseCodeGenFeaturePayload,
)


class CodeDocsGenerationInput(BaseCodeGenFeaturePayload):
    query: str
    custom_instructions: Optional[str] = None
    relevant_chunks: str
    create_pr: Optional[bool] = None
    pr_config: Optional[PRConfig] = None
    apply_diff: Optional[bool] = None
