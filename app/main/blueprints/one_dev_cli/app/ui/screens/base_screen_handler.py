from abc import ABC, abstractmethod
from typing import Any, Dict, Tuple

from app.main.blueprints.one_dev_cli.app.ui.screens.dataclasses.main import (
    AppContext,
    ScreenType,
)


class BaseScreenHandler(ABC):
    def __init__(self, app_context: AppContext) -> None:
        self.app_context = app_context

    @property
    @abstractmethod
    def screen_type(self) -> ScreenType:
        raise NotImplementedError("screen_type property must be implemented in child class")

    @abstractmethod
    async def render(self, **kwargs: Dict[str, Any]) -> Tuple[AppContext, ScreenType]:
        raise NotImplementedError("render method must be implemented in child class")
