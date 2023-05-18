from Icarus_main.Classes.OSM_network_class import OSM_Network, Link, OSMHandler, osm_Way, osm_Node
from typing import List, Optional, Tuple, Dict, Any
from shapely.geometry import Point, LineString, Polygon, MultiPolygon


def net_simplify(OG_network: OSM_Network) -> OSM_Network:
    """
    simplify the network and remove all nodes with only 2 degrees
    :return:
    """
    _graph = OG_network.net_to_nx() # get the network graph
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


def _get_individual_link(way: osm_Way, osm_obj: OSMHandler, net: OSM_Network) -> None:
    """
    An edge directly exported from OSM would have multiple points, and
    :param way:
    :param osm_obj:
    :
    :return: none
    """
    if len(way.ref_node_id_list) >= 2:
        _node_tuple = _get_link_list(way.ref_node_id_list)

        _links = {_: Link(node1=_[0],
                          node2=_[-1],
                          geometry=LineString(osm_obj.osm_node_dict[i].geometry for i in _),
                          osm_id=way.osm_way_id,
                          highway=way.highway_type) for _ in _node_tuple}
        net.links.update(_links)
    else:
        pass


def get_network(osm_obj: OSMHandler) -> OSM_Network:
    if not osm_obj.cleaned:
        osm_obj.cleanup()
    _network = OSM_Network(links={}, nodes={})
    [_get_individual_link(_, osm_obj, _network)
     for _ in osm_obj.osm_way_dict.values()]
    _network.nodes.update(osm_obj.osm_node_dict)
    return _network
