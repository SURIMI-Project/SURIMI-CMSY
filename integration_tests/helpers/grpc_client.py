import grpc
from google.protobuf import json_format
from surimi.v1 import (
    stock_assesment_service_pb2_grpc,
    cancel_experiment_pb2,
    experiment_step_pb2,
    finalise_experiment_pb2,
    get_protocol_version_pb2,
    initialise_experiment_pb2,
    update_biomass_statistics_pb2,
    update_catch_disposition_statistics_pb2,
)

SERVICE_ADDRESS = "localhost:5021"


class CmsyGrpcClient:
    def __init__(self, address: str = SERVICE_ADDRESS):
        self.channel = grpc.insecure_channel(address)
        self.stub = stock_assesment_service_pb2_grpc.StockAssesmentServiceStub(self.channel)

    def close(self):
        self.channel.close()

    def get_protocol_version(self, message_dict: dict):
        request = json_format.ParseDict(
            message_dict, get_protocol_version_pb2.GetProtocolVersionRequest()
        )
        return self.stub.GetProtocolVersion(request)

    def initialise_experiment(self, message_dict: dict):
        request = json_format.ParseDict(
            message_dict, initialise_experiment_pb2.InitialiseExperimentRequest()
        )
        return self.stub.InitialiseExperiment(request)

    def experiment_step(self, message_dict: dict):
        request = json_format.ParseDict(
            message_dict, experiment_step_pb2.ExperimentStepRequest()
        )
        return self.stub.ExperimentStep(request)

    def update_biomass_statistics(self, message_dict: dict):
        request = json_format.ParseDict(
            message_dict, update_biomass_statistics_pb2.UpdateBiomassStatisticsRequest()
        )
        return self.stub.UpdateBiomassStatistics(request)

    def update_catch_disposition_statistics(self, message_dict: dict):
        request = json_format.ParseDict(
            message_dict,
            update_catch_disposition_statistics_pb2.UpdateCatchDispositionStatisticsRequest(),
        )
        return self.stub.UpdateCatchDispositionStatistics(request)

    def finalise_experiment(self, message_dict: dict):
        request = json_format.ParseDict(
            message_dict, finalise_experiment_pb2.FinaliseExperimentRequest()
        )
        return self.stub.FinaliseExperiment(request)

    def cancel_experiment(self, message_dict: dict):
        request = json_format.ParseDict(
            message_dict, cancel_experiment_pb2.CancelExperimentRequest()
        )
        return self.stub.CancelExperiment(request)
