import grpc
from surimi.v1 import stock_assessment_pb2, stock_assessment_pb2_grpc
from r_scriptrunner import R_ScriptRunner
from opentelemetry import trace
from common_functions import log_and_abort

class StockAssessmentService(stock_assessment_pb2_grpc.StockAssessmentServiceServicer):
    def __init__(self, tracer, simulation_dictionary):
        self.simulation_dictionary = simulation_dictionary  # Will hold the current simulation instance
        self.tracer = tracer  # Store the tracer instance

    def CreateStockAssessment(self, request, context):
        trace.get_current_span().set_attribute("simulation_id", request.simulation_id)
        if not request.simulation_id in self.simulation_dictionary.keys():
            log_and_abort(context, grpc.StatusCode.INVALID_ARGUMENT, f"Simulation Id {request.simulation_id} not known.")

        print(f"Create Stock Assessment for simulation {request.simulation_id} ")

        # Run the R script. This messagehandler should be called by a client asynchonously and not awaited.
        # In that case the R script will run in the background and the client will not wait for the result.
        R_ScriptRunner.run_r_script_s3_upload("AA_CMSY++.R", request.simulation_id)

        return stock_assessment_pb2.CreateStockAssessmentResponse(
            simulation_id=request.simulation_id
        )

