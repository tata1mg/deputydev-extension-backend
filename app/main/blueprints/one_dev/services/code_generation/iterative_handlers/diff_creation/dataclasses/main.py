from typing import Optional

from app.main.blueprints.one_dev.services.code_generation.dataclasses.main import (
    PRConfig,
)
from app.main.blueprints.one_dev.services.code_generation.iterative_handlers.dataclass.main import (
    BaseCodeGenIterativeHandlerPayload,
)


class DiffCreationInput(BaseCodeGenIterativeHandlerPayload):
    pr_config: Optional[PRConfig] = None
