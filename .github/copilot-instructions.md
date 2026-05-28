# Copilot Instructions

## Build, run, and verification commands

- Create the expected local environment from the repository root:
  - `py -m venv .venv`
  - `.\.venv\Scripts\python.exe -m pip install -r requirements.txt`
- Start the gRPC service the same way the Docker image does:
  - `.\.venv\Scripts\python.exe server\app.py`
- Build the full runtime image from the root `Dockerfile`:
  - `docker build -f Dockerfile . -t ghcr.io/official-ewe/surimicmsy:latest`
- Run the container locally:
  - `docker run -p 5021:5021 ghcr.io/official-ewe/surimicmsy:latest`
- There is no checked-in unit test or lint configuration. The only repo-defined targeted smoke checks are the helper modules with `__main__` blocks:
  - `.\.venv\Scripts\python.exe server\species_lookup.py`
  - `.\.venv\Scripts\python.exe server\division_lookup.py`
- Integration tests live in `integration_tests\`. They start the CMSY service **in-process** (via `serve_in_thread`) and send real gRPC messages to it. Run them from the repo root with:
  - `.\venv\Scripts\python.exe -m pytest integration_tests\tests\ -v`
  - The JSON request fixtures are in `integration_tests\GrpcMessages\<MessageName>\StockAssessmentService_<MessageName>.json`

## High-level architecture

- This repository is a Python gRPC wrapper around the CMSY++ R model. The gRPC protocol is **not** stored in this repo; `server\app.py` imports generated stubs from the installed `surimi-surimi-protocol-grpc-python` package, which is version-pinned in `requirements.txt` and documented in `README.md`.
- `server\app.py` is the runtime entrypoint. It loads `.env`, optionally hydrates additional secrets from Vault, installs two interceptors, and hosts `StockAssessmentService` on port `5021`. It also exposes `serve_in_thread()` for in-process use by the integration test suite.
- `server\StockAssessment.py` is the core orchestration layer. It manages experiment lifecycle and bridges protobuf requests to filesystem, CSV, S3, and R-script operations:
  - `InitialiseExperiment` creates `experiments\<experiment_id>`, refreshes base files from `surimi-cmsy/config` in S3 into `R_files`, copies the working CMSY inputs, filters them down to the contract species from the init request, runs an initial historical assessment, then converts the experiment into the phase-2 simulated state.
  - `UpdateBiomassStatistics` and `UpdateCatchDispositionStatistics` accumulate monthly grid statistics in the in-memory `Simulation` object.
  - `ExperimentStep` advances time one month at a time; when a year boundary is crossed it writes that year’s aggregated rows into `catch_file.csv`, using FAO division lookup plus common-name lookup to build stock labels.
  - `FinaliseExperiment` updates `id_file.csv` with the simulated year range, writes `catch_comparison_detailed.csv`, reruns the R assessment, and uploads outputs through `S3_Storage`.
- `R_files\` contains the model inputs and lookup assets that the Python service expects to exist locally: `AA_CMSY++.R`, `ffnn.bin`, `catch_file.csv`, `catch_file_original.csv`, `id_file.csv`, the FAO shapefile, and the ASFIS common-name CSV.
- `server\r_scriptrunner.py` changes the process working directory into `experiments\<experiment_id>` before calling `Rscript`. That is why the R script uses plain filenames like `catch_file.csv` and `id_file.csv` instead of absolute paths.
- `AA_CMSY++.R` is configured for **CSV-only output**: `save.plots <- F`, `write.pdf <- F`, `mgraphs <- F`, `kobe.plot <- F`, `rk.diags <- F`. It produces no JPEG, PNG, or PDF files. This is why the Dockerfile contains no graphics libraries (libcairo, libjpeg, libpng, etc.) and no LaTeX/texlive packages.
- **JAGS** is installed from the Debian Bookworm apt package (`jags`) — version 4.3.1 — rather than compiled from source. Do not add a from-source compilation block; update the apt package version instead if a newer JAGS is needed.

## Key repository-specific conventions

- Only monthly simulations are supported. `StockAssessmentService` rejects any `simulation.time_step` other than `P1M`.
- Treat `experiments\<experiment_id>` as the canonical working directory for an experiment. New outputs and helper files should be written there, not back into `R_files\`.
- Preserve the CSV contracts expected by `AA_CMSY++.R`:
  - `catch_file.csv` uses `Stock,yr,ct,bt`
  - `id_file.csv` must keep the CMSY column set, especially fields such as `Stock`, `MinOfYear`, `MaxOfYear`, `StartYear`, `EndYear`, `stb.low`, `stb.hi`, and `btype`
- The service intentionally has a two-phase flow:
  1. Run a historical assessment using the filtered source data.
  2. Rename/copy historical outputs, derive new `stb.low` and `stb.hi` values from `*id_file_output_historical.csv`, force `btype` to `CPUE`, create a fresh empty `catch_file.csv`, and then accumulate simulated years.
- Species handling is split across two representations:
  - contract input species are FAO alpha codes from the protobuf request
  - yearly simulated catch rows are written as `"<common species name> - <FAO division>"`
  Do not collapse these formats unless the whole pipeline is updated together.
- `server\species_lookup.py` and `server\division_lookup.py` load their lookup datasets once at module import from `R_files\`. Changes to those file locations or schemas ripple into runtime behavior immediately.
- `server\app.py` currently mixes package imports (`from server...`) with a sibling import (`from vault_service import ...`). Follow the existing entrypoint pattern (`python server\app.py` and the Docker `CMD`) unless you are deliberately normalizing imports across the whole service.

## Related repositories

- The gRPC protocol definition (`.proto` files) lives in a sibling repository:
  - `C:\Users\Rik\source\repos\SURIMI-protocol\`
  - Consult the `.proto` files there for exact field names, message structures, enum values, and required vs optional fields when generating JSON test fixtures, assertions, or any protobuf-related code.
