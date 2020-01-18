# This script - 
# python ecosystem libraries
import geopandas as gpd
import glob
import os
from os.path import exists
import numpy as np
import pandas as pd
import sys
# user defined libraries
sys.path.append('lib/')
import admin
import exposures
import ssbn
import geospatial
from helper_downloads import unzip
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
if exposure_source == 'gpw':
    expo, expo_gt, expo_shape = exposures.get_asset_array() # gridded population of the workd
elif exposure_source == 'worldpop':
    expo_path = exposures.worldpop(iso3) # This downloads the worldpop dataset
else:
    assert False

# VULNERABILITY PARAMETERS
# Which type of damage function?
# which file?

# DATA AGRREGATION PARAMETERS
# HYDROBASINS dataset
# Pfascetter level to assume spatial correlation level at
pfas = 4
# TODO: need to make lookup table mapping countries to continents used in hydrobasins
hb_region = 'sa' 
hb_folder = './data/hydrobasins/{}/'.format(hb_region)
hb_path = hb_folder+ 'hybas_{}_lev0{}_v1c.shp'.format(hb_region, pfas)
if not exists(hb_path):
    hb_zip = './data/hydrobasins/{}/hybas_{}_lev0{}_v1c.zip'.format(hb_region,
    hb_region, pfas)
    if not exists(hb_zip):
        
        pass # TODO: download the hydrobasins dataset unzip the top level
    unzip(hb_zip, hb_folder)

# Filter the hydrobasins to the exposure (this is the population density tif)
# i.e. filters basins that aren't in the country. 
hb_df = geospatial.filter_polygons(expo_path, hb_path)
# hb_df.plot()
hb_df
# administrative boundary level(s) to run on: 0 corresponds to adm0 (national), 1 is subnational provinces, 2 is districts.
levels = [0,1,2]
# This takes a long time since there's nearly 4GB of data going into just getting the outlines of the subnational boundaries
admin_df = admin.get_admin_boundaries(c, levels = levels)

##############
# MAIN MODEL #
##############
# START: you now have the following:
# hazards & exposure grids,
# vulnerability function,
# basin & administrative boundaries
haz_params
expo_path
hb_df
admin_df


# Create a (basin, admin boundary) matrix that shows the fraction of (admin, basin) exposure over basin exposure
hb_mask = geospatial.shapefile2raster(hb_df,expo_path,'./intermediates/{}_mask_hydrobasin.tif'.format(iso3.lower()))
hb_mask = hb_mask.astype('int32')
pd.Series(hb_mask.ravel()).value_counts()

admin_mask = geospatial.shapefile2raster(admin_df,expo_path,'./intermediates/{}_mask_admin.tif'.format(iso3.lower()))



pd.Series(admin_mask.ravel()).value_counts()


d = {}
d['dtype'] = 'float32'
d
d['dtype']
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
    