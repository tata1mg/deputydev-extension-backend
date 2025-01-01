from app.main.blueprints.one_dev.services.code_generation.features.dataclass.main import (
    BaseCodeGenFeaturePayload,
)


class CodePlanGenerationInput(BaseCodeGenFeaturePayload):
    relevant_chunks: str
    query: str
