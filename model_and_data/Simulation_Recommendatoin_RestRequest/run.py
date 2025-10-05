import pandas as pd

data_path = "/content/recommendation system based on revenue.xlsx"  # adjust if needed

# 1) Load and normalize headers
df_raw = pd.read_excel(data_path)
df_raw.columns = [str(c).strip().lower() for c in df_raw.columns]

# 2) Drop Excel index-like columns
df_raw = df_raw.drop(columns=[c for c in df_raw.columns if c.startswith('unnamed:')], errors='ignore')

# 3) Detect cluster columns (digit-named)
cluster_cols = [c for c in df_raw.columns if str(c).isdigit()]
if not cluster_cols:
    raise ValueError(f"Couldn't find digit-named cluster columns. Found columns: {list(df_raw.columns)}")

# 4) Ensure required id columns exist
for need in ['day', 'hour']:
    if need not in df_raw.columns:
        raise ValueError(f"Missing required column '{need}' in the Excel file.")

# If weather is missing, default to 'clear'
if 'weather' not in df_raw.columns:
    df_raw['weather'] = 'clear'

# 5) Melt to long format: (day, time, weather, cluster, expected_revenue)
df_long = df_raw.melt(
    id_vars=['day', 'hour', 'weather'],
    value_vars=cluster_cols,
    var_name='cluster',
    value_name='expected_revenue'
)

# 6) Clean types and build the standardized dataframe for the simulator
df_long['day'] = df_long['day'].astype(int)
df_long['hour'] = df_long['hour'].astype(float) 
df_long['weather'] = df_long['weather'].astype(str).str.strip().str.lower()
df_long['cluster_id'] = df_long['cluster'].astype(int)
df_long['expected_revenue'] = pd.to_numeric(df_long['expected_revenue'], errors='coerce').fillna(0.0)

# FINAL dataset the simulator needs:
df_ready = df_long[['day','hour','weather','cluster_id','expected_revenue']].copy()
df_ready.head()
