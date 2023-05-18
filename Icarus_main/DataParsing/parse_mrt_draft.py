"""
Created on Mon Sep  12 20:46:48 2022

@author: ruili

read raster file

load links as a list of link objects with geometry
zonal statistics of the link shape and

create MRT object
get MRT temperature dict
update link object with MRT id
"""

import rasterio
import sqlite3
import pandas as pd
from shapely.geometry import LineString
from shapely.ops import transform
from shapely.errors import ShapelyDeprecationWarning
import warnings
warnings.filterwarnings("ignore", category=ShapelyDeprecationWarning)
import geopandas as gpd
from rasterstats import zonal_stats
import pyproj
import multiprocessing as mp
import time
import regex as re
from os import walk

from Classes.classes import Node, Link
from databaseHandler import readdata


def read_nodes(db_url: str):
    _conn = sqlite3.connect(db_url)
    _nodes = pd.read_sql(f"SELECT * FROM {'nodes'}", _conn)
    nodes_dict = {a.node_id: Node(node_id=a.node_id, x=a.x, y=a.y) for a in _nodes.itertuples()}
    return nodes_dict


def project(shape, crs_from, crs_to):
    CRS_from = pyproj.Proj(init = 'epsg:%s'%crs_from)
    CRS_to = pyproj.Proj(init = crs_to)
    project_funct = pyproj.Transformer.from_crs(CRS_from, CRS_to).transform
    _new_shape = transform(project_funct, shape)
    return _new_shape


def assign_link_geometry(nodes_dict: dict, _node1: int, _node2: int):
    nodes_list = [_node1, _node2]
    #print(LineString([(nodes_dict[_].x, nodes_dict[_].y) for _ in nodes_list]))
    return LineString([(nodes_dict[_].x, nodes_dict[_].y) for _ in nodes_list])


def split_dataframe_by_position(df, splits):
    """
    Takes a dataframe and an integer of the number of splits.
    Returns a list of dataframes.
    """
    dataframes = []
    index_to_split = len(df) // splits
    start = 0
    end = index_to_split
    for split in range(splits):
        temporary_df = df.iloc[start:end, :]
        dataframes.append(temporary_df)
        start += index_to_split
        end += index_to_split
    temporary_df = df.iloc[start:len(df), :]
    dataframes.append(temporary_df)
    return dataframes


def task(para):
    """
    generate first round of statistics
    """
    dt_seg = para[0]
    _ = para[1]

    #link_gdf = gpd.GeoDataFrame(dt_seg, geometry='geometry', crs=4326).to_crs(26912)
    #link_gdf['geometry'] = link_gdf.geometry.buffer(15)
    try:
        print(f'url {_}')
        temp_result = zonal_stats(dt_seg, _, stats=['mean'])
        print('zonal success')
        dt_seg[para[2]] = pd.DataFrame(temp_result)['mean'].to_list()
        print(dt_seg.columns)
    except:
        print('error %s'% _)
        pass
    #link_gdf = dt_seg.dropna()
    return dt_seg


def get_link_gdf(db_url):
    fetcher = readdata.LinkFetcher(db_url)
    link_df = fetcher.fetch_data_to_df(table_name='link_1')
    #links = fetcher.fetch_data_to_obj(table_name = 'link_1')
    # project the crs 4326 to the raster crs. use geopandas.series buffer() function
    return link_df


def _read_files(fld: str, reg_exp: str = '.*?(.tif$)'):
    p = re.compile(reg_exp)
    #p_shp = re.compile('.*?(.shp$)')
    _filenames = next(walk(fld), (None, None, []))
    _filename = [f'{fld}\{i}' for i in _filenames[-1] if p.match(i) ]
    return _filename


fld = r"C:\Users\ruili\Desktop\mrt_new\new_mrt_data_high_resolution"
raster_url_list = _read_files(fld, '.*?(.tif$)')


db_url = r'pythonsqlite.db'
nodes = read_nodes(db_url)


if __name__ == '__main__':
    #db = r'pythonsqlite.db'
    #start = time.time()
    #print('load raster')
    #link_gdt = get_link_gdf(db)
    #print(link_gdt.columns)
    #link_gdt = link_gdt.reset_index()
    #link_gdt = link_gdt.rename(columns={'index': 'mrt_id_n'})
    #link_gdt['geometry'] = link_gdt.apply(lambda x: assign_link_geometry(nodes, x.node1, x.node2), axis=1)
    #print('pass1')
    #link_gdf = gpd.GeoDataFrame(link_gdt, geometry='geometry', crs=4326).to_crs(26912)
    #print('pass2')
    #link_gdf['geometry'] = link_gdf.geometry.buffer(15)
    #link_gdf.crs = 26912
    #link_gdf.to_file(driver = 'ESRI Shapefile', filename = 'road_buffer.shp')
    #print('buffer')
    link_gdt = gpd.read_file(r"C:\Users\ruili\Desktop\mrt_new\road_buffer.shp")
    df_s = split_dataframe_by_position(link_gdt, 800)
    print('start iteration')

    for _ in raster_url_list[:1]:
        print(_)
        print(_[-8:-4])
        _df_s = [(i, _, _[-8:-4]) for i in df_s]
        start = time.time()
        p = mp.Pool()
        results = p.map(task, _df_s)
        print(time.time() - start)
        pd.concat(results).drop(columns = ['geometry']).to_csv(f'result/new_mrt_{int(_[-8:-4])//100*60}.csv')


    #pd.concat(results).to_csv(r'result/new_mrt_%s.csv'%str(int(_[-8:-4])//100*60))
#first round multiprocessing: generate data
