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

        sim = self.simulation_dictionary[request.simulation_id]

        # Loop over every grid in Disposition_grids
        for grid in request.disposition_grids:
            # Check if the species is already in the aggregated_catch_dictionary
            if grid.species_code not in sim.aggregated_catch_dictionary:
                sim.aggregated_catch_dictionary[grid.species_code] = {}

            # Loop over every cell in the grid
            for cell in grid.disposition_cells:
                cell_key = (cell.latitude, cell.longitude)
                # Check if the cell is already in the aggregated_catch_dictionary for the species   
                if cell_key not in sim.aggregated_catch_dictionary[grid.species_code]:
                    sim.aggregated_catch_dictionary[grid.species_code][cell_key] = 0.0
                
                # Add the catch of the cell to the aggregated_catch_dictionary for the species  
                sim.aggregated_catch_dictionary[grid.species_code][cell_key] += cell.gross_catch                    


        return ecology_pb2.UpdateCatchDispositionSummaryResponse()

