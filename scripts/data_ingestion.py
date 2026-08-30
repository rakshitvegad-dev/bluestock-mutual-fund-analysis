import os
import pandas as pd

# Folder containing all CSV files
DATA_FOLDER = "mutual-fund-analysis/data/raw"

# Check if folder exists
if not os.path.exists(DATA_FOLDER):
    print(f"Folder '{DATA_FOLDER}' not found.")
    exit()

# Get all CSV files
csv_files = [f for f in os.listdir(DATA_FOLDER) if f.endswith(".csv")]

if len(csv_files) == 0:
    print("No CSV files found in data/raw folder.")
    exit()

print("=" * 80)
print(f"Found {len(csv_files)} CSV file(s)")
print("=" * 80)

for file in csv_files:
    file_path = os.path.join(DATA_FOLDER, file)

    print("\n" + "=" * 80)
    print(f"File: {file}")
    print("=" * 80)

    try:
        df = pd.read_csv(file_path)

        print("\nShape:")
        print(df.shape)

        print("\nData Types:")
        print(df.dtypes)

        print("\nFirst 5 Rows:")
        print(df.head())

        print("\nMissing Values:")
        print(df.isnull().sum())

        print("\nDuplicate Rows:")
        print(df.duplicated().sum())

    except Exception as e:
        print(f"Error reading {file}")
        print(e)

print("\nData ingestion completed successfully.")