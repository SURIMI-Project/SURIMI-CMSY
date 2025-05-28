import grpc
from surimi.v1 import stock_assessment_pb2, stock_assessment_pb2_grpc
#from R_files.run_cmsy_python2 import run_r_script

class StockAssessmentService(stock_assessment_pb2_grpc.StockAssessmentServiceServicer):
    def __init__(self, tracer, simulation_dictionary):
        self.simulation_dictionary = simulation_dictionary  # Will hold the current simulation instance
        self.tracer = tracer  # Store the tracer instance

    def CreateStockAssessment(self, request, context):
        if not request.simulation_id in self.simulation_dictionary.keys():
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, "Simulation Id not known.")

        print(f"Create Stock Assessment for simulation {request.simulation_id} ")
     #   run_r_script()
        return stock_assessment_pb2.CreateStockAssessmentResponse()

