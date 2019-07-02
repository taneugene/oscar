# python ecosystem libraries
import glob
import os
import numpy as np
import pandas as pd
import sys
# user defined libraries
sys.path.append('lib/')
# import ssbn
import hydrobasins
import tifs
import geopandas as gpd

# Model parameters
unzip_all = True

# Unzip all data
if unzip_all:
    data_haz = './data_hazards/'
    inputs = os.path.join(data_haz, 'ssbn/')
    zips = sorted(glob.glob(inputs+'*.zip'))
    for zip in zips:
        ssbn.unzip(zip, inputs)

    # Check availability of both folders
    dir_fluvial, dir_pluvial = ssbn.folders(country)
    flist = sorted(glob.glob(dir_fluvial+'*'))
    ssbn.get_basic_info(flist[0])

def simulate_losses(_df, n = int(1E5), iso2 = c):
    """Adapted from Brian Walsh hh_resilience_model"""
    if type(_df.index) == pd.MultiIndex:
        spatial_unit = _df.index.names[-1]
        multi = True
    else:
        spatial_unit = _df.index.name
    _df[1] = 0
    _df = _df[sorted(_df.columns)]
    _df = _df.stack().to_frame()
    rps = np.array(list(_df.index.levels[-1].astype(int)))
    if rps[0] != 1.: rps = np.append([1.],[rps])
    inv_rps = [1/i for i in rps]
    # final rps that you want to be able to comparae against GAR
    final_rps = [1, 20, 50, 100,250, 500, 1000,1500,2000]
    # create dataframe of return periods
    years = np.arange(0, n).astype(int)
    loss = pd.DataFrame(index=_df.unstack().index, columns=years, data = 1/np.random.uniform(0,1,(_df.unstack().shape[0],n)))
    if not multi:
        loss['iso2'] = c
        loss.reset_index().set_index(('iso2',spatial_unit))
    # generate random numbers using a lookup on numpy arrays
    # (np.searchsorted(rps, loss.values, side = 'right')-1)
    # Get the relevant return period to look up based on the probability
    loss[years] = (np.searchsorted(rps, loss.values, side = 'right')-1)
    # lookup the relevant damage by basin by
    loss = loss.apply(lambda row: _df.loc[row.name].values[row.values].reshape(n), axis = 1, result_type='broadcast')
    lossc = loss.sum(level = _df.index.names[:-2])
    lossc = lossc.apply(lambda row: row.sort_values(ascending =False), axis = 1, result_type = 'broadcast')
    losscrp = lossc.values[:,(n/np.array(final_rps)).astype(int)-1]

    if multi:
        # Get an empty dataframe with country, final rps as the x axis
        final_exceedance = pd.DataFrame(index= lossc.index,columns = final_rps, data = losscrp)
    else:
        final_exceedance = pd.DataFrame(index= [c],columns = final_rps, data = losscrp)
    return final_exceedance



# load up geopandas dataframes with relative damages
countries = ['AR', 'PE', 'CO']
d  = []
# Make a dataframe from all geojsons with a iso2/flood_type/basin index
for c in countries:
    for pf in ['FU','PU']:
        # fname = "{}_floods_{}.geojson".format(c, pf)
        # Will be deprecated next version
        fname = "{}_floods_rp_{}.geojson".format(c, pf)
        fname = os.path.join('output', fname)
        df = gpd.read_file(fname)
        df['iso2'] = c
        df['flood_type'] = pf
        df.index = pd.Int64Index(df.index)
        df.index.name = 'basin'
        df = df.reset_index().set_index(['iso2','flood_type','basin'])
        d.append(df)
df = pd.concat(d)
total_pop = df['basin_pop'].astype(float).astype(int)
# Filter columns ONLY to the columns with return period data
print("deleted columns:", df.columns[:list(df.columns).index('basin_pop'):])
df = df[df.columns[list(df.columns).index('basin_pop'):]]
df = df.drop(['basin_pop','geometry'], axis = 1)
df.columns = df.columns.astype(int)
df = df.astype(float)
affected = simulate_losses(df)
fas = affected.divide(total_pop.sum(level = affected.index.names[:2]), axis = 0)
fas.columns.name = 'rp'
fas.stack().to_csv('output/ssbn_derived_fas.csv')




# Get to


# Ideal Structure of model
# Hazard class
    # Loads hazard data
    # Stores extents, xy grids
    # Return period management
    # Gives summary statistics
    # Crops to country borders if necessary.
# Exposure class
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
