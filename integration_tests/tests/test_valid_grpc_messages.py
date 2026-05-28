import json
import pytest
from pathlib import Path
from google.protobuf import json_format
from surimi.v1 import (
    cancel_experiment_pb2,
    experiment_step_pb2,
    finalise_experiment_pb2,
    get_protocol_version_pb2,
    get_stock_assessment_pb2,
    initialise_experiment_pb2,
    update_biomass_statistics_pb2,
    update_catch_disposition_statistics_pb2,
)

FOLDER_TO_MESSAGE = {
    "CancelExperiment":               cancel_experiment_pb2.CancelExperimentRequest,
    "ExperimentStep":                 experiment_step_pb2.ExperimentStepRequest,
    "FinaliseExperiment":             finalise_experiment_pb2.FinaliseExperimentRequest,
    "GetProtocolVersion":             get_protocol_version_pb2.GetProtocolVersionRequest,
    "GetStockAssessment":             get_stock_assessment_pb2.GetStockAssessmentRequest,
    "InitialiseExperiment":           initialise_experiment_pb2.InitialiseExperimentRequest,
    "UpdateBiomassStatistics":        update_biomass_statistics_pb2.UpdateBiomassStatisticsRequest,
    "UpdateCatchDispositionStatistics": update_catch_disposition_statistics_pb2.UpdateCatchDispositionStatisticsRequest,
}

_FIXTURES_ROOT = Path(__file__).parent.parent / "GrpcMessages"


def _collect_fixtures():
    params = []
    for folder, message_cls in FOLDER_TO_MESSAGE.items():
        folder_path = _FIXTURES_ROOT / folder
        if folder_path.is_dir():
            for json_file in sorted(folder_path.glob("*.json")):
                params.append(pytest.param(json_file, message_cls, id=f"{folder}/{json_file.name}"))
    return params


@pytest.mark.parametrize("json_file,message_cls", _collect_fixtures())
def test_grpc_message_is_valid(json_file, message_cls):
    data = json.loads(json_file.read_text(encoding="utf-8"))
    json_format.ParseDict(data, message_cls(), ignore_unknown_fields=False)
