"""
Bluestock Mutual Fund Analytics
Bonus B3 - Monte Carlo NAV Projection

Projects HDFC Top 100 Direct NAV over a 5-year horizon
using a geometric Brownian motion model calibrated from
historical daily log returns.
"""

from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


# ============================================================
# PROJECT PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

INPUT_PATH = BASE_DIR / "data" / "raw" / "HDFC_Top100_Direct.csv"
OUTPUT_DIR = BASE_DIR / "reports"
PROCESSED_DIR = BASE_DIR / "data" / "processed"

OUTPUT_CHART = OUTPUT_DIR / "monte_carlo_nav_projection.png"
OUTPUT_CSV = PROCESSED_DIR / "monte_carlo_nav_simulation.csv"


# ============================================================
# SIMULATION PARAMETERS
# ============================================================

YEARS = 5
TRADING_DAYS = 252
NUM_PATHS = 10_000
RANDOM_SEED = 42


# ============================================================
# LOAD AND VALIDATE DATA
# ============================================================

def load_nav_data() -> pd.DataFrame:
    """Load and validate historical NAV data."""

    if not INPUT_PATH.exists():
        raise FileNotFoundError(
            f"Input file not found:\n{INPUT_PATH}"
        )

    df = pd.read_csv(INPUT_PATH)

    required_columns = {"date", "nav"}

    missing_columns = required_columns - set(df.columns)

    if missing_columns:
        raise ValueError(
            f"Missing required columns: {sorted(missing_columns)}"
        )

    df["date"] = pd.to_datetime(
        df["date"],
        errors="coerce"
    )

    df["nav"] = pd.to_numeric(
        df["nav"],
        errors="coerce"
    )

    df = (
        df.dropna(subset=["date", "nav"])
        .sort_values("date")
        .drop_duplicates(subset=["date"])
    )

    df = df[df["nav"] > 0].copy()

    if len(df) < 100:
        raise ValueError(
            "Insufficient historical observations for simulation."
        )

    return df


# ============================================================
# CALCULATE HISTORICAL PARAMETERS
# ============================================================

def calculate_parameters(
    df: pd.DataFrame,
) -> tuple[float, float, float]:
    """Calculate daily log-return mean, volatility and latest NAV."""

    df["log_return"] = np.log(
        df["nav"] / df["nav"].shift(1)
    )

    returns = df["log_return"].dropna()

    daily_mean = returns.mean()
    daily_volatility = returns.std()

    latest_nav = df.iloc[-1]["nav"]

    return (
        daily_mean,
        daily_volatility,
        latest_nav,
    )


# ============================================================
# MONTE CARLO SIMULATION
# ============================================================

def run_simulation(
    latest_nav: float,
    daily_mean: float,
    daily_volatility: float,
) -> np.ndarray:
    """Generate Monte Carlo NAV paths using geometric Brownian motion."""

    total_days = YEARS * TRADING_DAYS

    rng = np.random.default_rng(RANDOM_SEED)

    random_shocks = rng.normal(
        0,
        1,
        size=(total_days, NUM_PATHS),
    )

    daily_returns = (
        daily_mean
        - 0.5 * daily_volatility**2
        + daily_volatility * random_shocks
    )

    cumulative_returns = np.cumsum(
        daily_returns,
        axis=0,
    )

    paths = latest_nav * np.exp(
        cumulative_returns
    )

    initial_row = np.full(
        (1, NUM_PATHS),
        latest_nav,
    )

    return np.vstack(
        [initial_row, paths]
    )


# ============================================================
# SAVE RESULTS
# ============================================================

def save_results(
    paths: np.ndarray,
) -> pd.DataFrame:
    """Create and save percentile simulation results."""

    days = np.arange(paths.shape[0])

    result = pd.DataFrame(
        {
            "trading_day": days,
            "nav_p05": np.percentile(paths, 5, axis=1),
            "nav_median": np.percentile(paths, 50, axis=1),
            "nav_p95": np.percentile(paths, 95, axis=1),
        }
    )

    PROCESSED_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    result.to_csv(
        OUTPUT_CSV,
        index=False,
    )

    return result


# ============================================================
# CREATE CHART
# ============================================================

def create_chart(
    result: pd.DataFrame,
) -> None:
    """Create the 5-year Monte Carlo projection chart."""

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    plt.figure(
        figsize=(12, 7)
    )

    plt.fill_between(
        result["trading_day"],
        result["nav_p05"],
        result["nav_p95"],
        alpha=0.2,
        label="5th–95th percentile",
    )

    plt.plot(
        result["trading_day"],
        result["nav_median"],
        linewidth=2,
        label="Median simulated NAV",
    )

    plt.xlabel(
        "Trading days"
    )

    plt.ylabel(
        "NAV (₹)"
    )

    plt.title(
        "HDFC Top 100 Direct — 5-Year Monte Carlo NAV Projection"
    )

    plt.legend()

    plt.grid(
        alpha=0.3
    )

    plt.tight_layout()

    plt.savefig(
        OUTPUT_CHART,
        dpi=200,
        bbox_inches="tight",
    )

    plt.close()


# ============================================================
# MAIN
# ============================================================

def main() -> None:
    """Run the complete Monte Carlo NAV projection."""

    print("=" * 70)
    print("HDFC TOP 100 DIRECT - MONTE CARLO NAV PROJECTION")
    print("=" * 70)

    df = load_nav_data()

    daily_mean, daily_volatility, latest_nav = (
        calculate_parameters(df)
    )

    paths = run_simulation(
        latest_nav,
        daily_mean,
        daily_volatility,
    )

    result = save_results(paths)

    create_chart(result)

    final_p05 = result.iloc[-1]["nav_p05"]
    final_median = result.iloc[-1]["nav_median"]
    final_p95 = result.iloc[-1]["nav_p95"]

    print(f"\nHistorical observations: {len(df):,}")
    print(f"Latest NAV: ₹{latest_nav:,.4f}")
    print(f"Daily mean log return: {daily_mean:.6f}")
    print(f"Daily volatility: {daily_volatility:.6f}")
    print(f"Simulation horizon: {YEARS} years")
    print(f"Trading days: {YEARS * TRADING_DAYS:,}")
    print(f"Simulation paths: {NUM_PATHS:,}")

    print("\n5-Year simulated NAV:")
    print(f"5th percentile:  ₹{final_p05:,.2f}")
    print(f"Median:          ₹{final_median:,.2f}")
    print(f"95th percentile: ₹{final_p95:,.2f}")

    print("\nOutput files:")
    print(f"CSV:   {OUTPUT_CSV}")
    print(f"Chart: {OUTPUT_CHART}")

    print("\nMonte Carlo simulation completed successfully.")


if __name__ == "__main__":
    main()