import os
import shutil

# Source and destination folder paths
source_folder = r"F:\CMSY++TEST\R files"
destination_folder = r"C:\Users\user\Desktop\SURIMI\SURIMI-CMSY\R files"

try:
    # Check if the source folder exists
    if not os.path.exists(source_folder):
        print(f"❌ Source folder not found: {source_folder}")
    else:
        print(f"✅ Source folder exists: {source_folder}")
        
        # Check if the destination subfolder exists, create if not
        if not os.path.exists(destination_folder):
            os.makedirs(destination_folder)
            print(f"✅ Created destination subfolder: {destination_folder}")

        # List all files in the source folder
        print("\n📂 Files in the source folder:")
        for file_name in os.listdir(source_folder):
            print(f"- {file_name}")
        
        # Loop through all files in the source folder
        for file_name in os.listdir(source_folder):
            # Check if the file is an R script or a binary file (.bin)
            if file_name.endswith(".R") or file_name.endswith(".bin"):
                source_path = os.path.join(source_folder, file_name)
                destination_path = os.path.join(destination_folder, file_name)
                
                # Print before copying
                print(f"📥 Importing file: {file_name}")

                # Copy the file
                shutil.copy2(source_path, destination_path)
                print(f"✅ Imported: {source_path} -> {destination_path}")

        print("\n✅ All relevant files imported successfully!")

except Exception as e:
    print(f"❌ Error importing files: {e}")
