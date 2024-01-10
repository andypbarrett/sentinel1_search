"""Searches for and downloads Sentinel-1 Extra Wide Ground Range Detected 
Dual Polarized (HH + HV) scenes over the Arctic for ML denoising pilot.

Dataset title on Earhdata Search is SENTINEL-1A_DUAL_POL_GRD_MEDIUM_RES
"""
import os
os.environ["XDG_SESSION_TYPE"] = "xcb"

from typing import List

import datetime as dt
import calendar
from itertools import chain
from pprint import pprint

import webbrowser
from pathlib import Path

import numpy as np

import earthaccess

import pandas as pd

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from shapely.geometry.polygon import Polygon


# Filters
concept_id = "C1214471521-ASF"  # Unique identifier for dataset
start_date = "2021-01-01"
end_date = "2021-12-31" #
region_of_interest = [(-79.7548, 54.5223),
                      (-8.8315, 53.9323),
                      (62.6918, 67.2121),
                      (-153.5766, 68.2373),
                      (-79.7548, 54.5223)]
platform = "SENTINEL-1A"


test_entries = [
    {
        'native_id': 'S1A_EW_GRDM_1SDH_20210121T041238_20210121T041338_036231_043FDA_F583-GRD_MD',
        'acquisition_date': '2021-01-21T04:13:38+00:00',
        'size': '214.16',
        'thumbnail': 'https://datapool.asf.alaska.edu/THUMBNAIL/SA/S1A_EW_GRDM_1SDH_20210121T041238_20210121T041338_036231_043FDA_F583_thumb.jpg',
        'visialization': 'https://datapool.asf.alaska.edu/BROWSE/SA/S1A_EW_GRDM_1SDH_20210121T041238_20210121T041338_036231_043FDA_F583.jpg'
    },
    {
        'native_id': 'S1A_EW_GRDM_1SDH_20210110T130733_20210110T130833_036076_043A82_D586-GRD_MD',
        'acquisition_date': '2021-01-10T13:08:33+00:00',
        'size': '248.95',
        'thumbnail': 'https://datapool.asf.alaska.edu/THUMBNAIL/SA/S1A_EW_GRDM_1SDH_20210110T130733_20210110T130833_036076_043A82_D586_thumb.jpg',
        'visialization': 'https://datapool.asf.alaska.edu/BROWSE/SA/S1A_EW_GRDM_1SDH_20210110T130733_20210110T130833_036076_043A82_D586.jpg'
    }
    ]


def get_month_range(year, month):
    date_fmt = "%Y-%m-%d"
    start = dt.datetime(year, month, 1)
    _, lastday = calendar.monthrange(year, month)
    end = dt.datetime(year, month, lastday)
    return (start.strftime(date_fmt), end.strftime(date_fmt))


def search_sentinel1():

    # You need a Earthdata Login
    # Easiest way of storing this is as a netrc
    auth = earthaccess.login()

    result = earthaccess.search_data(concept_id = concept_id,
                                     temporal = (start_date, end_date),
                                     polygon = region_of_interest,
                                     platform = platform,
                                     )

    return result
    # # print(result[0]["umm"]["Platforms"])
    # platforms = [r["umm"]["Platforms"][0]["ShortName"] for r in result]
    # print(set(platforms))


def get_observation_time(r):
    dd = r["umm"]["TemporalExtent"]["RangeDateTime"]
    begin, end = [dt.datetime.fromisoformat(d) for d in  dd.values()]
    return end


def get_observation_month(result: List) -> np.array:
    """Returns observation month"""
    return np.array([get_observation_time(r).month for r in result])


def stratified_selection(results, n=600):
    """Selects n data granules from months in the dataset

    Parameters
    ----------
    n : number of samples to return in general

    Returns
    -------
    Stratified sample
    """

    aresults = np.array(results)

    months = get_observation_month(results)

    these_months = set(months)
    nmonths = len(these_months)
    d, m  = divmod(n, nmonths)
    nsample = (np.ones(nmonths) * d).astype(int)
    nsample[:m] += 1

    #for ns, month in zip(nsample, set(months)):
    #    print(ns, month)
        
    subset = list(chain.from_iterable([np.random.choice(aresults[months == month], ns, replace=False)
                                       for ns, month in zip(nsample, set(months))]))
    
    return subset


def spatial2polygon(s, toproj=None):
    points = [tuple(point.values()) for point in s["umm"]["SpatialExtent"]["HorizontalSpatialDomain"]["Geometry"]["GPolygons"][0]["Boundary"]["Points"]]
    if toproj:
        points = toproj.transform_points(ccrs.PlateCarree(), *map(np.array, zip(*points)))[:,:2]
    polygon = Polygon(points)
    return polygon


def make_map(result, debug=False):
    """Create a map of selected scenes color coded by month


    TODO: Add search polygon
    """
    proj = ccrs.NorthPolarStereo()

    # Set face and edge colors by month
    months = get_observation_month(result)
    facecolors = [None, 'lightcoral', 'lightsalmon', 'peachpuff', 'bisque',
                  'cornsilk', 'greenyellow', 'lime', 'lightcyan',
                  'lightskyblue', 'lavender', 'thistle', 'pink']
    edgecolors = [None, 'darkred', 'orangered', 'saddlebrown', 'darkorange',
                  'gold', 'olivedrab', 'seagreen', 'cyan',
                  'steelblue', 'midnightblue', 'darkviolet', 'crimson']
    fc = [facecolors[m] for m in months]
    ec = [edgecolors[m] for m in months]
    
    fig = plt.figure(figsize=(7,7))
    ax = fig.add_subplot(projection=proj)
    ax.set_extent([-180., 180., 50., 90.], ccrs.PlateCarree())

    ax.add_feature(cfeature.LAND)

    polygon = [spatial2polygon(r, toproj=proj) for r in result]
    geom = ax.add_geometries(polygon, proj, facecolor=fc, edgecolor=ec, alpha=0.5)

    # Make the legend
    handles = []
    labels = []
    for mon, fcol, ecol in zip(np.unique(months), facecolors[1:], edgecolors[1:]):
        handles.append(
            mpatches.Rectangle(
                (0, 0), 1, 1,
                linewidth=1,
                edgecolor=ecol,
                facecolor=fcol
                )
            )
        labels.append(calendar.month_abbr[mon])

    #    red_patch = mpatches.Patch(color='red', label='The red data')
    ax.legend(handles, labels, title="Month")

    fig.tight_layout()
    
    fig.savefig('selected_scenes.png')
    if debug:
        plt.show()


def get_native_id(entry):
    """Returns the native id for granule"""
    return entry["meta"]["native-id"]


def get_thumbnail(entry):
    """Returns URL to thumbnail"""
    return [a["Values"][0] for a in entry["umm"]["AdditionalAttributes"] if a["Name"] == "THUMBNAIL_URL"][0]


def get_visualization(entry):
    """Returns url to visualization"""
    return [a["URL"] for a in entry["umm"]["RelatedUrls"] if a["Type"] == "GET RELATED VISUALIZATION"][0]


def get_table_values(entry):
    """Returns a dict of values for the html table"""
    values = {
        "native_id": get_native_id(entry),
        "acquisition_date": get_observation_time(entry).isoformat(),
        "size": f"{entry.size():.2f}",
        "thumbnail": get_thumbnail(entry),
        "visialization": get_visualization(entry),
        }
    return values


def make_table(result, debug=False):
    """Returns an html table"""
    # emoji_table.py

    import unicodedata

    if debug:
        all_scenes = test_entries
    else:
        all_scenes = pd.DataFrame([get_table_values(r) for r in result])

    all_scenes.sort_values("acquisition_date", inplace=True)
    
    columns = ["Native-ID", "Acquisition Date", "Size\nMB", "Thumbnail"]

    table_head = f"<thead>\n<tr><th>{'</th><th>'.join(columns)}</th></tr>\n</thead>"

    table_body = "\n<tbody>\n"
    for index, scene in all_scenes.iterrows():
#        print(scene.values[:-2])
        scene_data = scene.values[:-2]
        thumbnail_cell = f'<img align="center" src="{scene["thumbnail"]}" style="max-width: 500px; max-height: 375px;" >'
        thumbnail_link = f'<a href={scene["visialization"]} target="_blank" rel="noopener noreferrer">{thumbnail_cell}</a>'
        table_body += f"<tr><td>{'</td><td>'.join(scene_data)}</td><td>{thumbnail_link}</td></tr>\n"
    table_body += "</tbody>\n"

    return f"<table>\n{table_head}{table_body}</table>"


def create_html(result, debug=False):
    """Creates an html page containing the map showing scene locations
    and a table containing dynamic links to thumbnail images, and larger images


    Suggested solution to get page to refresh after loading
    
    ```
    from selenium import webdriver
    import urllib
    import urllib2
    driver = webdriver.Firefox()
    driver.get("Your desired URL goes here...")
    #now you can refresh the page!
    driver.refresh()
    """

    header = """<!-- index. html -->

<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <title>Sentinel-1 Scenes</title>
    <style>
        body {
            background-color: rgb(20, 40, 60);
            color: rgb(240, 248, 255);
            font-family: "Helvetica", "Arial", sans-serif;
            font-size: 1.3em;
        }

        a {
            color: rgb(255, 111, 111);
        }

        th,
        td {
            border: 1px solid black;
            font-size: .75em;
            padding: 15px;
        }
        td:nth-child(4) {
            padding: 0px
        }
    </style>
</head>

<body>
<h1>Sentinel-1 C-band SAR Scenes for Denoising Experiment</h1>
<p>A listing of C-band SAR image files from Sentinel-1A.  The spatial distribution of
scenes are shown below color coded by month of acquisition.</p>

<img src="selected_scenes.png" alt="Selected Sentinel-1 Scenes">

<h2>Selected Scenes</h2>
<p>Click on "Thumbnail" to see larger image.</p>
"""
    
    footer="""</body>
</html>
"""

    table = make_table(result)
    
    url = Path.cwd() / "index.html"
    with open(url, "w") as f:
        f.write(header)
        f.write(table)
        f.write(footer)

    webbrowser.open("file:///" + str(url))


def main():

    result = search_sentinel1()

    subset = stratified_selection(result, n=60)

    make_map(subset)

    create_html(subset)


if __name__ == "__main__":
    main()
