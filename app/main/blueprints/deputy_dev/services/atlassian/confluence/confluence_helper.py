class ConfluenceHelper:
    @staticmethod
    def parse_description(content: str) -> str:
        """
        Extracts the Confluence document ID from the given Confluence link.

        Args:
            content (str): Plain confluence data
        Returns:
            str: returns description of confluence doc
        Note: For now we are retuning HTML information
        """
        return content
