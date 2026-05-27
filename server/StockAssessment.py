from dateutil.relativedelta import relativedelta
import grpc
from server.s3_storage import S3_Storage
from server.Simulation import Simulation
from surimi.v1 import stock_assessment_service_pb2_grpc, get_stock_assessment_pb2, stock_assessment_pb2, species_pb2, initialise_experiment_pb2, finalise_experiment_pb2, experiment_step_pb2, finalise_experiment_pb2, cancel_experiment_pb2, update_biomass_statistics_pb2, update_catch_disposition_statistics_pb2, get_protocol_version_pb2
from pathlib import Path
import shutil
from server.division_lookup import get_division
from server.species_lookup import get_common_name

from server.common_functions import log_and_abort
from server.r_scriptrunner import R_ScriptRunner

class StockAssessmentService(stock_assessment_service_pb2_grpc.StockAssessmentServiceServicer):
    def __init__(self, experiment_dictionary: dict[str, Simulation], version: str):
        self.experiment_dictionary = experiment_dictionary  # Will hold the current simulation instance
        self.version = version  # Store the version

    def InitialiseExperiment(self, request: initialise_experiment_pb2.InitialiseExperimentRequest, context):
        print("InitialiseRequest fields:", [f.name for f in request.DESCRIPTOR.fields])
        print("[OK] CONTRACT FILTERING ENABLED (WORKFLOW_SERVICE.PY UPDATED)")

        if request.experiment_id in self.experiment_dictionary.keys():
            log_and_abort(context, grpc.StatusCode.INVALID_ARGUMENT, f"Experiment Id {request.experiment_id} already exists.")

        if request.simulation.time_step != "P1M":
            log_and_abort(
                context,
                grpc.StatusCode.INVALID_ARGUMENT,
                f"Error in experiment {request.experiment_id}: Only monthly steps are supported. Please set the step size to P1M."
            )

        simulation = Simulation(
            start_date_time=request.simulation.start_date_time.ToDatetime().replace(tzinfo=None),
            step_size=request.simulation.time_step,
        )
        print(
            f"Init experiment {request.experiment_id} for scenario {request.scenario_name} "
            f"with start date {request.simulation.start_date_time} and step size {request.simulation.time_step}"
        )

        S3_Storage.DownloadFilesFromS3("surimi-cmsy/config", "R_files")

        output_directory = Path(__file__).parent.parent.resolve() / Path("experiments") / request.experiment_id
        try:
            output_directory.mkdir(parents=True, exist_ok=True)
            print(f"Created experiment directory: {output_directory}")
        except FileExistsError:
            log_and_abort(context, grpc.StatusCode.ALREADY_EXISTS, f"Directory already exists: {output_directory}")
        except Exception as e:
            log_and_abort(context, grpc.StatusCode.INTERNAL, f"Directory creation failed: {str(e)}")

        src_dir = Path(__file__).parent.parent.resolve() / Path("R_files")
        print(f"Copying files from {src_dir} to {output_directory}")
        shutil.copy(src_dir / "catch_file.csv", output_directory / "catch_file.csv")
        shutil.copy(src_dir / "catch_file_original.csv", output_directory / "catch_file_original.csv")
        shutil.copy(src_dir / "id_file.csv", output_directory / "id_file.csv")
        shutil.copy(src_dir / "AA_CMSY++.R", output_directory / "AA_CMSY++.R")
        shutil.copy(src_dir / "ffnn.bin", output_directory / "ffnn.bin")

        # =============================
        # CONTRACT SPECIES FILTERING (RUN ONLY CONTRACT SPECIES; THROW EVERYTHING ELSE)
        # - CONTRACT SPECIES COME FROM INIT MESSAGE: request.simulation.items.species[*].species_code
        # - KEEP ONLY CONTRACT SPECIES IN catch_file.csv, catch_file_original.csv AND id_file.csv
        # - IF CONTRACT SPECIES ARE MISSING FROM FILES: CONTINUE (PRINT WARNING)
        # =============================
        import csv

        contract_codes = {
            s.species_code.strip()
            for s in request.simulation.items.species
            if getattr(s, "species_code", "").strip()
        }

        if not contract_codes:
            log_and_abort(
                context,
                grpc.StatusCode.INVALID_ARGUMENT,
                "Initialise request contains no species codes in simulation.items.species."
            )

        catch_file_path = output_directory / "catch_file.csv"
        catch_file_original_path = output_directory / "catch_file_original.csv"
        id_file_path = output_directory / "id_file.csv"

        print(f"[OK] Contract species ({len(contract_codes)}): {', '.join(sorted(contract_codes))}")

        # ---- FILTER id_file.csv (Stock column is FAO 3-alpha)
        with open(id_file_path, newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            if not reader.fieldnames or "Stock" not in reader.fieldnames:
                log_and_abort(
                    context,
                    grpc.StatusCode.INVALID_ARGUMENT,
                    f"id_file.csv must contain a 'Stock' column. Found columns: {reader.fieldnames}"
                )
            id_rows = list(reader)
            id_fieldnames = reader.fieldnames

        id_filtered_rows = []
        present_id = set()
        for r in id_rows:
            stock = (r.get("Stock") or "").strip()
            if stock in contract_codes:
                id_filtered_rows.append(r)
                present_id.add(stock)

        removed_id = len(id_rows) - len(id_filtered_rows)

        with open(id_file_path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=id_fieldnames)
            writer.writeheader()
            writer.writerows(id_filtered_rows)

        print(f"[CLEAN] id_file.csv filtered to contract species (removed {removed_id} non-contract stocks).")

        # IMPORTANT:
        # DO NOT FORCE btype TO CPUE HERE.
        # THE FIRST HISTORICAL ASSESSMENT MUST RUN WITH THE ORIGINAL FILTERED btype VALUES.

        # ---- FILTER catch_file.csv (working file for assessment)
        with open(catch_file_path, newline="", encoding="utf-8-sig") as f:
            all_catch_rows = [row for row in csv.reader(f) if row]

        filtered_catch_rows = []
        present_catch = set()

        original_data_rows = 0
        kept_data_rows = 0

        for row in all_catch_rows:
            stock = (row[0] or "").strip()

            if stock.lower() == "stock":  # header
                filtered_catch_rows.append(row)
                continue

            original_data_rows += 1

            if stock in contract_codes:
                filtered_catch_rows.append(row)
                present_catch.add(stock)
                kept_data_rows += 1

        removed_catch = original_data_rows - kept_data_rows

        with open(catch_file_path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerows(filtered_catch_rows)

        print(f"[CLEAN] catch_file.csv filtered to contract species (removed {removed_catch} non-contract rows).")

        # ---- FILTER catch_file_original.csv (full real time series kept for comparison)
        with open(catch_file_original_path, newline="", encoding="utf-8-sig") as f:
            all_original_rows = [row for row in csv.reader(f) if row]

        filtered_original_rows = []
        present_original = set()

        original_real_data_rows = 0
        kept_real_data_rows = 0

        for row in all_original_rows:
            stock = (row[0] or "").strip()

            if stock.lower() == "stock":  # header
                filtered_original_rows.append(row)
                continue

            original_real_data_rows += 1

            if stock in contract_codes:
                filtered_original_rows.append(row)
                present_original.add(stock)
                kept_real_data_rows += 1

        removed_original = original_real_data_rows - kept_real_data_rows

        with open(catch_file_original_path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerows(filtered_original_rows)

        print(f"[CLEAN] catch_file_original.csv filtered to contract species (removed {removed_original} non-contract rows).")

        # ---- WARN ABOUT MISSING CONTRACT SPECIES (DO NOT ABORT)
        missing_in_id = sorted(contract_codes - present_id)
        missing_in_catch = sorted(contract_codes - present_catch)
        missing_in_original = sorted(contract_codes - present_original)

        if missing_in_id:
            print(f"[WARNING] Contract species missing from id_file.csv (continuing): {', '.join(missing_in_id)}")
        if missing_in_catch:
            print(f"[WARNING] Contract species missing from catch_file.csv (continuing): {', '.join(missing_in_catch)}")
        if missing_in_original:
            print(f"[WARNING] Contract species missing from catch_file_original.csv (continuing): {', '.join(missing_in_original)}")

        # NOTE: The effective species that will run (present in BOTH working files)
        effective_species = sorted((present_id & present_catch) & contract_codes)
        print(f"[OK] Effective species to run (present in both files): {len(effective_species)}")

        # OPTIONAL: quick sanity peek (first few stocks)
        try:
            with open(id_file_path, newline="", encoding="utf-8-sig") as f:
                rdr = csv.DictReader(f)
                preview = [row["Stock"] for _, row in zip(range(10), rdr)]
            print(f"DEBUG: First id_file stocks: {preview}")
        except Exception as e:
            print(f"DEBUG: Could not preview id_file.csv: {e}")

        self.experiment_dictionary[request.experiment_id] = simulation

        print(f"Create Stock Assessment for experiment {request.experiment_id} ")

        # === FIRST CMSY RUN (HISTORICAL) ===
        R_ScriptRunner.run_r_script_s3_upload("AA_CMSY++.R", request.experiment_id)

        # === RENAME FIRST-RUN OUTPUTS LOCALLY TO _historical ===
        # NOTE: THIS DOES NOT YET CHANGE S3 FILENAMES
        self._rename_outputs_historical(request.experiment_id)

        # === NEW CHANGE ===
        # RENAME THE ORIGINAL HISTORICAL catch_file.csv
        self._rename_first_catch_file_historical(request.experiment_id)

        # === NEW CHANGE ===
        # KEEP A HISTORICAL COPY OF id_file.csv FOR PHASE 1 TRACEABILITY
        # NOTE: WE COPY INSTEAD OF RENAMING, BECAUSE PHASE 2 STILL NEEDS id_file.csv
        self._create_historical_id_file_copy(request.experiment_id)

        # === NEW CHANGE ===
        # UPDATE THE WORKING id_file.csv FOR PHASE 2 USING THE HISTORICAL OUTPUT
        # lcl.last.B_Bmsy / 2 -> stb.low
        # ucl.last.B_Bmsy / 2 -> stb.hi
        self._update_id_file_stb_from_historical_output(request.experiment_id)

        # === IMPORTANT FIX ===
        # FORCE btype TO CPUE ONLY AFTER THE HISTORICAL RUN
        self._force_btype_cpue(request.experiment_id)

        # === NEW CHANGE ===
        # CREATE A FRESH catch_file.csv FOR SIMULATED DATA ONLY
        self._create_empty_catch_file_for_experiment(request.experiment_id)

        return initialise_experiment_pb2.InitialiseExperimentResponse(
            experiment_id=request.experiment_id
        )

    def ExperimentStep(self, request: experiment_step_pb2.ExperimentStepRequest, context):
        if request.experiment_id not in self.experiment_dictionary:
            log_and_abort(context, grpc.StatusCode.INVALID_ARGUMENT, f"Experiment Id {request.experiment_id} not known.")

        sim = self.experiment_dictionary[request.experiment_id]

        if sim.step_size != "P1M":
            log_and_abort(context, grpc.StatusCode.INVALID_ARGUMENT, f"Error in experiment {request.experiment_id}: Only monthly steps are supported. Please set the step size to P1M.")

        print(f"SimulateStep for experiment {request.experiment_id} and date {sim.current_date_time}")

        current_year = sim.current_date_time.year
        sim.current_date_time += relativedelta(months=1)

        if current_year != sim.current_date_time.year:
            print(f"Year {current_year} is complete. Processing catch data.")

            catch_file_path = Path(__file__).parent.parent.resolve() / "experiments" / request.experiment_id / "catch_file.csv"

            if not sim.aggregated_catch_dictionary:
                print("[WARNING] No aggregated catch data found. Writing NA entries to catch_file.csv")
                id_file_path = Path(__file__).parent.parent / "experiments" / request.experiment_id / "id_file.csv"
                try:
                    import csv
                    stock_names = []
                    with open(id_file_path, newline='') as idfile:
                        reader = csv.DictReader(idfile)
                        for row in reader:
                            stock = row.get("Stock")
                            if stock and stock.strip():
                                clean = stock.strip()
                                print(f"[NOTE] Adding stock row: '{clean}'")
                                stock_names.append(clean)

                    # === NEW CHANGE ===
                    # STORE METADATA EVEN IN THE NA BRANCH SO FINALISE CAN UPDATE id_file.csv
                    sim.last_written_year = current_year
                    sim.last_written_stock_names = stock_names.copy()

                    with open(catch_file_path, mode='a', newline='') as csvfile:
                        import os
                        writer = csv.writer(csvfile)
                        count = 0
                        for stock_name in stock_names:
                            print(f"[NOTE] Writing: [{stock_name}, {current_year}, NA, NA]")
                            writer.writerow([stock_name, current_year, "NA", "NA"])
                            count += 1
                        csvfile.flush()
                        os.fsync(csvfile.fileno())
                        print(f"[OK] Wrote {count} NA rows to {catch_file_path}")
                except Exception as e:
                    print(f"[ERROR] Failed to write NA entries to catch_file.csv: {e}")
                return experiment_step_pb2.ExperimentStepResponse(
                    experiment_id=request.experiment_id
                )

            catch_file = {}
            for species_code, cell_catches in sim.aggregated_catch_dictionary.items():
                for cell_key, catch_value in cell_catches.items():
                    division = get_division(cell_key[0], cell_key[1])
                    common_name = get_common_name(species_code)

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

                        if catch_value > 0:
                            print(f"[OK] {stock_label}: {round(catch_value, 2)} kg in {current_year}")

            sim.aggregated_catch_dictionary.clear()
            sim.aggregated_biomass.clear()

            id_file_path = Path(__file__).parent.parent / "experiments" / request.experiment_id / "id_file.csv"
            try:
                with open(id_file_path, newline='') as idfile:
                    reader = csv.DictReader(idfile)
                    all_stocks = set(row.get("Stock", "").strip() for row in reader if row.get("Stock"))
                written_stocks = set(sim.last_written_stock_names)
                missing_stocks = all_stocks - written_stocks
                if missing_stocks:
                    print(f"[ADD] Appending NA rows for {len(missing_stocks)} stocks not written yet")
                    with open(catch_file_path, mode='a', newline='') as csvfile:
                        import os
                        writer = csv.writer(csvfile)
                        for stock_name in missing_stocks:
                            writer.writerow([stock_name, current_year, "NA", "NA"])
                        csvfile.flush()
                        os.fsync(csvfile.fileno())
                        print(f"[OK] Appended {len(missing_stocks)} NA rows to {catch_file_path}")
            except Exception as e:
                print(f"[ERROR] Failed to append missing NA rows: {e}")

        return experiment_step_pb2.ExperimentStepResponse(
            experiment_id=request.experiment_id
        )

    def FinaliseExperiment(self, request: finalise_experiment_pb2.FinaliseExperimentRequest, context):
        if request.experiment_id not in self.experiment_dictionary:
            log_and_abort(context, grpc.StatusCode.INVALID_ARGUMENT, f"Experiment Id {request.experiment_id} not known.")

        print(f"Finalise for experiment {request.experiment_id}")

        sim = self.experiment_dictionary[request.experiment_id]

        if sim.last_written_year is not None and sim.last_written_stock_names is not None:
            self._update_id_file(
                request.experiment_id,
                sim.last_written_stock_names,
                sim.last_written_year
            )
            print(f"[OK] Finalise: id_file.csv updated for experiment {request.experiment_id}")
        else:
            print(f"[WARNING] Finalise: No stock data found to update id_file.csv for experiment {request.experiment_id}")

        # === NEW CHANGE ===
        # CREATE DETAILED YEAR-BY-YEAR CATCH COMPARISON
        # USING FULL OVERLAPPING PERIOD PER STOCK
        self._create_catch_comparison_detailed(request.experiment_id)

        print(f"Create Stock Assessment for experiment {request.experiment_id} ")
        R_ScriptRunner.run_r_script_s3_upload("AA_CMSY++.R", request.experiment_id)

        return finalise_experiment_pb2.FinaliseExperimentResponse(
            experiment_id=request.experiment_id
        )

    def CancelExperiment(self, request: cancel_experiment_pb2.CancelExperimentRequest, context):
        if request.experiment_id not in self.experiment_dictionary:
            log_and_abort(context, grpc.StatusCode.INVALID_ARGUMENT, f"Experiment Id {request.experiment_id} not known.")

        print(f"Cancel for experiment {request.experiment_id}")

        return cancel_experiment_pb2.CancelExperimentResponse(
            experiment_id=request.experiment_id
        )

    def UpdateBiomassStatistics(self, request : update_biomass_statistics_pb2.UpdateBiomassStatisticsRequest, context):
        if request.experiment_id not in self.experiment_dictionary:
            log_and_abort(context, grpc.StatusCode.INVALID_ARGUMENT, f"Experiment Id {request.experiment_id} not known.")

        print(f"Update biomass for experiment {request.experiment_id}")
        # print(request)  # for debugging purposes

        sim = self.experiment_dictionary[request.experiment_id]

        # Loop over every grid in biomass_grids
        for grid in request.biomass_statistics_summary.biomass_grids_statistics:
            # Check if the species is already in the aggregated_biomass
            if grid.species.species_code not in sim.aggregated_biomass:
                sim.aggregated_biomass[grid.species.species_code] = {}

            # Loop over every cell in the grid
            for cell in grid.biomass_cells_statistics:
                cell_key = (cell.latitude, cell.longitude)
                # Check if the cell is already in the aggregated_biomass for the species   
                if cell_key not in sim.aggregated_biomass[grid.species.species_code]:
                    sim.aggregated_biomass[grid.species.species_code][cell_key] = 0.0
                # Add the biomass of the cell to the aggregated_biomass for the species  
                sim.aggregated_biomass[grid.species.species_code][cell_key] += cell.biomass.mean

        return update_biomass_statistics_pb2.UpdateBiomassStatisticsResponse(
            experiment_id=request.experiment_id
        )

    def UpdateCatchDispositionStatistics(self, request : update_catch_disposition_statistics_pb2.UpdateCatchDispositionStatisticsRequest, context):
        if not request.experiment_id in self.experiment_dictionary.keys():
            log_and_abort(context, grpc.StatusCode.INVALID_ARGUMENT, f"Experiment Id {request.experiment_id} not known.")

        print(f"Update CatchDisposition for experiment {request.experiment_id} ")
# Aggregate the catch data
# Check if the year is complete
# if so, add the catch of the species to the csv file
        # print(request)  # for debugging purposes

        sim = self.experiment_dictionary[request.experiment_id]

        # Loop over every grid in Disposition_grids
        for grid in request.catch_disposition_statistics_summary.disposition_grids_statistics:
            # Check if the species is already in the aggregated_catch_dictionary
            if grid.species.species_code not in sim.aggregated_catch_dictionary:
                sim.aggregated_catch_dictionary[grid.species.species_code] = {}

            # Loop over every cell in the grid
            for cell in grid.disposition_cells_statistics:
                cell_key = (cell.latitude, cell.longitude)
                # Check if the cell is already in the aggregated_catch_dictionary for the species   
                if cell_key not in sim.aggregated_catch_dictionary[grid.species.species_code]:
                    sim.aggregated_catch_dictionary[grid.species.species_code][cell_key] = 0.0
                
                # Add the catch of the cell to the aggregated_catch_dictionary for the species  
                sim.aggregated_catch_dictionary[grid.species.species_code][cell_key] += cell.gross_catch.mean                    

        return update_catch_disposition_statistics_pb2.UpdateCatchDispositionStatisticsResponse(
            experiment_id=request.experiment_id
        )

    def GetProtocolVersion(self, request: get_protocol_version_pb2.GetProtocolVersionRequest, context: grpc.ServicerContext):
        return get_protocol_version_pb2.GetProtocolVersionResponse(
            protocol_version=self.version
        )

    def GetStockAssessment(self, request: get_stock_assessment_pb2.GetStockAssessmentRequest, context: grpc.ServicerContext):
        if request.experiment_id not in self.experiment_dictionary:
            log_and_abort(context, grpc.StatusCode.INVALID_ARGUMENT, f"Experiment Id {request.experiment_id} not known.")

        print(f"GetStockAssessment for experiment {request.experiment_id}")

        # TODO: read the output csv file (West_Med_id_file_output.csv) and build a real response
        # Hardcoded dummy response for PIL, ANK, BOG
        summary = stock_assessment_pb2.StockAssessmentSummary(
            species_stock_assessments=[
                stock_assessment_pb2.SpeciesStockAssessment(
                    species=species_pb2.Species(species_code="PIL"),
                    stock_assessments=[
                        stock_assessment_pb2.StockAssessment(year=2013, exploitation=0.5, stock_status=0.8),
                        stock_assessment_pb2.StockAssessment(year=2014, exploitation=0.6, stock_status=0.7)
                    ]
                ),
                stock_assessment_pb2.SpeciesStockAssessment(
                    species=species_pb2.Species(species_code="ANK"),
                    stock_assessments=[
                        stock_assessment_pb2.StockAssessment(year=2013, exploitation=0.4, stock_status=0.75),
                        stock_assessment_pb2.StockAssessment(year=2014, exploitation=0.45, stock_status=0.72)
                    ]
                ),
                stock_assessment_pb2.SpeciesStockAssessment(
                    species=species_pb2.Species(species_code="BOG"),
                    stock_assessments=[
                        stock_assessment_pb2.StockAssessment(year=2013, exploitation=0.6, stock_status=0.65),
                        stock_assessment_pb2.StockAssessment(year=2014, exploitation=0.65, stock_status=0.6)
                    ]
                ),
            ]
        )

        return get_stock_assessment_pb2.GetStockAssessmentResponse(
            experiment_id=request.experiment_id,
            stock_assessment_summary=summary
        )

    def _update_id_file(self, experiment_id: str, stocks: list[str], year: int):
        import csv

        id_file_path = Path(__file__).parent.parent / "experiments" / experiment_id / "id_file.csv"

        if not id_file_path.exists():
            print(f"id_file.csv not found for experiment {experiment_id}")
            return

        # === NEW CHANGE ===
        # DETERMINE THE FIRST SIMULATED YEAR FROM catch_file.csv
        catch_file_path = Path(__file__).parent.parent / "experiments" / experiment_id / "catch_file.csv"
        sim_start_year = None

        try:
            with open(catch_file_path, newline='') as csvfile:
                reader = csv.DictReader(csvfile)
                years = []
                for row in reader:
                    year_value = row.get("yr")
                    if year_value and str(year_value).isdigit():
                        years.append(int(year_value))

                if years:
                    sim_start_year = min(years)
        except Exception as e:
            print(f"[WARNING] Could not determine experiment start year from catch_file.csv for experiment {experiment_id}: {e}")

        if sim_start_year is None:
            print(f"[WARNING] Could not determine experiment start year for experiment {experiment_id}. Falling back to final year {year}")
            sim_start_year = year

        with open(id_file_path, newline='') as csvfile:
            reader = list(csv.DictReader(csvfile))
            fieldnames = reader[0].keys() if reader else []

        updated_rows = []
        for row in reader:
            if row.get("Stock") in stocks:
                # === NEW CHANGE ===
                # SET THE FULL EXPERIMENT YEAR WINDOW
                row["MinOfYear"] = str(sim_start_year)
                row["StartYear"] = str(sim_start_year)
                row["MaxOfYear"] = str(year)
                row["EndYear"] = str(year)
            updated_rows.append(row)

        with open(id_file_path, mode='w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(updated_rows)

        print(f"[OK] id_file.csv updated with experiment years {sim_start_year}-{year} for stocks: {stocks}")

    # === NEW HELPER METHOD ===
    # THIS FORCES btype TO CPUE FOR ALL ROWS IN THE WORKING id_file.csv
    def _force_btype_cpue(self, experiment_id: str):
        import csv

        id_file_path = Path(__file__).parent.parent / "experiments" / experiment_id / "id_file.csv"

        if not id_file_path.exists():
            print(f"[WARNING] id_file.csv not found for experiment {experiment_id}")
            return

        with open(id_file_path, newline='', encoding='utf-8-sig') as csvfile:
            rows = list(csv.DictReader(csvfile))
            fieldnames = rows[0].keys() if rows else []

        if not fieldnames:
            print(f"[WARNING] id_file.csv is empty for experiment {experiment_id}")
            return

        if "btype" not in fieldnames:
            print(f"[WARNING] id_file.csv has no 'btype' column for experiment {experiment_id}")
            return

        updated_count = 0
        for row in rows:
            row["btype"] = "CPUE"
            updated_count += 1

        with open(id_file_path, mode='w', newline='', encoding='utf-8-sig') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

        print(f"[OK] Forced btype='CPUE' for {updated_count} rows in id_file.csv")

    # === NEW HELPER METHOD ===
    # THIS UPDATES THE WORKING id_file.csv FOR PHASE 2
    # USING THE HISTORICAL ASSESSMENT OUTPUT:
    # lcl.last.B_Bmsy / 2 -> stb.low
    # ucl.last.B_Bmsy / 2 -> stb.hi
    def _update_id_file_stb_from_historical_output(self, experiment_id: str):
        import csv

        experiment_dir = Path(__file__).parent.parent / "experiments" / experiment_id
        id_file_path = experiment_dir / "id_file.csv"

        if not id_file_path.exists():
            print(f"[WARNING] id_file.csv not found for experiment {experiment_id}")
            return

        # === FIND THE HISTORICAL OUTPUT CSV PRODUCED BY THE FIRST ASSESSMENT ===
        candidate_files = sorted(experiment_dir.glob("*id_file_output_historical.csv"))

        if not candidate_files:
            print(f"[WARNING] No historical id_file output found in {experiment_dir}")
            return

        historical_output_path = candidate_files[0]
        print(f"[OK] Using historical assessment output: {historical_output_path.name}")

        # === READ THE HISTORICAL OUTPUT ===
        with open(historical_output_path, newline='', encoding='utf-8-sig') as csvfile:
            hist_reader = csv.DictReader(csvfile)

            if not hist_reader.fieldnames:
                print(f"[WARNING] Historical output file has no header: {historical_output_path}")
                return

            required_hist_columns = {"Stock", "lcl.last.B_Bmsy", "ucl.last.B_Bmsy"}
            missing_hist_columns = required_hist_columns - set(hist_reader.fieldnames)

            if missing_hist_columns:
                print(
                    f"[WARNING] Historical output missing required columns: {', '.join(sorted(missing_hist_columns))}. "
                    f"Found columns: {hist_reader.fieldnames}"
                )
                return

            historical_map = {}
            for row in hist_reader:
                stock = (row.get("Stock") or "").strip()
                if not stock:
                    continue

                lcl_val = row.get("lcl.last.B_Bmsy", "")
                ucl_val = row.get("ucl.last.B_Bmsy", "")

                try:
                    lcl_float = float(lcl_val)
                    ucl_float = float(ucl_val)

                    # === NEW CHANGE ===
                    # CONVERT B/Bmsy TO B/k USING SCHAEFER: B/Bmsy = 2 * (B/k)
                    stb_low = lcl_float * 0.5
                    stb_hi = ucl_float * 0.5

                    # KEEP VALUES IN VALID B/k RANGE
                    if stb_low <= 0 or stb_hi <= 0:
                        print(f"[WARNING] Invalid converted stb values for {stock}: {stb_low}, {stb_hi}. Skipping.")
                        continue

                    if stb_low >= stb_hi:
                        print(f"[WARNING] Converted stb.low >= stb.hi for {stock}: {stb_low}, {stb_hi}. Skipping.")
                        continue

                    if stb_hi > 1:
                        print(f"[WARNING] Converted stb.hi > 1 for {stock}: {stb_hi}. Clamping to 1.0")
                        stb_hi = 1.0

                    if stb_low >= stb_hi:
                        print(f"[WARNING] Converted and clamped stb.low >= stb.hi for {stock}: {stb_low}, {stb_hi}. Skipping.")
                        continue

                    historical_map[stock] = {
                        "stb.low": str(stb_low),
                        "stb.hi": str(stb_hi),
                    }

                except (TypeError, ValueError):
                    print(f"[WARNING] Could not convert historical B/Bmsy values for {stock}: {lcl_val}, {ucl_val}")

        if not historical_map:
            print(f"[WARNING] No valid stock values found in historical output: {historical_output_path.name}")
            return

        # === READ THE WORKING id_file.csv ===
        with open(id_file_path, newline='', encoding='utf-8-sig') as csvfile:
            id_rows = list(csv.DictReader(csvfile))
            fieldnames = id_rows[0].keys() if id_rows else []

        if not fieldnames:
            print(f"[WARNING] id_file.csv is empty for experiment {experiment_id}")
            return

        required_id_columns = {"Stock", "stb.low", "stb.hi"}
        missing_id_columns = required_id_columns - set(fieldnames)

        if missing_id_columns:
            print(
                f"[WARNING] id_file.csv missing required columns: {', '.join(sorted(missing_id_columns))}. "
                f"Found columns: {list(fieldnames)}"
            )
            return

        updated_count = 0
        missing_stock_count = 0

        for row in id_rows:
            stock = (row.get("Stock") or "").strip()

            if stock in historical_map:
                row["stb.low"] = historical_map[stock]["stb.low"]
                row["stb.hi"] = historical_map[stock]["stb.hi"]
                updated_count += 1
            else:
                missing_stock_count += 1
                print(f"[WARNING] Stock not found in historical output, stb.low/stb.hi unchanged: {stock}")

        # === WRITE BACK THE UPDATED WORKING id_file.csv ===
        with open(id_file_path, mode='w', newline='', encoding='utf-8-sig') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(id_rows)

        print(
            f"[OK] Updated stb.low/stb.hi in id_file.csv from historical output for {updated_count} stocks. "
            f"Unmatched stocks: {missing_stock_count}"
        )

    # === NEW HELPER METHOD ===
    # THIS CREATES A DETAILED YEAR-BY-YEAR COMPARISON FILE
    # BETWEEN SIMULATED AND REAL CATCH (ct) AND BIOMASS (bt)
    # USING THE FULL OVERLAPPING PERIOD PER STOCK
    def _create_catch_comparison_detailed(self, experiment_id: str):
        import csv

        experiment_dir = Path(__file__).parent.parent / "experiments" / experiment_id
        simulated_path = experiment_dir / "catch_file.csv"
        original_path = experiment_dir / "catch_file_original.csv"
        comparison_path = experiment_dir / "catch_comparison_detailed.csv"

        if not simulated_path.exists():
            print(f"[WARNING] Simulated catch file not found: {simulated_path}")
            return

        if not original_path.exists():
            print(f"[WARNING] Original catch file not found: {original_path}")
            return

        try:
            with open(simulated_path, newline='', encoding='utf-8-sig') as csvfile:
                simulated_rows = list(csv.DictReader(csvfile))

            with open(original_path, newline='', encoding='utf-8-sig') as csvfile:
                original_rows = list(csv.DictReader(csvfile))
        except Exception as e:
            print(f"[ERROR] Failed to read catch files for comparison: {e}")
            return

        if not simulated_rows:
            print(f"[WARNING] Simulated catch file is empty: {simulated_path}")
            return

        if not original_rows:
            print(f"[WARNING] Original catch file is empty: {original_path}")
            return

        def parse_float_or_none(value):
            if value is None:
                return None
            value_str = str(value).strip()
            if value_str == "" or value_str.upper() == "NA":
                return None
            try:
                return float(value_str)
            except (TypeError, ValueError):
                return None

        sim_by_stock = {}
        real_by_stock = {}

        for row in simulated_rows:
            stock = (row.get("Stock") or "").strip()
            year_value = row.get("yr")

            if not stock or year_value is None:
                continue

            try:
                year_int = int(year_value)
            except (TypeError, ValueError):
                continue

            ct = parse_float_or_none(row.get("ct"))
            bt = parse_float_or_none(row.get("bt"))

            if stock not in sim_by_stock:
                sim_by_stock[stock] = {}

            sim_by_stock[stock][year_int] = {
                "ct": ct,
                "bt": bt,
            }

        for row in original_rows:
            stock = (row.get("Stock") or "").strip()
            year_value = row.get("yr")

            if not stock or year_value is None:
                continue

            try:
                year_int = int(year_value)
            except (TypeError, ValueError):
                continue

            ct = parse_float_or_none(row.get("ct"))
            bt = parse_float_or_none(row.get("bt"))

            if stock not in real_by_stock:
                real_by_stock[stock] = {}

            real_by_stock[stock][year_int] = {
                "ct": ct,
                "bt": bt,
            }

        all_stocks = sorted(set(sim_by_stock.keys()) & set(real_by_stock.keys()))

        if not all_stocks:
            print(f"[WARNING] No overlapping stocks found between simulated and original catch files for experiment {experiment_id}")
            return

        comparison_rows = []

        for stock in all_stocks:
            sim_years = sorted(sim_by_stock[stock].keys())
            real_years = sorted(real_by_stock[stock].keys())

            if not sim_years or not real_years:
                continue

            overlap_start = max(min(sim_years), min(real_years))
            overlap_end = min(max(sim_years), max(real_years))

            if overlap_start > overlap_end:
                print(f"[WARNING] No overlapping years for stock {stock}")
                continue

            matched_years = 0

            for year in range(overlap_start, overlap_end + 1):
                if year not in sim_by_stock[stock]:
                    continue
                if year not in real_by_stock[stock]:
                    continue

                sim_ct = sim_by_stock[stock][year]["ct"]
                sim_bt = sim_by_stock[stock][year]["bt"]

                real_ct = real_by_stock[stock][year]["ct"]
                real_bt = real_by_stock[stock][year]["bt"]

                if sim_ct is not None and real_ct is not None:
                    diff_ct = sim_ct - real_ct
                    abs_diff_ct = abs(diff_ct)
                    pct_diff_ct = (diff_ct / real_ct * 100.0) if real_ct != 0 else ""
                else:
                    diff_ct = ""
                    abs_diff_ct = ""
                    pct_diff_ct = ""

                if sim_bt is not None and real_bt is not None:
                    diff_bt = sim_bt - real_bt
                    abs_diff_bt = abs(diff_bt)
                    pct_diff_bt = (diff_bt / real_bt * 100.0) if real_bt != 0 else ""
                else:
                    diff_bt = ""
                    abs_diff_bt = ""
                    pct_diff_bt = ""

                comparison_rows.append({
                    "Stock": stock,
                    "yr": year,

                    "ct_real": real_ct,
                    "ct_sim": sim_ct,
                    "diff_ct": diff_ct,
                    "abs_diff_ct": abs_diff_ct,
                    "pct_diff_ct": pct_diff_ct,

                    "bt_real": real_bt,
                    "bt_sim": sim_bt,
                    "diff_bt": diff_bt,
                    "abs_diff_bt": abs_diff_bt,
                    "pct_diff_bt": pct_diff_bt,
                })

                matched_years += 1

            print(f"[OK] Comparison rows created for stock {stock}: {matched_years} matched years ({overlap_start}-{overlap_end})")

        if not comparison_rows:
            print(f"[WARNING] No comparison rows created for experiment {experiment_id}")
            return

        comparison_rows.sort(key=lambda x: (x["Stock"], x["yr"]))

        with open(comparison_path, mode='w', newline='', encoding='utf-8-sig') as csvfile:
            fieldnames = [
                "Stock", "yr",
                "ct_real", "ct_sim", "diff_ct", "abs_diff_ct", "pct_diff_ct",
                "bt_real", "bt_sim", "diff_bt", "abs_diff_bt", "pct_diff_bt",
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(comparison_rows)

        print(f"[OK] Detailed catch & biomass comparison written to {comparison_path}")

    # === HELPER METHOD ===
    # THIS RENAMES ONLY OUTPUT FILES, NOT CORE INPUT / CONFIG FILES
    def _rename_outputs_historical(self, experiment_id: str):
        experiment_dir = Path(__file__).parent.parent / "experiments" / experiment_id

        protected_files = {
            "catch_file.csv",
            "catch_file_original.csv",
            "id_file.csv",
            "AA_CMSY++.R",
            "ffnn.bin",
            "r2jags.bug",
        }

        if not experiment_dir.exists():
            print(f"[WARNING] Experiment directory not found: {experiment_dir}")
            return

        renamed_count = 0

        for file_path in experiment_dir.iterdir():
            if not file_path.is_file():
                continue

            if file_path.name in protected_files:
                continue

            if file_path.stem.endswith("_historical"):
                continue

            new_path = file_path.with_name(f"{file_path.stem}_historical{file_path.suffix}")

            try:
                file_path.rename(new_path)
                renamed_count += 1
                print(f"[OK] Renamed: {file_path.name} -> {new_path.name}")
            except Exception as e:
                print(f"[ERROR] Failed to rename {file_path.name}: {e}")

        print(f"[OK] Historical renaming complete. Renamed {renamed_count} files.")

    # === NEW HELPER METHOD ===
    # THIS RENAMES THE ORIGINAL HISTORICAL catch_file.csv
    def _rename_first_catch_file_historical(self, experiment_id: str):
        experiment_dir = Path(__file__).parent.parent / "experiments" / experiment_id
        catch_file_path = experiment_dir / "catch_file.csv"
        historical_catch_file_path = experiment_dir / "catch_file_historical.csv"

        if not catch_file_path.exists():
            print(f"[WARNING] catch_file.csv not found for experiment {experiment_id}")
            return

        if historical_catch_file_path.exists():
            print(f"[WARNING] catch_file_historical.csv already exists for experiment {experiment_id}. Skipping rename.")
            return

        try:
            catch_file_path.rename(historical_catch_file_path)
            print(f"[OK] Renamed catch_file.csv -> catch_file_historical.csv for experiment {experiment_id}")
        except Exception as e:
            print(f"[ERROR] Failed to rename catch_file.csv to catch_file_historical.csv: {e}")

    # === NEW HELPER METHOD ===
    # THIS KEEPS A HISTORICAL COPY OF THE FILTERED id_file.csv
    # NOTE: WE DO NOT RENAME THE WORKING id_file.csv, BECAUSE PHASE 2 STILL NEEDS IT
    def _create_historical_id_file_copy(self, experiment_id: str):
        experiment_dir = Path(__file__).parent.parent / "experiments" / experiment_id
        id_file_path = experiment_dir / "id_file.csv"
        historical_id_file_path = experiment_dir / "id_file_historical.csv"

        if not id_file_path.exists():
            print(f"[WARNING] id_file.csv not found for experiment {experiment_id}")
            return

        if historical_id_file_path.exists():
            print(f"[WARNING] id_file_historical.csv already exists for experiment {experiment_id}. Skipping copy.")
            return

        try:
            shutil.copy(id_file_path, historical_id_file_path)
            print(f"[OK] Created historical copy: id_file.csv -> id_file_historical.csv for experiment {experiment_id}")
        except Exception as e:
            print(f"[ERROR] Failed to create id_file_historical.csv for experiment {experiment_id}: {e}")

    # === NEW HELPER METHOD ===
    # THIS CREATES A NEW EMPTY catch_file.csv FOR SIMULATED DATA ONLY
    def _create_empty_catch_file_for_experiment(self, experiment_id: str):
        import csv

        experiment_dir = Path(__file__).parent.parent / "experiments" / experiment_id
        catch_file_path = experiment_dir / "catch_file.csv"

        try:
            with open(catch_file_path, mode='w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(["Stock", "yr", "ct", "bt"])
            print(f"[OK] Created new empty catch_file.csv for simulated data: {catch_file_path}")
        except Exception as e:
            print(f"[ERROR] Failed to create new empty catch_file.csv for simulated data: {e}")

