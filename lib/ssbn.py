import os
from os.path import exists, isfile
import glob
import zipfile

def unzip(path, pwd):
    """Unzips a file unless the output folder already exists"""
    # Get a set of current files
    fl = set(glob.glob(pwd+"*"))
    # If the input pth doesn't exist, try to find the file
    if not os.path.exists(path):
        raise AssertionError("Incorrect Path")
    output_path = path[:-4]+'/'
    print("Extracting {} to {}".format(path, output_path))
    if os.path.exists(output_path):
        print("Output folder {} already exists".format(output_path))
        return
    zip_ref = zipfile.ZipFile(path, 'r')
    zip_ref.extractall(pwd)
    print("Extracted {}".format(list((set(glob.glob(pwd+"*")) - fl))[0]))
    zip_ref.close()

def availability(c):
    """checks availability of fluvial and pluvial filepaths

    Parameters
    ----------
    c : 2 letter string for country

    Returns
    -------
    tuple(fluvial, pluvial):
        filepaths for the fluvial and pluvial undefended folder in
        the ssbn folder if available, return false otherwise. If folder doesn't exist
        but zips exist, extract using unzip then return filepaths."""

    folder = "./data_hazards/ssbn/"
    fluvial = folder+c+"_fluvial_undefended/"
    pluvial = folder+c+"_pluvial_undefended/"
    if exists(fluvial) and exists(pluvial):
        return fluvial, pluvial
    elif (exists(pluvial) and (not exists(fluvial))):
        print("Fluvial Data Folder Missing \n")
        zip = fluvial[:-1]+".zip"
    elif (exists(fluvial) and (not exists(pluvial))):
        print("Pluvial Data Folder Missing \n")
        zip = pluvial[:-1]+".zip"
    else:
        print("Data is missing")
        return False
    if isfile(zip):
        unzip(zip, folder)
        return fluvial, pluvial
    else:
        print("Zip does not exist")
        return False
