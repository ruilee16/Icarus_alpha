import pyproj
import geopandas as gpd
from shapely.ops import transform

import rasterio


def check_shape_raster_crs(shape_file: gpd.GeoDataFrame, raster_url: str):
    _raster_crs = rasterio.open(raster_url).crs
    if shape_file.get_crs == _raster_crs:
        return True
    else:
        print('raster and shapefile used different coordinate system')
        return False
