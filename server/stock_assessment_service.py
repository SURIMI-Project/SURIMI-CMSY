import os
import grpc
from surimi.v1 import stock_assessment_pb2, stock_assessment_pb2_grpc
from r_scriptrunner import R_ScriptRunner
from s3_storage import S3_Storage
import boto3
from pathlib import Path


class StockAssessmentService(stock_assessment_pb2_grpc.StockAssessmentServiceServicer):
    def __init__(self, tracer, simulation_dictionary):
        self.simulation_dictionary = simulation_dictionary  # Will hold the current simulation instance
        self.tracer = tracer  # Store the tracer instance

    def CreateStockAssessment(self, request, context):
        if not request.simulation_id in self.simulation_dictionary.keys():
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, "Simulation Id not known.")

        print(f"Create Stock Assessment for simulation {request.simulation_id} ")
        output_directory = Path("..").resolve() / Path("simulations") / request.simulation_id
        R_ScriptRunner.run_r_script(str(output_directory / "AA_CMSY++.R"))

        S3_Storage.UploadFilesToS3(output_directory, f"Surimi-cmsy/Simulations/{request.simulation_id}")

        return stock_assessment_pb2.CreateStockAssessmentResponse()

