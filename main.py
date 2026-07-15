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

# 1. ANALYZE MAINE SPECIFICALLY
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



# Create scatter plots: Spread vs Weather Variables
weather_vars = ["Temperature", "Humidity", "Dew Point", "Cloud Coverage"]

for zone_name in zones.keys():
    if zone_name == "Total":
        continue

    rt_df = zones[zone_name]["Real Time"]
    da_df = zones[zone_name]["Day Ahead"]

    # Calculate spreads
    spreads = rt_df.join(da_df, on="tstamp", suffix="_da").sort("tstamp").with_columns(
        spread=pl.col("demand") - pl.col("demand_da")
    )

    # Create subplots for each weather variable
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=weather_vars
    )

    for idx, weather_var in enumerate(weather_vars):
        row = (idx // 2) + 1
        col = (idx % 2) + 1

        # Get weather data
        weather_df = vars[zone_name][weather_var]

        # Join weather with spreads
        combined = spreads.join(weather_df, on="tstamp", suffix="_weather").sort("tstamp")

        # Get the weather column name (it should be the first non-tstamp column)
        weather_col = [c for c in weather_df.columns if c != "tstamp"][0]

        fig.add_trace(
            go.Scatter(
                x=combined[weather_col],
                y=combined["spread"],
                mode='markers',
                name=weather_var,
                marker=dict(size=4, opacity=0.6),
                text=combined["tstamp"],
                hovertemplate=f"<b>{weather_var}</b>: %{{x:.2f}}<br>Spread: %{{y:.2f}} MWh<br>Time: %{{text}}<extra></extra>"
            ),
            row=row, col=col
        )

        fig.update_xaxes(title_text=weather_var, row=row, col=col)
        fig.update_yaxes(title_text="Spread (MWh)", row=row, col=col)

    fig.update_layout(
        title=f"{zone_name}: Spread vs Weather Conditions",
        height=800,
        showlegend=False,
        template='plotly_white'
    )

    filename = f"spread_vs_weather_{zone_name.replace(' ', '_').replace('/', '_')}.html"
    fig.write_html(filename)
    print(f"Saved: {filename}")

# CORRELATION ANALYSIS: Which weather variable correlates most with spreads?
print("\n=== WEATHER CORRELATION WITH SPREADS ===")

for zone_name in zones.keys():
    if zone_name == "Total":
        continue

    rt_df = zones[zone_name]["Real Time"]
    da_df = zones[zone_name]["Day Ahead"]

    spreads = rt_df.join(da_df, on="tstamp", suffix="_da").sort("tstamp").with_columns(
        spread=pl.col("demand") - pl.col("demand_da")
    )

    print(f"\n{zone_name}:")

    for weather_var in weather_vars:
        weather_df = vars[zone_name][weather_var]
        weather_col = [c for c in weather_df.columns if c != "tstamp"][0]

        combined = spreads.join(weather_df, on="tstamp", suffix="_weather").sort("tstamp")

        correlation = combined.select(
            pl.corr("spread", weather_col)
        ).item()

        print(f"  {weather_var}: {correlation:.4f}")

# MAINE DEEP DIVE: Temperature Bins
print("\n=== MAINE DEEP DIVE: Temperature Bins ===")

maine_rt = zones["Maine"]["Real Time"]
maine_da = zones["Maine"]["Day Ahead"]
maine_spreads = maine_rt.join(maine_da, on="tstamp", suffix="_da").sort("tstamp").with_columns(
    spread=pl.col("demand") - pl.col("demand_da")
)

maine_temp_df = vars["Maine"]["Temperature"]
maine_temp_col = [c for c in maine_temp_df.columns if c != "tstamp"][0]

maine_combined = maine_spreads.join(maine_temp_df, on="tstamp", suffix="_weather").sort("tstamp").with_columns(
    temp_bin=pl.when(pl.col(maine_temp_col) < 32).then(pl.lit("<32°F"))
    .when(pl.col(maine_temp_col) < 50).then(pl.lit("32-50°F"))
    .when(pl.col(maine_temp_col) < 70).then(pl.lit("50-70°F"))
    .when(pl.col(maine_temp_col) < 90).then(pl.lit("70-90°F"))
    .otherwise(pl.lit(">90°F"))
)

temp_analysis = maine_combined.group_by("temp_bin").agg(
    pl.col("spread").mean().alias("avg_spread"),
    pl.col("spread").std().alias("std_spread"),
    pl.col("spread").count().alias("count")
).sort("temp_bin")

print(temp_analysis)

fig = go.Figure()
fig.add_trace(go.Bar(
    x=temp_analysis["temp_bin"],
    y=temp_analysis["avg_spread"],
    error_y=dict(type='data', array=temp_analysis["std_spread"]),
    marker_color='lightblue'
))
fig.update_layout(
    title="Maine: Average Spread by Temperature Range",
    xaxis_title="Temperature Range",
    yaxis_title="Average Spread (MWh)",
    template='plotly_white'
)
fig.write_html("maine_temperature_analysis.html")
print("Saved: maine_temperature_analysis.html")

# COMBINED HEATMAP: Hour of Day vs Temperature
print("\n=== MAINE: Hour vs Temperature Heatmap ===")

maine_combined_heatmap = maine_combined.with_columns(
    hour = pl.col("tstamp").dt.hour()
).group_by("hour", "temp_bin").agg(
    pl.col("spread").mean().alias("avg_spread")
)

heatmap_data = maine_combined_heatmap.pivot(index="hour", columns="temp_bin", values="avg_spread")

fig = go.Figure(data=go.Heatmap(
    z=heatmap_data.to_numpy(),
    x=heatmap_data.columns,
    y=heatmap_data["hour"],
    colorscale='RdBu'
))
fig.update_layout(
    title="Maine: Spread Heatmap (Hour of Day vs Temperature)",
    xaxis_title="Temperature Range",
    yaxis_title="Hour of Day",
    template='plotly_white'
)
fig.write_html("maine_heatmap_hour_temp.html")
print("Saved: maine_heatmap_hour_temp.html")
