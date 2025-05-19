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
        
        # Check if the destination folder exists, create if not
        if not os.path.exists(destination_folder):
            os.makedirs(destination_folder)
            print(f"Created destination folder: {destination_folder}")

        # Loop through all files in the source folder
        for file_name in os.listdir(source_folder):
            if file_name.endswith(".csv"):
                source_path = os.path.join(source_folder, file_name)
                destination_path = os.path.join(destination_folder, file_name)
                
                # Print paths before copying
                print(f"Attempting to copy from {source_path} to {destination_path}")
                
                # Copy the file
                shutil.copy2(source_path, destination_path)
                print(f"Copied: {source_path} -> {destination_path}")

        print("All CSV files copied successfully!")

except Exception as e:
    print(f"Error copying files: {e}")
