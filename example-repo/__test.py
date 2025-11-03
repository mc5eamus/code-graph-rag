import dotenv
import os
from plugins.metrics import VmMetricsClient
from plugins.weaviate import QueryLibraryPlugin
from plugins.kusto import KustoQueryExecutor
from plugins.embeddings import EmbeddingsClient
from plugins.advisor import AzureAdvisorClient
from azure.mgmt.resourcegraph import ResourceGraphClient
from azure.mgmt.resourcegraph.models import QueryRequest

import requests
import json
from datetime import datetime, timezone, timedelta
from azure.identity import DefaultAzureCredential, AzureCliCredential

dotenv.load_dotenv()

# authentication via DefaultAzureCredential()
credentials = AzureCliCredential()
#token = credentials.get_token(f"https://management.azure.com/.default").token

embeddings_client = EmbeddingsClient(
    endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    engine=os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME"),
    api_key=os.getenv("AZURE_OPENAI_API_KEY", None)
)

async def test_query_suggestions():
    query_library_plugin = QueryLibraryPlugin(embeddings_client=embeddings_client)
    purpose = "count of subscriptions"
    keywords = ["subscriptions", "count"]

    results = await query_library_plugin.get_query_suggestions(purpose, keywords)
    for r in results:
        print(f"ID: {r.id}")
        print(f"Title: {r.title}")
        print(f"Description: {r.description}")
        print(f"Query: {r.query}")
        print("-----")

async def test_advisor_recommendations():
    subscription_id = "404015db-0ca0-4e13-ae86-7f011c202d40"
    resource_group = "rg-shh-prod-rmp-01"
    resource_name = "shhwsr2867"

    
    advisor_plugin = AzureAdvisorClient()
    recommendations = advisor_plugin.get_recommendations(subscription_id=subscription_id, resource_name=resource_name)
    print(recommendations)

    

async def graph_main(
        subscription_id: str = "290c25ee-c645-46e9-ae89-24db2105d527",
        resource_group: str = "rg-genix-hsc", 
        resource_name: str = "edgesouth"):

    # Create the client
    client = ResourceGraphClient(credentials)

    query = f"""
    advisorresources
    | where resourceGroup=='{resource_group}' and subscriptionId=='{subscription_id}'
    | where type == 'microsoft.advisor/recommendations'
    | where properties contains_cs "Right-size"
    | extend resourceName = split(id, '/')[8]
    | where resourceName == '{resource_name}'
    """

    # Define the query
    query = QueryRequest(
        subscriptions=[subscription_id],
        query=query
    )

    # Execute the query
    response = client.resources(query)
    print(response)

async def main():

    subscription_id = "75e8f45a-2aca-41b3-83ea-c3ee4c60e579"
    resource_group = "rg-cis-prod-vdistandard-01"
    vm_name = "crdwcl02194"

    vm_metrics_client = VmMetricsClient()
    metrics = vm_metrics_client.get_vm_metrics(subscription_id, resource_group, vm_name)
    print(metrics)


if __name__ == "__main__":
    import asyncio
    # asyncio.run(graph_main())
    # asyncio.run(test_query_suggestions())
    asyncio.run(test_advisor_recommendations())

