from ice_data_py import cds
import polars as pl

def load_zones(
        t1,
        t2
):
    print("=" * 70)
    print("Loading hourly realtime and day ahead data from CDS")
    print("Time Period:", t1, " to ", t2)
    print("=" * 70)

    # Load in hourly zones with zone-specific temperatures
    ct_rt_hourly = cds.fetch_all(
        [cds.QuerySpec(ms="NEISO", mn="load_zone._z_connecticut", mp="realtime_hourly_demand")], t1, t2)
    ct_da_hourly = cds.fetch_all(
        [cds.QuerySpec(ms="NEISO", mn="load_zone._z_connecticut", mp="dayahead_hourly_demand")], t1, t2)

    maine_rt_hourly = cds.fetch_all([cds.QuerySpec(ms="NEISO", mn="load_zone._z_maine", mp="realtime_hourly_demand")],
                                    t1, t2)
    maine_da_hourly = cds.fetch_all([cds.QuerySpec(ms="NEISO", mn="load_zone._z_maine", mp="dayahead_hourly_demand")],
                                    t1, t2)

    nemass_rt_hourly = cds.fetch_all([cds.QuerySpec(ms="NEISO", mn="load_zone._z_nemassbost", mp="realtime_hourly_demand")],
                                     t1, t2)
    nemass_da_hourly = cds.fetch_all([cds.QuerySpec(ms="NEISO", mn="load_zone._z_nemassbost", mp="dayahead_hourly_demand")],
                                     t1, t2)

    nh_rt_hourly = cds.fetch_all(
        [cds.QuerySpec(ms="NEISO", mn="load_zone._z_newhampshire", mp="realtime_hourly_demand")], t1, t2)
    nh_da_hourly = cds.fetch_all(
        [cds.QuerySpec(ms="NEISO", mn="load_zone._z_newhampshire", mp="dayahead_hourly_demand")], t1, t2)

    ri_rt_hourly = cds.fetch_all(
        [cds.QuerySpec(ms="NEISO", mn="load_zone._z_rhodeisland", mp="realtime_hourly_demand")], t1, t2)
    ri_da_hourly = cds.fetch_all(
        [cds.QuerySpec(ms="NEISO", mn="load_zone._z_rhodeisland", mp="dayahead_hourly_demand")], t1, t2)

    semass_rt_hourly = cds.fetch_all([cds.QuerySpec(ms="NEISO", mn="load_zone._z_semass", mp="realtime_hourly_demand")],
                                     t1, t2)
    semass_da_hourly = cds.fetch_all([cds.QuerySpec(ms="NEISO", mn="load_zone._z_semass", mp="dayahead_hourly_demand")],
                                     t1, t2)

    vt_rt_hourly = cds.fetch_all([cds.QuerySpec(ms="NEISO", mn="load_zone._z_vermont", mp="realtime_hourly_demand")],
                                 t1, t2)
    vt_da_hourly = cds.fetch_all([cds.QuerySpec(ms="NEISO", mn="load_zone._z_vermont", mp="dayahead_hourly_demand")],
                                 t1, t2)

    wcmass_rt_hourly = cds.fetch_all([cds.QuerySpec(ms="NEISO", mn="load_zone._z_wcmass", mp="realtime_hourly_demand")],
                                     t1, t2)
    wcmass_da_hourly = cds.fetch_all([cds.QuerySpec(ms="NEISO", mn="load_zone._z_wcmass", mp="dayahead_hourly_demand")],
                                     t1, t2)

    # Rename all demand columns to a standard name
    ct_rt_hourly = ct_rt_hourly.rename({"NEISO.load_zone._z_connecticut.realtime_hourly_demand": "demand"})
    maine_rt_hourly = maine_rt_hourly.rename({"NEISO.load_zone._z_maine.realtime_hourly_demand": "demand"})
    nemass_rt_hourly = nemass_rt_hourly.rename({"NEISO.load_zone._z_nemassbost.realtime_hourly_demand": "demand"})
    nh_rt_hourly = nh_rt_hourly.rename({"NEISO.load_zone._z_newhampshire.realtime_hourly_demand": "demand"})
    ri_rt_hourly = ri_rt_hourly.rename({"NEISO.load_zone._z_rhodeisland.realtime_hourly_demand": "demand"})
    semass_rt_hourly = semass_rt_hourly.rename({"NEISO.load_zone._z_semass.realtime_hourly_demand": "demand"})
    vt_rt_hourly = vt_rt_hourly.rename({"NEISO.load_zone._z_vermont.realtime_hourly_demand": "demand"})
    wcmass_rt_hourly = wcmass_rt_hourly.rename({"NEISO.load_zone._z_wcmass.realtime_hourly_demand": "demand"})

    total_rt_hourly = pl.concat(
        [ct_rt_hourly, maine_rt_hourly, nemass_rt_hourly, nh_rt_hourly, ri_rt_hourly, semass_rt_hourly, vt_rt_hourly,
         wcmass_rt_hourly]).group_by("tstamp").sum()

    ct_da_hourly = ct_da_hourly.rename({"NEISO.load_zone._z_connecticut.dayahead_hourly_demand": "demand"})
    maine_da_hourly = maine_da_hourly.rename({"NEISO.load_zone._z_maine.dayahead_hourly_demand": "demand"})
    nemass_da_hourly = nemass_da_hourly.rename({"NEISO.load_zone._z_nemassbost.dayahead_hourly_demand": "demand"})
    nh_da_hourly = nh_da_hourly.rename({"NEISO.load_zone._z_newhampshire.dayahead_hourly_demand": "demand"})
    ri_da_hourly = ri_da_hourly.rename({"NEISO.load_zone._z_rhodeisland.dayahead_hourly_demand": "demand"})
    semass_da_hourly = semass_da_hourly.rename({"NEISO.load_zone._z_semass.dayahead_hourly_demand": "demand"})
    vt_da_hourly = vt_da_hourly.rename({"NEISO.load_zone._z_vermont.dayahead_hourly_demand": "demand"})
    wcmass_da_hourly = wcmass_da_hourly.rename({"NEISO.load_zone._z_wcmass.dayahead_hourly_demand": "demand"})

    total_da_hourly = pl.concat(
        [ct_da_hourly, maine_da_hourly, nemass_da_hourly, nh_da_hourly, ri_da_hourly, semass_da_hourly, vt_da_hourly,
         wcmass_da_hourly]).group_by("tstamp").sum()

    # Load zones
    load_zones = {
        "Connecticut": {"Real Time": ct_rt_hourly, "Day Ahead": ct_da_hourly},
        "Maine": {"Real Time": maine_rt_hourly, "Day Ahead": maine_da_hourly},
        "North East Massachusetts": {"Real Time": nemass_rt_hourly, "Day Ahead": nemass_da_hourly},
        "New Hampshire": {"Real Time": nh_rt_hourly, "Day Ahead": nh_da_hourly},
        "Rhode Island": {"Real Time": ri_rt_hourly, "Day Ahead": ri_da_hourly},
        "South East Massachusetts": {"Real Time": semass_rt_hourly, "Day Ahead": semass_da_hourly},
        "Vermont": {"Real Time": vt_rt_hourly, "Day Ahead": vt_da_hourly},
        "West Central Massachusetts": {"Real Time": wcmass_rt_hourly, "Day Ahead": wcmass_da_hourly},
        "Total": {"Real Time": total_rt_hourly, "Day Ahead": total_da_hourly},
    }
    print("=" * 70)
    print("Hourly realtime and day ahead data from CDS successfully loaded")
    print("=" * 70)

    return load_zones


def load_vars(
        t1,
        t2
):
    print("=" * 70)
    print("Loading variables data from CDS")
    print("=" * 70)

    ct_temp = cds.fetch_all(
        [cds.QuerySpec(ms="NOAA-Forecast", mn="CT-Groton", mp="temperature[degF]")], t1, t2)
    ct_hum = cds.fetch_all(
        [cds.QuerySpec(ms="NOAA-Forecast", mn="CT-Groton", mp="relativeHumidity[percent]")], t1, t2)
    ct_dew = cds.fetch_all(
        [cds.QuerySpec(ms="NOAA-Forecast", mn="CT-Groton", mp="dewpoint[degF]")], t1, t2)
    ct_cloud = pl.DataFrame({
        "tstamp": ct_temp["tstamp"],  # Use same timestamps as other CT data
        "cloud_coverage": [0.0] * len(ct_temp)
    })

    maine_temp = cds.fetch_all(
        [cds.QuerySpec(ms="dev4-TWC-Forecasts", mn="ME.Fairfield.coordinates", mp="temperature_F")], t1, t2)
    maine_hum = cds.fetch_all(
        [cds.QuerySpec(ms="dev4-TWC-Forecasts", mn="ME.Fairfield.coordinates", mp="relativeHumidity")], t1, t2)
    maine_dew = cds.fetch_all(
        [cds.QuerySpec(ms="dev4-TWC-Forecasts", mn="ME.Fairfield.coordinates", mp="dewPoint_F")], t1, t2)
    maine_cloud = cds.fetch_all(
        [cds.QuerySpec(ms="dev4-TWC-Forecasts", mn="ME.Fairfield.coordinates", mp="cloudCoverage")], t1, t2)

    nemass_temp = cds.fetch_all(
        [cds.QuerySpec(ms="dev4-TWC-Forecasts", mn="MA.Lowell.coordinates", mp="temperature_F")], t1, t2)
    nemass_hum = cds.fetch_all(
        [cds.QuerySpec(ms="dev4-TWC-Forecasts", mn="MA.Lowell.coordinates", mp="relativeHumidity")], t1, t2)
    nemass_dew = cds.fetch_all(
        [cds.QuerySpec(ms="dev4-TWC-Forecasts", mn="MA.Lowell.coordinates", mp="dewPoint_F")], t1, t2)
    nemass_cloud = cds.fetch_all(
        [cds.QuerySpec(ms="dev4-TWC-Forecasts", mn="MA.Lowell.coordinates", mp="cloudCoverage")], t1, t2)

    nh_temp = nemass_temp
    nh_hum = nemass_hum
    nh_dew = nemass_dew
    nh_cloud = nemass_cloud

    ri_temp = ct_temp
    ri_hum = ct_hum
    ri_dew = ct_dew
    ri_cloud = ct_cloud

    semass_temp = cds.fetch_all(
        [cds.QuerySpec(ms="dev4-TWC-Forecasts", mn="MA.Bridgewater.coordinates", mp="temperature_F")], t1, t2)
    semass_hum = cds.fetch_all(
        [cds.QuerySpec(ms="dev4-TWC-Forecasts", mn="MA.Bridgewater.coordinates", mp="relativeHumidity")], t1, t2)
    semass_dew = cds.fetch_all(
        [cds.QuerySpec(ms="dev4-TWC-Forecasts", mn="MA.Bridgewater.coordinates", mp="dewPoint_F")], t1, t2)
    semass_cloud = cds.fetch_all(
        [cds.QuerySpec(ms="dev4-TWC-Forecasts", mn="MA.Bridgewater.coordinates", mp="cloudCoverage")], t1, t2)

    vt_temp = cds.fetch_all(
        [cds.QuerySpec(ms="dev4-TWC-Forecasts", mn="VT.Georgia.coordinates", mp="temperature_F")], t1, t2)
    vt_hum = cds.fetch_all(
        [cds.QuerySpec(ms="dev4-TWC-Forecasts", mn="VT.Georgia.coordinates", mp="relativeHumidity")], t1, t2)
    vt_dew = cds.fetch_all(
        [cds.QuerySpec(ms="dev4-TWC-Forecasts", mn="VT.Georgia.coordinates", mp="dewPoint_F")], t1, t2)
    vt_cloud = cds.fetch_all(
        [cds.QuerySpec(ms="dev4-TWC-Forecasts", mn="VT.Georgia.coordinates", mp="cloudCoverage")], t1, t2)

    wcmass_temp = cds.fetch_all(
        [cds.QuerySpec(ms="dev4-TWC-Forecasts", mn="MA.Worcester.coordinates", mp="temperature_F")], t1, t2)
    wcmass_hum = cds.fetch_all(
        [cds.QuerySpec(ms="dev4-TWC-Forecasts", mn="MA.Worcester.coordinates", mp="relativeHumidity")], t1, t2)
    wcmass_dew = cds.fetch_all(
        [cds.QuerySpec(ms="dev4-TWC-Forecasts", mn="MA.Worcester.coordinates", mp="dewPoint_F")], t1, t2)
    wcmass_cloud = cds.fetch_all(
        [cds.QuerySpec(ms="dev4-TWC-Forecasts", mn="MA.Worcester.coordinates", mp="cloudCoverage")], t1, t2)

    vars = {
        "Connecticut": {"Temperature": ct_temp, "Humidity": ct_hum, "Dew Point": ct_dew, "Cloud Coverage": ct_cloud},
        "Maine": {"Temperature": maine_temp, "Humidity": maine_hum, "Dew Point": maine_dew, "Cloud Coverage": maine_cloud},
        "North East Massachusetts": {"Temperature": nemass_temp, "Humidity": nemass_hum, "Dew Point": nemass_dew, "Cloud Coverage": nemass_cloud},
        "New Hampshire":{"Temperature": nh_temp, "Humidity": nh_hum, "Dew Point": nh_dew, "Cloud Coverage": nh_cloud},
        "Rhode Island": {"Temperature": ri_temp, "Humidity": ri_hum, "Dew Point": ri_dew, "Cloud Coverage": ri_cloud},
        "South East Massachusetts": {"Temperature": semass_temp, "Humidity": semass_hum, "Dew Point": semass_dew, "Cloud Coverage": semass_cloud},
        "Vermont": {"Temperature": vt_temp, "Humidity": vt_hum, "Dew Point": vt_dew, "Cloud Coverage": vt_cloud},
        "West Central Massachusetts": {"Temperature": wcmass_temp, "Humidity": wcmass_hum, "Dew Point": wcmass_dew, "Cloud Coverage": wcmass_cloud},
    }

    print("=" * 70)
    print("Variable data from CDS successfully loaded")
    print("=" * 70)

    return vars