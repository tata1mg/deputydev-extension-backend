class RetryException(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(f"Retrying event: {self.message}")
