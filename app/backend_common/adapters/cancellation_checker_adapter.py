from typing import Optional

from deputydev_core.llm_handler.interfaces.cancellation_interface import CancellationCheckerInterface

from app.main.blueprints.one_dev.utils.cancellation_checker import CancellationChecker


class CancellationCheckerAdapter(CancellationCheckerInterface):
    """Adapter that wraps your existing ChatAttachmentsRepository"""

    def __init__(self, checker: CancellationChecker) -> None:
        self.checker: Optional[CancellationChecker] = checker

    async def enforce_cancellation_with_cleanup(self) -> None:
        """
        Delegate to the checker's built-in enforcement.
        Intended call sites: streaming loops and other long-running steps.
        """
        if self.checker:
            await self.checker.enforce_cancellation_with_cleanup()

    async def stop_monitoring(self) -> None:
        """Stop the periodic cancellation check"""
        if self.checker:
            await self.checker.stop_monitoring()

    def is_cancelled(self) -> bool:
        """
        Delegate to the checker's built-in enforcement.
        Intended call sites: streaming loops and other long-running steps.
        """
        if self.checker:
            self.checker.is_cancelled()
