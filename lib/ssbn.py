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
from shapely.geometry import box,Point, Polygon
import zipfile

def unzip(path, pwd):
    """Unzips a zipfile unless the output folder already exists
    """
    # Get a set of current files
    fl = set(glob.glob(pwd+"*.zip"))
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
def gtiff_to_array(fname, get_global = False):
    """Open a gtiff and convert it to an array.  Store coordinates in global variables if toggle is on"""
    tif = gdal.Open(fname)
    a = tif.ReadAsArray()
    gt = tif.GetGeoTransform()
    if get_global:
        print(gdal.Info(tif))
        global lons, lats, loni, lati, xx, yy, xi, yi
        lons = np.array([round(gt[0]+gt[1]*i,5) for i in range(a.shape[1])])
        lats = np.array([round(gt[3]+gt[5]*i,5) for i in range(a.shape[0])])
        loni = np.array([i for i in range(a.shape[1])])
        lati = np.array([i for i in range(a.shape[0])])
        xx,yy = np.meshgrid(lons, lats)
        xi,yi = np.meshgrid(loni,lati)
    return a
def get_basic_info(path):
    """Retrieves information from the SSBN filename convention and
    stores it as a dictionary.
    """
    # print(path)
    neg_pos = path[::-1].find('/')
    fname = path[-neg_pos:]
    # print(fname)
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
    d['iso2'] = lis[0]['iso2']
    d['type'] = lis[0]['type']
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
    a = tif.ReadAsArray()
    gt = tif.GetGeoTransform()
    shape = (tif.RasterXSize, tif.RasterYSize)
    return a, gt, shape
def resample_assets_to_ssbn_tiles(ssbn_fname, asset_fname = None, resampleAlg = 'near'):
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
        bounds = get_bounds(ssbn_fname)
        print('creating {}'.format(outfile))
        gdal.Translate(outdir + outfile, get_asset_tif(), xRes = gt[1], yRes = gt[5], projWin = bounds, resampleAlg = resampleAlg, creationOptions = ["COMPRESS=DEFLATE"])
def mosaic(flist):
    """Mosaics or merges by tiling several files"""
    print("\nCombining the following files...")
    print(flist)
    out_fp = flist[0][:-5]+'all.tif'
    print('Output file is {}'.format(out_fp))

    # Iterates and opens files using rasterio and appends to list
    files_to_mosaic = []
    for f in flist:
        src = rasterio.open(f)
        files_to_mosaic.append(src)
    # rasterio.merge.merge over list
    out_tif, out_trans = merge(files_to_mosaic)
    # Configure output metadata
    out_meta = src.meta.copy()
    # print(src.profile)
    out_meta.update({'width': out_tif.shape[2],
                     'height': out_tif.shape[1],
                     'transform': out_trans,
                    # Docs say that this should be compression, but 'compress'
                    # is actually the toggle that works.
                    # Makes a 10x difference to filesize!
                     'compress': "DEFLATE"
                     })
    with rasterio.open(out_fp, "w", **out_meta) as dest:
        dest.write(out_tif)
    return True
def get_bounds(fname, shp = False):
    tif = gdal.Open(fname)
    gt,ts = tif.GetGeoTransform(),(tif.RasterXSize, tif.RasterYSize)
    if shp:
        return [Point(gt[0],gt[3]),Point(gt[0]+gt[1]*ts[0], gt[3]+gt[5]*ts[1])]
    else:
        return [gt[0],gt[3],gt[0]+gt[1]*ts[0], gt[3]+gt[5]*ts[1]]
def filter_polygons(fname, hb = './data_exposures/hydrobasins/hybas_sa_lev04_v1c.shp'):
    """Filters a shapefile based on whether the polygons intersect with
    a bounding box based on a geotiff fname."""
    # get south american basins
    # pfa = sorted(glob.glob(basins+'*sa*.shp'))
    # Use pfascetter level 4
    # gpd.read_file(pfa[3])['geometry'].plot()
    df = gpd.read_file(hb)
    b = gpd.GeoSeries(box(*get_bounds(fname,False)), crs = {'init': 'epsg:4326'})
    # Need to forward the crs manually wtf geopandas
    b = gpd.GeoDataFrame(b,columns = ['geometry'], crs = b.crs)
    return gpd.overlay( b, df,how = 'intersection')
def get_tiles(country, folder, rp):
    floods = sorted(glob.glob(folder+country+'-*-' + str(rp)+'-*.tif'))
    exposures = sorted(glob.glob('data_exposures/gpw/{}*'.format(c)))[:-1]
    return floods, exposures
def Rasterize(shapefile, inras, outras):
    """From: https://gist.github.com/mhweber/1a07b0881c2ab88d062e3b32060e5486"""
    with rasterio.open(inras) as src:
        kwargs = src.meta.copy()
        kwargs.update({
            'driver': 'GTiff',
            'compress': 'lzw'
        })
        windows = src.block_windows(1)
        with rasterio.open(outras, 'w', **kwargs) as dst:
            for idx, window in windows:
                out_arr = np.zeros_like(src.read(1, window=window))
                # this is where we create a generator of geom, value pairs to use in rasterizing
                shapes = ((geom,value) for geom, value in zip(shapefile.geometry, shapefile.index))
                burned = features.rasterize(shapes=shapes, fill=0, out=out_arr, transform=src.transform)
                dst.write_band(1, burned, window=window)


# Resample assets grids (e.g. gpw) to the tile sizes that ssbn gives
country = ['NG','AR','PE','CO']
[resample_assets_to_ssbn_tiles(f) for c in country for f in sorted(glob.glob(folders(c)[0]+'*'))]
# Unzip all basin data
basins = './data_exposures/hydrobasins/'
[unzip(f,basins) for f in glob.glob(basins+'*.zip')]
# Mosaic all the GPW data to the country level
for c in country:
    flist = sorted(glob.glob("data_exposures/gpw/{}_*".format(c)))
    mosaic(flist)
# # Test mosaic on the 250 return periods for fluvial only - it works, but you don't need this
# for c in country:
#     flist = sorted(glob.glob(folders(c)[0]+'*250*'))
#     mosaic(flist)


c = 'CO'
folder = folders(c)[0]
fname = 'data_exposures/gpw/{}_population_count_all.tif'.format(c)
df = filter_polygons(fname)
tiles = sorted((glob.glob(folder+'*')))
params = get_param_info(tiles)
floods, exposures = get_tiles(c,folder, params['rps'][0])
a,gt,s = get_ssbn_array(floods[0], True)
b = get_bounds(floods[0])

lons = np.array([round(gt[0]+gt[1]*i,5) for i in range(a.shape[1])])
lats = np.array([round(gt[3]+gt[5]*i,5) for i in range(a.shape[0])])
loni = np.array([i for i in range(a.shape[1])])
lati = np.array([i for i in range(a.shape[0])])
xx,yy = np.meshgrid(lons, lats)


# Try burning the basins to grid.
out_fn = './{}rasterized_basins.tif'.format(c)
# Rasterize

# After rasterizing
df.
a = Rasterize(df, floods[3], out_fn)
b = gtiff_to_array(out_fn)

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

def get_correlation_grid():
    """A simplification of the flood model is that major basins in a country are
    perfectly correlated.  We can get basin data from the
    """

# Use gricells_to_adm0 function to simulate floods that are perfectly correlated across hydrobasins

#
