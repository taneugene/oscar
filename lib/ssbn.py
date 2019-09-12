import gdal
import geopandas as gpd
import glob
import numpy as np
import os
from os.path import exists, isfile
import pandas as pd
import rasterio
from rasterio import features
from rasterio.merge import merge
from rasterio.plot import show
import re
import seaborn as sns
from shapely.geometry import box, Point, Polygon
import zipfile
# from lib.vulnerability_flood_depth import damage_function as flood_damage

# Keep in this file:
   # SSBN file management


def unzip(path, pwd):
    """Unzips a zipfile unless the output folder already exists
    """
    # Get a set of current files
    fl = set(glob.glob(pwd + "*.zip"))
    # If the input pth doesn't exist, try to find the file
    if not exists(path):
        raise AssertionError("Incorrect Path")
    output_path = path[:-4] + '/'
    print("Extracting {} to {}".format(path, output_path))
    if exists(output_path):
        print("Output folder {} already exists".format(output_path))
        return
    zip_ref = zipfile.ZipFile(path, 'r')
    zip_ref.extractall(pwd)
    print("Extracted {}".format(list((set(glob.glob(pwd + "*")) - fl))[0]))
    zip_ref.close()


def folders(c, flood_type, defended='undefended'):
    """checks availability of the folder for a particular country, flood type and defendedness"""
    folder = "./data/hazards/ssbn/{}_{}_{}/".format(c, flood_type, defended)
    if exists(folder):
        return folder
    else:
        zip = folder + ".zip"
    if exists(zip) and isfile(zip):
        unzip(zip, folder)
        return folder
    else:
        print("Neither folder nor zip file exists in the correct place")
        return False


def get_basic_info(path):
    """Retrieves information from the SSBN filename convention and
    stores it as a dictionary.
    """
    # print(path)
    neg_pos = path[::-1].find('/')
    fname = path[-neg_pos:]
    # print(fname)
    m = re.match(
        "^([A-Z]{2})-([FPUM])([DU]{0,1})-([0-9]{1,4})-([0-9])*\.tif$", fname)
    d = {}
    d['folder'] = path[:-neg_pos]
    d['path'] = path
    d['filename'] = m[0]
    d['iso2'] = m[1]
    d['type'] = m[2]
    d['return_period'] = int(m[4])
    d['tile'] = int(m[5])
    d['defended'] = m[3]
    return d


def get_param_info(flist):
    lis = [get_basic_info(f) for f in flist]
    d = {}
    d['folder'] = lis[0]['folder']
    d['flist'] = flist
    d['defended'] = lis[0]['defended']
    d['iso2'] = lis[0]['iso2']
    d['type'] = lis[0]['type']
    d['rps'] = sorted(pd.Series([d['return_period']for d in lis]).unique())
    d['tiles'] = sorted(pd.Series([d['tile']for d in lis]).unique())
    return d
# Loading SSBN dataset


def get_ssbn_array(fname, return_geotransform=False):
    """Open a gtiff and convert it to an array."""
    tif = gdal.Open(fname)
    a = tif.ReadAsArray()
    a = convert_nulls(a)
    # print(gdal.Info(tif))
    if return_geotransform:
        gt = tif.GetGeoTransform()
        # print(gt)
        # return a tuple of array, geotransform, xysize
        return a, gt, (tif.RasterXSize, tif.RasterYSize)
    return a


# SSBN Processing
# Convert to boolean
# GPW Processing
# Nearest neighbor to ssbn grid
# Basin processing`
# Rasterizing to SSBN grid
# 1/0


# Loop_through_tifs:
# Loop through the rows of the basin GeoDataFrame,
# create a separate array for whether each point in a tiff is in the polygon or not
# Multiply inPolygon * population * bool_depth = pop_affected
# Multiply inPolygon * population = population in basin
# Add both counts to the dataframe.


# Write function that tells you whether cells in a tiff are inside a polygon or not.

# Use gricells_to_adm0 function to simulate floods that are perfectly correlated across hydrobasins

# def estimate_affected(row, country, params):
#     # Loop through tiles for each basin
#     print(row.name)
#     for tile in params['tiles']:
#         # Get the raster of basin == the current basin
#         fname = './data_exposures/{}_hybas_raster_{}.tif'.format(params['iso2'], tile)
#         hybas = gtiff_to_array(fname)
#         hybas_mask = (hybas == row.name)
#         # Get the raster of population
#         exp_fname = './data_exposures/gpw/{}_population_count_{}.tif'.format(params['iso2'], tile)
#         exp = gtiff_to_array(exp_fname)
#         exp[exp<0] = 0
#         # Nearest neighbor went from 30s to 3s
#         exp = exp/100
#         # Get the total population by basin and store it
#         assert hybas_mask.shape == exp.shape
#         total_pop = (hybas_mask*exp)
#         row['basin_pop'] += total_pop.sum()
#         # Loop through return periods
#         for rp in params['rps']:
#             # Get the raster of boolean floods by return period
#             fname = '{}{}-{}{}-{}-{}.tif'.format(params['folder'],c,params['type'],params['defended'], str(int(rp)), tile)
#             floods = get_ssbn_array(fname)
#             # Store the population affected for floods
#             total_affected = vulnerability(floods, total_pop).sum()
#             row[rp] += total_affected
#     return row
