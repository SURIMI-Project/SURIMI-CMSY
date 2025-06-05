import subprocess
import os

class R_ScriptRunner:
    @staticmethod
    def run_r_script(script):
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
        else:
            print(f"❌ CMSY++ failed with exit code {result.returncode}.")