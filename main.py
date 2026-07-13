#######################################################################################################################
# Imports #
#######################################################################################################################

from datetime import datetime, timedelta
from features import loadsave as ls

#######################################################################################################################
# Data Import #
#######################################################################################################################

# Define start and end time
t1 = datetime(2024, 1, 1, 0)
t2 = datetime(2025, 1, 1, 0)

print("=" * 70)
print("Loading hourly realtime and day ahead data from CDS")
print("Time Period:", t1, " to ", t2)
print("=" * 70)

load_zones = ls.load_zones(t1, t2)

print("=" * 70)
print("Hourly realtime and day ahead data from CDS successfully loaded")
print("=" * 70)

# Load in variables
print("=" * 70)
print("Loading variables data from CDS")
print("=" * 70)

vars = {}

print("=" * 70)
print("Variable data from CDS successfully loaded")
print("=" * 70)

#######################################################################################################################
# Data Import #
#######################################################################################################################