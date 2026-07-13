#######################################################################################################################
# Imports #
#######################################################################################################################
import os
from idlelib import mainmenu

import polars as pl

from ice_data_py import cds, hist3
from datetime import datetime, timedelta

#######################################################################################################################
# Data Import #
#######################################################################################################################

# Define start and end time
t1 = datetime(2021, 6, 1, 0)
t2 = datetime(2025, 12, 31, 23)

print("=" * 70)
print("Loading hourly generation data from CDS")
print("Time Period:", t1, " to ", t2)
print("=" * 70)

## Load in hourly zones with zone-specific temperatures
print("\nLoading demand data...")
ct_rt_hourly = cds.fetch_all([cds.QuerySpec(ms="NEISO", mn="load_zone._z_connecticut", mp="realtime_hourly_demand")], t1, t2)
ct_da_hourly = cds.fetch_all([cds.QuerySpec(ms="NEISO", mn="load_zone._z_connecticut", mp="dayahead_hourly_demand")], t1, t2)

maine_rt_hourly =  cds.fetch_all([cds.QuerySpec(ms="NEISO", mn="load_zone._z_maine", mp="realtime_hourly_demand")], t1, t2)
maine_da_hourly =  cds.fetch_all([cds.QuerySpec(ms="NEISO", mn="load_zone._z_maine", mp="dayahead_hourly_demand")], t1, t2)

nemass_rt_hourly = cds.fetch_all([cds.QuerySpec(ms="NEISO", mn="load_zone._z_nemass", mp="realtime_hourly_demand")], t1, t2)
nemass_da_hourly = cds.fetch_all([cds.QuerySpec(ms="NEISO", mn="load_zone._z_nemass", mp="dayahead_hourly_demand")], t1, t2)

nh_rt_hourly = cds.fetch_all([cds.QuerySpec(ms="NEISO", mn="load_zone._z_newhampshire", mp="realtime_hourly_demand")], t1, t2)
nh_da_hourly = cds.fetch_all([cds.QuerySpec(ms="NEISO", mn="load_zone._z_newhampshire", mp="dayahead_hourly_demand")], t1, t2)

ri_rt_hourly = cds.fetch_all([cds.QuerySpec(ms="NEISO", mn="load_zone._z_rhodeisland", mp="realtime_hourly_demand")], t1, t2)
ri_da_hourly = cds.fetch_all([cds.QuerySpec(ms="NEISO", mn="load_zone._z_rhodeisland", mp="dayahead_hourly_demand")], t1, t2)

semass_rt_hourly = cds.fetch_all([cds.QuerySpec(ms="NEISO", mn="load_zone._z_semass", mp="realtime_hourly_demand")], t1, t2)
semass_da_hourly = cds.fetch_all([cds.QuerySpec(ms="NEISO", mn="load_zone._z_semass", mp="dayahead_hourly_demand")], t1, t2)

vt_rt_hourly = cds.fetch_all([cds.QuerySpec(ms="NEISO", mn="load_zone._z_vermont", mp="realtime_hourly_demand")], t1, t2)
vt_da_hourly = cds.fetch_all([cds.QuerySpec(ms="NEISO", mn="load_zone._z_vermont", mp="dayahead_hourly_demand")], t1, t2)

wcmass_rt_hourly = cds.fetch_all([cds.QuerySpec(ms="NEISO", mn="load_zone._z_wcmass", mp="realtime_hourly_demand")], t1, t2)
wcmass_da_hourly = cds.fetch_all([cds.QuerySpec(ms="NEISO", mn="load_zone._z_wcmass", mp="dayahead_hourly_demand")], t1, t2)



#Load zones
load_zones = {
    "Connecticut": {"Real Time": ct_rt_hourly, "Day Ahead": ct_da_hourly},
    "Maine": {"Real Time": maine_rt_hourly, "Day Ahead": maine_da_hourly},
}

print(load_zones)