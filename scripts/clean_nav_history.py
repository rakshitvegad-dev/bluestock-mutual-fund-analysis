import pandas as pd

# Load dataset
df = pd.read_csv(r"D:\mutual-fund-analysis\data\raw\nav_history.csv")

print("Original Shape:", df.shape)

# --------------------------
# Convert date column
# --------------------------
df["date"] = pd.to_datetime(df["date"], errors="coerce")

# --------------------------
# Sort data
# --------------------------
df = df.sort_values(["amfi_code", "date"])

# --------------------------
# Forward fill NAV
# --------------------------
df["nav"] = df.groupby("amfi_code")["nav"].ffill()

# --------------------------
# Remove duplicates
# --------------------------
df = df.drop_duplicates()

# --------------------------
# Remove invalid NAV
# --------------------------
df = df[df["nav"] > 0]

print("Cleaned Shape:", df.shape)

# Save cleaned file
df.to_csv("data/processed/nav_history_cleaned.csv", index=False)

print("nav_history cleaned successfully!")