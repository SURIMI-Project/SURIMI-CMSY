from datetime import datetime
from dateutil.relativedelta import relativedelta
import grpc
from server.Simulation import Simulation
from surimi.v1 import workflow_pb2, workflow_pb2_grpc
from pathlib import Path

class WorkflowService(workflow_pb2_grpc.WorkflowServiceServicer):
    def __init__(self, tracer, simulation_dictionary):
        self.simulation_dictionary = simulation_dictionary  # Will hold the current simulation instance
        self.tracer = tracer  # Store the tracer instance

    def Init(self, request, context):
        if request.simulation_id in self.simulation_dictionary.keys():
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, "Simulation Id already exists.")

        if(request.step_size != "P1M"):
           # calculation of other step sizes is not implemented yet
           context.abort(grpc.StatusCode.INVALID_ARGUMENT, "Only monthly steps are supported. Please set the step size to P1M.")

        simulation = Simulation(
            start_date_time=datetime.now(), #request.start_date_time,
            step_size=request.step_size,
        )
        print(f"Init simulation {request.simulation_id} for scenario {request.scenario_id} with start date {request.start_date_time} and step size {request.step_size}")

# ✅ Create a directory named after the simulation_id inside ./simulations
        output_directory = Path("simulations") / request.simulation_id
        try:
            # Creates the directory. parents=True makes sure "simulations/" is created if missing.
            # exist_ok=False means it will fail if the folder already exists — avoids overwriting.
            output_directory.mkdir(parents=True, exist_ok=False)
            print(f"Created simulation directory: {output_directory}")
        except FileExistsError:
            context.abort(grpc.StatusCode.ALREADY_EXISTS, f"Directory already exists: {output_directory}")
        except Exception as e:
            context.abort(grpc.StatusCode.INTERNAL, f"Directory creation failed: {str(e)}")

##TODO: COPY CATCH.CSV AND ID FILES TO THE NEW DIRECTORY
#           Create a new directory for the simulation results
#            new_simulation = Simulation(request.simulation_id, request.scenario_id, request.start_date_time, request.step_size)
        self.simulation_dictionary[request.simulation_id] = simulation

        return workflow_pb2.InitResponse()

    def UpdateBiomass(self, request, context):
        if not request.simulation_id in self.simulation_dictionary.keys():
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, "Simulation Id not known.")

        print(f"Update biomass for simulation {request.simulation_id} and measurement unit {request.measurement_unit}")
        print(request)  # for debugging purposes

        sim = self.simulation_dictionary[request.simulation_id]

        # Loop over every grid in biomass_grids
        for grid in request.biomass_grids:
            # Check if the species is already in the aggregated_biomass
            if grid.species_code not in sim.aggregated_biomass:
                sim.aggregated_biomass[grid.species_code] = {}

            # Loop over every cell in the grid
            for cell in grid.biomass_cells:
                cell_key = (cell.latitude, cell.longitude)
                # Check if the cell is already in the aggregated_biomass for the species   
                if cell_key not in sim.aggregated_biomass[grid.species_code]:
                    sim.aggregated_biomass[grid.species_code][cell_key] = 0.0
                
                # Add the biomass of the cell to the aggregated_biomass for the species  
                sim.aggregated_biomass[grid.species_code][cell_key] += cell.biomass                    

        return workflow_pb2.InitResponse()

    # this method is called at the end of the month.
    def SimulateStep(self, request, context):
        if not request.simulation_id in self.simulation_dictionary.keys():
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, "Simulation Id not known.")

        if(self.simulation_dictionary[request.simulation_id].step_size != "P1M"):
           # calculation of other step sizes is not implemented yet
           context.abort(grpc.StatusCode.INVALID_ARGUMENT, "Only monthly steps are supported. Please set the step size to P1M.")

        print(f"SimulateStep for simulation {request.simulation_id}")
        # Check if the year is complete
        # if so, add the biomass of the species to the csv file

        current_year = self.simulation_dictionary[request.simulation_id].current_date_time.year
        # Increment the current date time by one month
        self.simulation_dictionary[request.simulation_id].current_date_time += relativedelta(months=1)

        if(current_year != self.simulation_dictionary[request.simulation_id].current_date_time.year):
            print(f"Year {current_year} is complete. Adding biomass data to the csv file.")
            # Here you would add the logic to write the biomass data to a CSV file or database
            #ALSO CHANGE THE YEAR IN THE ID_FILE.CSV TO THE CURRENT YEAR

            del self.simulation_dictionary[request.simulation_id].aggregated_catch  # Reset the aggregated catch for the new year
            del self.simulation_dictionary[request.simulation_id].aggregated_biomass  # Reset the aggregated biomass for the new year

        return workflow_pb2.SimulateStepResponse()
