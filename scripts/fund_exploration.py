import pandas as pd

# Load the dataset
df = pd.read_csv(r"D:\mutual-fund-analysis\data\raw\fund_master.csv")

print("=" * 60)
print("Fund Master Dataset")
print("=" * 60)

print("\nColumns:")
print(df.columns.tolist())

print("\nUnique Fund Houses:")
print(df["fund_house"].unique())

print("\nUnique Categories:")
print(df["category"].unique())

print("\nUnique Sub-Categories:")
print(df["sub_category"].unique())

print("\nUnique Risk Grades:")
print(df["risk_category"].unique())