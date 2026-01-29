import os
import time
import uuid

import pytest
from dotenv import load_dotenv

from spoon_ai.neofs.client import NeoFSClient, NeoFSAPIException
from spoon_ai.neofs.models import Attribute, Bearer, ContainerPostInfo, Rule
from urllib.parse import urlparse, urlunparse

load_dotenv()

# Skip all tests in this module if environment variables are not set
pytestmark = pytest.mark.skipif(
    not all(os.getenv(key) for key in ["NEOFS_BASE_URL", "NEOFS_OWNER_ADDRESS", "NEOFS_PRIVATE_KEY_WIF"]),
    reason="Missing required environment variables for NeoFS integration tests"
)


def _ensure_mainnet_base_url(client: NeoFSClient) -> str:
    parsed = urlparse(client.base_url)
    host = parsed.netloc
    if host.startswith("rest.t5."):
        host = host.replace("rest.t5.", "rest.", 1)
        return urlunparse(parsed._replace(netloc=host))
    return client.base_url


@pytest.fixture(scope="module")
def client():
    """Provides a NeoFSClient instance for the test module."""
    original = NeoFSClient()
    override_base_url = _ensure_mainnet_base_url(original)
    if override_base_url != original.base_url:
        return NeoFSClient(base_url=override_base_url)
    return original

@pytest.fixture(scope="module")
def container_tokens(client: NeoFSClient):
    """Generates bearer tokens for container CRUD operations."""
    put_rule = Rule(verb="PUT", containerId="")
    delete_rule = Rule(verb="DELETE", containerId="")
    put_bearer = Bearer(name="container-put-token", container=put_rule)
    delete_bearer = Bearer(name="container-delete-token", container=delete_rule)
    responses = client.create_bearer_tokens([put_bearer, delete_bearer])
    mapping = {resp.name: resp.token for resp in responses}
    return {
        "put": mapping[put_bearer.name],
        "delete": mapping[delete_bearer.name],
    }


def wait_for_container_absence(client: NeoFSClient, container_id: str, *, poll_interval: int = 10, max_attempts: int = 12) -> bool:
    """Polls the gateway until the container disappears or the attempts are exhausted."""
    for _ in range(max_attempts):
        time.sleep(poll_interval)
        try:
            client.get_container(container_id)
        except NeoFSAPIException as exc:
            message = exc.error.message.lower()
            if exc.error.code == 3072 or "container not found" in message:
                return True
            raise
    return False

def test_get_network_info(client: NeoFSClient):
    """Tests fetching network information."""
    info = client.get_network_info()
    assert info.epoch_duration > 0
    assert info.storage_price > 0

def test_get_balance(client: NeoFSClient):
    """Tests fetching the account balance."""
    balance = client.get_balance()
    assert balance.address == client.owner_address
    assert int(balance.value) >= 0

def test_create_container(client: NeoFSClient, container_tokens: dict[str, str]):
    """Ensure a container can be created and retrieved."""
    container_name = f"test-container-{uuid.uuid4()}"
    container_info = ContainerPostInfo(
        containerName=container_name,
        placementPolicy="REP 3",
        basicAcl="public-read-write",
        attributes=[Attribute(key="test-key", value="test-value")],
    )

    created_container = client.create_container(container_info, container_tokens["put"])
    assert created_container.container_name == container_name
    assert created_container.owner_id == client.owner_address

    # Follow-up fetch to confirm propagation.
    time.sleep(5)
    fetched_container = client.get_container(created_container.container_id)
    assert fetched_container.container_id == created_container.container_id

    # Cleanup
    delete_response = client.delete_container(
        created_container.container_id,
        bearer_token=container_tokens["delete"],
        wallet_connect=True,
    )
    assert delete_response.success is True
    try:
        assert wait_for_container_absence(client, created_container.container_id)
    except NeoFSAPIException as exc:
        pytest.xfail(f"Gateway confirmation timeout during cleanup: {exc}")
