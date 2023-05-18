import pyproj
import geopandas as gpd
from shapely.ops import transform
import regex as re
from os import walk
from typing import List
import rasterio


def check_shape_raster_crs(shape_file: gpd.GeoDataFrame, raster_url: str):
    _raster_crs = rasterio.open(raster_url).crs
    if shape_file.get_crs == _raster_crs:
        return True
    else:
        print('raster and shapefile used different coordinate system')
        return False


def read_files_names_in_folder(fld: str, reg_exp: str = '.*?(.tif$)') -> List[str]:
    p = re.compile(reg_exp)
    #p_shp = re.compile('.*?(.shp$)')
    _filenames = next(walk(fld), (None, None, []))
    return [f'{fld}\\{i}' for i in _filenames[-1] if p.match(i)]