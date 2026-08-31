import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path


# ============================================================
# PROJECT PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

NAV_PATH = BASE_DIR / "data" / "raw" / "nav_history.csv"
FUND_PATH = BASE_DIR / "data" / "raw" / "fund_master.csv"

OUTPUT_CSV = (
    BASE_DIR
    / "data"
    / "processed"
    / "markowitz_portfolios.csv"
)

OUTPUT_CHART = (
    BASE_DIR
    / "reports"
    / "markowitz_efficient_frontier.png"
)


# ============================================================
# SELECTED FUNDS
# ============================================================

SELECTED_FUNDS = {
    125497: "HDFC Top 100 Direct",
    125498: "HDFC Mid-Cap Opportunities Direct",
    119599: "SBI Small Cap Direct",
    119120: "SBI Magnum Gilt",
    102885: "UTI Nifty 50 Index",
}


# ============================================================
# CONFIGURATION
# ============================================================

TRADING_DAYS = 252
SIMULATIONS = 20000
RISK_FREE_RATE = 0.06

np.random.seed(42)


# ============================================================
# LOAD DATA
# ============================================================

print("=" * 70)
print("MARKOWITZ EFFICIENT FRONTIER")
print("=" * 70)

nav = pd.read_csv(NAV_PATH)

nav["date"] = pd.to_datetime(
    nav["date"],
    errors="coerce"
)

nav["amfi_code"] = pd.to_numeric(
    nav["amfi_code"],
    errors="coerce"
)

nav["nav"] = pd.to_numeric(
    nav["nav"],
    errors="coerce"
)

nav = nav.dropna(
    subset=["date", "amfi_code", "nav"]
)

nav = nav[
    nav["amfi_code"].isin(
        SELECTED_FUNDS.keys()
    )
]

print(
    f"\nSelected funds found: "
    f"{nav['amfi_code'].nunique()}"
)


# ============================================================
# PIVOT NAV DATA
# ============================================================

prices = nav.pivot_table(
    index="date",
    columns="amfi_code",
    values="nav"
)

prices = prices.sort_index()

# Use common observations across all five funds
prices = prices.dropna()

print(
    f"Common trading observations: "
    f"{len(prices):,}"
)


# ============================================================
# DAILY RETURNS
# ============================================================

returns = prices.pct_change().dropna()

print(
    f"Return observations: "
    f"{len(returns):,}"
)


# ============================================================
# EXPECTED RETURN + COVARIANCE
# ============================================================

annual_returns = returns.mean() * TRADING_DAYS

annual_covariance = (
    returns.cov() * TRADING_DAYS
)

annual_volatility = np.sqrt(
    np.diag(annual_covariance)
)


# ============================================================
# MONTE CARLO PORTFOLIOS
# ============================================================

results = []

fund_codes = list(SELECTED_FUNDS.keys())

for _ in range(SIMULATIONS):

    weights = np.random.random(
        len(fund_codes)
    )

    weights = (
        weights
        / weights.sum()
    )

    portfolio_return = np.dot(
        weights,
        annual_returns.values
    )

    portfolio_variance = np.dot(
        weights,
        np.dot(
            annual_covariance.values,
            weights
        )
    )

    portfolio_volatility = np.sqrt(
        portfolio_variance
    )

    sharpe_ratio = (
        portfolio_return
        - RISK_FREE_RATE
    ) / portfolio_volatility

    row = {
        "expected_return": portfolio_return,
        "volatility": portfolio_volatility,
        "sharpe_ratio": sharpe_ratio,
    }

    for i, code in enumerate(fund_codes):

        row[
            f"weight_{code}"
        ] = weights[i]

    results.append(row)


portfolios = pd.DataFrame(results)


# ============================================================
# FIND OPTIMAL PORTFOLIOS
# ============================================================

min_volatility = portfolios.loc[
    portfolios["volatility"].idxmin()
]

max_sharpe = portfolios.loc[
    portfolios["sharpe_ratio"].idxmax()
]


# ============================================================
# DISPLAY RESULTS
# ============================================================

print("\n" + "=" * 70)
print("FUND STATISTICS")
print("=" * 70)

for code in fund_codes:

    print(
        f"{SELECTED_FUNDS[code]:40s} "
        f"Return={annual_returns[code]:7.2%} "
        f"Volatility={annual_volatility[fund_codes.index(code)]:7.2%}"
    )


print("\n" + "=" * 70)
print("MINIMUM VOLATILITY PORTFOLIO")
print("=" * 70)

print(
    f"Expected return: "
    f"{min_volatility['expected_return']:.2%}"
)

print(
    f"Volatility: "
    f"{min_volatility['volatility']:.2%}"
)

print(
    f"Sharpe ratio: "
    f"{min_volatility['sharpe_ratio']:.3f}"
)


print("\nWeights:")

for code in fund_codes:

    print(
        f"{SELECTED_FUNDS[code]:40s} "
        f"{min_volatility[f'weight_{code}']:.2%}"
    )


print("\n" + "=" * 70)
print("MAXIMUM SHARPE PORTFOLIO")
print("=" * 70)

print(
    f"Expected return: "
    f"{max_sharpe['expected_return']:.2%}"
)

print(
    f"Volatility: "
    f"{max_sharpe['volatility']:.2%}"
)

print(
    f"Sharpe ratio: "
    f"{max_sharpe['sharpe_ratio']:.3f}"
)


print("\nWeights:")

for code in fund_codes:

    print(
        f"{SELECTED_FUNDS[code]:40s} "
        f"{max_sharpe[f'weight_{code}']:.2%}"
    )


# ============================================================
# SAVE PORTFOLIOS
# ============================================================

OUTPUT_CSV.parent.mkdir(
    parents=True,
    exist_ok=True
)

OUTPUT_CHART.parent.mkdir(
    parents=True,
    exist_ok=True
)

portfolios.to_csv(
    OUTPUT_CSV,
    index=False
)


# ============================================================
# EFFICIENT FRONTIER CHART
# ============================================================

plt.figure(
    figsize=(10, 7)
)

plt.scatter(
    portfolios["volatility"],
    portfolios["expected_return"],
    c=portfolios["sharpe_ratio"],
    s=8,
    alpha=0.35
)

plt.scatter(
    min_volatility["volatility"],
    min_volatility["expected_return"],
    marker="*",
    s=250,
    label="Minimum Volatility"
)

plt.scatter(
    max_sharpe["volatility"],
    max_sharpe["expected_return"],
    marker="*",
    s=250,
    label="Maximum Sharpe"
)

plt.xlabel(
    "Annualized Volatility"
)

plt.ylabel(
    "Expected Annual Return"
)

plt.title(
    "Markowitz Efficient Frontier - 5 Mutual Funds"
)

plt.grid(
    alpha=0.25
)

plt.legend()

plt.tight_layout()

plt.savefig(
    OUTPUT_CHART,
    dpi=200
)

plt.close()


# ============================================================
# COMPLETE
# ============================================================

print("\n" + "=" * 70)
print("B4 MARKOWITZ OPTIMIZATION COMPLETED")
print("=" * 70)

print(
    f"Portfolio simulations: {SIMULATIONS:,}"
)

print(
    f"CSV: {OUTPUT_CSV}"
)

print(
    f"Chart: {OUTPUT_CHART}"
)