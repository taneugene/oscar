import gc
import gdal
import glob
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import sys
%matplotlib inline

myC = 'CO'

# Function to load GEOTIFFS filetypes,
def gtiff_to_array(fname, get_global = False):
    """Open a gtiff and convert it to an array.  Store coordinates in global variables if toggle is on"""
    tif = gdal.Open(fname)
    a = tif.ReadAsArray()
    gt = tif.GetGeoTransform()
    print(gt)
    if get_global:
        print(gdal.Info(tif))
        global lons, lats, loni, lati, xx, yy, xi, yi
        lons = np.array([round(gt[0]+gt[1]*i,5) for i in range(a.shape[1])])
        lats = np.array([round(gt[3]+gt[5]*i,5) for i in range(a.shape[0])])
        loni = np.array([i for i in range(a.shape[1])])
        lati = np.array([i for i in range(a.shape[0])])
        xx,yy = np.meshgrid(lons, lats)
        xi,yi = np.meshgrid(loni,lati)
    return
def random_to_loss(County,pval):
    for _nrp, _rp in enumerate(inv_rps):
        if pval > _rp:
            try: return int(_df.loc[(County,rps[_nrp-1])])
            except: return 0
            # ^ this is because the RP=0 isn't in the df
    # print(_df.loc[(County,rps[-1])].values)
    return int(_df.loc[(County,rps[-1])])
def gricells_to_adm0(myC = 'CO', _haz='PF', src = 'pop_affected.csv'):
    """Assumes perfect correlation within an individual grid cell and resample the exceedance curve from the grid cell level to the national level
    This is to lower the overestimation of impacts since a 1000 year flood doesn't affect the whole country at the maximum exceedance at the same time"""
    global _df
    # Find the pop/space affected
    var = src[:src.index('_')]
    # Get the return period x basin data
    _df = pd.read_csv(src).drop(var, axis = 1)
    # Assign names to the indices
    _df.index.name = 'gridcell'
    _df.columns.name = 'rp'
    # assign dtypes
    _df.columns = _df.columns.astype(int)
    # get a basin,rp index
    _df = _df.stack().to_frame()
    global rps,inv_rps
    # Get a list of RPS
    rps = list(_df.index.levels[1].astype(int))
    # If the first rp isn't 1, then add it to the beginning and assume that there isn't any damage
    if rps[0] != 1.: rps = np.append([1.],[rps])
    # Calculate inverse RPS
    inv_rps = [1/i for i in rps]
    # Calculate final rps... any reason why this is missing 5?
    final_rps = [1, 20, 50, 100,250, 500, 1000,1500,2000]
    # Get an empty dataframe with country, final rps as the x axis
    final_exceedance = pd.DataFrame(index= pd.MultiIndex.from_product([[myC],final_rps]))
    # Set loss to None
    final_exceedance['loss'] = None
    # create dataframe to store random numbers
    loss = pd.DataFrame(index=_df.sum(level='gridcell').index).reset_index()
    loss['myC'] = myC
    loss.set_index(['myC','gridcell'], inplace = True)
    lossc = loss.sum(level = 'myC')
    loss = loss.reset_index().set_index('myC')

    # generate random numbers
    NYECOS = int(1E4) # <-- any multiple of 10K
    for _yn in range(NYECOS):
        loss['_'] = [np.random.uniform(0,1) for i in range(loss.shape[0])]
        loss['y'+str(_yn)] = loss.apply(lambda x:random_to_loss(x.gridcell,x['_']),axis=1)

        if _yn != 0 and (_yn+1)%500 == 0:

            lossc = pd.concat([lossc,loss.drop('_',axis=1).sum(level='myC')],axis=1)
            loss = loss[['gridcell']]
            print(_yn+1)

    for _reg in loss.index.values:
        aReg = lossc.loc[_reg].sort_values(ascending=False).reset_index()

        for _frp in final_rps:
            final_exceedance.loc[(_reg,_frp),'loss'] = float(aReg.iloc[int((NYECOS-1)/_frp)][_reg])

    total_pop = pd.read_csv('{}_affected.csv'.format(var))[var].sum()
    (final_exceedance/total_pop).to_csv('../inputs/'+myC+'regional_exceedance_'+_haz+src[:2]+'.csv')

gricells_to_adm0(src = 'pop_affected.csv')
gricells_to_adm0(src = 'space_affected.csv')
