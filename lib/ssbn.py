import gdal
import geopandas
import glob
import numpy as np
import os
from os.path import exists, isfile
import pandas as pd
import seaborn as sns
import re
import zipfile

def unzip(path, pwd):
    """Unzips a zipfile unless the output folder already exists
    """
    # Get a set of current files
    fl = set(glob.glob(pwd+"*"))
    # If the input pth doesn't exist, try to find the file
    if not exists(path):
        raise AssertionError("Incorrect Path")
    output_path = path[:-4]+'/'
    print("Extracting {} to {}".format(path, output_path))
    if exists(output_path):
        print("Output folder {} already exists".format(output_path))
        return
    zip_ref = zipfile.ZipFile(path, 'r')
    zip_ref.extractall(pwd)
    print("Extracted {}".format(list((set(glob.glob(pwd+"*")) - fl))[0]))
    zip_ref.close()
def folders(c):
    """checks availability of fluvial and pluvial filepaths and returns the
    folder filepaths.

    Parameters
    ----------
    c : 2 letter string for country

    Returns
    -------
    tuple(fluvial, pluvial):
        filepaths for the fluvial and pluvial undefended folder in
        the ssbn folder if available, return false otherwise. If folder doesn't exist
        but zips exist, extract using unzip then return filepaths."""

    folder = "./data_hazards/ssbn/"
    fluvial = folder+c+"_fluvial_undefended/"
    pluvial = folder+c+"_pluvial_undefended/"
    if exists(fluvial) and exists(pluvial):
        return fluvial, pluvial
    elif (exists(pluvial) and (not exists(fluvial))):
        print("Fluvial Data Folder Missing \n")
        zip = fluvial[:-1]+".zip"
    elif (exists(fluvial) and (not exists(pluvial))):
        print("Pluvial Data Folder Missing \n")
        zip = pluvial[:-1]+".zip"
    else:
        print("Data is missing")
        return False
    if isfile(zip):
        unzip(zip, folder)
        return fluvial, pluvial
    else:
        print("Zip does not exist")
        return False
def get_basic_info(path):
    """Retrieves information from the SSBN filename convention and
    stores it as a dictionary.
    """
    # print(path)
    neg_pos = path[::-1].find('/')
    fname = path[-neg_pos:]
    m = re.match("^([A-Z]{2})-([FPUM])([DU]{0,1})-([0-9]{1,4})-([0-9])*\.tif$", fname)
    d = {}
    d['path'] = path
    d['filename'] = m[0]
    d['iso2'] = m[1]
    d['type'] = m[2]
    d['return_period'] = int(m[4])
    d['tile'] = int(m[5])
    if m[3] == "D":
        d['defended'] = True
    elif m[3] == 'U':
        d['defended'] = False
    else:
        print("Regex is not capturing defended-ness from filename correctly")
        assert(False)
    return d
def gpw_basic_info(asset_fname):
    f = asset_fname[-(asset_fname[::-1].find('/')):]
    d = {}
    d['dataset'] = f[:f.find('_population')]
    d['resolution'] = f[f.find('30_sec'):]
    d['type'] = f[f.find('pop'):f.find('_rev11')]
    return d
def get_param_info(flist):
    lis = [get_basic_info(f) for f in flist]
    d = {}
    d['rps'] = sorted(pd.Series([d['return_period']for d in lis]).unique())
    d['tiles'] = sorted(pd.Series([d['tile']for d in lis]).unique())
    return d
def convert_nulls(ssbn_array):
    """SSBN has several null values corresponding to sea and null value tiles"""
    a = ssbn_array
    # Null values, no reading
    a[a == -9999] = np.nan
    # Null values, sea/ocean tiles with no possible flooding.
    a[a == 999] = np.nan
    return a
def get_ssbn_array(fname, return_geotransform = False):
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
# """Deprecated: currently only uses population count tif from GPW - replace to
# get different forms of exposuure grids. """
def get_asset_fname():
    s = "data_exposures/gpw_v4_population_count_rev11_2015_30_sec.tif"
    return s
def get_asset_tif():
    tif = gdal.Open(get_asset_fname())
    return tif
def get_asset_array():
    tif = get_asset_tif()
    return tif.ReadAsArray()
def resample_to_tile(ssbn_fname, asset_fname = None, resampleAlg = 'near'):
    """transforms an asset grid to the dimensions (x,y,step) of the ssbn tif.
    """
    if not asset_fname:
        asset_fname = get_asset_fname()
    else:
        pass
    ssbn_info = get_basic_info(ssbn_fname)
    asset_info = gpw_basic_info(asset_fname)
    # Need to check that file doesn't already exist.
    outdir = './data_exposures/gpw/'
    outfile = '{}_{}_{}.tif'.format(ssbn_info['iso2'],asset_info['type'],ssbn_info['tile'])
    if exists(outdir+outfile):
        print('skipping {}'.format(outfile))
    # Use nearest neighbor method to create a file
    else:
        # a,gt,ts = array, geotransform, xy_tiles
        a,gt,ts= get_ssbn_array(ssbn_fname, True)
        # secs = str(int(gt[1]*60*60))
        bounds = [gt[0],gt[3],gt[0]+gt[1]*ts[0], gt[3]+gt[5]*ts[1]]
        print('creating {}'.format(outfile))
        gdal.Translate(outdir + outfile, get_asset_tif(), xRes = gt[1], yRes = gt[5], projWin = bounds, resampleAlg = resampleAlg, creationOptions = ["COMPRESS=DEFLATE"])
def get_correlation_grid():
    """A simplification of the flood model is that major basins in a country are
    perfectly correlated.  We can get basin data from the
    """



country = ['AR','PE','CO','NG']
[resample_to_tile(f) for c in country for f in sorted(glob.glob(folders(c)[0]+'*'))]
basins = './data_exposures/hydrobasins/'
[unzip(f,basins) for f in glob.glob(basins+'*')]
