#######################################################################################################################
# Imports #
#######################################################################################################################
import sys
from datetime import datetime, timedelta
from features import loadsave as ls
from features import graphs as gphs
import polars as pl
import plotly.graph_objects as go
from plotly.subplots import make_subplots

#######################################################################################################################
# Data Import #
#######################################################################################################################

# Define start and end time
t1 = datetime(2020, 1, 1, 0)
t2 = datetime(2025, 1, 1, 0)

# Load in zones
zones = ls.load_zones(t1, t2)

# Load in variables.
vars = ls.load_vars(t1, t2)

#######################################################################################################################
# Data Import #
#######################################################################################################################
#gphs.plot_spreads(zones)

# 1. ANALYZE MAINE SPECIFICALLY - Why is it so different?
print("=== DEEP DIVE: MAINE ===")
maine_rt = zones["Maine"]["Real Time"]
maine_da = zones["Maine"]["Day Ahead"]

maine_combined = maine_rt.join(maine_da, on="tstamp", suffix="_da").sort("tstamp").with_columns(
    spread=pl.col("demand") - pl.col("demand_da"),
    hour=pl.col("tstamp").dt.hour(),
    day_of_week=pl.col("tstamp").dt.weekday()
)

# By hour
hourly_maine = maine_combined.group_by("hour").agg(
    pl.col("spread").mean().alias("avg_spread"),
    pl.col("spread").std().alias("std_spread")
).sort("hour")
print("\nMaine spreads by hour:")
print(hourly_maine)

# By day of week
daily_maine = maine_combined.group_by("day_of_week").agg(
    pl.col("spread").mean().alias("avg_spread")
).sort("day_of_week")
print("\nMaine spreads by day of week (0=Mon, 6=Sun):")
print(daily_maine)

# 2. COMPARE ALL ZONES - Which are most predictable?
print("\n=== PREDICTABILITY RANKING ===")
predictability = []

for zone_name, zone_data in zones.items():
    rt_df = zone_data["Real Time"]
    da_df = zone_data["Day Ahead"]

    combined = rt_df.join(da_df, on="tstamp", suffix="_da").with_columns(
        spread=pl.col("demand") - pl.col("demand_da")
    )

    avg_spread = combined["spread"].mean()
    spread_volatility = combined["spread"].std()

    predictability.append({
        "zone": zone_name,
        "avg_spread": avg_spread,
        "spread_volatility": spread_volatility,
        "abs_avg_spread": abs(avg_spread)
    })

pred_df = pl.DataFrame(predictability).sort("spread_volatility", descending=True)
print(pred_df)

# 3. PLOT: Spread volatility vs average spread
fig = go.Figure()
fig.add_trace(go.Scatter(
    x=pred_df["avg_spread"],
    y=pred_df["spread_volatility"],
    mode='markers+text',
    text=pred_df["zone"],
    textposition="top center",
    marker=dict(size=12, color=pred_df["spread_volatility"], colorscale='Viridis')
))
fig.update_layout(
    title="Zone Predictability: Average Spread vs Spread Volatility",
    xaxis_title="Average Spread (RT - DA)",
    yaxis_title="Spread Volatility (Std Dev)",
    template='plotly_white',
    height=600
)
fig.write_html("predictability_analysis.html")
print("\nSaved: predictability_analysis.html")

# 4. CORRELATION: Does higher RT volatility = higher spreads?
print("\n=== CORRELATION ANALYSIS ===")
for zone_name, zone_data in zones.items():
    rt_vol = zone_data["Real Time"]["demand"].std()
    da_vol = zone_data["Day Ahead"]["demand"].std()

    rt_df = zone_data["Real Time"]
    da_df = zone_data["Day Ahead"]

    combined = rt_df.join(da_df, on="tstamp", suffix="_da").with_columns(
        spread=pl.col("demand") - pl.col("demand_da")
    )

    avg_spread = combined["spread"].mean()

    print(f"{zone_name}:")
    print(f"  RT Vol: {rt_vol:.2f}, DA Vol: {da_vol:.2f}, Vol Diff: {rt_vol - da_vol:.2f}")
    print(f"  Avg Spread: {avg_spread:.2f}")

# Create subplots for Maine analysis
fig = make_subplots(
    rows=2, cols=2,
    subplot_titles=("Maine: Hourly Spread Pattern",
                    "Maine: Day of Week Pattern",
                    "All Zones: Spread Comparison",
                    "Volatility vs Spread Bias")
)

# 1. Maine hourly
maine_rt = zones["Maine"]["Real Time"]
maine_da = zones["Maine"]["Day Ahead"]
maine_combined = maine_rt.join(maine_da, on="tstamp", suffix="_da").sort("tstamp").with_columns(
    spread = pl.col("demand") - pl.col("demand_da"),
    hour = pl.col("tstamp").dt.hour()
)
hourly = maine_combined.group_by("hour").agg(pl.col("spread").mean()).sort("hour")

fig.add_trace(
    go.Scatter(x=hourly["hour"], y=hourly["spread"], mode='lines+markers', name='Maine Hourly'),
    row=1, col=1
)

# 2. Maine daily
daily = maine_combined.group_by(pl.col("tstamp").dt.date()).agg(pl.col("spread").mean()).sort("tstamp")
fig.add_trace(
    go.Scatter(x=daily["tstamp"], y=daily["spread"], mode='lines', name='Maine Daily'),
    row=1, col=2
)

# 3. All zones comparison
zone_spreads = []
zone_names = []
for zone_name, zone_data in zones.items():
    rt_df = zone_data["Real Time"]
    da_df = zone_data["Day Ahead"]
    combined = rt_df.join(da_df, on="tstamp", suffix="_da").with_columns(
        spread = pl.col("demand") - pl.col("demand_da")
    )
    zone_spreads.append(combined["spread"].mean())
    zone_names.append(zone_name)

fig.add_trace(
    go.Bar(x=zone_names, y=zone_spreads, marker_color=['red' if x > 0 else 'green' for x in zone_spreads]),
    row=2, col=1
)

fig.update_xaxes(title_text="Hour of Day", row=1, col=1)
fig.update_yaxes(title_text="Spread (MWh)", row=1, col=1)
fig.update_xaxes(title_text="Date", row=1, col=2)
fig.update_yaxes(title_text="Spread (MWh)", row=1, col=2)
fig.update_xaxes(title_text="Zone", row=2, col=1)
fig.update_yaxes(title_text="Avg Spread (MWh)", row=2, col=1)

fig.update_layout(height=800, showlegend=False, title_text="Maine Demand Forecast Analysis")
fig.write_html("maine_deep_dive.html")
print("Saved: maine_deep_dive.html")