import grpc
from surimi.v1 import ecology_pb2, ecology_pb2_grpc

class EcologyService(ecology_pb2_grpc.EcologyServiceServicer):
    def __init__(self, tracer, simulation_dictionary):
        self.simulation_dictionary = simulation_dictionary  # Will hold the current simulation instance
        self.tracer = tracer  # Store the tracer instance

    def UpdateCatchDispositionSummary(self, request, context):
        if not request.simulation_id in self.simulation_dictionary.keys():
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, "Simulation Id not known.")

        print(f"Update CatchDisposition for simulation {request.simulation_id} ")
# Aggregate the catch data
# Check if the year is complete
# if so, add the catch of the species to the csv file
        print(request)  # for debugging purposes


        catch = 545.23  # for example

        self.simulation_dictionary[request.simulation_id].aggregated_catch += catch

        return ecology_pb2.UpdateCatchDispositionSummaryResponse()

