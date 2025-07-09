import grpc
from surimi.v1 import ecology_pb2, ecology_pb2_grpc

class EcologyService(ecology_pb2_grpc.EcologyServiceServicer):
    def __init__(self, tracer, simulation_dictionary):
        self.simulation_dictionary = simulation_dictionary  # Will hold the current simulation instance
        self.tracer = tracer  # Store the tracer instance

    def UpdateBiomass(self, request, context):
        if request.simulation_id not in self.simulation_dictionary:
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, "Simulation Id not known.")

        print(f"Update biomass for simulation {request.simulation_id}")
        print(request)  # for debugging purposes

        sim = self.simulation_dictionary[request.simulation_id]

        # Loop over every grid in biomass_grids
        for grid in request.biomass_summary.biomass_grids:
            # Check if the species is already in the aggregated_biomass
            if grid.species.species_code not in sim.aggregated_biomass:
                sim.aggregated_biomass[grid.species.species_code] = {}

            # Loop over every cell in the grid
            for cell in grid.biomass_cells:
                cell_key = (cell.latitude, cell.longitude)
                # Check if the cell is already in the aggregated_biomass for the species   
                if cell_key not in sim.aggregated_biomass[grid.species.species_code]:
                    sim.aggregated_biomass[grid.species.species_code][cell_key] = 0.0
                # Add the biomass of the cell to the aggregated_biomass for the species  
                sim.aggregated_biomass[grid.species.species_code][cell_key] += cell.biomass

        return ecology_pb2.UpdateBiomassResponse(
            simulation_id=request.simulation_id
        )
