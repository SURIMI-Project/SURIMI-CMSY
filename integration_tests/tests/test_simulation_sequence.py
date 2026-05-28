import uuid
from pathlib import Path
from integration_tests.helpers.message_loader import load_message
from surimi.v1 import get_stock_assessment_pb2



def test_full_simulation_sequence(grpc_client):
   
    init_message = load_message("InitialiseExperiment", "StockAssessmentService_InitialiseExperiment_sequence.json")
    experiment_id = init_message["experiment_id"]
    grpc_client.initialise_experiment(init_message)

    message = load_message("UpdateCatchDispositionStatistics", "StockAssessmentService_UpdateCatchDispositionStatistics_2013_10.json")
    response = grpc_client.update_catch_disposition_statistics(message)
    assert response is not None
    assert response.experiment_id == experiment_id

    message = load_message("UpdateBiomassStatistics", "StockAssessmentService_UpdateBiomassStatistics_2013_10.json")
    response = grpc_client.update_biomass_statistics(message)
    assert response is not None
    assert response.experiment_id == experiment_id

    message = load_message("ExperimentStep", "StockAssessmentService_ExperimentStep_2013_10.json")
    response = grpc_client.experiment_step(message)
    assert response is not None
    assert response.experiment_id == experiment_id
    
    message = load_message("UpdateCatchDispositionStatistics", "StockAssessmentService_UpdateCatchDispositionStatistics_2013_11.json")
    response = grpc_client.update_catch_disposition_statistics(message)
    assert response is not None
    assert response.experiment_id == experiment_id

    message = load_message("UpdateBiomassStatistics", "StockAssessmentService_UpdateBiomassStatistics_2013_11.json")
    response = grpc_client.update_biomass_statistics(message)
    assert response is not None
    assert response.experiment_id == experiment_id

    message = load_message("ExperimentStep", "StockAssessmentService_ExperimentStep_2013_11.json")
    response = grpc_client.experiment_step(message)
    assert response is not None
    assert response.experiment_id == experiment_id

    message = load_message("UpdateCatchDispositionStatistics", "StockAssessmentService_UpdateCatchDispositionStatistics_2013_12.json")
    response = grpc_client.update_catch_disposition_statistics(message)
    assert response is not None
    assert response.experiment_id == experiment_id

    message = load_message("UpdateBiomassStatistics", "StockAssessmentService_UpdateBiomassStatistics_2013_12.json")
    response = grpc_client.update_biomass_statistics(message)
    assert response is not None
    assert response.experiment_id == experiment_id

    message = load_message("ExperimentStep", "StockAssessmentService_ExperimentStep_2013_12.json")
    response = grpc_client.experiment_step(message)
    assert response is not None
    assert response.experiment_id == experiment_id

    message = load_message("UpdateCatchDispositionStatistics", "StockAssessmentService_UpdateCatchDispositionStatistics_2014_01.json")
    response = grpc_client.update_catch_disposition_statistics(message)
    assert response is not None
    assert response.experiment_id == experiment_id

    message = load_message("UpdateBiomassStatistics", "StockAssessmentService_UpdateBiomassStatistics_2014_01.json")
    response = grpc_client.update_biomass_statistics(message)
    assert response is not None
    assert response.experiment_id == experiment_id

    message = load_message("ExperimentStep", "StockAssessmentService_ExperimentStep_2014_01.json")
    response = grpc_client.experiment_step(message)
    assert response is not None
    assert response.experiment_id == experiment_id

    message = load_message("FinaliseExperiment", "StockAssessmentService_FinaliseExperiment_sequence.json")
    response = grpc_client.finalise_experiment(message)
    assert response is not None
    assert response.experiment_id == experiment_id