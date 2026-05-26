from integration_tests.helpers.message_loader import load_message
from integration_tests.helpers.grpc_client import CmsyGrpcClient
import copy


def test_cancel_experiment_succeeds(grpc_client):
    """Initialise a dedicated experiment then cancel it."""
    cancel_experiment_id = "cancel-test-00000000-0000-0000-0000-000000000001"

    # Initialise a dedicated experiment for the cancel test using the standard fixture
    init_message = copy.deepcopy(load_message("InitialiseExperiment"))
    init_message["experiment_id"] = cancel_experiment_id
    grpc_client.initialise_experiment(init_message)

    cancel_message = {"experiment_id": cancel_experiment_id}
    response = grpc_client.cancel_experiment(cancel_message)
    assert response is not None
    assert response.experiment_id == cancel_experiment_id
