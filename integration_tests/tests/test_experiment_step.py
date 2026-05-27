from integration_tests.helpers.message_loader import load_message


def test_experiment_step_advances_time(grpc_client):
    message = load_message("ExperimentStep", "StockAssesmentService_ExperimentStep.json")
    response = grpc_client.experiment_step(message)
    assert response is not None
    assert response.experiment_id == message["experiment_id"]
