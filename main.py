# This script - 
# Parameter Setting
    # Sets Hazard parameters
    # Set Exposure parameters
    # Set Vulnerability params
    # Set Damage aggregation parameters
# Call separate libraries to get the different funcitons from each library
    # Get the hazard layer
        # hazard.ssbn or hazard.gar etc
            # Based on the gridded depths or intensities
            # This function assumes a spatial correlation for hazard intensity 
            # (e.g. similar basins for floods, paths for hurricanes)
            # and an
    # Get the Exposure layer
        # exposure.pop.gpw or exposure.worldpop or exposure.landsat
    # Check that resolutions match
        # native
    # Apply the vectorized vulnerability function
        # lib.vulnerability_flood_depth or other damage function
    # Aggregate damage by basin/political boundary
        # lib.aggregate
    # Produce output
# Summarize Data
    # Make and visualize maps.

# python ecosystem libraries
import gdal
import geopandas as gpd
import glob
import os
import numpy as np
import pandas as pd
import sys

# user defined libraries
sys.path.append('lib/')
import admin
import exposures
import ssbn
from vulnerability_flood_depth import damage_function as flood_damage
import vulnerability_flood_depth



# Notes for iteration 2
    # Make an interoperable Hazard class that works on SSBN, GAR, other gridded exposure data
    # Loads hazard data
    # Stores extents, xy grids
    # Return period management
    # Gives summary statistics
    # Crops to country borders if necessary.
    # Make an Exposure class that works on different asset grids, can estimate ones from gdp grids (e.g. Kummu)
    # loads gridded exposure data
    # Residential assets
    # Industrial assets
    # Commercial Assets
    # Ag assets (cropland grids)
    # infrastructure
    # All assets
    # Poor population
    # Rich Population
    # Calibrates against an external dataset or number
    # Calculates exposure bias
    # Vulnerability
    # Function that goes from hazard and exposure to a mathematical
    # function you can apply over both classes

##################
# SET PARAMETERS #
##################
# List of countries (can be name, iso2, or iso3)
c = 'Argentina'
c = admin.get_wbcountry(c)
iso2 = admin.get_wbcountry(c, 'iso2')
iso3 = admin.get_wbcountry(c, 'iso3')
print('Countries being run on:', c, '\n')
# administrative boundary level(s) to run on
adm = 0
# Pfascetter level to assume spatial correlation level at
pfas = 4
# Hydrobasins continent code - see hb_regions below
hb_reg = 'sa'
# Type of flood - 'pluvial' or 'fluvial'
haz = 'fluvial'

####################################
# DATA AVAILABILITY CHECK AND PREP #
####################################
# - for each data source you want to load the respective non-RP datasets into memory
# - check whether they all exist.

# Hazard grid
haz_folder = ssbn.folders(iso2, haz)
haz_flist = sorted(glob.glob(haz_folder + '*'))
haz_params = ssbn.get_param_info(haz_flist)
haz_params
# Exposures grid
expo, expo_gt, expo_shape = exposures.get_asset_array()

# Vulnerability function
def vulnerability(hazard, method='depth', reg= 'sa'):
    """Applies a vulnerability function to an array. Returns an array of
    imputed damages as a % of assets"""
    # Assume all people that get flooded are damaged completely
    if method == 'depth':
        # Returns a % damage map based on EU data
        fd = flood_damage(reg)
        # Change nans to 0
        hazard = np.nan_to_num(hazard)
        # Fast way to vectorize a sorted lookup (as opposed to a dictionary lookup)
        indices = np.searchsorted(fd.index, hazard, side='right') - 1
        damage = fd.values[indices]
    elif method == 'boolean':
        damage = hazard.astype(bool)
    else:
        raise AssertionError('vulnerability function not specified correctly')
    return damage

# Basins boundaries
hb_regions = {'af': 'Africa',
              'ar': 'North American Arctic',
              'as': 'Central and South-East Asia',
              'au': 'Australia and Oceania',
              'eu': 'Europe and Middle East',
              'gr': 'Greenland',
              'na': 'North America and Caribbean',
              'sa': 'South America',
              'si': 'Siberia'}
# TODO - write a key or function that takes a wb name and returns the hb dataset.
# right now this is hardcoded.
hb = './data/geobounds/hydrobasins/hybas_{}_lev0{}_v1c.shp'.format(
    hb_reg, pfas)
# Check if the data file for basins exists
assert os.path.exists(
    hb), "hydrobasins data file for chosen region and pfascetter level does not exist"

# Admin boundaries

# Administrative level for exceedance curves
print("Administrative boundary data at the selected admin level {} available at {}"
      .format(adm, admin.get_boundaries_fpath(adm)))

###################
# DATA PREPRATION #
###################

# Hazard grid
# Exposures grid
# Vulnerability function
# Basins boundaries
# Admin boundaries


##############
# MAIN MODEL #
##############

# START: you now have the following:
# hazards & exposure grids,
# vulnerability function,
# basin & administrative boundaries

# crop the hazard grids to the extent of the basins.
# resample the exposure grids to the resolution of the hazard grids
# apply the vulnerability function across the hazard and the exposure grid
# sums the maximum total damage (spatial sum of exposure) and sums the damage at each return period for each basin
# randomly samples n years of flooding where each basin is correlated.
# calculate the total exposure for each administrative region
# Create a (basin, admin boundary) matrix that shows the fraction of (admin, basin) exposure over basin exposure
# Runs a simulation of n years of floods that are perfectly correlated across hydrological basins
# Multiplies the n x basin matrix by the basin x admin boundary matrix to get a n x admin boundary matrix
# Now sort the n x admin boundary matrix by impacts and divide by the total exposure per admin boundary to get the % damage by admin boundary
# Checks whether data is all available, given the above Parameters - flags only if not available before any processing
