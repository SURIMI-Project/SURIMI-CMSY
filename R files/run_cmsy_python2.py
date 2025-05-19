import os
os.environ['R_HOME'] = r'C:\Program Files\R\R-4.4.1'  # Keep this part intact
import rpy2.robjects as robjects
import rpy2.situation
import sys

# 1. Manually set R_HOME using the hardcoded path
os.environ["R_HOME"] = rpy2.situation.get_r_home()
print(f"R_HOME is set to: {os.environ['R_HOME']}")

def run_r_script(stocks="NA"):
    # 2. Locate the .R driver (no change here)
    this_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 3. Construct the path to the R script inside the "R files" folder (correcting this part)
    r_script = os.path.join(this_dir, "AA_CMSY++.R")

    try:
        print("▶ Running CMSY++ analysis using rpy2...")

        # Set environment variables (if needed)
        os.environ["LANG"] = "en_US.UTF-8"
        os.environ["TINYTEX_USERMODE"] = "true"

        # Check if the R script exists
        if not os.path.isfile(r_script):
            print(f"❌ R script not found at: {r_script}")
            sys.exit(1)

        # Set the working directory for the R script explicitly (this should be in the "R files" folder)
        robjects.r(f'setwd("{this_dir.replace("\\", "/")}")')
        print(f"Setting R working directory to: {this_dir}")

        # Set the environment variable for the stock name
        os.environ['STOCK_NAME'] = stocks
        print(f"Environment variable set: STOCK_NAME={stocks}")

        # Run the R script using rpy2
        robjects.r.source(r_script)

        print("✅ CMSY++ R script completed successfully.")
    except Exception as e:
        print("❌ Error during R script execution.")
        print(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    # Check if a stock name is provided as a command-line argument
    if len(sys.argv) > 1:
        # Join all parts of the argument to handle spaces correctly
        stock_name = " ".join(sys.argv[1:])
        print(f"Received stock name from argument: {stock_name}")
        run_r_script(stock_name)
    else:
        print("No stock name provided, running for all stocks (NA)")
        run_r_script()
