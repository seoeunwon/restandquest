# Ensure df_ready has 'time' (you already renamed from 'hour' above)
# df_ready = df_ready.rename(columns={'hour':'time'})   # if needed

K = int(df_ready['cluster_id'].nunique())

# One 6-hour animation (Recommendation vs Random)
trace = simulate_path_for_animation(
    df_rev=df_ready, n_clusters=K, n_drivers=30, time_horizon_hours=6.0,
    start_day=None, start_time=None, weather="clear",
    model="saturation", alpha=0.6, seed=7
)
anim = animate_paths(trace, n_clusters=K, title="Taxi moves (6h) — Macro Rec vs Random",
                     save_mp4="taxi_sim.mp4", save_gif="taxi_sim.gif")

# (Optional) a second different run
trace2 = simulate_path_for_animation(
    df_rev=df_ready, n_clusters=K, n_drivers=30, time_horizon_hours=6.0,
    start_day=None, start_time=None, weather="clear",
    model="saturation", alpha=0.6, seed=42
)
anim2 = animate_paths(trace2, n_clusters=K, title="Taxi moves (6h) — Run #2",
                      save_mp4="taxi_sim_run2.mp4", save_gif="taxi_sim_run2.gif")
