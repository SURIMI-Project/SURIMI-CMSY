from datetime import datetime
import os
from dateutil.relativedelta import relativedelta
import grpc
from server.s3_storage import S3_Storage
from server.simulation import Simulation
from surimi.v1 import workflow_pb2, workflow_pb2_grpc
from pathlib import Path
import shutil

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

        # download the catch_file.csv, if_file.csv and AA_CMSY++.R from the S3 bucket to R_files
        S3_Storage.DownloadFilesFromS3("Surimi-cmsy/Config", "R_files")

# ✅ Create a directory named after the simulation_id inside ./simulations
        output_directory = Path(__file__).parent.parent.parent.resolve() / Path("simulations") / request.simulation_id
        try:
            # Creates the directory. parents=True makes sure "simulations/" is created if missing.
            # exist_ok=False means it will fail if the folder already exists — avoids overwriting.
            output_directory.mkdir(parents=True, exist_ok=True)
            print(f"Created simulation directory: {output_directory}")
        except FileExistsError:
            context.abort(grpc.StatusCode.ALREADY_EXISTS, f"Directory already exists: {output_directory}")
        except Exception as e:
            context.abort(grpc.StatusCode.INTERNAL, f"Directory creation failed: {str(e)}")

        # Copy catch_file.csv, if_file.csv and AA_CMSY++.R from R_files to output_directory
        src_dir = Path(__file__).parent.parent / Path("R_files")
        shutil.copy(src_dir / "catch_file.csv", output_directory / "catch_file.csv")
        shutil.copy(src_dir / "id_file.csv", output_directory / "id_file.csv")
        shutil.copy(src_dir / "AA_CMSY++.R", output_directory / "AA_CMSY++.R")
        shutil.copy(src_dir / "ffnn.bin", output_directory / "ffnn.bin")

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

        sim = self.simulation_dictionary[request.simulation_id]

        if(sim.step_size != "P1M"):
           # calculation of other step sizes is not implemented yet
           context.abort(grpc.StatusCode.INVALID_ARGUMENT, "Only monthly steps are supported. Please set the step size to P1M.")

        print(f"SimulateStep for simulation {request.simulation_id}")
        # Check if the year is complete
        # if so, add the biomass of the species to the csv file

        current_year = sim.current_date_time.year
        # Increment the current date time by one month
        sim.current_date_time += relativedelta(months=1)

        if(current_year != sim.current_date_time.year):
            print(f"Year {current_year} is complete. Adding biomass data to the csv file.")
            # Here you would add the logic to write the biomass data to a CSV file or database
            #ALSO CHANGE THE YEAR IN THE ID_FILE.CSV TO THE CURRENT YEAR

            catch_file = {}
            # catch_file is a dictionary that will hold the catch data for each species and division

            # Loop over every species in the aggregated_catch_dictionary
            for species_code, cell_catches in sim.aggregated_catch_dictionary.items():
                if species_code not in catch_file:
                    catch_file[species_code] = {}

                for cell_key, catch_value in sim.aggregated_catch_dictionary[species_code].items():
                    division = self.GetDivision(cell_key[0], cell_key[1])

                    if division not in catch_file[species_code]:
                        catch_file[species_code][division] = 0.0
                    # Add the catch of the cell to the catch file for the species  
                    catch_file[species_code][division] += catch_value

            # Write the catch_file to a CSV file
            
            sim.aggregated_catch_dictionary.clear()  # Reset the aggregated catch for the new year
            sim.aggregated_biomass.clear()  # Reset the aggregated biomass for the new year

        return workflow_pb2.SimulateStepResponse()

    def GetDivision(self, latitude: float, longitude: float) -> str:
        # Example logic: return a division string based on coordinates
        if 50.0 <= latitude < 60.0 and -5.0 <= longitude < 2.0:
            return "North Sea"
        elif 48.0 <= latitude < 50.0 and -6.0 <= longitude < -2.0:
            return "Western Channel"
        else:
            return "Unknown Division"
    
