from typing import Optional

from app.main.blueprints.one_dev.services.code_generation.dataclasses.main import (
    PRConfig,
)
from app.main.blueprints.one_dev.services.code_generation.features.dataclass.main import (
    BaseCodeGenFeaturePayload,
)


class TestCaseGenerationInput(BaseCodeGenFeaturePayload):
    create_pr: Optional[bool] = None
    pr_config: Optional[PRConfig] = None
    query: str
    relevant_chunks: str
    custom_instructions: Optional[str] = None
