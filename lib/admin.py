import pandas as pd
import geopandas as gpd
import glob
import os

# CONVERT ANY COUNTRY INPUT TO A UNIQUE NAME #
##############################################

# List of lookup tables to iterate over to get a unique values
country_wbcountry = pd.read_csv('data/admin/any_name_to_wb_name.csv', index_col=0).squeeze()
iso2_wbcountry = pd.read_csv('data/admin/names_to_iso.csv', index_col=1)['country'].squeeze()
iso3_wbcountry = pd.read_csv('data/admin/names_to_iso.csv', index_col=2)['country'].squeeze()
country_lookups = [country_wbcountry,iso2_wbcountry, iso3_wbcountry]

def in_series(dict_like, key):
    """Check if key is in dict-like, instead of throwing an error when not found, return None"""
    try:
        name = dict_like[key]
        return name
    except:
        return None

def get_wbcountry(country, lookups = country_lookups):
    """iteratively look through the lookup series and return the name if found.  Otherwise, return None"""
    if lookups == 'iso2':
        n = in_series(pd.read_csv('data/admin/names_to_iso.csv', index_col=0)['iso2'].squeeze(), country)
        if n: return n
    elif lookups =='iso3':
        n = in_series(pd.read_csv('data/admin/names_to_iso.csv', index_col=0)['iso3'].squeeze(), country)
        if n: return n
    elif lookups == country_lookups:
        for l in lookups:
            n = in_series(l, country)
            if n: return n
    return None

# GET ADMINISTRATIVE BOUNDARIES FROM THE GAUL DATASET #
#######################################################

# Use the GeoJSON data from the GAUL dataset.
# The shapefile is crappy and there isn't a widely used TopoJSON library in python
# The file sizes here are big, but the alternative to reading in directly using
# gpd.read_file is to write a library that would stream GEOJSON.

adm_path = "data/admin/20160921_GAUL_GeoJSON_TopoJSON/GeoJSON/"
adm_naming_convention = "g2015_2014_{0}.geojson"

def get_boundaries_fpath(level, adm_path = adm_path, adm_naming_convention = adm_naming_convention):
    """
    Check if files with the adm_path, naming convention, and level exist in the
    adm_folder
    """
    if not os.path.exists(adm_path):
        assert False, "Geospatial bounds folder (GAUL dataset is unavailable)"
    path = os.path.join(adm_path, adm_naming_convention).format(level)
    if os.path.exists(path):
        return path
    else:
        assert False, "Files at that administrative level do not exist\n check {}".format(path)

def get_adm_boundaries(level, country,adm_path = adm_path, adm_naming_convention = adm_naming_convention):
    """
    Returns the adm1 boundaries as a GeoDataFrame of a country, if country isn't in the GeoJSON,
    print the full list of unique countries in the dataset"""
    df = gpd.read_file(get_boundaries_fpath(level,adm_path = adm_path, adm_naming_convention = adm_naming_convention))
    filtered = df.ADM0_NAME == country
    if filtered.sum() == 0:
        print('country not found')
        return sorted(df.ADM0_NAME.unique())
    else:
        return df[df.ADM0_NAME == country]
