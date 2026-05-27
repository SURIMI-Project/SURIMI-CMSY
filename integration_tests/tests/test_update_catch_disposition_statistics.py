import pytest
import grpc
import uuid
from integration_tests.helpers.message_loader import load_message


def test_update_catch_disposition_statistics_fails(grpc_client):
    message = load_message("UpdateCatchDispositionStatistics", "StockAssesmentService_UpdateCatchDispositionStatistics.json")
    with pytest.raises(grpc.RpcError) as exc_info:
        grpc_client.update_catch_disposition_statistics(message)
    assert "Experiment Id 3CD4786B-AABA-482E-9A2D-CAC4B2F6BAD6 not known" in str(exc_info.value)


def test_update_catch_disposition_statistics_succeeds(grpc_client):

    init_message = load_message("InitialiseExperiment", "StockAssesmentService_InitialiseExperiment.json")
    experiment_id = init_message["experiment_id"]
    grpc_client.initialise_experiment(init_message)

    message = load_message("UpdateCatchDispositionStatistics", "StockAssesmentService_UpdateCatchDispositionStatistics.json")
    response = grpc_client.update_catch_disposition_statistics(message)
    assert response is not None
    assert response.experiment_id == experiment_id
