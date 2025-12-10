import grpc
from surimi.v1 import fishery_service_pb2, fishery_service_pb2_grpc
from opentelemetry import trace
from common_functions import log_and_abort

class FisheryService(fishery_service_pb2_grpc.FisheryServiceServicer):
    def __init__(self, tracer, simulation_dictionary):
        self.simulation_dictionary = simulation_dictionary  # Will hold the current simulation instance
        self.tracer = tracer  # Store the tracer instance

    def UpdateCatchDisposition(self, request, context):
        trace.get_current_span().set_attribute("simulation_id", request.simulation_id)
        if not request.simulation_id in self.simulation_dictionary.keys():
            log_and_abort(context, grpc.StatusCode.INVALID_ARGUMENT, f"Simulation Id {request.simulation_id} not known.")

        print(f"Update CatchDisposition for simulation {request.simulation_id} ")
# Aggregate the catch data
# Check if the year is complete
# if so, add the catch of the species to the csv file
        print(request)  # for debugging purposes

        sim = self.simulation_dictionary[request.simulation_id]

        # Loop over every grid in Disposition_grids
        for grid in request.catch_disposition_summary.disposition_grids:
            # Check if the species is already in the aggregated_catch_dictionary
            if grid.species.species_code not in sim.aggregated_catch_dictionary:
                sim.aggregated_catch_dictionary[grid.species.species_code] = {}

            # Loop over every cell in the grid
            for cell in grid.disposition_cells:
                cell_key = (cell.latitude, cell.longitude)
                # Check if the cell is already in the aggregated_catch_dictionary for the species   
                if cell_key not in sim.aggregated_catch_dictionary[grid.species.species_code]:
                    sim.aggregated_catch_dictionary[grid.species.species_code][cell_key] = 0.0
                
                # Add the catch of the cell to the aggregated_catch_dictionary for the species  
                sim.aggregated_catch_dictionary[grid.species.species_code][cell_key] += cell.gross_catch                    


        return fishery_service_pb2.UpdateCatchDispositionResponse(
            simulation_id=request.simulation_id
        )

