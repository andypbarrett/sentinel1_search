# Sentinel1_search
Code to search for and download Sentinel-1A scenes for denoising experiment

## Install

If you want to run `search_and_download_sentinel1.py` it is best to clone this repository.

```
git clone
```

It is best to create a virtual environment.  I recommend using `mamba`.

```
mamba env create -f environment.yml
```

## Usage

```
$ python search_and_download_sentinel1.py -h
usage: search_and_download_sentinel1.py [-h] [--nscenes NSCENES]

Searches for and downloads Sentinel-1 scenes for a region of interest

options:
  -h, --help            show this help message and exit
  --nscenes NSCENES, -n NSCENES
                        Number of scenes to search for
```

Default is 600 scenes for all months.

This script creates the following output.
```
index.html
selected_scenes.png
sentinel1_data_links.txt
```

`sentinel1_data_links.txt` contains url to the scenes and can be passed to wget.  [`index.html`](index.html) is a simple html page that contains a map of scene locations and a 
list of files with links to thumbnails and quicklooks.

The scenes are downloaded using `wget_for_sentinel1.sh`.  This will download data to the local machine.  By default files are put in `./Data`.  This can be modified by changing
the `OUTDIR` variable in the script.  You will need an [Earthdata login](https://urs.earthdata.nasa.gov/).  The download script expects Earthdata login credentials to be
stored in a `.netrc` file in your `$HOME`.  See details [here](https://nsidc.org/data/user-resources/help-center/programmatic-data-access-guide).
