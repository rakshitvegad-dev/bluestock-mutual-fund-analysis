import pandas as pd

df = pd.read_csv(r"D:\mutual-fund-analysis\data\raw\scheme_performance.csv")

print("Shape:", df.shape)
print("\nColumns:")
print(df.columns.tolist())

print("\nData Types:")
print(df.dtypes)

print("\nReturn columns:")
return_cols = [
    "return_1yr_pct",
    "return_3yr_pct",
    "return_5yr_pct",
    "benchmark_3yr_pct"
]

print(df[return_cols].dtypes)

print("\nExpense Ratio:")
print(df["expense_ratio_pct"].describe())

print("\nExpense ratios outside 0.1% - 2.5%:")
print(
    df[
        (df["expense_ratio_pct"] < 0.1) |
        (df["expense_ratio_pct"] > 2.5)
    ][
        ["scheme_name", "expense_ratio_pct"]
    ]
)