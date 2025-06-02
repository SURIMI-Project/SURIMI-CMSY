import os
from pathlib import Path

class R_ScriptRunner:
    @staticmethod
    def run_r_script():

        # test code to write to a file
        path_prefix = os.environ.get("EDITO_INFRA_OUTPUT", "C:/Temp")
        my_file_path = Path(path_prefix) / "myfile.txt"
        print(f"Writing to test-file: {my_file_path}")
        f = open(my_file_path, "a")
        f.write("Now the file has more content!")
        f.close()

        # Set R_HOME **before** importing rpy2
#        os.environ['R_HOME'] = r'C:\Program Files\R\R-4.4.1'  # Make sure this is the correct R install path
        os.environ["LANG"] = "en_US.UTF-8"
        os.environ["TINYTEX_USERMODE"] = "true"

        # Import rpy2 here, after env vars are set
        from rpy2 import robjects

        current_dir = Path.cwd()
        print(f"Current working directory: {current_dir}")
        
        if current_dir.name != "R_files":
            current_dir = current_dir / "R_files"
            os.chdir(current_dir)

        # Full path to the R script
        script_path = Path.cwd() / "AA_CMSY++.R"

        # Run the R script
        print(f"Start executing {str(script_path)}.")
        robjects.r.source(str(script_path))

        print("✅ CMSY++ completed.")