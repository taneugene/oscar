import gdal

def gpw_basic_info(asset_fname):
    f = asset_fname[-(asset_fname[::-1].find('/')):]
    d = {}
    d['dataset'] = f[:f.find('_population')]
    d['resolution'] = f[f.find('30_sec'):]
    d['type'] = f[f.find('pop'):f.find('_rev11')]
    return d
def get_asset_fname():
    s = "data/exposures/gpw/gpw_v4_population_count_rev11_2015_30_sec.tif"
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
