from datetime import datetime
from dateutil.relativedelta import relativedelta
import grpc
from server.s3_storage import S3_Storage
from server.simulation import Simulation
from surimi.v1 import workflow_pb2, workflow_pb2_grpc
from pathlib import Path
import shutil
from server.division_lookup import get_division
from server.species_lookup import get_common_name
import logging

logger = logging.getLogger(__name__)

class WorkflowService(workflow_pb2_grpc.WorkflowServiceServicer):
    def __init__(self, tracer, simulation_dictionary):
        self.simulation_dictionary = simulation_dictionary  # Will hold the current simulation instance
        self.tracer = tracer  # Store the tracer instance

    def Initialise(self, request, context):
        if request.simulation_id in self.simulation_dictionary.keys():
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, "Simulation Id already exists.")

        if request.step_size != "P1M":
            # calculation of other step sizes is not implemented yet
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, "Only monthly steps are supported. Please set the step size to P1M.")

        simulation = Simulation(
            start_date_time=datetime.now(),
            step_size=request.step_size,
        )
        print(f"Init simulation {request.simulation_id} for scenario {request.scenario_id} with start date {request.start_date_time} and step size {request.step_size}")

        # download the catch_file.csv, if_file.csv and AA_CMSY++.R from the S3 bucket to R_files
        S3_Storage.DownloadFilesFromS3("Surimi-cmsy/Config", "R_files")

        # ✅ Create a directory named after the simulation_id inside ./simulations
        output_directory = Path(__file__).parent.parent.resolve() / Path("simulations") / request.simulation_id
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
        src_dir = Path(__file__).parent.parent.resolve() / Path("R_files")
        print(f"Copying files from {src_dir} to {output_directory}")
        shutil.copy(src_dir / "catch_file.csv", output_directory / "catch_file.csv")
        shutil.copy(src_dir / "id_file.csv", output_directory / "id_file.csv")
        shutil.copy(src_dir / "AA_CMSY++.R", output_directory / "AA_CMSY++.R")
        shutil.copy(src_dir / "ffnn.bin", output_directory / "ffnn.bin")

        self.simulation_dictionary[request.simulation_id] = simulation
        return workflow_pb2.InitialiseResponse(
            simulation_id=request.simulation_id
        )

    # this method is called at the end of the month.
    def SimulateStep(self, request, context):
        if request.simulation_id not in self.simulation_dictionary:
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, "Simulation Id not known.")

        sim = self.simulation_dictionary[request.simulation_id]

        if sim.step_size != "P1M":
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, "Only monthly steps are supported. Please set the step size to P1M.")

        print(f"SimulateStep for simulation {request.simulation_id}")

        current_year = sim.current_date_time.year
        sim.current_date_time += relativedelta(months=1)

        if current_year != sim.current_date_time.year:
            print(f"Year {current_year} is complete. Processing catch data.")

            # ✅ CATCH FILE PATH IS ONLY NEEDED INSIDE HERE
            catch_file_path = Path(__file__).parent.parent.resolve() / "simulations" / request.simulation_id / "catch_file.csv"

            catch_file = {}

            for species_code, cell_catches in sim.aggregated_catch_dictionary.items():
                for cell_key, catch_value in cell_catches.items():
                    division = get_division(cell_key[0], cell_key[1])
                    common_name = get_common_name(species_code)
                    print(f"📦 Catch for species {species_code} ({common_name}) in division {division}")

                    if common_name not in catch_file:
                        catch_file[common_name] = {}

                    if division not in catch_file[common_name]:
                        catch_file[common_name][division] = 0.0

                    catch_file[common_name][division] += catch_value

            import csv
            sim.last_written_stock_names = []  # ✅ ADDED TO STORE STOCKS FOR FINALISE
            sim.last_written_year = current_year  # ✅ ADDED TO STORE YEAR FOR FINALISE

            with open(catch_file_path, mode='a', newline='') as csvfile:
                writer = csv.writer(csvfile)
                for common_name, divisions in catch_file.items():
                    for division, catch_value in divisions.items():
                        stock_label = f"{common_name} - {division}"
                        row = [stock_label, current_year, round(catch_value, 2), "NA"]
                        writer.writerow(row)
                        sim.last_written_stock_names.append(stock_label)  # ✅ SAVE STOCK NAMES

            # ✅ MOVED TO FINALISE:
            # self._update_id_file(request.simulation_id, stock_names, current_year)

            sim.aggregated_catch_dictionary.clear()
            sim.aggregated_biomass.clear()

        return workflow_pb2.SimulateStepResponse(
            simulation_id=request.simulation_id
        )

    def Finalise(self, request, context):  # ✅ BRITISH SPELLING, POSITION MATCHES .PROTO
        if request.simulation_id not in self.simulation_dictionary:
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, "Simulation Id not known.")

        sim = self.simulation_dictionary[request.simulation_id]

        # ✅ MOVED FROM SimulateStep
        if hasattr(sim, "last_written_stock_names") and hasattr(sim, "last_written_year"):
            self._update_id_file(
                request.simulation_id,
                sim.last_written_stock_names,
                sim.last_written_year
            )
            print(f"✅ Finalise: id_file.csv updated for simulation {request.simulation_id}")
        else:
            print(f"⚠️ Finalise: No stock data found to update id_file.csv for {request.simulation_id}")

        return workflow_pb2.FinaliseResponse(
            simulation_id=request.simulation_id
        )

    def Cancel(self, request, context):  # ✅ NOW COMES AFTER FINALISE TO MATCH .PROTO
        if request.simulation_id not in self.simulation_dictionary:
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, "Simulation Id not known.")

        # Todo: Implement cancellation logic if needed, such as stopping ongoing processes or cleaning up resources

        return workflow_pb2.CancelResponse(  # ✅ FIXED TO MATCH .PROTO
            simulation_id=request.simulation_id
        )

    def _update_id_file(self, simulation_id: str, stocks: list[str], year: int):  # <-- NEW METHOD INSIDE CLASS
        import csv

        id_file_path = Path(__file__).parent.parent / "simulations" / simulation_id / "id_file.csv"

        if not id_file_path.exists():
            logger.error(f"id_file.csv not found for simulation {simulation_id}")
            return

        with open(id_file_path, newline='') as csvfile:
            reader = list(csv.DictReader(csvfile))
            fieldnames = reader[0].keys() if reader else []

        updated_rows = []
        for row in reader:
            if row.get("Stock") in stocks:
                row["MaxOfYear"] = str(year)
                row["EndYear"] = str(year)
            updated_rows.append(row)

        with open(id_file_path, mode='w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(updated_rows)

        print(f"✅ id_file.csv updated for year {year} and stocks: {stocks}")
