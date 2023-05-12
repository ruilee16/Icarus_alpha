import networkx as nx
import pandas as pd
import geopandas as gpd
from Icarus_main.Classes.OSM_network_class import OSM_Network, Link, OSMHandler, osm_Way
from typing import List, Tuple, Dict, Any
from shapely.geometry import Point, LineString, Polygon, MultiPolygon


def net_to_nx(network_obj):
    _G = nx.Graph()
    _G.add_nodes_from(
        [(i, {'x': network_obj.nodes[i].geometry.x, 'y': network_obj.nodes[i].geometry.y}) for i in list(network_obj.nodes)])
    _G.add_edges_from(
        [(network_obj.links[i].node1, network_obj.links[i].node2) for i in network_obj.links])
    _G.graph["crs"] = f'epsg:{str(network_obj.crs)}'
    return _G


def net_to_shp(network_obj, url: str):
    if bool(network_obj.links):
        temp = pd.DataFrame(network_obj.links.values())
        gdf = gpd.GeoDataFrame(temp, geometry='geometry', crs='epsg:%s' % network_obj.crs)
        gdf.to_file(url, driver='ESRI Shapefile')


def net_simplify(OG_network: OSM_Network) -> OSM_Network:
    """
    simplify the network and remove all nodes with only 2 degrees
    :return:
    """
    _graph = net_to_nx(OG_network) # get the network graph
    non_two_degree_nodes = [n for n, d in _graph.degree if d != 2] # find all nodes only has two degrees
    _simplified_edges = {}
    [_simplified_edges.update(build_simplified_edges(_graph, [_, n])) for _ in non_two_degree_nodes for n in
     _graph.neighbors(_)]
    # construct new network
    _network = OSM_Network(links={}, nodes={})
    [_network.links.update(
        {_: Link(node1=_[0],
                 node2=_[1],
                 geometry=LineString(OG_network.nodes[i].geometry for i in _simplified_edges[_])
                 )})
        for _ in _simplified_edges]
    _network.nodes = {i: OG_network.nodes[i] for i in non_two_degree_nodes}
    return _network


def build_simplified_edges(net_graph, st_node_list: List) -> Dict[Tuple[Any, ...], list]:
    """
    build edges
    """
    if net_graph.degree(st_node_list[-1]) == 2:
        new_neighbor_node = [_ for _ in net_graph.neighbors(st_node_list[-1]) if _ not in st_node_list]
        if len(new_neighbor_node) > 0:
            st_node_list.append(new_neighbor_node[0])
            return build_simplified_edges(net_graph, st_node_list)
        else:
            _index = sorted([st_node_list[0], st_node_list[-1]])
            return {tuple(_index): st_node_list}
    else:
        _index = sorted([st_node_list[0], st_node_list[-1]])
        return {tuple(_index): st_node_list}


def _get_link_list(route: list) -> list:
    """
    get the link used as a list from the route
    :param route: a list of nodes on the route
    :return: a list of links
    """
    link_list = list(zip(route[0:-1], route[1:]))
    return [tuple(sorted(i)) for i in link_list]


