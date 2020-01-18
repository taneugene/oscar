import glob
import zipfile
from os.path import exists


def unzip(path, pwd):
    """Unzips a zipfile unless the output folder already exists
    """
    # Get a set of current files
    fl = set(glob.glob(pwd + "*.zip"))
    # If the input pth doesn't exist, try to find the file
    if not exists(path):
        raise AssertionError("Incorrect Path")
    output_path = path[:-4] + '/'
    print("Extracting {} to {}".format(path, output_path))
    if exists(output_path):
        print("Output folder {} already exists".format(output_path))
        return
    zip_ref = zipfile.ZipFile(path, 'r')
    zip_ref.extractall(pwd)
    print("Extracted {}".format(list((set(glob.glob(pwd + "*")) - fl))[0]))
    zip_ref.close()