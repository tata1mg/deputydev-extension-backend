from weaviate.classes.config import DataType, Property, Tokenization

from app.common.models.dao.weaviate.base import Base


class ChunkFiles(Base):
    properties = [
        Property(
            name="file_path",
            data_type=DataType.TEXT,
            vectorize_property_name=False,
            skip_vectorization=True,
            tokenization=Tokenization.FIELD,
            index_filterable=True,
        ),
        Property(
            name="chunk_hash",
            data_type=DataType.TEXT,
            vectorize_property_name=False,
            tokenization=Tokenization.FIELD,
            skip_vectorization=True,
        ),
        Property(
            name="start_line",
            data_type=DataType.INT,
            vectorize_property_name=False,
            tokenization=None,
            skip_vectorization=True,
        ),
        Property(
            name="end_line",
            data_type=DataType.INT,
            vectorize_property_name=False,
            tokenization=None,
            skip_vectorization=True,
        ),
        Property(
            name="file_hash",
            data_type=DataType.TEXT,
            vectorize_property_name=False,
            tokenization=Tokenization.FIELD,
            skip_vectorization=True,
            index_filterable=True,
        ),
        Property(
            name="last_used_at",
            data_type=DataType.DATE,
            vectorize_property_name=False,
            tokenization=None,
            skip_vectorization=True,
            index_range_filters=True,
        ),
    ]
    collection_name = "chunk_files"
