# This script - 
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
import exposure.exposures as exposures
import hazard.ssbn as ssbn
from vulnerability_flood_depth import damage_function as flood_damage
import vulnerability_flood_depth

# Parameter Setting
    # Sets Hazard parameters
    # Set Exposure parameters
    # Set Vulnerability params
    # Set Damage aggregation parameters
# Call separate libraries to get the different funcitons from each library
    # Get the hazard layer
        # hazard.ssbn or hazard.gar etc
    # Get the Exposure layer
        # exposure.pop.gpw or exposure.worldpop or exposure.landsat
    # Check that resolutions match
        # native
    # Apply the vectorized vulnerability function
        # Based on the gridded depths or intensities
        # This function assumes a spatial correlation for hazard intensity 
        # And then simulates 1000s of potential hazards based on this spatial correlation
        # For 
        # lib.vulnerability_flood_depth or other damage function
    # Aggregate damage by basin/political boundary
        # lib.aggregate
    # Produce output
# Summarize Data
    # Make and visualize maps.

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
# TODO: need to make lookup table mapping countries to continents used in hydrobasins
hb_region = 'sa' 
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
# print(haz_params)
# Exposures grid
# expo, expo_gt, expo_shape = exposures.get_asset_array() # gridded population of the workd
expo_path = exposures.worldpop(iso3)

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
hb = './data/hydrobasins/hybas_{}_lev0{}_v1c.shp'.format(
    hb_region, pfas)
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
# Loop_through_tifs:
# Loop through the rows of the basin GeoDataFrame,
# create a separate array for whether each point in a tiff is in the polygon or not
# Multiply inPolygon * population * bool_depth = pop_affected
# Multiply inPolygon * population = population in basin
# Add both counts to the dataframe.
# Write function that tells you whether cells in a tiff are inside a polygon or not.
# Use gricells_to_adm0 function to simulate floods that are perfectly correlated across hydrobasins


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
    
    


def estimate_affected(row, country, params):
    # Loop through tiles for each basin
    print(row.name)
    for tile in params['tiles']:
        # Get the raster of basin == the current basin
        fname = './data_exposures/{}_hybas_raster_{}.tif'.format(params['iso2'], tile)
        hybas = gtiff_to_array(fname)
        hybas_mask = (hybas == row.name)
        # Get the raster of population
        exp_fname = './data_exposures/gpw/{}_population_count_{}.tif'.format(params['iso2'], tile)
        exp = gtiff_to_array(exp_fname)
        exp[exp<0] = 0
        # Nearest neighbor went from 30s to 3s
        exp = exp/100
        # Get the total population by basin and store it
        assert hybas_mask.shape == exp.shape
        total_pop = (hybas_mask*exp)
        row['basin_pop'] += total_pop.sum()
        # Loop through return periods
        for rp in params['rps']:
            # Get the raster of boolean floods by return period
            fname = '{}{}-{}{}-{}-{}.tif'.format(params['folder'],c,params['type'],params['defended'], str(int(rp)), tile)
            floods = get_ssbn_array(fname)
            # Store the population affected for floods
            total_affected = vulnerability(floods, total_pop).sum()
            row[rp] += total_affected
    return row