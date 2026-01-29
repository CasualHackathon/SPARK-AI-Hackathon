# tools/github_client.py
import os
from gql import Client
from gql.transport.requests import RequestsHTTPTransport

github_token = os.environ.get("GITHUB_TOKEN")
if not github_token:
    raise RuntimeError("Missing GITHUB_TOKEN environment variable.")
    

transport = RequestsHTTPTransport(
    url="https://api.github.com/graphql",
    headers={"Authorization": f"Bearer {github_token}"},
    use_json=True,
)

client = Client(transport=transport, fetch_schema_from_transport=True)
