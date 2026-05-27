from integration_tests.helpers.message_loader import load_message
from integration_tests.helpers.grpc_client import CmsyGrpcClient
import copy


def test_cancel_experiment_succeeds(grpc_client):
    """Initialise a dedicated experiment then cancel it."""

    # Initialise a dedicated experiment for the cancel test using the standard fixture
    init_message = load_message("InitialiseExperiment", "StockAssesmentService_InitialiseExperiment.json")
    grpc_client.initialise_experiment(init_message)

    cancel_message = {"experiment_id": init_message["experiment_id"]}
    response = grpc_client.cancel_experiment(cancel_message)
    assert response is not None
    assert response.experiment_id == init_message["experiment_id"]
