import polars as pl
import plotly.graph_objects as go

def plot_spreads(
        zones
):
    # 1. COMPARE SPREADS (RT - DA) OVER TIME FOR EACH ZONE
    for zone_name, zone_data in zones.items():
        rt_df = zone_data["Real Time"]
        da_df = zone_data["Day Ahead"]

        # Join RT and DA data on timestamp
        spreads = rt_df.join(da_df, on="tstamp", suffix="_da").with_columns(
            spread=pl.col("demand") - pl.col("demand_da")
        )

        # Plot
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=spreads["tstamp"],
            y=spreads["spread"],
            mode='lines',
            name='Spread',
            line=dict(color='blue', width=1)
        ))

        fig.update_layout(
            title=f"{zone_name}: Real-Time vs Day-Ahead Demand Spreads",
            xaxis_title="Time",
            yaxis_title="Spread (RT Demand - DA Demand)",
            hovermode='x unified',
            template='plotly_white',
            height=600
        )

        # Save as HTML
        filename = f"figs/spreads_{zone_name.replace(' ', '_').replace('/', '_')}.html"
        fig.write_html(filename)
        print(f"Saved: {filename}")

    # 2. AVERAGE SPREADS BY ZONE (Bar Chart)
    print("\n=== AVERAGE SPREADS BY ZONE ===")
    zone_names = []
    avg_spreads = []

    for zone_name, zone_data in zones.items():
        rt_df = zone_data["Real Time"]
        da_df = zone_data["Day Ahead"]

        spreads = rt_df.join(da_df, on="tstamp", suffix="_da").with_columns(
            spread=pl.col("demand") - pl.col("demand_da")
        )

        avg_spread = spreads["spread"].mean()

        zone_names.append(zone_name)
        avg_spreads.append(avg_spread)

        print(f"{zone_name}: {avg_spread:.2f}")

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=zone_names,
        y=avg_spreads,
        marker_color=['red' if x > 0 else 'green' for x in avg_spreads]
    ))
    fig.update_layout(
        title="Average Spreads by Zone (RT - DA)",
        xaxis_title="Zone",
        yaxis_title="Average Spread (MWh)",
        template='plotly_white',
        hovermode='x'
    )
    fig.write_html("figs/average_spreads_by_zone.html")
    print("Saved: average_spreads_by_zone.html")

    # 3. VOLATILITY DIFFERENCES
    print("\n=== VOLATILITY ANALYSIS ===")
    zone_names = []
    rt_vols = []
    da_vols = []

    for zone_name, zone_data in zones.items():
        rt_vol = zone_data["Real Time"]["demand"].std()
        da_vol = zone_data["Day Ahead"]["demand"].std()

        zone_names.append(zone_name)
        rt_vols.append(rt_vol)
        da_vols.append(da_vol)

        print(f"{zone_name}: RT={rt_vol:.2f}, DA={da_vol:.2f}")

    fig = go.Figure()
    fig.add_trace(go.Bar(x=zone_names, y=rt_vols, name='RT Volatility', marker_color='red'))
    fig.add_trace(go.Bar(x=zone_names, y=da_vols, name='DA Volatility', marker_color='blue'))
    fig.update_layout(
        title="Volatility Comparison: Real-Time vs Day-Ahead",
        xaxis_title="Zone",
        yaxis_title="Volatility (Std Dev)",
        barmode='group',
        template='plotly_white'
    )
    fig.write_html("figs/volatility_comparison.html")
    print("Saved: volatility_comparison.html")

    # 4. SPREADS BY HOUR OF DAY
    fig = go.Figure()

    for zone_name, zone_data in zones.items():
        rt_df = zone_data["Real Time"]
        da_df = zone_data["Day Ahead"]

        hourly_spreads = rt_df.join(da_df, on="tstamp", suffix="_da").with_columns(
            hour=pl.col("tstamp").dt.hour(),
            spread=pl.col("demand") - pl.col("demand_da")
        ).group_by("hour").agg(
            pl.col("spread").mean().alias("avg_spread")
        ).sort("hour")

        fig.add_trace(go.Scatter(
            x=hourly_spreads["hour"],
            y=hourly_spreads["avg_spread"],
            mode='lines+markers',
            name=zone_name
        ))

    fig.update_layout(
        title="Average Spreads by Hour of Day",
        xaxis_title="Hour of Day",
        yaxis_title="Average Spread (MWh)",
        template='plotly_white',
        hovermode='x unified'
    )
    fig.write_html("figs/spreads_by_hour.html")
    print("Saved: spreads_by_hour.html")

    print("\n All figures saved!")


    return