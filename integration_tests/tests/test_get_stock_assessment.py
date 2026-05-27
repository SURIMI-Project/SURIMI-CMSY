from integration_tests.helpers.message_loader import load_message


def test_get_stock_assessment_returns_species(grpc_client):

    init_message = load_message("InitialiseExperiment", "StockAssessmentService_InitialiseExperiment.json")
    experiment_id = init_message["experiment_id"]
    grpc_client.initialise_experiment(init_message)

    message = load_message("GetStockAssessment", "StockAssessmentService_GetStockAssessment.json")
    response = grpc_client.get_stock_assessment(message)

    assert response is not None
    assert response.experiment_id == message["experiment_id"]

    species_codes = {
        ssa.species.species_code
        for ssa in response.stock_assessment_summary.species_stock_assessments
    }
    assert "PIL" in species_codes
    assert "ANK" in species_codes
    assert "BOG" in species_codes

    for ssa in response.stock_assessment_summary.species_stock_assessments:
        assert len(ssa.stock_assessments) > 0
        for sa in ssa.stock_assessments:
            assert sa.year > 0
