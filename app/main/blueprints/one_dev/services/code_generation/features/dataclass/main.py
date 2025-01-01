from enum import Enum

from pydantic import BaseModel

from app.main.blueprints.one_dev.utils.dataclasses.main import AuthData


class CodeGenFeature(Enum):
    CODE_GENERATION = "CODE_GENERATION"
    TEST_CASE_GENERATION = "TEST_CASE_GENERATION"
    PLAN_GENERATION = "PLAN_GENERATION"
    DOCS_GENERATION = "DOCS_GENERATION"


class BaseCodeGenFeaturePayload(BaseModel):
    session_id: str
    auth_data: AuthData
