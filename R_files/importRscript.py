import os
import shutil

# Source and destination folder paths
source_folder = r"F:\CMSY++TEST\R files"
destination_folder = r"C:\Users\user\Desktop\SURIMI\SURIMI-CMSY\R files"

try:
    # Check if the source folder exists
    if not os.path.exists(source_folder):
        print(f"Source folder not found: {source_folder}")
    else:
        print(f"Source folder exists: {source_folder}")
        
        # Check if the destination subfolder exists, create if not
        if not os.path.exists(destination_folder):
            os.makedirs(destination_folder)
            print(f"Created destination subfolder: {destination_folder}")

        # Loop through all files in the source folder
        for file_name in os.listdir(source_folder):
            # Check if the file is an R script
            if file_name.endswith(".R"):
                source_path = os.path.join(source_folder, file_name)
                destination_path = os.path.join(destination_folder, file_name)
                
                # Copy the R script
                shutil.copy2(source_path, destination_path)
                print(f"Imported R script: {source_path} -> {destination_path}")

        print("All R scripts imported successfully!")

except Exception as e:
    print(f"Error importing R scripts: {e}")
