import rasterio
fname = "./data_hazards/ssbn/AR_pluvial_undefended/AR-PU-10-1.tif"

dataset = rasterio.open(fname)

print(dataset.name)
print(dataset.mode)
print(dataset.closed)
print(dataset.count)
print(dataset.width)
print(dataset.height)
print(dataset.indexes)
print(dataset.dtypes)
print(dataset.bounds)
print(dataset.transform)


dataset.transform * (dataset.width, dataset.height)

dataset.crs

type(dataset.read(1))
print(gdal.info)
dataset.bounds

dataset.xy(dataset.height//2, dataset.width//2)
