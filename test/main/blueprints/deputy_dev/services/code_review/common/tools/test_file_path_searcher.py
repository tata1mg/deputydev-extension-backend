from app.backend_common.services.llm.dataclasses.main import ConversationTool, JSONSchema
from app.main.blueprints.deputy_dev.services.code_review.common.tools.file_path_searcher import (
    FILE_PATH_SEARCHER,
)
from test.fixtures.main.blueprints.deputy_dev.services.code_review.common.tools.file_path_searcher_fixtures import (
    FilePathSearcherFixtures,
)


class TestFilePathSearcher:
    """Test cases for FILE_PATH_SEARCHER tool definition."""

    def test_file_path_searcher_is_conversation_tool(self) -> None:
        """Test FILE_PATH_SEARCHER is a ConversationTool instance."""
        # Assert
        assert isinstance(FILE_PATH_SEARCHER, ConversationTool)

    def test_file_path_searcher_name(self) -> None:
        """Test FILE_PATH_SEARCHER has correct name."""
        # Assert
        assert FILE_PATH_SEARCHER.name == "file_path_searcher"

    def test_file_path_searcher_description(self) -> None:
        """Test FILE_PATH_SEARCHER has proper description."""
        # Arrange
        expected_keywords = FilePathSearcherFixtures.get_expected_description_keywords()

        # Assert
        assert isinstance(FILE_PATH_SEARCHER.description, str)
        assert len(FILE_PATH_SEARCHER.description) > 0

        # Check for key functionality descriptions
        for keyword in expected_keywords:
            assert keyword in FILE_PATH_SEARCHER.description

    def test_file_path_searcher_input_schema(self) -> None:
        """Test FILE_PATH_SEARCHER has correct input schema."""
        # Arrange
        schema = FILE_PATH_SEARCHER.input_schema

        # Assert
        assert isinstance(schema, JSONSchema)
        assert schema.type == "object"
        assert "properties" in schema.__dict__
        assert "required" in schema.__dict__

    def test_file_path_searcher_schema_properties(self) -> None:
        """Test FILE_PATH_SEARCHER schema has correct properties."""
        # Arrange
        properties = FILE_PATH_SEARCHER.input_schema.properties

        # Assert
        assert "directory" in properties
        assert "search_terms" in properties

        # Test directory property
        directory_prop = properties["directory"]
        assert directory_prop.type == "string"
        assert directory_prop.description is not None

        # Test search_terms property
        search_terms_prop = properties["search_terms"]
        assert isinstance(search_terms_prop, JSONSchema)
        assert search_terms_prop.type == "array"

    def test_file_path_searcher_schema_required_fields(self) -> None:
        """Test FILE_PATH_SEARCHER schema has correct required fields."""
        # Arrange
        required_fields = FILE_PATH_SEARCHER.input_schema.required

        # Assert
        assert isinstance(required_fields, list)
        assert "directory" in required_fields
        assert "search_terms" not in required_fields  # Should be optional

    def test_file_path_searcher_search_terms_schema(self) -> None:
        """Test FILE_PATH_SEARCHER search_terms has correct schema."""
        # Arrange
        search_terms_schema = FILE_PATH_SEARCHER.input_schema.properties["search_terms"]

        # Assert
        assert isinstance(search_terms_schema, JSONSchema)
        assert search_terms_schema.type == "array"
        assert hasattr(search_terms_schema, "items")
        assert isinstance(search_terms_schema.items, JSONSchema)
        assert search_terms_schema.items.type == "string"
        assert "description" in search_terms_schema.__dict__

    def test_file_path_searcher_description_mentions_key_features(self) -> None:
        """Test FILE_PATH_SEARCHER description mentions key features."""
        # Arrange
        description = FILE_PATH_SEARCHER.description
        key_features = FilePathSearcherFixtures.get_key_features()

        # Assert
        for feature in key_features:
            assert feature in description

    def test_file_path_searcher_description_mentions_limitations(self) -> None:
        """Test FILE_PATH_SEARCHER description mentions limitations."""
        # Arrange
        description = FILE_PATH_SEARCHER.description
        limitations = FilePathSearcherFixtures.get_limitations()

        # Assert
        for limitation in limitations:
            assert limitation in description

    def test_file_path_searcher_directory_property_description(self) -> None:
        """Test directory property has meaningful description."""
        # Arrange
        directory_prop = FILE_PATH_SEARCHER.input_schema.properties["directory"]

        # Assert
        assert directory_prop.description is not None
        assert isinstance(directory_prop.description, str)
        assert len(directory_prop.description) > 0
        assert "path" in directory_prop.description.lower()

    def test_file_path_searcher_search_terms_property_description(self) -> None:
        """Test search_terms property has meaningful description."""
        # Arrange
        search_terms_prop = FILE_PATH_SEARCHER.input_schema.properties["search_terms"]

        # Assert
        assert hasattr(search_terms_prop, "description")
        assert isinstance(search_terms_prop.description, str)
        assert len(search_terms_prop.description) > 0
        assert "search terms" in search_terms_prop.description.lower()

    def test_file_path_searcher_schema_structure_completeness(self) -> None:
        """Test FILE_PATH_SEARCHER schema structure is complete."""
        # Arrange
        schema = FILE_PATH_SEARCHER.input_schema

        # Assert - Check all required schema components exist
        assert hasattr(schema, "type")
        assert hasattr(schema, "properties")
        assert hasattr(schema, "required")

        # Check properties structure
        properties = schema.properties
        assert isinstance(properties, dict)
        assert len(properties) == 2  # directory and search_terms

        # Check required fields structure
        required = schema.required
        assert isinstance(required, list)
        assert len(required) == 1  # only directory is required

    def test_file_path_searcher_tool_definition_immutability(self) -> None:
        """Test FILE_PATH_SEARCHER tool definition properties."""
        # Assert - Tool should have consistent properties
        original_name = FILE_PATH_SEARCHER.name
        original_description = FILE_PATH_SEARCHER.description

        # These should remain constant
        assert FILE_PATH_SEARCHER.name == original_name
        assert FILE_PATH_SEARCHER.description == original_description
        assert isinstance(FILE_PATH_SEARCHER.input_schema, JSONSchema)

    def test_file_path_searcher_search_terms_items_type(self) -> None:
        """Test FILE_PATH_SEARCHER search_terms items are string type."""
        # Arrange
        search_terms_schema = FILE_PATH_SEARCHER.input_schema.properties["search_terms"]
        items_schema = search_terms_schema.items

        # Assert
        assert items_schema.type == "string"
