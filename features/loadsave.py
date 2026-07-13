from ice_data_py import cds
import polars as pl

def load_zones(
        t1,
        t2
):
    ## Load in hourly zones with zone-specific temperatures
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

    return load_zones