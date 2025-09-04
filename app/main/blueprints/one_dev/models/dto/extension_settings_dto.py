from datetime import datetime
from typing import List

from pydantic import BaseModel

from app.backend_common.utils.dataclasses.main import Clients


class TerminalSettings(BaseModel):
    enable_yolo_mode: bool
    command_deny_list: List[str]


class Settings(BaseModel):
    terminal_settings: TerminalSettings


class ExtensionSettingsData(BaseModel):
    user_team_id: int
    client: Clients
    settings: Settings


class ExtensionSettingsDTO(ExtensionSettingsData):
    id: int
    created_at: datetime
    updated_at: datetime
