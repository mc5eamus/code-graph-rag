from typing import List, Dict, Iterator, Optional
from abc import ABC, abstractmethod
import logging

# Weaviate imports used by the default adapter
import weaviate
from weaviate.classes.query import MetadataQuery
from plugins.config import COLLECTION_NAME


class VectorStore(ABC):
    """Abstract interface for a minimal vector store used by this repo.
    Concrete adapters should implement these methods.
    """

    @abstractmethod
    def exists(self, collection_name: str) -> bool:
        raise NotImplementedError

    @abstractmethod
    def create_collection(self, collection_name: str, properties_schema: Optional[dict] = None) -> None:
        raise NotImplementedError

    @abstractmethod
    def delete_collection(self, collection_name: str) -> None:
        raise NotImplementedError

    @abstractmethod
    def insert_many(self, collection_name: str, items: List[Dict]) -> None:
        """Insert many items. Each item should be a dict with keys: title, description, query, vector"""
        raise NotImplementedError

    @abstractmethod
    def query_nearest(self, collection_name: str, vector: List[float], limit: int = 3) -> List[Dict]:
        """Return a list of dicts with at least: title, description, query, distance"""
        raise NotImplementedError

    @abstractmethod
    def get_collection_iterator(self, collection_name: str) -> Iterator:
        raise NotImplementedError

    @abstractmethod
    def close(self) -> None:
        raise NotImplementedError


class WeaviateAdapter(VectorStore):
    """Adapter that implements the VectorStore interface using a local Weaviate instance.

    This preserves the current behavior of the repo so it can be used as the default
    adapter while you implement alternatives.
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        # Create a long-lived weaviate client (connect_to_local returns a client)
        # The original code used `with connect_to_local() as client:` for short-lived usage.
        # Keeping a persistent client here simplifies adapter usage.
        self.client = weaviate.connect_to_local()

    def exists(self, collection_name: str) -> bool:
        return self.client.collections.exists(collection_name)

    def create_collection(self, collection_name: str, properties_schema: Optional[dict] = None) -> None:
        # properties_schema is not required for the current repo uses; we create the collection
        # with a simple schema matching the repo expectations.
        if not self.exists(collection_name):
            from weaviate.classes.config import Property, DataType, Configure

            # If a caller provided a properties_schema, attempt to honor it. Otherwise, use defaults.
            if properties_schema is None:
                properties = [
                    Property(name="title", data_type=DataType.TEXT),
                    Property(name="description", data_type=DataType.TEXT),
                    Property(name="query", data_type=DataType.TEXT),
                ]
            else:
                # properties_schema expected as a list of property descriptors compatible with parser usage
                properties = properties_schema

            self.client.collections.create(
                name=collection_name,
                vectorizer_config=Configure.Vectorizer.none(),
                properties=properties,
            )

    def delete_collection(self, collection_name: str) -> None:
        if self.exists(collection_name):
            self.client.collections.delete(collection_name)

    def insert_many(self, collection_name: str, items: List[Dict]) -> None:
        """Insert items. Each item is expected to be a dict with keys: title, description, query, vector"""
        if not self.exists(collection_name):
            # Create collection with defaults if not exists
            self.create_collection(collection_name)

        collection = self.client.collections.get(collection_name)
        # The original code used DataObject instances; here we accept plain dicts and insert them
        # into Weaviate using insert_many.
        # Ensure items are in the expected shape for Weaviate SDK insert_many
        prepared = []
        for it in items:
            prepared.append(
                {
                    "properties": {
                        "title": it.get("title", ""),
                        "description": it.get("description", ""),
                        "query": it.get("query", ""),
                    },
                    "vector": it.get("vector", None),
                }
            )
        collection.data.insert_many(prepared)

    def query_nearest(self, collection_name: str, vector: List[float], limit: int = 3) -> List[Dict]:
        queries_collection = self.client.collections.get(collection_name)
        # Request distance metadata so the caller can log/inspect it
        result = queries_collection.query.near_vector(
            near_vector=vector,
            limit=limit,
            return_metadata=MetadataQuery(distance=True),
        )

        out = []
        for obj in result.objects:
            props = obj.properties
            out.append(
                {
                    "title": props.get("title", ""),
                    "description": props.get("description", ""),
                    "query": props.get("query", ""),
                    "distance": obj.metadata.distance if hasattr(obj, "metadata") and getattr(obj, "metadata") is not None and hasattr(obj.metadata, "distance") else None,
                }
            )
        return out

    def get_collection_iterator(self, collection_name: str) -> Iterator:
        collection = self.client.collections.get(collection_name)
        return collection.iterator()

    def close(self) -> None:
        # Close the underlying client if supported
        if hasattr(self.client, "close"):
            try:
                self.client.close()
            except Exception:
                pass
