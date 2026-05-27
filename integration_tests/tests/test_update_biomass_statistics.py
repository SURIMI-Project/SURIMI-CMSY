from integration_tests.helpers.message_loader import load_message


def test_update_biomass_statistics_succeeds(grpc_client):
    message = load_message("UpdateBiomassStatistics")
    response = grpc_client.update_biomass_statistics(message)
    assert response is not None
    assert response.experiment_id == message["experiment_id"]
