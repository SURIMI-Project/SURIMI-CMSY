import pytest
from integration_tests.helpers.service_runner import start_service, stop_service
from integration_tests.helpers.grpc_client import CmsyGrpcClient


@pytest.fixture(scope="session")
def cmsy_service():
    """Start the CMSY gRPC server in a background thread within the pytest process.

    Because the server runs in the same process, VS Code breakpoints in
    StockAssessment.py are hit automatically when using 'Debug Tests'.
    """
    thread = start_service()
    yield thread
    stop_service(thread)


@pytest.fixture(scope="session")
def grpc_client(cmsy_service):
    """Create a gRPC client connected to the running CMSY service."""
    client = CmsyGrpcClient()
    yield client
    client.close()
