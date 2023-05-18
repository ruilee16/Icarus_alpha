import geopandas as gpd
from rasterstats import zonal_stats
import pandas as pd
from Icarus_main.NetworkFunctions.utility import *
from typing import List, Dict


def parsing_raster_to_link(link_shape: gpd.GeoDataFrame, raster: str, time: str) -> List[Dict]:
    try:
        _zonal_mean = zonal_stats(link_shape, raster, stats=['mean'])
        return [{time: round(_['mean'], 2)} for _ in _zonal_mean]
        # pd.DataFrame([_['mean'] for _ in _zonal_mean], columns=[time])
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        print(f'error in parsing {raster}')
        pass


def get_temperature(link_shape: gpd.GeoDataFrame, raster_list: List[str]):
    _temperature_on_link = {}
    for _ in raster_list:
        _time_stamp = int(_[-8:-4]) // 100 * 60
        _temperature_on_link[_time_stamp] = parsing_raster_to_link(link_shape, _, _time_stamp)
    return _temperature_on_link

