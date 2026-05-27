from integration_tests.helpers.message_loader import load_message


def test_finalise_experiment_succeeds(grpc_client):
    message = load_message("FinaliseExperiment", "StockAssesmentService_FinaliseExperiment.json")
    response = grpc_client.finalise_experiment(message)
    assert response is not None
    assert response.experiment_id == message["experiment_id"]
