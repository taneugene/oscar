# python ecosystem libraries
import glob
import os
import sys

# user defined libraries
sys.path.append('lib/')
import ssbn

# Model parameters
unzip_all = True
country = "AR"

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






# Function to look through a directory and merge tifs into one big tif?

# Function to convert a gtiff to an array
    # Function to get all the relevant details and metadata from a tif





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
