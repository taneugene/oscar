# Downloads the Hydrobasins dataset from the dropbox link provided at 
# https://www.hydrosheds.org/downloads

## A NOTE ON THE DROPBOX API
# the ?dl=0 suffix means open the web browser for the public folder. 
# Setting ?dl=1 takes you to a zip for the folder which you can wget or send a request. 

# Get the Hydrobasins 15as dataset (tif format) from the dropbox link # 
wget -c https://www.dropbox.com/sh/hmpwobbz9qixxpe/AACmLIlbyJgcQ7BuDVIiAiOEa/HydroSHEDS_BAS/BAS_15s
mv BAS_15s BAS_15s.zip
unzip BAS_15s.zip

# Get the Hydrobasins standardized (without lakes) basin dataset from dropbox. 
wget -c https://www.dropbox.com/sh/hmpwobbz9qixxpe/AACPCyoHHAQUt_HNdIbWOFF4a/HydroBASINS/standard
mv standard standard.zip
unzip standard.zip
