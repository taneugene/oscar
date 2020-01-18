# Ingest SSBN data

# This script just grabs ssbn data given the country and different assumptions 
# on the return period and type of flood. 
# Inputs: zip file 
# Want the final output to be called like hazard.ssbn.get('AR','fluvial','defended')
# and to return an a structured glob of AR fluvials at different tiles and 
# return periods OR have them all in memory.  

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

# # Test unzip
# folder = 'data/ssbn'
# path = folder + '/AR_pluvial_undefended.zip'
# unzip (path, folder)

def folders(c, flood_type, defended='undefended'):
    """checks availability of the folder for a particular country, flood type and defendedness"""
    folder = "./data/ssbn/{}_{}_{}/".format(c, flood_type, defended)
    if exists(folder):
        return folder
    else:
        zip = folder[:-1] + ".zip"
    if exists(zip) and isfile(zip):
        unzip(zip, "data/ssbn")
        return folder
    else:
        print("Neither folder nor zip file exists in the correct place")
        return False

# # Test folders
# c = 'AR'
# flood_type = 'fluvial'
# folders(c, flood_type)

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