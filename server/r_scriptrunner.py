from pathlib import Path
import subprocess
import os
import threading

from server.s3_storage import S3_Storage

class R_ScriptRunner:
    @staticmethod
    def run_r_script_s3_upload(script_name, simulation_id):
        script = Path(__file__).parent.parent.resolve() / Path("simulations") / simulation_id / script_name

        print(f"Running R script: {script}")

        os.environ["LANG"] = "en_US.UTF-8"
        os.environ["TINYTEX_USERMODE"] = "true"

        directory = os.path.dirname(script)
        print(f"Changing working directory to: {directory}")
        os.chdir(directory)

        # Run the R script using subprocess
        print(f"Start executing {script} using Rscript.")
        result = subprocess.run(
            ["Rscript", script],
            capture_output=True,
            text=True
        )

        print("Rscript stdout:")
        print(result.stdout)
        print("Rscript stderr:")
        print(result.stderr)

        if result.returncode == 0:
            print("✅ CMSY++ completed.")
            S3_Storage.UploadFilesToS3(os.path.dirname(script), f"Surimi-cmsy/Simulations/{simulation_id}")
        else:
            print(f"❌ CMSY++ failed with exit code {result.returncode}.")

    @staticmethod
    def run_r_script_s3_upload_background(script_name, simulation_id):
        threading.Thread(target=R_ScriptRunner.run_r_script_s3_upload, args=(script_name,simulation_id), daemon=True).start()