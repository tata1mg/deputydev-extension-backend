from weaviate.classes.config import DataType, Property, Tokenization

from app.common.models.dao.weaviate.base import Base
from app.common.models.dao.weaviate.constants.collection_names import (
    CHUNKS_COLLECTION_NAME,
)


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
            tokenization=Tokenization.WORD,
            skip_vectorization=True,
            index_searchable=True,
        ),
    ]
    collection_name = CHUNKS_COLLECTION_NAME
