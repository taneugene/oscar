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
import exposures
import ssbn
from vulnerability_flood_depth import damage_function as flood_damage
import vulnerability_flood_depth

##################
# SET PARAMETERS #
##################

# Parameter Setting
    # Input country and data sources
    # Sets Hazard parameters
    # Set Exposure parameters
    # Set Vulnerability params
    # Set Damage aggregation parameters

# COUNTRY AND DATA SOURCES

# List of countries (can be name, iso2, or iso3)
c = 'Argentina'
c = admin.get_wbcountry(c)
iso2 = admin.get_wbcountry(c, 'iso2')
iso3 = admin.get_wbcountry(c, 'iso3')
print('Countries being run on:', c, '\n')

# HAZARD PARAMETERS
# Type of flood - 'pluvial' or 'fluvial'
haz = 'fluvial'
# Hazard grid
haz_folder = ssbn.folders(iso2, haz)
haz_flist = sorted(glob.glob(haz_folder + '*'))
haz_params = ssbn.get_param_info(haz_flist)

# EXPOSURE PARAMETERS
exposure_source = 'worldpop' # 'gpw' or 'worldpop'
# expo, expo_gt, expo_shape = exposures.get_asset_array() # gridded population of the workd
expo_path = exposures.worldpop(iso3)

# VULNERABILITY PARAMETERS


# DATA AGRREGATION PARAMETERS
# HYDROBASINS dataset
# Pfascetter level to assume spatial correlation level at
pfas = 4
# TODO: need to make lookup table mapping countries to continents used in hydrobasins
hb_region = 'sa' 
hb_path = './data/hydrobasins/hybas_{}_lev0{}_v1c.shp'.format(
    hb_region, pfas)
# Check if the data file for basins exists
assert os.path.exists(hb_path), "hydrobasins data file for chosen region and pfascetter level does not exist"

# administrative boundary level(s) to run on
levels = [0,1,2]
# adm = 0
# adm_path = admin.get_boundaries_fpath(adm)
# # Administrative level for exceedance curves
# print("Administrative boundary data at the selected admin level {} available at {}"
#       .format(adm, adm_path))

##############
# MAIN MODEL #
##############
# START: you now have the following:
# hazards & exposure grids,
# vulnerability function,
# basin & administrative boundaries
haz_params
expo_path
hb_path
adm_path

# Get the basin layer and assume that it is well correlated across the basin
# Filter for the relevant admin layers. 

    # Create a (basin, admin boundary) matrix that shows the fraction of (admin, basin) exposure over basin exposure

# Now simulate 1000s of probabilities in an array that matches the extent of the basin
# From the probabilities, (basin x sims)
# map to a return period (1/probability) (basin x sims)
# look up ssbn data for that return period and return flood depth # (lat x lon x sims)
    # only complex because data is tiled
    
# preprocessing for next step:
    # resample the exposure grids to the resolution of the hazard grids
    # Write function that tells you whether cells in a tiff are inside a polygon or not.
    # Loop_through_tifs:
        # Loop through the rows of the basin GeoDataFrame,
            # create a separate array for whether each point in a tiff is in the polygon or not

# Map the flood depth to vulnerability # (sims x lat x lon) or (sims x basin)
    # Assume exposures don't affect vulnerability
        # Simple lookup map
    # Otherwise tcd dhey affect vulnerability
        # e.g. population -> land use -> different vulnerability functions
    # Or multiple grids (sims x lat x lon x exposure dimensions) 
        # vulnerability(industrial, flood_depth)
        # vulnerability(residential, flood_depth)
        # sum vulnerabilities
    # Aggregate back up to sims x basin # sims x lat x lon is too big on memory
        # Multiply inPolygon * population * bool_depth = pop_affected
        # Multiply inPolygon * population = population in basin
        # multiply damage fraction by exposures

# Upscaling/aggregating
    # use the basin x admin matrix to multiply by the basin x admin boundary matrix to get a sims x admin boundary matrix         
    # calculate the total exposure for each administrative region
        # sums the maximum total damage (spatial sum of exposure) for each simulation
    # Calculate return period based on sorted version for each administrative region
        # Now sort the n x admin boundary matrix by impacts and divide by the total exposure per admin boundary to get the % damage by admin boundary


        



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
    