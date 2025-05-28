import os

# Set R_HOME **before** importing rpy2
os.environ['R_HOME'] = r'C:\Program Files\R\R-4.4.1'  # Make sure this is the correct R install path
os.environ["LANG"] = "en_US.UTF-8"
os.environ["TINYTEX_USERMODE"] = "true"

from rpy2 import robjects  # ✅ Import only after setting R_HOME

# Full path to the R script
script_path = os.path.join(os.path.dirname(__file__), "AA_CMSY++.R")

# Run the R script
robjects.r(f'setwd("{os.path.dirname(script_path).replace("\\", "/")}")')
robjects.r.source(script_path)

print("✅ CMSY++ completed.")
