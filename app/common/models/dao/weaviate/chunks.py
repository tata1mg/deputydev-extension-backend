from weaviate.classes.config import DataType, Property, Tokenization

from app.common.models.dao.weaviate.base import Base


class Chunks(Base):
    properties = [
        Property(
            name="chunk_hash",
            data_type=DataType.TEXT,
            vectorize_property_name=False,
            tokenization=Tokenization.FIELD,
            skip_vectorization=True,
            index_filterable=True,
        ),
        Property(
            name="text",
            data_type=DataType.TEXT,
            vectorize_property_name=False,
            tokenization=Tokenization.TRIGRAM,
            skip_vectorization=True,
            index_searchable=True,
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
    collection_name = "chunks"
