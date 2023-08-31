# load network and parse to database
"""
Goal : load network, save nodes links to database
"""
from Icarus_main.Classes.OSM_network_class import OSMHandler
from Icarus_main.NetworkFunctions.Network_func import osm_net_simplify, osm_net, net_to_csv, net_to_shp
from Icarus_main.DataParsing.parse_temperature import parse_raster_temperature, parse_air_temp

import sqlite3
import geopandas as gpd
import os
import rasterio


def load_network_from_OSM(OSM_dt_loc: str, output_loc: str, simplify_network: bool = True, save_dt_as: str = 'shp'):
    """
    read OSM data and save as network file
    :param OSM_dt_loc:
    :param output_loc:
    :param simplify_network:
    :param save_dt_as: the data saving format. It can be 'shp' or 'csv'.
    :return: None
    """
    osm_handler = OSMHandler()
    osm_handler.apply_file(OSM_dt_loc)
    if simplify_network:
        network = osm_net_simplify(osm_handler.get_network())
    else:
        network = osm_net(osm_handler.get_network())
    if save_dt_as == 'shp':
        net_to_shp(network, f"{output_loc}\\network.shp")
    elif save_dt_as == 'csv':
        net_to_csv(network, output_loc)


def parse_raster_to_roadway(geometry_location, raster_folder, buffer: int = 0.01, target_crs: int = 26912):
    """
    this function parse the raster file to link
    :param target_crs:
    :param geometry_location:
    :param raster_folder:
    :param buffer:
    :return:
    """
    # load the roadway shapefile saved by previous step
    link_gdf = gpd.read_file(geometry_location)
    link_gdf = link_gdf.to_crs(target_crs)
    link_gdf['buffer'] = link_gdf.geometry.buffer(buffer)
    tif_files = [file for file in os.listdir(raster_folder) if file.endswith('.tif')]
    for _ in tif_files:
        if int(_[13:15]):
            raster_dataset = rasterio.open(f'{raster_folder}\\{_}')
            link_gdf[f"t{_[13:15]}"] = parse_raster_temperature(link_gdf, raster_dataset, geometry_name='buffer')
    return link_gdf.drop(columns=['link_id', 'osm_id', 'length', 'env', 'geometry', 'buffer'])


def parse_ntf_to_roadway(geometry_location, tmax_url, tmin_url, day=1):
    """

    :param geometry_location:
    :param tmax_url:
    :param tmin_url:
    :param day:
    :return:
    """
    # load the roadway shapefile saved by previous step
    link_gdf = gpd.read_file(geometry_location)
    link_gdf = link_gdf.to_crs(4326)
    _temp = parse_air_temp(link_gdf, tmax_url, tmin_url, day)
    link_gdf['tmax'] = _temp['t_max']
    link_gdf['tmin'] = _temp['t_min']
    return link_gdf.drop(columns=['link_id','osm_id', 'length', 'env', 'geometry' ])


def main():
    network_test_location = r"E:\Dropbox (ASU)\2020 ICARUS_Rui_Work\new simulation\network prepare\tempe\tempe.osm"
    network_out_location = r"E:\Dropbox (ASU)\2020 ICARUS_Rui_Work\new simulation\network prepare\tempe"
    raster_folder = r"C:\Users\ruili\Desktop\mrt_new\new_mrt_data_high_resolution"
    tmax_url = r"C:\Dropbox (ASU)\Icarus\Data\RuiLi\2129_daymet_v4_daily_na_tmax_2012.nc"
    tmin_url = r"C:\Dropbox (ASU)\Icarus\Data\RuiLi\2129_daymet_v4_daily_na_tmin_2012.nc"
    load_network_from_OSM(network_test_location, network_out_location)
    input_link_loc = f"{network_out_location}\\network.shp"
    #initialize database


    link_with_MRT = parse_raster_to_roadway(input_link_loc, raster_folder)
    link_with_MRT.to_csv('Module_1/Data/output/network_mrt.csv',index = False)
    link_with_daymet = parse_ntf_to_roadway(input_link_loc, tmax_url, tmin_url)
    link_with_daymet.to_csv('Module_1/Data/output/network_air.csv', index = False)
