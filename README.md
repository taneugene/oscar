# OSCAR
This is an Open Source Catastrophe And Resilience model.
The goal of this project is to make a general framework for modelling hazard data from a variety of sources using datasets commonly used by the World Bank and other multilateral organizations. Whereas some of the datasets supported are proprietary, most will be open source. 

This project is supported by [GFDRR](https://www.gfdrr.org/en) a Trust Fund within the Climate Change Group at the World Bank.

Developed by [Eugene Tan Perk Han](eugene.tan@columbia.edu). Please do contribute by submitting pull requests, raising issues and questions as needed, especially for those questions and issues that others may be interested in learning about or being able ot answer. 

## Setup

Set up a virtual environment for this project. I prefer using anaconda/miniconda.

Run the following:
`git clone https://github.com/jmat# Setup

Set up a virtual environment for this project. I prefer using anaconda/miniconda.

Run the following:
```
git clone https://github.com/taneugene/oscar
conda create -n oscar python=3.7 pip gdal
conda activate oscar
conda install -y matplotlib jupyter ipykernel seaborn geopandas
conda install -y rasterio -c conda-forge 
```

## Downloads

### Geospatial Boundaries
Get the GAUL dataset from the world bank microcatalog. 
put it in data/admin/20160921_gaul_geojson_topojson.zip
Then
```
cd data/admin
unzip 20160921_gaul_geojson_topojson.zip
cd ../..
```

### Hydrobasins
go to the [hydrobasins](data/hydrobasins) folder and then run the download_data.sh script. You may have to use `chmod +x` to give your computer the ability to run the script.  

### Hazard Data

#### SSBN/Fathom



## Code
The [main file of this program](main.ipynb) runs in a jupyter notebook since it is meant to be edited and visualized. However, it is supported by additional helper libraries found in the [lib folder](./lib).