

# Unzips and prepares all data, stores an admin layer, cropped gridded layer,
# exposure layer, hydrological boundary layer for each country or admin level.

# Unzip all SSBN data
if unzip_exposures:
    data_haz = './data_hazards/'
    inputs = os.path.join(data_haz, 'ssbn/')
    zips = sorted(glob.glob(inputs + '*.zip'))
    for zip in zips:
        ssbn.unzip(zip, inputs)

    # Check availability of both folders
    dir_fluvial, dir_pluvial = ssbn.folders(country)
    flist = sorted(glob.glob(dir_fluvial + '*'))
    ssbn.get_basic_info(flist[0])


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

# Function to simulation floods from a _df


def simulate_losses(_df, n=int(1E5), iso2='AR'):
    """
    maps randomly generated probabilities to damages.  iteratively does this
    Adapted from bwalsh1/hh_resilience_model"""
    if type(_df.index) == pd.MultiIndex:
        spatial_unit = _df.index.names[-1]
        multi = True
    else:
        spatial_unit = _df.index.name
    _df[1] = 0
    _df = _df[sorted(_df.columns)]
    _df = _df.stack().to_frame()
    rps = np.array(list(_df.index.levels[-1].astype(int)))
    if rps[0] != 1.:
        rps = np.append([1.], [rps])
    inv_rps = [1 / i for i in rps]
    # final rps that you want to be able to comparae against GAR
    final_rps = [1, 20, 50, 100, 250, 500, 1000, 1500, 2000]
    # create dataframe of return periods
    years = np.arange(0, n).astype(int)
    loss = pd.DataFrame(index=_df.unstack().index, columns=years,
                        data=1 / np.random.uniform(0, 1, (_df.unstack().shape[0], n)))
    if not multi:
        loss['iso2'] = iso2
        loss.reset_index().set_index(('iso2', spatial_unit))
    # generate random numbers using a lookup on numpy arrays
    # (np.searchsorted(rps, loss.values, side = 'right')-1)
    # Get the relevant return period to look up based on the probability
    loss[years] = (np.searchsorted(rps, loss.values, side='right') - 1)
    # lookup the relevant damage by basin by
    loss = loss.apply(lambda row: _df.loc[row.name].values[row.values].reshape(
        n), axis=1, result_type='broadcast')
    lossc = loss.sum(level=_df.index.names[:-2])
    lossc = lossc.apply(lambda row: row.sort_values(
        ascending=False), axis=1, result_type='broadcast')
    losscrp = lossc.values[:, (n / np.array(final_rps)).astype(int) - 1]

    if multi:
        # Get an empty dataframe with country, final rps as the x axis
        final_exceedance = pd.DataFrame(
            index=lossc.index, columns=final_rps, data=losscrp)
    else:
        final_exceedance = pd.DataFrame(
            index=[c], columns=final_rps, data=losscrp)
    return final_exceedance

# Builds a df with return period x basin to simulate floods in each basin, which
# is then multiplied by a basin x country matrix to give a return period x country matrix.


# load up geopandas dataframes with relative damages
countries = ['AR', 'PE', 'CO']
d = []
# Make a dataframe from all geojsons with a iso2/flood_type/basin index
# These geojsons include return periods x basin damages.
for c in countries:
    for pf in ['FU', 'PU']:
        # fname = "{}_floods_{}.geojson".format(c, pf)
        # Will be deprecated next version
        fname = "{}_floods_rp_{}.geojson".format(c, pf)
        fname = os.path.join('output', fname)
        df = gpd.read_file(fname)
        df['iso2'] = c
        df['flood_type'] = pf
        df.index = pd.Int64Index(df.index)
        df.index.name = 'basin'
        df = df.reset_index().set_index(['iso2', 'flood_type', 'basin'])
        d.append(df)
df = pd.concat(d)
total_pop = df['basin_pop'].astype(float).astype(int)
# Filter columns ONLY to the columns with return period data
print("deleted columns:", df.columns[:list(df.columns).index('basin_pop'):])
df = df[df.columns[list(df.columns).index('basin_pop'):]]
geometry = df['geometry']
df = df.drop(['basin_pop', 'geometry'], axis=1)
df.columns = df.columns.astype(int)
df = df.astype(float)
df['geometry'] = geometry
df.loc['PE'].plot(1000, legend=True)
affected = simulate_losses(df)
fas = affected.divide(total_pop.sum(level=affected.index.names[:2]), axis=0)
fas.columns.name = 'rp'
fas.stack().to_csv('output/ssbn_derived_fas.csv')

def estimate_affected(df, params):
    # Loop through tiles
    for tile in params['tiles']:
        # Get the raster of basin == the current basin
        fname = './data_exposures/{}_hybas_raster_{}.tif'.format(
            params['iso2'], tile)
        hybas = gtiff_to_array(fname)
        exp_fname = './data_exposures/gpw/{}_population_count_{}.tif'.format(
            params['iso2'], tile)
        exp = gtiff_to_array(exp_fname)
        exp[exp < 0] = 0
        # Nearest neighbor went from 30s to 3s
        exp = exp / 100
        assert hybas.shape == exp.shape
        print('TILE {} of {} tiles'.format(tile, len(params['tiles'])))
        print('basin raster: {}'.format(fname))
        print('asset raster: {}'.format(exp_fname))
        # Create a list of tiles to run over that resets after each tile, if 0 it'll be skipped when computing damages
        df['check_this_tile'] = 0
        # Get assets by spatial unit
        df = df.apply(get_assets_by_spatial_unit, axis=1,
                      result_type='broadcast', basin_grid=hybas, exp=exp)
        # Loop through rps
        for rp in params['rps']:
            # Get the raster of floods by return period
            ssbn_fname = '{}{}-{}{}-{}-{}.tif'.format(
                params['folder'], c, params['type'], params['defended'], str(int(rp)), tile)
            print('ssbn raster: {}'.format(ssbn_fname))
            floods = get_ssbn_array(ssbn_fname)
            # Store the % damage from floods
            damages_percent = vulnerability(floods)
            damages_total = damages_percent * exp
            df = df.apply(get_damage_by_spatial_unit, axis=1, damages=damages_total,
                          basin_grid=hybas, rp=rp, result_type='broadcast')
        df = df.drop('check_this_tile', axis=1)
    return df

# Resample assets grids (e.g. gpw) to the tile sizes that ssbn gives
country = ['NG', 'AR', 'PE', 'CO']

[resample_assets_to_ssbn_tiles(f) for c in country for f in sorted(
    glob.glob(folders(c)[0] + '*'))]
# Unzip all basin data
basins = './data_exposures/hydrobasins/'
[unzip(f, basins) for f in glob.glob(basins + '*.zip')]
# Mosaic all the GPW data to the country level
for c in country:
    flist = sorted(glob.glob("data_exposures/gpw/{}_*".format(c)))
    mosaic(flist)
# # Test mosaic on the 250 return periods for fluvial only - it works, but you don't need this
# for c in country:
#     flist = sorted(glob.glob(folders(c)[0]+'*250*'))
#     mosaic(flist)

c = 'AR'
folder = folders(c)[0]
fname = 'data_exposures/gpw/{}_population_count_all.tif'.format(c)
df = filter_polygons(fname)
tiles = sorted((glob.glob(folder + '*')))
params = get_param_info(tiles)
floods, exposures = get_tiles(c, folder, params['rps'][0])
a, gt, s = get_ssbn_array(floods[0], True)
b = get_bounds(floods[0])


# Get the df of basins
fname = 'data_exposures/gpw/{}_population_count_all.tif'.format(c)
df = filter_polygons(fname=fname)
# basins don't change with return period
floods, exposures = get_tiles(c, folder, params['rps'][0])
for tile in floods:
    print(tile)
    d = get_basic_info(tile)
    outras = './data_exposures/{}_hybas_raster_{}.tif'.format(
        d['iso2'], d['tile'])
    # print(outras)
    Rasterize(df, tile, outras)
# Initialize to 0
df['basin_pop'] = 0
for rp in params['rps']:
    df[rp] = 0
# Apply over basins
df = estimate_affected(df, params)
df.columns = [str(a) for a in df.columns]
df.plot('basin_pop')
df.to_file("output/{}_floods_{}.geojson".format(c,
                                                params['type'] + params['defended']), driver='GeoJSON')
