import gdal
import json
import requests
from ftplib import FTP
import os
import shutil
import urllib.request as request
from contextlib import closing

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
def get_asset_tif(source):
    tif = gdal.Open(get_asset_fname(source))
    return tif
def get_asset_array(source):
    tif = get_asset_tif(source)
    a = tif.ReadAsArray()
    gt = tif.GetGeoTransform()
    shape = (tif.RasterXSize, tif.RasterYSize)
    return a, gt, shape

def worldpop(iso3, year = 2020):
    url = "https://www.worldpop.org/rest/data/pop/wpgp?iso3={}".format(iso3)
    r = requests.get(url)
    metadata = json.loads(r.content)
    metadata = metadata['data'][year - 2000]
    url = metadata['files'][0] # worldpop returns a list with one element
    # Find the last instance of / to get the same file name
    fname = url[len(url) - url[::-1].find('/'):]
    path = 'data/worldpop/{}'.format(fname)
    if not os.path.exists(path):
        print('Downloading {} to {}'.format(url, fname))
        with closing(request.urlopen(url)) as r:
            with open(path, 'wb') as f:
                shutil.copyfileobj(r, f)
    else:
        print('{} exists'.format(fname))
    return path