from pathlib import Path
import subprocess
import os

from server.s3_storage import S3_Storage

class R_ScriptRunner:
    @staticmethod
    def run_r_script_s3_upload(script_name, experiment_id):
        script = Path(__file__).parent.parent.resolve() / Path("experiments") / experiment_id / script_name

        print(f"Running R script: {script}")

        os.environ["LANG"] = "en_US.UTF-8"
        os.environ["TINYTEX_USERMODE"] = "true"

        directory = os.path.dirname(script)
        print(f"Changing working directory to: {directory}")
        os.chdir(directory)

        # Run the R script using subprocess
        print(f"Start executing {script} using Rscript. Please wait...")
        result = subprocess.run(
            ["Rscript", script],
            capture_output=True,
            text=True
        )

        print("Rscript stdout:")
        print(result.stdout)
        print("Rscript stderr:")
        print(result.stderr)

        print("[OK] CMSY++ completed.")
        if result.returncode != 0:
            raise RuntimeError(f"R script {script} failed with return code {result.returncode}")