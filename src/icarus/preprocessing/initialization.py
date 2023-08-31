"""
initialize the Icarus project. preparing the database with agent, travel & activity plan,
network and environment information.
1. create database if not exist
2. preparing network if not exist in database
    Node location in table: L_Node
    Link location in table: L_Link
    Parcel location : L_Parcel
3. parse temperature to network if not exist in database
    Link MRT temperature: E_Link_mrt
    Link Daymet temperature: E_Link_air
4. preparing agent (synthetic people) and daily travel/activity plan in to database if not exist.
    Household: P_Household
    Activity: P_Activity
    Trip: P_Trip
    People: P_Person
5. parse temperature to parcels
"""
import os
import sys
import geopandas as gpd
import pandas as pd
from geopy.distance import geodesic
import geopandas as gpd
import os
import rasterio

module_path = os.path.abspath(os.path.join(r"D:\Icarus_RL"))
if module_path not in sys.path:
    sys.path.append(module_path)
from src.icarus.project.project_class import *
from src.icarus.util.sqlite_db_general_func import *
from Icarus_main.Classes.OSM_network_class import OSMHandler
from Icarus_main.Classes.network_class import Network
from Icarus_main.NetworkFunctions.Network_func import osm_net_simplify, osm_net, net_to_csv, net_to_shp
from Icarus_main.DataParsing.parse_temperature import parse_raster_temperature, parse_air_temp
from Icarus_main.utils.utilities import read_files_in_folder, update_dataclass


def load_network_from_osm(OSM_dt_loc: str, simplify_network: bool = True) -> Network:
    """
    read OSM data and return a Network object.
    :rtype:
    :param OSM_dt_loc: the .osm file location
    :param simplify_network: a bool value determine if simplify the network
    :return: Network object
    """
    osm_handler = OSMHandler()
    osm_handler.apply_file(OSM_dt_loc)
    if simplify_network:
        network = osm_net_simplify(osm_handler.get_network())
    else:
        network = osm_net(osm_handler.get_network())
    return network


def load_parcel_location(parcel_file_url: str, project_crs: int = 4326) -> pd.DataFrame:
    """
    get the parcel location and APN of the parcel data
    :param parcel_file_url:
    :param project_crs:
    :return: a dataframe showing the parcel APN and location
    """
    parcel_data = gpd.read_file(parcel_file_url)
    # [edit: check]
    if parcel_data.crs.to_epsg() != project_crs:
        parcel_data = parcel_data.to_crs(f"EPSG:{project_crs}")
    parcel_data['x'] = parcel_data.centroid.x
    parcel_data['y'] = parcel_data.centroid.y
    return parcel_data[['APN', 'x', 'y']].groupby('APN').first().reset_index()


def update_link_length(links: list, crs: int = 4326) -> None:
    """
    estimate the length (meter) of each link
    :param links:
    :param crs:
    :return:
    """
    if not crs == 4326:
        print('error: the projection system is not 4326')
    [update_dataclass(_, length=geodesic(reversed(_.geometry.coords[0]),
                                         reversed(_.geometry.coords[-1])).meters) for _ in links]


def parse_raster_to_roadway(link_gdf: gpd.GeoDataFrame, raster_folder: str, buffer: int = 0.01,
                            target_crs: int = 26912) -> pd.DataFrame:
    """
    this function parse the raster file to link. Notice: this function is strictly linked to the input data format.
    :param target_crs:
    :param link_gdf:
    :param raster_folder:
    :param buffer:
    :return:
    """
    # load the roadway shapefile saved by previous step
    link_gdf = link_gdf.to_crs(target_crs)
    link_gdf['buffer'] = link_gdf.geometry.buffer(buffer)
    tif_files = [file for file in os.listdir(raster_folder) if file.endswith('.tif')]
    for _ in tif_files:
        if int(_[13:15]):
            raster_dataset = rasterio.open(f'{raster_folder}\\{_}')
            link_gdf[f"t{_[13:15]}"] = parse_raster_temperature(link_gdf, raster_dataset, geometry_name='buffer')
            link_gdf[f"t{_[13:15]}"].fillna(link_gdf[f"t{_[13:15]}"].mean(), inplace=True)
    return link_gdf.drop(columns=['link_id', 'osm_id', 'length', 'env', 'geometry', 'buffer'])


def parse_ntf_to_roadway(link_gdf: gpd.GeoDataFrame, tmax_url, tmin_url, day=1):
    """
    parse the max and min air temperature to roadway
    :param link_gdf:
    :param tmax_url:
    :param tmin_url:
    :param day: the day number in the study
    :return:
    """
    _temp = parse_air_temp(link_gdf, tmax_url, tmin_url, day)
    link_gdf['tmax'] = _temp['t_max']
    link_gdf['tmin'] = _temp['t_min']
    return link_gdf.drop(columns=['link_id', 'osm_id', 'length', 'env', 'geometry'])


def load_person(abm_person) -> pd.DataFrame:
    pass


def main():
    parcel_data_url =  r"C:\Dropbox (ASU)\Icarus\Data\Shapefiles\Maricopa Parcels\Parcels_-_Maricopa_County_Arizona_(2020)\parcels_maricnty_2020.shp" # [reminder: add location in the config file]
    network_data_url = r"E:\Dropbox (ASU)\2020 ICARUS_Rui_Work\new simulation\network prepare\tempe\tempe.osm"
    raster_folder_loc = r"C:\Users\ruili\Desktop\mrt_new\new_mrt_data_high_resolution"
    tmax_url = r"C:\Dropbox (ASU)\Icarus\Data\RuiLi\2129_daymet_v4_daily_na_tmax_2012.nc"
    tmin_url = r"C:\Dropbox (ASU)\Icarus\Data\RuiLi\2129_daymet_v4_daily_na_tmin_2012.nc"
    try:
        project = get_project_database()
        # check project and give options
        project.connect()
        # [done]load network into database as L_Node, L_Link:
        print('loading network')
        network = load_network_from_osm(OSM_dt_loc=network_data_url, simplify_network=True)
        update_link_length(network.links.values())
        add_dataframe_to_database(conn=project.db_conn,
                                  data_frame=pd.DataFrame([{'node_id': _.osm_id, 'x': _.geometry.x, 'y': _.geometry.y}
                                                           for _ in network.nodes.values()]),
                                  table_name='L_Node', primary_keys=['node_id'])
        add_dataframe_to_database(conn=project.db_conn,
                                  data_frame=pd.DataFrame(network.links.values())[['node1', 'node2', 'length']],
                                  table_name='L_Link', primary_keys=['node1', 'node2'])

        print('loading environments')
        # [done]load link mrt temperature as E_Link_mrt
        _link_gdf = gpd.GeoDataFrame(pd.DataFrame(network.links.values()), geometry='geometry', crs=4326)
        add_dataframe_to_database(conn=project.db_conn, data_frame=parse_raster_to_roadway(
            link_gdf=_link_gdf, raster_folder=raster_folder_loc), table_name='E_Link_mrt',
                                  primary_keys=['node1', 'node2'])
        # [done]load link mrt temperature as E_Link_air
        add_dataframe_to_database(conn=project.db_conn, data_frame=parse_ntf_to_roadway(
            link_gdf=_link_gdf, tmin_url=tmin_url, tmax_url=tmax_url),
                                  table_name='E_Link_air', primary_keys=['node1', 'node2'])

        print('loading parcels')
        # [done]load parcel and location (x, y) as L_Parcel
        add_dataframe_to_database(conn=project.db_conn, table_name='L_Parcel',
                                  data_frame=load_parcel_location(parcel_data_url),
                                  primary_keys=['APN'])
        print('done')
        project.close_connection()
        return

    except Exception as e:
        error_message = str(e)
        print("An error occurred:", error_message)
        print("Stopping the program due to the error.")
        return  # This will stop the code execution


if __name__ == "__main__":
    main()
