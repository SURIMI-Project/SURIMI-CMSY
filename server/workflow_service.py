from datetime import datetime
from dateutil.relativedelta import relativedelta
import grpc
from server.s3_storage import S3_Storage
from server.Simulation import Simulation
from surimi.v1 import workflow_service_pb2, workflow_service_pb2_grpc
from pathlib import Path
import shutil
from server.division_lookup import get_division
from server.species_lookup import get_common_name
from opentelemetry import trace
from common_functions import log_and_abort
from r_scriptrunner import R_ScriptRunner


class WorkflowService(workflow_service_pb2_grpc.WorkflowServiceServicer):
    def __init__(self, tracer, simulation_dictionary):
        self.simulation_dictionary = simulation_dictionary  # Will hold the current simulation instance
        self.tracer = tracer  # Store the tracer instance

    def Initialise(self, request, context):
        trace.get_current_span().set_attribute("simulation_id", request.simulation_id)
        if request.simulation_id in self.simulation_dictionary.keys():
            log_and_abort(context, grpc.StatusCode.INVALID_ARGUMENT, f"Simulation Id {request.simulation_id} already exists.")          

        if request.simulation.time_step != "P1M":
            log_and_abort(context, grpc.StatusCode.INVALID_ARGUMENT, f"Error in simulation {request.simulation_id}: Only monthly steps are supported. Please set the step size to P1M.")
    
        simulation = Simulation(
            start_date_time=datetime.now(),
            step_size=request.simulation.time_step,
        )
        print(f"Init simulation {request.simulation_id} for scenario {request.scenario_id} with start date {request.simulation.start_date_time} and step size {request.simulation.time_step}")

        S3_Storage.DownloadFilesFromS3("surimi-cmsy/Config", "R_files")

        output_directory = Path(__file__).parent.parent.resolve() / Path("simulations") / request.simulation_id
        try:
            output_directory.mkdir(parents=True, exist_ok=True)
            print(f"Created simulation directory: {output_directory}")
        except FileExistsError:
            log_and_abort(context, grpc.StatusCode.ALREADY_EXISTS, f"Directory already exists: {output_directory}")
        except Exception as e:
            log_and_abort(context, grpc.StatusCode.INTERNAL, f"Directory creation failed: {str(e)}")

        src_dir = Path(__file__).parent.parent.resolve() / Path("R_files")
        print(f"Copying files from {src_dir} to {output_directory}")
        shutil.copy(src_dir / "catch_file.csv", output_directory / "catch_file.csv")
        shutil.copy(src_dir / "id_file.csv", output_directory / "id_file.csv")
        shutil.copy(src_dir / "AA_CMSY++.R", output_directory / "AA_CMSY++.R")
        shutil.copy(src_dir / "ffnn.bin", output_directory / "ffnn.bin")

        self.simulation_dictionary[request.simulation_id] = simulation

        print(f"Create Stock Assessment for simulation {request.simulation_id} ")

        # Run the R script. This messagehandler should be called by a client asynchonously and not awaited.
        # In that case the R script will run in the background and the client will not wait for the result.
        R_ScriptRunner.run_r_script_s3_upload("AA_CMSY++.R", request.simulation_id)

        return workflow_service_pb2.InitialiseResponse(
            simulation_id=request.simulation_id
        )

    def SimulateStep(self, request, context):
        trace.get_current_span().set_attribute("simulation_id", request.simulation_id)
        if request.simulation_id not in self.simulation_dictionary:
            log_and_abort(context, grpc.StatusCode.INVALID_ARGUMENT, f"Simulation Id {request.simulation_id} not known.")

        sim = self.simulation_dictionary[request.simulation_id]

        if sim.step_size != "P1M":
            log_and_abort(context, grpc.StatusCode.INVALID_ARGUMENT, f"Error in simulation {request.simulation_id}: Only monthly steps are supported. Please set the step size to P1M.")

        print(f"SimulateStep for simulation {request.simulation_id}")

        current_year = sim.current_date_time.year
        sim.current_date_time += relativedelta(months=1)

        if current_year != sim.current_date_time.year:
            print(f"Year {current_year} is complete. Processing catch data.")

            catch_file_path = Path(__file__).parent.parent.resolve() / "simulations" / request.simulation_id / "catch_file.csv"

            if not sim.aggregated_catch_dictionary:
                print("⚠️ No aggregated catch data found. Writing NA entries to catch_file.csv")
                id_file_path = Path(__file__).parent.parent / "simulations" / request.simulation_id / "id_file.csv"
                try:
                    import csv
                    stock_names = []
                    with open(id_file_path, newline='') as idfile:
                        reader = csv.DictReader(idfile)
                        for row in reader:
                            stock = row.get("Stock")
                            if stock and stock.strip():
                                clean = stock.strip()
                                print(f"📋 Adding stock row: '{clean}'")
                                stock_names.append(clean)
                    with open(catch_file_path, mode='a', newline='') as csvfile:
                        import os
                        writer = csv.writer(csvfile)
                        count = 0
                        for stock_name in stock_names:
                            print(f"📝 Writing: [{stock_name}, {current_year}, NA, NA]")
                            writer.writerow([stock_name, current_year, "NA", "NA"])
                            count += 1
                        csvfile.flush()
                        os.fsync(csvfile.fileno())
                        print(f"✅ Wrote {count} NA rows to {catch_file_path}")
                except Exception as e:
                    print(f"❌ Failed to write NA entries to catch_file.csv: {e}")
                return workflow_service_pb2.SimulateStepResponse(
                    simulation_id=request.simulation_id
                )

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
            sim.last_written_stock_names = []
            sim.last_written_year = current_year

            with open(catch_file_path, mode='a', newline='') as csvfile:
                writer = csv.writer(csvfile)
                for common_name, divisions in catch_file.items():
                    for division, catch_value in divisions.items():
                        stock_label = f"{common_name} - {division}"
                        row = [stock_label, current_year, round(catch_value, 2), "NA"]
                        writer.writerow(row)
                        sim.last_written_stock_names.append(stock_label)

                        # ✅ PRINT ONLY NON-ZERO CATCHES TO TERMINAL
                        if catch_value > 0:
                            print(f"✅ {stock_label}: {round(catch_value, 2)} kg in {current_year}")

            sim.aggregated_catch_dictionary.clear()
            sim.aggregated_biomass.clear()

            id_file_path = Path(__file__).parent.parent / "simulations" / request.simulation_id / "id_file.csv"
            try:
                with open(id_file_path, newline='') as idfile:
                    reader = csv.DictReader(idfile)
                    all_stocks = set(row.get("Stock", "").strip() for row in reader if row.get("Stock"))
                written_stocks = set(sim.last_written_stock_names)
                missing_stocks = all_stocks - written_stocks
                if missing_stocks:
                    print(f"➕ Appending NA rows for {len(missing_stocks)} stocks not written yet")
                    with open(catch_file_path, mode='a', newline='') as csvfile:
                        import os
                        writer = csv.writer(csvfile)
                        for stock_name in missing_stocks:
                            writer.writerow([stock_name, current_year, "NA", "NA"])
                        csvfile.flush()
                        os.fsync(csvfile.fileno())
                        print(f"✅ Appended {len(missing_stocks)} NA rows to {catch_file_path}")
            except Exception as e:
                print(f"❌ Failed to append missing NA rows: {e}")

        return workflow_service_pb2.SimulateStepResponse(
            simulation_id=request.simulation_id
        )

    def Finalise(self, request, context):
        trace.get_current_span().set_attribute("simulation_id", request.simulation_id)
        if request.simulation_id not in self.simulation_dictionary:
            log_and_abort(context, grpc.StatusCode.INVALID_ARGUMENT, f"Simulation Id {request.simulation_id} not known.")

        print(f"Finalise for simulation {request.simulation_id}")

        print(f"Create Stock Assessment for simulation {request.simulation_id} ")
        R_ScriptRunner.run_r_script_s3_upload("AA_CMSY++.R", request.simulation_id)

        sim = self.simulation_dictionary[request.simulation_id]

        if hasattr(sim, "last_written_stock_names") and hasattr(sim, "last_written_year"):
            self._update_id_file(
                request.simulation_id,
                sim.last_written_stock_names,
                sim.last_written_year
            )
            print(f"✅ Finalise: id_file.csv updated for simulation {request.simulation_id}")
        else:
            print(f"⚠️ Finalise: No stock data found to update id_file.csv for {request.simulation_id}")

        return workflow_service_pb2.FinaliseResponse(
            simulation_id=request.simulation_id
        )

    def Cancel(self, request, context):
        trace.get_current_span().set_attribute("simulation_id", request.simulation_id)
        if request.simulation_id not in self.simulation_dictionary:
            log_and_abort(context, grpc.StatusCode.INVALID_ARGUMENT, f"Simulation Id {request.simulation_id} not known.")

        print(f"Cancel for simulation {request.simulation_id}")

        return workflow_service_pb2.CancelResponse(
            simulation_id=request.simulation_id
        )

    def _update_id_file(self, simulation_id: str, stocks: list[str], year: int):
        import csv

        id_file_path = Path(__file__).parent.parent / "simulations" / simulation_id / "id_file.csv"

        if not id_file_path.exists():
            print(f"id_file.csv not found for simulation {simulation_id}")
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
