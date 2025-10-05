
"""


Key features:
- day: 0=Mon..6=Sun (random per simulation if not fixed)
- time: hour-of-day with fractions; simulation advances in 0.5h steps (30 min travel slot)
- weather: fixed to "clear" by default (or use a value from your data)
- travel time: moving between clusters takes 0.5h (no revenue during that slot)
- priority rule: drivers with higher hours_left are assigned first in the recommendation strategy
- congestion model: 'saturation' (concave R*(1-exp(-alpha*n))) or 'split' (coverage-like)
- flexible loader: accepts either long format (cluster, expected_revenue) or wide with digit-named cluster columns ('0','1',...); fills missing weather with 'clear' if needed.
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple
import warnings

# =========================
# Configuration defaults
# =========================
DEFAULT_N_CLUSTERS = 6
DEFAULT_N_DRIVERS = 30
DEFAULT_TIME_HORIZON_HOURS = 6.0           # total simulated horizon (hours)
DT = 0.5                                    # slot size (hours) to model 30-min travel
DEFAULT_ALPHA = 0.6                         # saturation curvature
RANDOM_SEED = 12345
warnings.filterwarnings('ignore')

# =========================
# Data loading utilities
# =========================
EXPECTED_COLUMNS_LONG = ['day', 'time', 'weather', 'cluster', 'expected_revenue']

def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [str(c).strip().lower() for c in df.columns]
    # Common aliases
    aliases = {
        'cluster_id': 'cluster',
        'rev': 'expected_revenue',
        'expected revenue': 'expected_revenue',
        'weekday': 'day',
        'hour': 'time',
        'tod': 'time',
    }
    for old, new in aliases.items():
        if old in df.columns and new not in df.columns:
            df[new] = df.pop(old)
    # Drop excel index artifacts
    for c in list(df.columns):
        if c.startswith('unnamed:'):
            df.drop(columns=c, inplace=True, errors='ignore')
    return df

def _try_melt_wide(df: pd.DataFrame) -> Optional[pd.DataFrame]:
    """If the dataframe is wide with digit-named cluster columns, melt to long."""
    digit_cols = [c for c in df.columns if c.isdigit()]
    if not digit_cols:
        return None
    # Ensure id columns exist
    for base in ['day', 'time']:
        if base not in df.columns:
            raise ValueError(f"Column '{base}' is required to melt wide data.")
    if 'weather' not in df.columns:
        df['weather'] = 'clear'  # default to clear if missing
    df_m = df.melt(
        id_vars=['day', 'time', 'weather'],
        value_vars=digit_cols,
        var_name='cluster',
        value_name='expected_revenue'
    )
    df_m['cluster'] = df_m['cluster'].astype(int)
    return df_m

def load_revenue_table(path: str) -> pd.DataFrame:
    """
    Load a table with either:
      (A) Long format columns (case-insensitive):
          day, time, weather, cluster, expected_revenue
      (B) Wide format: columns include digit-named clusters ('0','1',...) + day, time, [weather]
          -> will be melted automatically.

    Returns standardized columns: day, time, weather, cluster_id, expected_revenue
    """
    path_obj = Path(path)
    if not path_obj.exists():
        raise FileNotFoundError(f'File not found: {path}')
    if path_obj.suffix.lower() in ['.xlsx', '.xls']:
        df = pd.read_excel(path_obj)
    else:
        df = pd.read_csv(path_obj)
    df = _normalize_columns(df)

    # Try wide -> long first
    melted = _try_melt_wide(df)
    if melted is not None:
        df = melted

    # If still not in long format, verify columns
    missing = [c for c in ['day','time','cluster','expected_revenue'] if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}. Present: {list(df.columns)}")

    # weather default to clear if missing
    if 'weather' not in df.columns:
        df['weather'] = 'clear'

    # Clean & types
    df['day'] = df['day'].astype(int)
    df['time'] = df['time'].astype(float) % 24.0
    df['weather'] = df['weather'].astype(str).str.strip().str.lower()

    # Normalize cluster to integer ids 0..K-1 (preserve ordering of unique values)
    if pd.api.types.is_numeric_dtype(df['cluster']):
        clusters_sorted = sorted(df['cluster'].unique())
        mapping = {c:i for i, c in enumerate(clusters_sorted)}
    else:
        mapping = {c:i for i, c in enumerate(df['cluster'].astype(str).unique())}
    df['cluster_id'] = df['cluster'].map(mapping)

    df['expected_revenue'] = pd.to_numeric(df['expected_revenue'], errors='coerce').fillna(0.0)
    df_std = df[['day','time','weather','cluster_id','expected_revenue']].copy()
    return df_std

# =========================
# Revenue lookup
# =========================
def _nearest_time_index(series: pd.Series, t: float) -> np.ndarray:
    # distances on a circular 24h clock
    delta = np.minimum(np.abs(series - t), 24.0 - np.abs(series - t))
    return np.argsort(delta.values)

def expected_revenue_vector(df: pd.DataFrame, day: int, time_h: float, weather: str, n_clusters: int) -> np.ndarray:
    """
    Return expected revenue per cluster for given (day, time, weather).
    If exact rows don't exist, use nearest time (and same day/weather), then relax to same day, then global mean.
    """
    day = int(day) % 7
    time_h = float(time_h) % 24.0
    weather = str(weather).strip().lower()

    subset = df[(df['day'] == day) & (df['weather'] == weather)]
    if len(subset) == 0:
        subset = df[df['day'] == day]
    if len(subset) == 0:
        subset = df.copy()

    # Find nearest time rows
    order = _nearest_time_index(subset['time'], time_h)
    subset = subset.iloc[order]

    # Take the best row per cluster by nearest time
    best = subset.groupby('cluster_id', as_index=False).first()
    rev = np.zeros(n_clusters, dtype=float)
    for _, row in best.iterrows():
        k = int(row['cluster_id'])
        if 0 <= k < n_clusters:
            rev[k] = float(row['expected_revenue'])

    # Fallback: if some clusters missing, fill with their global mean
    if np.any(rev == 0):
        global_means = df.groupby('cluster_id')['expected_revenue'].mean()
        for k in range(n_clusters):
            if rev[k] == 0:
                rev[k] = float(global_means.get(k, global_means.mean()))
    return rev

# =========================
# Congestion models
# =========================
def macro_saturation(n: int, R: float, alpha: float) -> float:
    if n <= 0:
        return 0.0
    return R * (1 - np.exp(-alpha * n))

def macro_split(n: int, R: float) -> float:
    return R if n > 0 else 0.0

def compute_macro(assignments: np.ndarray, revenues: np.ndarray, model: str, alpha: float) -> float:
    K = len(revenues)
    counts = np.bincount(assignments, minlength=K)
    total = 0.0
    if model == 'saturation':
        for k in range(K):
            total += macro_saturation(int(counts[k]), float(revenues[k]), alpha)
    elif model == 'split':
        for k in range(K):
            total += macro_split(int(counts[k]), float(revenues[k]))
    else:
        raise ValueError('Unknown model')
    return total

# =========================
# Allocation logic
# =========================
def greedy_macro_allocation(num_drivers: int, revenues: np.ndarray, model: str, alpha: float) -> np.ndarray:
    """Return counts per cluster that greedily maximize macro revenue."""
    K = len(revenues)
    counts = np.zeros(K, dtype=int)
    for _ in range(num_drivers):
        best_k, best_gain = 0, -1e18
        for k in range(K):
            n = counts[k]
            if model == 'saturation':
                cur = macro_saturation(n, revenues[k], alpha)
                new = macro_saturation(n+1, revenues[k], alpha)
            else:
                cur = macro_split(n, revenues[k])
                new = macro_split(n+1, revenues[k])
            gain = new - cur
            if gain > best_gain:
                best_gain, best_k = gain, k
        counts[best_k] += 1
    return counts

@dataclass
class Driver:
    cluster: int
    hours_left: float

def assign_recommendation(active: List[Driver], target_counts: np.ndarray) -> List[int]:
    """Assign target clusters to active drivers, prioritizing higher hours_left."""
    # Build slots per cluster
    slots = []
    for k, c in enumerate(target_counts):
        slots += [k] * int(c)
    # Priority by hours_left desc
    order = np.argsort([-d.hours_left for d in active])
    targets = [-1] * len(active)
    for i, didx in enumerate(order):
        targets[didx] = slots[i]
    return targets

# =========================
# Simulation core
# =========================
def simulate_once(
    df_rev: pd.DataFrame,
    n_clusters: int,
    n_drivers: int,
    time_horizon_hours: float,
    start_day: Optional[int],
    start_time: Optional[float],
    weather_scenario: Optional[str],
    model: str = 'saturation',
    alpha: float = DEFAULT_ALPHA,
    rng: Optional[np.random.Generator] = None
) -> Tuple[float, float]:
    """
    Returns (total_macro_recommendation, total_macro_random) over the horizon.
    Travel time = DT (0.5h). Drivers moving earn 0 in the travel slot, then arrive.
    By default: weather='clear', day is chosen randomly per simulation, start_time random per simulation.
    """
    if rng is None:
        rng = np.random.default_rng(RANDOM_SEED)

    # Scenario settings
    if start_day is None:
        day = int(rng.integers(0, 7))
    else:
        day = int(start_day) % 7
    if start_time is None:
        time_h = float(rng.uniform(0, 24))
    else:
        time_h = float(start_time) % 24.0
    weather = (weather_scenario or 'clear').strip().lower()

    # Initialize drivers
    drivers_rec = [Driver(cluster=int(rng.integers(0, n_clusters)), hours_left=float(rng.integers(1, 9)))
                   for _ in range(n_drivers)]
    drivers_rand = [Driver(cluster=d.cluster, hours_left=d.hours_left) for d in drivers_rec]

    total_rec = 0.0
    total_rand = 0.0

    steps = int(np.ceil(time_horizon_hours / DT))

    for _ in range(steps):
        # Revenues vector for current slot
        revenues_vec = expected_revenue_vector(df_rev, day, time_h, weather, n_clusters)

        # ----- Recommendation strategy -----
        active_rec = [d for d in drivers_rec if d.hours_left > 0]
        if active_rec:
            # Macro-optimal counts and assignment with hours-left priority
            counts = greedy_macro_allocation(len(active_rec), revenues_vec, model, alpha)
            targets = assign_recommendation(active_rec, counts)

            # Decide who moves; moving consumes DT and yields 0 this slot
            staying_clusters = []
            for d, tgt in zip(active_rec, targets):
                if int(tgt) == int(d.cluster):
                    staying_clusters.append(d.cluster)  # earns this slot
                else:
                    # moving: change cluster but only arrive next slot
                    d.cluster = int(tgt)

            if len(staying_clusters) > 0:
                staying_assignments = np.array(staying_clusters, dtype=int)
                total_rec += compute_macro(staying_assignments, revenues_vec, model, alpha)

            # decrement hours
            for d in active_rec:
                d.hours_left = max(0.0, d.hours_left - DT)

        # ----- Random strategy -----
        active_rand = [d for d in drivers_rand if d.hours_left > 0]
        if active_rand:
            staying_clusters_r = []
            for d in active_rand:
                tgt = int(rng.integers(0, n_clusters))
                if tgt == d.cluster:
                    staying_clusters_r.append(d.cluster)
                else:
                    d.cluster = tgt  # arrive next slot
            if len(staying_clusters_r) > 0:
                staying_assign_r = np.array(staying_clusters_r, dtype=int)
                total_rand += compute_macro(staying_assign_r, revenues_vec, model, alpha)
            for d in active_rand:
                d.hours_left = max(0.0, d.hours_left - DT)

        # advance clock
        time_h = (time_h + DT) % 24.0
        if abs(time_h) < 1e-9:  # wrapped around to ~0
            day = (day + 1) % 7

    return total_rec, total_rand

# =========================
# Experiment runner
# =========================
def run_experiment(
    df_rev: pd.DataFrame,
    n_clusters: Optional[int] = None,
    n_sim: int = 1000,
    n_drivers: int = DEFAULT_N_DRIVERS,
    time_horizon_hours: float = DEFAULT_TIME_HORIZON_HOURS,
    model: str = 'saturation',
    alpha: float = DEFAULT_ALPHA,
    start_day: Optional[int] = None,
    start_time: Optional[float] = None,
    weather_scenario: Optional[str] = "clear",   # DEFAULT: clear weather
    seed: int = RANDOM_SEED
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Repeats simulate_once n_sim times; returns (results_df, summary_df).
    By default, weather='clear', day and start time are randomized per simulation.
    """
    rng = np.random.default_rng(seed)
    if n_clusters is None:
        n_clusters = int(df_rev['cluster_id'].nunique()) if 'cluster_id' in df_rev.columns else DEFAULT_N_CLUSTERS

    rec_totals = np.zeros(n_sim)
    rand_totals = np.zeros(n_sim)
    for i in range(n_sim):
        r, u = simulate_once(
            df_rev=df_rev,
            n_clusters=n_clusters,
            n_drivers=n_drivers,
            time_horizon_hours=time_horizon_hours,
            start_day=start_day,          # None => random day per sim
            start_time=start_time,        # None => random time per sim
            weather_scenario=weather_scenario,  # default 'clear'
            model=model,
            alpha=alpha,
            rng=rng
        )
        rec_totals[i] = r
        rand_totals[i] = u

    results = pd.DataFrame({'rec_total': rec_totals, 'rand_total': rand_totals, 'diff': rec_totals - rand_totals})
    summary = pd.DataFrame({
        'Strategy': ['Recommendation', 'Random'],
        'Mean total revenue': [results['rec_total'].mean(), results['rand_total'].mean()],
        'Std total revenue': [results['rec_total'].std(ddof=1), results['rand_total'].std(ddof=1)]
    })
    return results, summary

# =========================
# Demo / CLI (optional)
# =========================
def _synthetic_revenue_table(n_clusters: int = DEFAULT_N_CLUSTERS) -> pd.DataFrame:
    """Create a simple synthetic table across all days, 24h at 1h granularity, one weather='clear'."""
    rows = []
    rng = np.random.default_rng(RANDOM_SEED)
    base = rng.uniform(8, 25, size=n_clusters)
    for day in range(7):
        for hour in range(24):
            for k in range(n_clusters):
                # add some day/time modulation
                tod_factor = 1.0 + 0.2 * np.sin((hour / 24.0) * 2*np.pi)
                day_factor = 1.0 + 0.1 * np.sin((day / 7.0) * 2*np.pi)
                rows.append({
                    'day': day,
                    'time': float(hour),
                    'weather': 'clear',
                    'cluster_id': k,
                    'expected_revenue': base[k] * tod_factor * day_factor
                })
    return pd.DataFrame(rows)

def _plot_histograms(results: pd.DataFrame) -> None:
    plt.figure()
    plt.hist(results['rand_total'], bins=30, alpha=0.6, label='Random')
    plt.hist(results['rec_total'], bins=30, alpha=0.6, label='Recommendation')
    plt.xlabel('Total revenue per simulation')
    plt.ylabel('Frequency')
    plt.title('Distribution of total revenue')
    plt.legend()
    plt.show()

    plt.figure()
    plt.hist(results['diff'], bins=30, alpha=0.8)
    plt.xlabel('Recommendation - Random (total revenue)')
    plt.ylabel('Frequency')
    plt.title('Revenue uplift per simulation')
    plt.show()

def main():
    # Optional local run: if an Excel named like your file is present, try to load it.
    default_path = Path('recommendation system based on revenue.xlsx')
    if default_path.exists():
        try:
            df_rev = load_revenue_table(str(default_path))
            print('Loaded revenue table from Excel.')
        except Exception as e:
            print(f'Could not parse provided Excel; using synthetic revenue table. Reason: {e}')
            df_rev = _synthetic_revenue_table()
    else:
        print('Excel not found; using synthetic revenue table.')
        df_rev = _synthetic_revenue_table()

    print(f'Rows in revenue table: {len(df_rev)}  | clusters: {df_rev["cluster_id"].nunique()}')

    # By default: weather='clear', random day/time per simulation
    results, summary = run_experiment(
        df_rev=df_rev,
        n_sim=500,
        n_drivers=30,
        time_horizon_hours=6.0,
        model="saturation",
        alpha=0.6,
        weather_scenario="clear",
        start_day=None,
        start_time=None
    )
    win_rate = (results["diff"] > 0).mean()
    uplift_pct = (results["rec_total"].mean() / results["rand_total"].mean() - 1) * 100.0
    print(summary)
    print(f"Win rate (rec > random): {win_rate:.2%}")
    print(f"Average uplift: {uplift_pct:.2f}%")
    _plot_histograms(results)
    results.to_csv('sim_results_with_day_time_weather.csv', index=False)
    print('Saved results: sim_results_with_day_time_weather.csv')

if __name__ == '__main__':
    main()
