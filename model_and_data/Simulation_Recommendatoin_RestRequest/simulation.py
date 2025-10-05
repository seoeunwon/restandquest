import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, PillowWriter
from dataclasses import dataclass

from taxi_macro_sim import (
    expected_revenue_vector,
    greedy_macro_allocation,
    compute_macro,
    Driver,
    DT,                  # 0.5 hour slot
    DEFAULT_ALPHA
)

def simulate_path_for_animation(
    df_rev, n_clusters, n_drivers=30, time_horizon_hours=6.0,
    start_day=None, start_time=None, weather="clear",
    model="saturation", alpha=DEFAULT_ALPHA, seed=123
):
    """
    Returns a dict with per-slot details for BOTH strategies:
      - 'T' = number of slots
      - For each strategy in {'rec','rand'}:
          'old_clusters' : list of length T; each is int array shape (n_drivers,) with cluster BEFORE decisions (start of slot)
          'new_clusters' : list of length T; each is int array shape (n_drivers,) with target cluster AFTER decisions
                           (drivers that stay have same old==new; movers will arrive next slot)
          'slot_revenue' : float array length T with macro revenue earned this slot (only stayers earn)
    """
    rng = np.random.default_rng(seed)

    # Scenario
    day  = int(rng.integers(0,7)) if start_day  is None else int(start_day) % 7
    time = float(rng.uniform(0,24)) if start_time is None else float(start_time) % 24.0
    weather = str(weather).lower().strip()

    # Drivers (same initial state for both strategies)
    drivers_rec  = [Driver(cluster=int(rng.integers(0, n_clusters)), hours_left=float(rng.integers(1,9))) for _ in range(n_drivers)]
    drivers_rand = [Driver(cluster=d.cluster, hours_left=d.hours_left) for d in drivers_rec]

    steps = int(np.ceil(time_horizon_hours / DT))
    rec_old, rec_new, rec_rev = [], [], []
    rnd_old, rnd_new, rnd_rev = [], [], []

    for _ in range(steps):
        R = expected_revenue_vector(df_rev, day, time, weather, n_clusters)

        # ---------- Recommendation ----------
        old_clusters_rec = np.array([d.cluster for d in drivers_rec], dtype=int)
        rec_old.append(old_clusters_rec.copy())

        active_idx = [i for i,d in enumerate(drivers_rec) if d.hours_left > 0]
        new_clusters_rec = old_clusters_rec.copy()
        slot_rev_rec = 0.0

        if active_idx:
            # target counts from greedy macro allocation
            counts = greedy_macro_allocation(len(active_idx), R, model, alpha)
            # build slots: list of target clusters by counts
            slots = []
            for k,c in enumerate(counts):
                slots += [k]*int(c)
            # sort active by hours_left (desc) = "move longest first"
            order = sorted(active_idx, key=lambda i: -drivers_rec[i].hours_left)
            # assign
            movers = []
            stayers = []
            for di, tgt in zip(order, slots):
                tgt = int(tgt)
                if drivers_rec[di].cluster == tgt:
                    stayers.append(di)
                else:
                    new_clusters_rec[di] = tgt
                    movers.append(di)

            # earn this slot: stayers only
            stay_clusters = np.array([drivers_rec[i].cluster for i in stayers], dtype=int)
            if len(stay_clusters) > 0:
                slot_rev_rec = compute_macro(stay_clusters, R, model, alpha)

            # decrement hours
            for i in active_idx:
                drivers_rec[i].hours_left = max(0.0, drivers_rec[i].hours_left - DT)

            # move: set cluster to target but arrival is next slot (we already set new_clusters_rec)
            for i in movers:
                drivers_rec[i].cluster = new_clusters_rec[i]

        rec_new.append(new_clusters_rec.copy())
        rec_rev.append(slot_rev_rec)

        # ---------- Random ----------
        old_clusters_rnd = np.array([d.cluster for d in drivers_rand], dtype=int)
        rnd_old.append(old_clusters_rnd.copy())

        active_idx_r = [i for i,d in enumerate(drivers_rand) if d.hours_left > 0]
        new_clusters_rnd = old_clusters_rnd.copy()
        slot_rev_rnd = 0.0

        if active_idx_r:
            movers_r = []
            stayers_r = []
            for i in active_idx_r:
                tgt = int(rng.integers(0, n_clusters))
                if tgt == drivers_rand[i].cluster:
                    stayers_r.append(i)
                else:
                    new_clusters_rnd[i] = tgt
                    movers_r.append(i)

            stay_clusters_r = np.array([drivers_rand[i].cluster for i in stayers_r], dtype=int)
            if len(stay_clusters_r) > 0:
                slot_rev_rnd = compute_macro(stay_clusters_r, R, model, alpha)

            for i in active_idx_r:
                drivers_rand[i].hours_left = max(0.0, drivers_rand[i].hours_left - DT)

            for i in movers_r:
                drivers_rand[i].cluster = new_clusters_rnd[i]

        rnd_new.append(new_clusters_rnd.copy())
        rnd_rev.append(slot_rev_rnd)

        # advance 30 minutes
        time = (time + DT) % 24.0
        if abs(time) < 1e-9:
            day = (day + 1) % 7

    return {
        "T": steps,
        "rec": {"old_clusters": rec_old, "new_clusters": rec_new, "slot_revenue": np.array(rec_rev)},
        "rnd": {"old_clusters": rnd_old, "new_clusters": rnd_new, "slot_revenue": np.array(rnd_rev)},
        "dt": DT
    }
