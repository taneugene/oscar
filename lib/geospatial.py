# Tif loading functions
import geopandas as gpd
import rasterio
from rasterio import features
import gdal
from os.path import exists
import numpy as np
from shapely.geometry import box

def shapefile2raster(shapefile, inras, outras):
    print('burning shapefile geometry to a raster')
    if exists(outras):
        print('{} already exists'.format(outras))        
        return rasterio.open(outras).read(1)
    with rasterio.open(inras) as src:
        kwargs = src.meta.copy()
        kwargs.update({
            'driver': 'GTiff',
            'compress': 'DEFLATE',
            'dtype':'int32' # This assumes the index is only integers...
        })
        transform = src.transform
        nodata = src.nodata
        out_shape = src.read(1).shape
    # print(kwargs)
    assert nodata != 0 # make sure it isn't 0
    # BUG IN SOURCE CODE: fill isn't implemented well in rasterio, still defaults to 0
    # quick workaround # use default_value instead?
    # shift = 1
    with rasterio.open(outras, 'w', **kwargs) as dst:
        # this is where we create a generator of geom, value pairs to use in rasterizing
        shapes = ((geom, value) for geom, value in zip(
            shapefile.geometry, shapefile.index))
        burned = features.rasterize(
            shapes=shapes, fill=nodata, default_value=nodata, out_shape = out_shape, transform=transform)
        dst.write_band(1, burned.astype(kwargs['dtype']))
        return burned 

def get_bounds(fname, shp=False):
    tif = gdal.Open(fname)
    gt, ts = tif.GetGeoTransform(), (tif.RasterXSize, tif.RasterYSize)
    if shp:
        return [Point(gt[0], gt[3]), Point(gt[0] + gt[1] * ts[0], gt[3] + gt[5] * ts[1])]
    else:
        return [gt[0], gt[3], gt[0] + gt[1] * ts[0], gt[3] + gt[5] * ts[1]]

# Getting exposure data
def get_tiles(country, folder, rp):
    floods = sorted(glob.glob(folder + country + \
                    '-*-' + str(rp) + '-*.tif'))
    exposures = sorted(glob.glob('data_exposures/gpw/{}*'.format(c)))[:-1]
    return floods, exposures
# Getting basin data

def filter_polygons(country_tif, hb='./data/geobounds/hydrobasins/hybas_sa_lev04_v1c.shp'):
    """Filters a shapefile based on whether the polygons intersect with
    a bounding box based on a geotiff fname."""
    # TODO: convert getbounds to a rasterio function. Should be super easy 
    # get south american basins
    # pfa = sorted(glob.glob(basins+'*sa*.shp'))
    # Use pfascetter level 4
    # gpd.read_file(pfa[3])['geometry'].plot()
    #  Get a list of hydrobasins
    df = gpd.read_file(hb)
    # Get the extent of
    b = gpd.GeoSeries(box(*get_bounds(country_tif, False)),
                      crs={'init': 'epsg:4326'})
    # Need to forward the crs manually wtf geopandas
    b = gpd.GeoDataFrame(b, columns=['geometry'], crs=b.crs)
    return gpd.overlay(b, df, how='intersection')





def gtiff_to_array(fname, get_global=False):
    """Open a gtiff and convert it to an array.  Store coordinates in global variables if toggle is on"""
    tif = gdal.Open(fname)
    a = tif.ReadAsArray()
    gt = tif.GetGeoTransform()
    if get_global:
        print(gdal.Info(tif))
        global lons, lats, loni, lati, xx, yy, xi, yi
        lons = np.array([round(gt[0] + gt[1] * i, 5)
                         for i in range(a.shape[1])])
        lats = np.array([round(gt[3] + gt[5] * i, 5)
                         for i in range(a.shape[0])])
        loni = np.array([i for i in range(a.shape[1])])
        lati = np.array([i for i in range(a.shape[0])])
        xx, yy = np.meshgrid(lons, lats)
        xi, yi = np.meshgrid(loni, lati)
    return a

def mosaic(flist):
    """Mosaics or merges by tiling several files"""
    print("\nCombining the following files...")
    print(flist)
    out_fp = flist[0][:-5] + 'all.tif'
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
# Geospatial operations

def convert_nulls(ssbn_array):
    """SSBN has several null values corresponding to sea and null value tiles"""
    a = ssbn_array
    # Null values, no reading
    a[a == -9999] = np.nan
    # Null values, sea/ocean tiles with no possible flooding.
    a[a == 999] = np.nan
    return a

def get_assets_by_spatial_unit(row, basin_grid, exp):
    """In a df with a different spatial unit in each row whose index corresponds to the
    numbers in basin_grid,iteratively create a mask for each basin and sum the assets over each basin
    """
    hybas_mask = (basin_grid == row.name)
    if hybas_mask.sum() == 0:
        return row
    tile_basin_assets = exp * hybas_mask
    total = tile_basin_assets.sum()
    if total > 0:
        # Set a toggle for this basin, tile combination to 1, will skip later when apply % damages if 0.
        row.check_this_tile = 1
        print("Adding {} population to basin {}".format(total, row.name))
        row['basin_pop'] += total
        return row
    else:
        return row
# Resampling to resolution of SSBN grid

def resample_assets_to_ssbn_tiles(ssbn_fname, asset_fname=None, resampleAlg='near'):
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
    outfile = '{}_{}_{}.tif'.format(
        ssbn_info['iso2'], asset_info['type'], ssbn_info['tile'])
    if exists(outdir + outfile):
        print('skipping {}'.format(outfile))
    # Use nearest neighbor method to create a file
    else:
        # a,gt,ts = array, geotransform, xy_tiles
        a, gt, ts = get_ssbn_array(ssbn_fname, True)
        # secs = str(int(gt[1]*60*60))
        bounds = get_bounds(ssbn_fname)
        print('creating {}'.format(outfile))
        gdal.Translate(outdir + outfile, get_asset_tif(),
                       xRes=gt[1], yRes=gt[5], projWin=bounds, resampleAlg=resampleAlg, creationOptions=["COMPRESS=DEFLATE"])

# Damage function
def get_damage_by_spatial_unit(row, damages, basin_grid, rp):
    """In a df with a different spatial unit in each row whose index corresponds to the
    numbers in basin_grid, iteratively create a mask for each basin and sum the damages over each basin
    """
    if not row.check_this_tile:
        return row
    hybas_mask = (basin_grid == row.name)
    if hybas_mask.sum() == 0:
        return row
    tile_basin_damages = damages * hybas_mask
    total = tile_basin_damages.sum()
    print('{} damaged in basin {} at rp = {}'.format(total, row.name, rp))
    row[rp] += total
    return row