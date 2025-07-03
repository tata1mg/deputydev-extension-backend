from abc import ABC, abstractmethod


class BaseReviewPreProcessor(ABC):
    def __init__(self):
        self.is_valid = True
        self.review_status = None

    @abstractmethod
    async def pre_process_pr(self, data: dict):
        """
        Abstract method to pre-process a review request.
        """
        pass
