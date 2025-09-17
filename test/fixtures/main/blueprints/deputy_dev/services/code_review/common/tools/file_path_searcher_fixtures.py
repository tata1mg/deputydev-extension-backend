from typing import List


class FilePathSearcherFixtures:
    """Fixtures for FilePathSearcher tests."""

    @staticmethod
    def get_expected_description_keywords() -> List[str]:
        """Return keywords that should be present in the tool description."""
        return ["Searches for files", "search terms", "directory path", "fuzzy search", "file paths", "100 files"]

    @staticmethod
    def get_key_features() -> List[str]:
        """Return key features mentioned in the description."""
        return ["fuzzy search", "directory path", "search terms", "file paths"]

    @staticmethod
    def get_limitations() -> List[str]:
        """Return limitations mentioned in the description."""
        return ["100 files", "correct and complete directory path"]

    @staticmethod
    def get_valid_directory_paths() -> List[str]:
        """Return valid directory paths for testing."""
        return ["/src", "/app/main", "/tests/unit", "/docs/api", "/config", "src/components", "tests/integration", "."]

    @staticmethod
    def get_valid_search_terms() -> List[List[str]]:
        """Return valid search terms combinations."""
        return [
            ["test"],
            ["component", "react"],
            ["config", "json"],
            ["util", "helper"],
            ["main", "app"],
            ["model", "dto"],
            ["service", "handler"],
            [],  # Empty list should be valid
        ]

    @staticmethod
    def get_schema_property_names() -> List[str]:
        """Return expected schema property names."""
        return ["directory", "search_terms"]

    @staticmethod
    def get_required_fields() -> List[str]:
        """Return required schema fields."""
        return ["directory"]

    @staticmethod
    def get_optional_fields() -> List[str]:
        """Return optional schema fields."""
        return ["search_terms"]

    @staticmethod
    def get_expected_property_types() -> dict[str, str]:
        """Return expected property types."""
        return {"directory": "string", "search_terms": "array"}

    @staticmethod
    def get_tool_metadata() -> dict[str, str]:
        """Return expected tool metadata."""
        return {"name": "file_path_searcher", "type": "search_tool", "category": "file_operations"}

    @staticmethod
    def get_description_sections() -> List[str]:
        """Return sections that should be in the description."""
        return [
            "Searches for files with given search terms",
            "correct and complete directory path",
            "fuzzy search to match the search terms",
            "list down files in a given directory",
            "max 100 files",
        ]
