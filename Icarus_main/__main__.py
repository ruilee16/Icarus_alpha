"""
RL: entry point of the Icarus_main module
"""
# load network
from Icarus_main.Classes.OSM_network_class import OSMHandler
from Icarus_main.NetworkFunctions.Network_func import osm_net_simplify
from Icarus_main.DataParsing.env_parse_func import *
import rasterio


osm_handler = OSMHandler()
osm_handler.apply_file(r"E:\Dropbox (ASU)\2020 ICARUS_Rui_Work\new simulation\network prepare\tempe\tempe.osm")
network = osm_net_simplify(osm_handler.get_network())
# save loaded network to database

# load temperature
fld = r"C:\Users\ruili\Desktop\mrt_new\new_mrt_data_high_resolution"
raster_url_list = read_files_names_in_folder(fld, '.*?(.tif$)')
_raster_crs = rasterio.open(raster_url_list[0]).crs
# parse temperature
links_shp = pd.DataFrame(network.links.values())
links_shp = gpd.GeoDataFrame(links_shp, geometry='geometry', crs=network.crs).to_crs(_raster_crs)

temperature = get_temperature(links_shp, raster_url_list[0:2])
#