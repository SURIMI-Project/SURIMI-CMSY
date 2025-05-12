import grpc
from surimi.v1 import workflow_pb2, workflow_pb2_grpc

class WorkflowService(workflow_pb2_grpc.WorkflowServiceServicer):
    def __init__(self, tracer, simulation_dictionary):
        self.simulation_dictionary = simulation_dictionary  # Will hold the current simulation instance
        self.tracer = tracer  # Store the tracer instance

    def Init(self, request, context):
        if request.simulation_id in self.simulation_dictionary.keys():
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, "Simulation Id already exists.")

        print(f"Init simulation {request.simulation_id} for scenario {request.scenario_id} with start date {request.start_date_time} and step size {request.step_size}")

#           Create a new directory for the simulation results
#            new_simulation = Simulation(request.simulation_id, request.scenario_id, request.start_date_time, request.step_size)
        self.simulation_dictionary[request.simulation_id] = "new_simulation"

        return workflow_pb2.InitResponse()

    def UpdateBiomass(self, request, context):
        if not request.simulation_id in self.simulation_dictionary.keys():
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, "Simulation Id not known.")

        print(f"Update biomass for simulation {request.simulation_id} and measurement unit {request.measurement_unit}")
# Aggregate the biomass data
# Check if the year is complete
# if so, add the biomass of the species to the csv file

        return workflow_pb2.InitResponse()

