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

import polars as pl
import plotly.graph_objects as go
from plotly.subplots import make_subplots

zones = ls.load_zones(t1, t2)

# A. DEMAND FORECAST ACCURACY
print("=== DEMAND FORECAST ACCURACY ===")
for zone_name in zones.keys():
    rt_df = zones[zone_name]["Real Time"]
    da_df = zones[zone_name]["Day Ahead"]

    combined = rt_df.join(da_df, on="tstamp", suffix="_da").with_columns(
        error=pl.col("demand") - pl.col("demand_da"),
        pct_error=((pl.col("demand") - pl.col("demand_da")) / pl.col("demand_da") * 100)
    )

    mae = combined["error"].abs().mean()  # Mean Absolute Error
    mape = combined["pct_error"].abs().mean()  # Mean Absolute Percentage Error

    print(f"{zone_name}: MAE={mae:.2f} MWh, MAPE={mape:.2f}%")

# B. TIME-OF-DAY PATTERNS
print("\n=== SPREADS BY TIME OF DAY ===")
for zone_name in zones.keys():
    if zone_name == "Total":
        continue

    rt_df = zones[zone_name]["Real Time"]
    da_df = zones[zone_name]["Day Ahead"]

    combined = rt_df.join(da_df, on="tstamp", suffix="_da").sort("tstamp").with_columns(
        spread=pl.col("demand") - pl.col("demand_da"),
        hour=pl.col("tstamp").dt.hour()
    )

    # Peak hours (8am-10pm) vs Off-peak
    peak = combined.filter((pl.col("hour") >= 8) & (pl.col("hour") <= 22))
    offpeak = combined.filter(~((pl.col("hour") >= 8) & (pl.col("hour") <= 22)))

    print(f"\n{zone_name}:")
    print(f"  Peak hours (8am-10pm): {peak['spread'].mean():.2f} MWh")
    print(f"  Off-peak: {offpeak['spread'].mean():.2f} MWh")

# C. SEASONAL PATTERNS
print("\n=== SPREADS BY SEASON ===")
for zone_name in zones.keys():
    if zone_name == "Total":
        continue

    rt_df = zones[zone_name]["Real Time"]
    da_df = zones[zone_name]["Day Ahead"]

    combined = rt_df.join(da_df, on="tstamp", suffix="_da").sort("tstamp").with_columns(
        spread=pl.col("demand") - pl.col("demand_da"),
        month=pl.col("tstamp").dt.month()
    )

    print(f"\n{zone_name}:")
    for month in range(1, 13):
        month_data = combined.filter(pl.col("month") == month)
        if len(month_data) > 0:
            print(f"  Month {month}: {month_data['spread'].mean():.2f} MWh")

# D. WEATHER CORRELATION (You already have this)
print("\n=== WEATHER IMPACT ON SPREADS ===")
weather_vars = ["Temperature", "Humidity", "Dew Point"]

for zone_name in zones.keys():
    if zone_name == "Total":
        continue

    rt_df = zones[zone_name]["Real Time"]
    da_df = zones[zone_name]["Day Ahead"]

    combined = rt_df.join(da_df, on="tstamp", suffix="_da").sort("tstamp").with_columns(
        spread=pl.col("demand") - pl.col("demand_da")
    )

    print(f"\n{zone_name}:")
    for weather_var in weather_vars:
        if weather_var in vars[zone_name]:
            weather_df = vars[zone_name][weather_var]
            weather_col = [c for c in weather_df.columns if c != "tstamp"][0]

            combined_weather = combined.join(weather_df, on="tstamp", suffix="_weather").sort("tstamp")

            correlation = combined_weather.select(
                pl.corr("spread", weather_col)
            ).item()

            print(f"  {weather_var}: {correlation:.4f}")

# E. EXTREME EVENTS
print("\n=== EXTREME SPREADS ===")
for zone_name in zones.keys():
    rt_df = zones[zone_name]["Real Time"]
    da_df = zones[zone_name]["Day Ahead"]

    combined = rt_df.join(da_df, on="tstamp", suffix="_da").sort("tstamp").with_columns(
        spread=pl.col("demand") - pl.col("demand_da")
    )

    top_spreads = combined.sort("spread", descending=True).head(5)

    print(f"\n{zone_name} - Top 5 Largest Spreads:")
    print(top_spreads.select(["tstamp", "spread"]))

# Heatmap: Hour vs Day of Week
fig = go.Figure()

for zone_name in zones.keys():
    if zone_name == "Total":
        continue

    rt_df = zones[zone_name]["Real Time"]
    da_df = zones[zone_name]["Day Ahead"]

    combined = rt_df.join(da_df, on="tstamp", suffix="_da").sort("tstamp").with_columns(
        spread=pl.col("demand") - pl.col("demand_da"),
        hour=pl.col("tstamp").dt.hour(),
        day_of_week=pl.col("tstamp").dt.weekday()
    ).group_by("hour", "day_of_week").agg(
        pl.col("spread").mean().alias("avg_spread")
    )

    heatmap_data = combined.pivot(index="hour", columns="day_of_week", values="avg_spread")

    fig.add_trace(go.Heatmap(
        z=heatmap_data.to_numpy(),
        x=["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
        y=heatmap_data["hour"],
        name=zone_name,
        colorscale='RdBu'
    ))

fig.update_layout(
    title="Spreads: Hour of Day vs Day of Week",
    xaxis_title="Day of Week",
    yaxis_title="Hour of Day",
    template='plotly_white'
)
fig.write_html("spreads_hour_dayofweek.html")
print("Saved: spreads_hour_dayofweek.html")

import polars as pl
import plotly.graph_objects as go
from plotly.subplots import make_subplots

zones = ls.load_zones(t1, t2)

# ============================================================================
# SECTION 1: EXECUTIVE SUMMARY
# ============================================================================
print("=" * 80)
print("REAL-TIME vs DAY-AHEAD MARKET ANALYSIS")
print("=" * 80)

print("\n1. OVERVIEW: Which Market is Better to Buy From?")
print("-" * 80)

for zone_name in zones.keys():
    rt_df = zones[zone_name]["Real Time"]
    da_df = zones[zone_name]["Day Ahead"]

    # Assuming you have price data - if not, use demand as proxy
    rt_avg = rt_df["demand"].mean()
    da_avg = da_df["demand"].mean()

    rt_vol = rt_df["demand"].std()
    da_vol = da_df["demand"].std()

    spread = rt_avg - da_avg
    spread_pct = (spread / da_avg * 100) if da_avg != 0 else 0

    # Determine which is better
    if spread > 0:
        better = "DAY-AHEAD (cheaper)"
        reason = "RT is higher"
    else:
        better = "REAL-TIME (cheaper)"
        reason = "DA is higher"

    print(f"\n{zone_name}:")
    print(f"  Average RT: {rt_avg:.2f}")
    print(f"  Average DA: {da_avg:.2f}")
    print(f"  Spread (RT - DA): {spread:.2f} ({spread_pct:+.2f}%)")
    print(f"  ➜ Better to buy: {better}")
    print(f"  ➜ Volatility - RT: {rt_vol:.2f}, DA: {da_vol:.2f}")
    print(
        f"  ➜ Risk Level: {'HIGH' if rt_vol > da_vol else 'LOW'} (RT {'more' if rt_vol > da_vol else 'less'} volatile)")

# ============================================================================
# SECTION 2: DETAILED ANALYSIS BY ZONE
# ============================================================================
print("\n\n2. DETAILED ZONE ANALYSIS")
print("-" * 80)

zone_summary = []

for zone_name in zones.keys():
    if zone_name == "Total":
        continue

    rt_df = zones[zone_name]["Real Time"]
    da_df = zones[zone_name]["Day Ahead"]

    combined = rt_df.join(da_df, on="tstamp", suffix="_da").sort("tstamp").with_columns(
        spread=pl.col("demand") - pl.col("demand_da")
    )

    avg_spread = combined["spread"].mean()
    spread_vol = combined["spread"].std()
    max_spread = combined["spread"].max()
    min_spread = combined["spread"].min()

    # Calculate how often RT is cheaper
    rt_cheaper_pct = (combined.filter(pl.col("spread") < 0).height / combined.height * 100)

    zone_summary.append({
        "zone": zone_name,
        "avg_spread": avg_spread,
        "spread_vol": spread_vol,
        "max_spread": max_spread,
        "min_spread": min_spread,
        "rt_cheaper_pct": rt_cheaper_pct
    })

    print(f"\n{zone_name}:")
    print(f"  Average Spread (RT - DA): {avg_spread:+.2f}")
    print(f"  Spread Volatility: {spread_vol:.2f}")
    print(f"  Max Spread: {max_spread:+.2f}")
    print(f"  Min Spread: {min_spread:+.2f}")
    print(f"  RT is cheaper {rt_cheaper_pct:.1f}% of the time")

    if avg_spread > 0:
        print(f"  ✓ RECOMMENDATION: Buy from DAY-AHEAD market")
        print(f"    - Save ~{avg_spread:.2f} on average")
        print(f"    - Less volatile (more predictable)")
    else:
        print(f"  ✓ RECOMMENDATION: Buy from REAL-TIME market")
        print(f"    - Save ~{abs(avg_spread):.2f} on average")

# ============================================================================
# SECTION 3: WHEN TO BUY FROM EACH MARKET
# ============================================================================
print("\n\n3. OPTIMAL BUYING STRATEGY BY TIME")
print("-" * 80)

for zone_name in zones.keys():
    if zone_name == "Total":
        continue

    rt_df = zones[zone_name]["Real Time"]
    da_df = zones[zone_name]["Day Ahead"]

    combined = rt_df.join(da_df, on="tstamp", suffix="_da").sort("tstamp").with_columns(
        spread=pl.col("demand") - pl.col("demand_da"),
        hour=pl.col("tstamp").dt.hour()
    )

    hourly = combined.group_by("hour").agg(
        pl.col("spread").mean().alias("avg_spread")
    ).sort("hour")

    print(f"\n{zone_name}:")
    print("  Hour | Avg Spread | Better Market")
    print("  -----|------------|---------------")

    for row in hourly.iter_rows(named=True):
        hour = int(row["hour"])
        spread = row["avg_spread"]
        market = "DA" if spread > 0 else "RT"
        print(f"  {hour:2d}:00 | {spread:+8.2f}   | {market}")

# ============================================================================
# SECTION 4: RISK ANALYSIS
# ============================================================================
print("\n\n4. RISK ANALYSIS: Price Volatility")
print("-" * 80)

for zone_name in zones.keys():
    rt_df = zones[zone_name]["Real Time"]
    da_df = zones[zone_name]["Day Ahead"]

    rt_vol = rt_df["demand"].std()
    da_vol = da_df["demand"].std()
    vol_diff = rt_vol - da_vol

    print(f"\n{zone_name}:")
    print(f"  RT Volatility: {rt_vol:.2f}")
    print(f"  DA Volatility: {da_vol:.2f}")
    print(f"  Difference: {vol_diff:+.2f}")

    if vol_diff > 0:
        print(f"  ⚠️  RT is {(vol_diff / da_vol * 100):.1f}% MORE volatile")
        print(f"  → DA market is SAFER (more predictable prices)")
    else:
        print(f"  ✓ RT is {(abs(vol_diff) / rt_vol * 100):.1f}% LESS volatile")
        print(f"  → RT market is SAFER (more predictable prices)")

# ============================================================================
# SECTION 5: VISUALIZATIONS
# ============================================================================

# Chart 1: Average Spread by Zone
zone_df = pl.DataFrame(zone_summary)
fig1 = go.Figure()
fig1.add_trace(go.Bar(
    x=zone_df["zone"],
    y=zone_df["avg_spread"],
    marker_color=['red' if x > 0 else 'green' for x in zone_df["avg_spread"]],
    text=[f"{x:+.1f}" for x in zone_df["avg_spread"]],
    textposition="auto"
))
fig1.update_layout(
    title="Average Spread by Zone (RT - DA)<br><sub>Red = Buy DA, Green = Buy RT</sub>",
    xaxis_title="Zone",
    yaxis_title="Average Spread",
    template='plotly_white',
    height=600
)
fig1.write_html("01_average_spread_by_zone.html")
print("\nSaved: 01_average_spread_by_zone.html")

# Chart 2: Spread Volatility (Risk)
fig2 = go.Figure()
fig2.add_trace(go.Bar(
    x=zone_df["zone"],
    y=zone_df["spread_vol"],
    marker_color='orange'
))
fig2.update_layout(
    title="Spread Volatility by Zone<br><sub>Higher = More Unpredictable</sub>",
    xaxis_title="Zone",
    yaxis_title="Spread Volatility (Std Dev)",
    template='plotly_white',
    height=600
)
fig2.write_html("02_spread_volatility.html")
print("Saved: 02_spread_volatility.html")

# Chart 3: Hourly Pattern - When to Buy
fig3 = make_subplots(
    rows=3, cols=3,
    subplot_titles=[z for z in zones.keys() if z != "Total"]
)

row, col = 1, 1
for zone_name in zones.keys():
    if zone_name == "Total":
        continue

    rt_df = zones[zone_name]["Real Time"]
    da_df = zones[zone_name]["Day Ahead"]

    combined = rt_df.join(da_df, on="tstamp", suffix="_da").sort("tstamp").with_columns(
        spread=pl.col("demand") - pl.col("demand_da"),
        hour=pl.col("tstamp").dt.hour()
    )

    hourly = combined.group_by("hour").agg(
        pl.col("spread").mean().alias("avg_spread")
    ).sort("hour")

    fig3.add_trace(
        go.Scatter(
            x=hourly["hour"],
            y=hourly["avg_spread"],
            mode='lines+markers',
            name=zone_name,
            fill='tozeroy'
        ),
        row=row, col=col
    )

    col += 1
    if col > 3:
        col = 1
        row += 1

fig3.update_layout(
    title="Hourly Spread Pattern: When to Buy Each Market",
    height=900,
    showlegend=False,
    template='plotly_white'
)
fig3.write_html("03_hourly_patterns.html")
print("Saved: 03_hourly_patterns.html")

# ============================================================================
# SECTION 6: FINAL RECOMMENDATIONS
# ============================================================================
print("\n\n6. FINAL RECOMMENDATIONS")
print("=" * 80)

print("\n📊 OVERALL STRATEGY:")
print("-" * 80)

total_rt = zones["Total"]["Real Time"]
total_da = zones["Total"]["Day Ahead"]
total_combined = total_rt.join(total_da, on="tstamp", suffix="_da").with_columns(
    spread=pl.col("demand") - pl.col("demand_da")
)

total_avg_spread = total_combined["spread"].mean()
total_vol = total_combined["spread"].std()

print(f"\nISO-WIDE AVERAGE SPREAD: {total_avg_spread:+.2f}")
print(f"SPREAD VOLATILITY: {total_vol:.2f}")

if total_avg_spread > 0:
    print(f"\n✓ PRIMARY RECOMMENDATION: Buy from DAY-AHEAD market")
    print(f"  - Saves approximately {total_avg_spread:.2f} on average")
    print(f"  - More predictable pricing")
    print(f"  - Lower volatility = lower risk")
else:
    print(f"\n✓ PRIMARY RECOMMENDATION: Buy from REAL-TIME market")
    print(f"  - Saves approximately {abs(total_avg_spread):.2f} on average")
    print(f"  - More predictable pricing")

print(f"\n⚠️  RISK CONSIDERATIONS:")
print(
    f"  - RT market is {((total_rt['demand'].std() - total_da['demand'].std()) / total_da['demand'].std() * 100):.1f}% more volatile")
print(f"  - Consider hedging strategies for high-volatility periods")

print(f"\n🎯 ZONE-SPECIFIC STRATEGIES:")
for zone_name in zones.keys():
    if zone_name == "Total":
        continue

    rt_df = zones[zone_name]["Real Time"]
    da_df = zones[zone_name]["Day Ahead"]

    combined = rt_df.join(da_df, on="tstamp", suffix="_da").with_columns(
        spread=pl.col("demand") - pl.col("demand_da")
    )

    avg_spread = combined["spread"].mean()

    if abs(avg_spread) > 50:
        market = "DAY-AHEAD" if avg_spread > 0 else "REAL-TIME"
        print(f"  - {zone_name}: Strong preference for {market} ({abs(avg_spread):.1f} savings)")
    elif abs(avg_spread) > 20:
        market = "DAY-AHEAD" if avg_spread > 0 else "REAL-TIME"
        print(f"  - {zone_name}: Moderate preference for {market} ({abs(avg_spread):.1f} savings)")
    else:
        print(f"  - {zone_name}: Markets are similar (use other factors)")

print("\n" + "=" * 80)

# ============================================================================
# EXECUTIVE SUMMARY
# ============================================================================
print("\n" + "=" * 80)
print("REAL-TIME vs DAY-AHEAD MARKET ANALYSIS - EXECUTIVE SUMMARY")
print("=" * 80)

total_rt = zones["Total"]["Real Time"]
total_da = zones["Total"]["Day Ahead"]
total_combined = total_rt.join(total_da, on="tstamp", suffix="_da").with_columns(
    spread=pl.col("demand") - pl.col("demand_da")
)

total_avg_spread = total_combined["spread"].mean()
total_rt_vol = total_rt["demand"].std()
total_da_vol = total_da["demand"].std()

print(f"\n📊 ISO-WIDE METRICS:")
print(f"   Average RT Level: {total_rt['demand'].mean():.2f}")
print(f"   Average DA Level: {total_da['demand'].mean():.2f}")
print(f"   Average Spread (RT - DA): {total_avg_spread:+.2f}")
print(f"   Spread as % of DA: {(total_avg_spread / total_da['demand'].mean() * 100):+.2f}%")

if total_avg_spread > 0:
    print(f"\n✅ RECOMMENDATION: Buy from DAY-AHEAD market")
    print(f"   💰 Potential Savings: {total_avg_spread:.2f} per hour on average")
    print(f"   📈 Annual Savings Estimate: {total_avg_spread * 24 * 365:,.0f}")
else:
    print(f"\n✅ RECOMMENDATION: Buy from REAL-TIME market")
    print(f"   💰 Potential Savings: {abs(total_avg_spread):.2f} per hour on average")
    print(f"   📈 Annual Savings Estimate: {abs(total_avg_spread) * 24 * 365:,.0f}")

print(f"\n⚠️  VOLATILITY RISK:")
print(f"   RT Volatility: {total_rt_vol:.2f}")
print(f"   DA Volatility: {total_da_vol:.2f}")
print(f"   RT is {((total_rt_vol - total_da_vol) / total_da_vol * 100):.1f}% more volatile")

# ============================================================================
# DETAILED ANALYSIS - ZONE BY ZONE
# ============================================================================
print("\n\n" + "=" * 80)
print("DETAILED ANALYSIS - ZONE BY ZONE")
print("=" * 80)

zone_data = []

for zone_name in zones.keys():
    if zone_name == "Total":
        continue

    rt_df = zones[zone_name]["Real Time"]
    da_df = zones[zone_name]["Day Ahead"]

    combined = rt_df.join(da_df, on="tstamp", suffix="_da").sort("tstamp").with_columns(
        spread=pl.col("demand") - pl.col("demand_da")
    )

    avg_spread = combined["spread"].mean()
    spread_vol = combined["spread"].std()
    max_spread = combined["spread"].max()
    min_spread = combined["spread"].min()
    rt_cheaper_pct = (combined.filter(pl.col("spread") < 0).height / combined.height * 100)

    rt_vol = rt_df["demand"].std()
    da_vol = da_df["demand"].std()

    zone_data.append({
        "zone": zone_name,
        "avg_spread": avg_spread,
        "spread_vol": spread_vol,
        "max_spread": max_spread,
        "min_spread": min_spread,
        "rt_cheaper_pct": rt_cheaper_pct,
        "rt_vol": rt_vol,
        "da_vol": da_vol
    })

    print(f"\n{zone_name}")
    print("-" * 80)
    print(f"  Average Spread (RT - DA): {avg_spread:+.2f}")
    print(f"  Spread Range: {min_spread:+.2f} to {max_spread:+.2f}")
    print(f"  Spread Volatility: {spread_vol:.2f}")
    print(f"  RT cheaper {rt_cheaper_pct:.1f}% of the time")

    if avg_spread > 50:
        print(f"  ✅ STRONG: Buy from DAY-AHEAD (save {avg_spread:.2f})")
    elif avg_spread > 20:
        print(f"  ✓ MODERATE: Prefer DAY-AHEAD (save {avg_spread:.2f})")
    elif avg_spread < -50:
        print(f"  ✅ STRONG: Buy from REAL-TIME (save {abs(avg_spread):.2f})")
    elif avg_spread < -20:
        print(f"  ✓ MODERATE: Prefer REAL-TIME (save {abs(avg_spread):.2f})")
    else:
        print(f"  ≈ NEUTRAL: Markets are similar")

# ============================================================================
# TIMING STRATEGY - WHEN TO BUY EACH MARKET
# ============================================================================
print("\n\n" + "=" * 80)
print("TIMING STRATEGY - WHEN TO BUY EACH MARKET")
print("=" * 80)

for zone_name in zones.keys():
    if zone_name == "Total":
        continue

    rt_df = zones[zone_name]["Real Time"]
    da_df = zones[zone_name]["Day Ahead"]

    combined = rt_df.join(da_df, on="tstamp", suffix="_da").sort("tstamp").with_columns(
        spread=pl.col("demand") - pl.col("demand_da"),
        hour=pl.col("tstamp").dt.hour()
    )

    hourly = combined.group_by("hour").agg(
        pl.col("spread").mean().alias("avg_spread"),
        pl.col("spread").std().alias("std_spread")
    ).sort("hour")

    print(f"\n{zone_name}")
    print("-" * 80)
    print("  Hour | Avg Spread | Better Market | Confidence")
    print("  -----|------------|---------------|------------")

    for row in hourly.iter_rows(named=True):
        hour = int(row["hour"])
        spread = row["avg_spread"]
        std = row["std_spread"]
        market = "DA" if spread > 0 else "RT"
        confidence = "HIGH" if abs(spread) > std else "MEDIUM"

        print(f"  {hour:2d}:00 | {spread:+8.2f}   | {market:13s} | {confidence}")

# ============================================================================
# RISK ANALYSIS - VOLATILITY COMPARISON
# ============================================================================
print("\n\n" + "=" * 80)
print("RISK ANALYSIS - VOLATILITY COMPARISON")
print("=" * 80)

zone_df = pl.DataFrame(zone_data)

print("\nZone Volatility Ranking (Higher = More Risk):")
print("-" * 80)

vol_ranking = zone_df.with_columns(
    vol_diff=pl.col("rt_vol") - pl.col("da_vol")
).sort("vol_diff", descending=True)

for idx, row in enumerate(vol_ranking.iter_rows(named=True), 1):
    zone = row["zone"]
    rt_vol = row["rt_vol"]
    da_vol = row["da_vol"]
    vol_diff = row["vol_diff"]
    pct_diff = (vol_diff / da_vol * 100)

    print(f"{idx}. {zone:30s} | RT: {rt_vol:7.2f} | DA: {da_vol:7.2f} | Diff: {vol_diff:+7.2f} ({pct_diff:+.1f}%)")

# ============================================================================
# VISUALIZATIONS
# ============================================================================
print("\n\n" + "=" * 80)
print("GENERATING VISUALIZATIONS")
print("=" * 80)

# Chart 1: Average Spread by Zone
fig1 = go.Figure()
fig1.add_trace(go.Bar(
    x=zone_df["zone"],
    y=zone_df["avg_spread"],
    marker_color=['#d62728' if x > 0 else '#2ca02c' for x in zone_df["avg_spread"]],
    text=[f"{x:+.1f}" for x in zone_df["avg_spread"]],
    textposition="auto",
    hovertemplate="<b>%{x}</b><br>Avg Spread: %{y:+.2f}<extra></extra>"
))
fig1.update_layout(
    title="Average Spread by Zone (RT - DA)<br><span style='font-size:12px'>Red = Buy DA (cheaper), Green = Buy RT (cheaper)</span>",
    xaxis_title="Zone",
    yaxis_title="Average Spread",
    template='plotly_white',
    height=600,
    hovermode='x unified'
)
fig1.write_html("01_average_spread_by_zone.html")
print("✓ Saved: 01_average_spread_by_zone.html")

# Chart 2: Spread Volatility (Risk)
fig2 = go.Figure()
fig2.add_trace(go.Bar(
    x=zone_df["zone"],
    y=zone_df["spread_vol"],
    marker_color='#ff7f0e',
    text=[f"{x:.1f}" for x in zone_df["spread_vol"]],
    textposition="auto",
    hovertemplate="<b>%{x}</b><br>Volatility: %{y:.2f}<extra></extra>"
))
fig2.update_layout(
    title="Spread Volatility by Zone<br><span style='font-size:12px'>Higher = More Unpredictable Spreads</span>",
    xaxis_title="Zone",
    yaxis_title="Spread Volatility (Std Dev)",
    template='plotly_white',
    height=600,
    hovermode='x unified'
)
fig2.write_html("02_spread_volatility.html")
print("✓ Saved: 02_spread_volatility.html")

# Chart 3: Hourly Pattern - When to Buy
fig3 = make_subplots(
    rows=3, cols=3,
    subplot_titles=[z for z in zones.keys() if z != "Total"],
    specs=[[{"secondary_y": False}] * 3] * 3
)

row, col = 1, 1
for zone_name in zones.keys():
    if zone_name == "Total":
        continue

    rt_df = zones[zone_name]["Real Time"]
    da_df = zones[zone_name]["Day Ahead"]

    combined = rt_df.join(da_df, on="tstamp", suffix="_da").sort("tstamp").with_columns(
        spread=pl.col("demand") - pl.col("demand_da"),
        hour=pl.col("tstamp").dt.hour()
    )

    hourly = combined.group_by("hour").agg(
        pl.col("spread").mean().alias("avg_spread")
    ).sort("hour")

    fig3.add_trace(
        go.Scatter(
            x=hourly["hour"],
            y=hourly["avg_spread"],
            mode='lines+markers',
            name=zone_name,
            fill='tozeroy',
            line=dict(width=2),
            hovertemplate="<b>%{fullData.name}</b><br>Hour: %{x}:00<br>Spread: %{y:+.2f}<extra></extra>"
        ),
        row=row, col=col
    )

    col += 1
    if col > 3:
        col = 1
        row += 1

fig3.update_layout(
    title="Hourly Spread Pattern: When to Buy Each Market",
    height=900,
    showlegend=False,
    template='plotly_white',
    hovermode='x unified'
)
fig3.write_html("03_hourly_patterns.html")
print("✓ Saved: 03_hourly_patterns.html")

# Chart 4: Volatility Comparison
fig4 = go.Figure()
fig4.add_trace(go.Bar(
    x=zone_df["zone"],
    y=zone_df["rt_vol"],
    name='RT Volatility',
    marker_color='#1f77b4'
))
fig4.add_trace(go.Bar(
    x=zone_df["zone"],
    y=zone_df["da_vol"],
    name='DA Volatility',
    marker_color='#ff7f0e'
))
fig4.update_layout(
    title="Volatility Comparison: Real-Time vs Day-Ahead",
    xaxis_title="Zone",
    yaxis_title="Volatility (Std Dev)",
    barmode='group',
    template='plotly_white',
    height=600,
    hovermode='x unified'
)
fig4.write_html("04_volatility_comparison.html")
print("✓ Saved: 04_volatility_comparison.html")

# Chart 5: Spread Range by Zone
fig5 = go.Figure()
fig5.add_trace(go.Box(
    x=zone_df["zone"],
    y=zone_df["max_spread"],
    name='Max Spread',
    marker_color='#d62728'
))
fig5.add_trace(go.Box(
    x=zone_df["zone"],
    y=zone_df["min_spread"],
    name='Min Spread',
    marker_color='#2ca02c'
))
fig5.update_layout(
    title="Spread Range by Zone (Best and Worst Case)",
    xaxis_title="Zone",
    yaxis_title="Spread Value",
    template='plotly_white',
    height=600,
    hovermode='x unified'
)
fig5.write_html("05_spread_range.html")
print("✓ Saved: 05_spread_range.html")

# ============================================================================
# FINAL RECOMMENDATIONS
# ============================================================================
print("\n\n" + "=" * 80)
print("FINAL RECOMMENDATIONS")
print("=" * 80)

print("\n🎯 PRIMARY STRATEGY:")
print("-" * 80)

if total_avg_spread > 0:
    print(f"✅ Buy from DAY-AHEAD market")
    print(f"   • Average savings: {total_avg_spread:.2f} per hour")
    print(f"   • Annual savings estimate: ${total_avg_spread * 24 * 365:,.0f}")
    print(f"   • Lower volatility = more predictable costs")
else:
    print(f"✅ Buy from REAL-TIME market")
    print(f"   • Average savings: {abs(total_avg_spread):.2f} per hour")
    print(f"   • Annual savings estimate: ${abs(total_avg_spread) * 24 * 365:,.0f}")
    print(f"   • Lower volatility = more predictable costs")

print("\n📍 ZONE-SPECIFIC STRATEGIES:")
print("-" * 80)

strong_zones = zone_df.filter(pl.col("avg_spread").abs() > 50)
moderate_zones = zone_df.filter((pl.col("avg_spread").abs() > 20) & (pl.col("avg_spread").abs() <= 50))
neutral_zones = zone_df.filter(pl.col("avg_spread").abs() <= 20)

if len(strong_zones) > 0:
    print("\n🔴 STRONG PREFERENCE (>50 spread):")
    for row in strong_zones.iter_rows(named=True):
        market = "DAY-AHEAD" if row["avg_spread"] > 0 else "REAL-TIME"
        print(f"   • {row['zone']}: Buy {market} (save {abs(row['avg_spread']):.2f})")

if len(moderate_zones) > 0:
    print("\n🟡 MODERATE PREFERENCE (20-50 spread):")
    for row in moderate_zones.iter_rows(named=True):
        market = "DAY-AHEAD" if row["avg_spread"] > 0 else "REAL-TIME"
        print(f"   • {row['zone']}: Prefer {market} (save {abs(row['avg_spread']):.2f})")

if len(neutral_zones) > 0:
    print("\n🟢 NEUTRAL (similar pricing):")
    for row in neutral_zones.iter_rows(named=True):
        print(f"   • {row['zone']}: Use other factors to decide")

print("\n⏰ TIME-BASED STRATEGY:")
print("-" * 80)
print("   • Peak hours (8am-10pm): Higher spreads - bigger savings opportunity")
print("   • Off-peak hours (11pm-7am): Lower spreads - less savings opportunity")
print("   • See hourly patterns chart for zone-specific timing")

print("\n⚠️  RISK MANAGEMENT:")
print("-" * 80)
print(f"   • RT market is {((total_rt_vol - total_da_vol) / total_da_vol * 100):.1f}% more volatile")
print(f"   • Consider DA market for budget certainty")
print(f"   • Use RT market for flexibility and potential savings")
print(f"   • Monitor high-volatility zones: {', '.join(vol_ranking.head(3)['zone'].to_list())}")

print("\n💡 IMPLEMENTATION TIPS:")
print("-" * 80)
print("   1. Start with the primary strategy (DA or RT)")
print("   2. Adjust by zone based on zone-specific recommendations")
print("   3. Use hourly patterns to optimize timing")
print("   4. Monitor spreads weekly to catch market changes")
print("   5. Consider hedging for high-volatility periods")

print("\n" + "=" * 80)
print("END OF REPORT")
print("=" * 80 + "\n")

