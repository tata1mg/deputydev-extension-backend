from typing import Optional

from app.main.blueprints.one_dev.services.code_generation.dataclasses.main import (
    PRConfig,
)
from app.main.blueprints.one_dev.services.code_generation.features.dataclass.main import (
    BaseCodeGenFeaturePayload,
)


class CodeGenerationInput(BaseCodeGenFeaturePayload):
    query: str
    pr_config: Optional[PRConfig] = None
    apply_diff: Optional[bool] = None
    relevant_chunks: str
