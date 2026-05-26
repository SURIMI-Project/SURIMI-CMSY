import pytest
from integration_tests.helpers.service_runner import start_service, stop_service
from integration_tests.helpers.grpc_client import CmsyGrpcClient


@pytest.fixture(scope="session")
def cmsy_service():
    """Start the CMSY service once for the entire test session."""
    process = start_service()
    yield process
    stop_service(process)


@pytest.fixture(scope="session")
def grpc_client(cmsy_service):
    """Create a gRPC client connected to the running CMSY service."""
    client = CmsyGrpcClient()
    yield client
    client.close()
