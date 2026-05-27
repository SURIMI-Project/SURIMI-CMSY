import grpc
import pytest
from integration_tests.helpers.message_loader import load_message


def test_initialise_experiment_succeeds(grpc_client):
    message = load_message("InitialiseExperiment", "StockAssesmentService_InitialiseExperiment.json")
    response = grpc_client.initialise_experiment(message)
    assert response is not None
    assert response.experiment_id == message["experiment_id"]


# def test_initialise_experiment_duplicate_id_raises(grpc_client):
#     """Sending the same experiment_id twice must be rejected."""
#    message = load_message("InitialiseExperiment", "StockAssesmentService_InitialiseExperiment.json")
#     with pytest.raises(grpc.RpcError) as exc_info:
#         grpc_client.initialise_experiment(message)
#     assert exc_info.value.code() == grpc.StatusCode.INVALID_ARGUMENT


# def test_initialise_experiment_wrong_timestep_raises(grpc_client):
#     """A time_step other than P1M must be rejected."""
#    message = load_message("InitialiseExperiment", "StockAssesmentService_InitialiseExperiment.json")
#     message = dict(message)  # shallow copy
#     message["experiment_id"] = "test-experiment-wrong-step"
#     message["simulation"] = dict(message["simulation"])
#     message["simulation"]["time_step"] = "P1Y"
#     with pytest.raises(grpc.RpcError) as exc_info:
#         grpc_client.initialise_experiment(message)
#     assert exc_info.value.code() == grpc.StatusCode.INVALID_ARGUMENT
