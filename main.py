# Public libraries
import glob
import os
import sys

# User defined libraries
sys.path.append('lib/')
import ssbn

# Model params
unzip_all = False
c = "NG"

# Unzip all data
if unzip_all:
    data_haz = './data_hazards/'
    inputs = os.path.join(data_haz, 'ssbn/')
    zips = sorted(glob.glob(inputs+'*.zip'))
    for zip in zips:
        ssbn.unzip(zip, inputs)

ssbn.availability(c)
