import logging
from dataclasses import dataclass
from typing import List
from weaviate import connect_to_local
from weaviate.classes.query import MetadataQuery
from plugins.embeddings import EmbeddingsClient
from plugins.model import DashboardQuery, QuerySuggestionResponse
from plugins.config import COLLECTION_NAME

class QueryLibraryPlugin:
    
    def __init__(self,  embeddings_client: EmbeddingsClient, vectorstore):
        self.embeddings_client = embeddings_client
        self.vectorstore = vectorstore
        self.logger = logging.getLogger(__name__)

    async def get_query_suggestions(
        self,
        query_purpose: str,
        keywords: List[str]
    ) -> QuerySuggestionResponse:
        
        """
        Provides samples of queries for a specific task.
        
        Args:
            query_purpose: Purpose of the query
            keywords: Keywords extracted from the query
            
        Returns:
            List of DashboardQuery objects
        """
        self.logger.info(f"Searching for queries matching: '{query_purpose}', keywords: {', '.join(keywords)}")
        
        try:
            # Generate embedding for the query purpose
            embedded_question = await self.embeddings_client.get_embedding(query_purpose)

            # Ensure collection exists
            if not self.vectorstore.exists(COLLECTION_NAME):
                return {
                    "error": f"Collection '{COLLECTION_NAME}' does not exist, please make sure to populate it with query examples.",
                    "queries": []
                }

            # Perform vector search
            result = self.vectorstore.query_nearest(COLLECTION_NAME, embedded_question[0], limit=3)

            queries = []
            for obj in result:
                dashboard_query = DashboardQuery(
                    id=obj.get("id", ""),
                    title=obj.get("title", ""),
                    description=obj.get("description", ""),
                    query=obj.get("query", "")
                )
                queries.append(dashboard_query)

                self.logger.info(f"Found query candidate: {dashboard_query.title} - {dashboard_query.description} (distance: {obj.get('distance')})")

            return {"queries": queries}
            
        except Exception as e:
            self.logger.error(f"Error while searching for queries: {e}")
            return {
                "error": str(e),
                "queries": []
            }
