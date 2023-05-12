import dataclasses
from typing import List, Optional, Dict
import geopandas as gpd
import networkx as nx
import osmium as osm
import pandas as pd
from shapely.geometry import Point, LineString, Polygon, MultiPolygon

"""
creater: Rui Li
function: load OSM data in either .osm or .pbf, read the transportation network, 
extract links where pedestrians can travel on. Simplify the network to non-directional.
Export the network into a database. 
"""

"""
Dev notes:
    May 2nd, finished loading network and export networkx.graph
    solved
    next: 
    May 3rd, finished cleaning/ simplifying the network to exclude the nodes with 2 degrees (middle of a line)
    next: 
    parse temperature to roadway network (May 5- May 7th. Push to GitHub around May 10th)
"""


@dataclasses.dataclass
class osm_Way:
    """

    """
    osm_way_id: Optional[int] = None
    highway_type: Optional[str] = None
    maxspeed: Optional[str] = None
    pedestrian_allowed: Optional[str] = None
    service: Optional[str] = None
    access_mode: Optional[str] = None
    hov: Optional[str] = None
    ref_node_id_list: List[int] = None


# define Node class to hold the node data record from .osm file
@dataclasses.dataclass
class osm_Node:
    """
    create node object
    :param osm_id: openstreetmap node id
    :param geometry: Point object
    :param crs: the coordinate system code. By ddfault crs equals to 4326, which is the default coordinate from
    open street map.
    example:
        node1 = Node(osm_id = 1, Point(33.123, -111.225), crs=2656)
        node2 = Node(osm_id = 2, Point(32.123, -112.225), crs=2656)
    """
    osm_id: int
    geometry: Point
    crs: int = dataclasses.field(default=4326)


@dataclasses.dataclass
class Link:
    """
    create Link object.
    *** NOTICE ****
    a Link object only has two nodes.
    example:
        link = Link(node_list = (1, 2), geometry)
    """
    node1: Optional[
        int] = None  # A tuple of two integers representing the OpenStreetMap node ids that the link connects.
    node2: Optional[int] = None
    geometry: Optional[LineString] = None  # An optional LineString object representing the geometry of the link.
    length: Optional[float] = None  # An optional float representing the length of the link in meters.
    osm_id: Optional[int] = None  # An optional integer representing the OpenStreetMap id of the link.
    highway: Optional[str] = None  # An optional string representing the type of road that the link belongs to.
    daymet_id: Optional[int] = None  # An optional integer representing the Daymet id of the link.
    mrt_id: Optional[int] = None  # An optional integer representing the MRT id of the link.


@dataclasses.dataclass
class OSM_Network:
    links: Dict[str, Link]
    nodes: Dict[str, osm_Node]
    crs: int = dataclasses.field(default=4326)
    simplified: bool = dataclasses.field(default=False)


class OSMHandler(osm.SimpleHandler):

    def __init__(self):
        osm.SimpleHandler.__init__(self)
        self.osm_node_dict = {}
        self.osm_way_dict = {}
        self.cleaned = False

    def node(self, n):
        _node = osm_Node(
            osm_id=int(n.id),
            geometry=Point(n.location.lon, n.location.lat))
        self.osm_node_dict[_node.osm_id] = _node

    def way(self, w):
        if w.tags.get('highway') is not None:
            _way = osm_Way(
                osm_way_id=int(w.id),
                highway_type=w.tags.get('highway'),
                maxspeed=w.tags.get('maxspeed'),
                pedestrian_allowed=w.tags.get('foot'),
                service=w.tags.get('service'),
                access_mode=w.tags.get('access'),
                hov=w.tags.get('hov'),
                ref_node_id_list=[int(node.ref) for node in w.nodes])
            self.osm_way_dict[_way.osm_way_id] = _way

    def cleanup(self):
        """
        only keep the information of roadways.
        :return:
        """
        used_nodes = set()
        [used_nodes.update(self.osm_way_dict[_].ref_node_id_list) for _ in self.osm_way_dict]
        self.osm_node_dict = {key: value for key, value in self.osm_node_dict.items() if key in used_nodes}
        self.cleaned = True

    def get_network(self) -> OSM_Network:
        """
        return a Network object which contains links and nodes. The links are the collection of edges in the OSM data
        which meets the filter requirement in way() function defined above.
        *** notice ***
        THE LINKS in this network contains lots of un intersected edges which can cause hard to find path or can't find
        the right path in routing.
        :return: Network object
        """
        if not self.cleaned:
            self.cleanup()
        _links = {_: Link(node1=self.osm_way_dict[_].ref_node_id_list[0],
                          node2=self.osm_way_dict[_].ref_node_id_list[-1],
                          geometry=
                          LineString(self.osm_node_dict[i].geometry for i in
                                     self.osm_way_dict[_].ref_node_id_list),
                          osm_id=self.osm_way_dict[_].osm_way_id,
                          highway=self.osm_way_dict[_].highway_type)
                  for _ in self.osm_way_dict if len(self.osm_way_dict[_].ref_node_id_list) >= 2}
        _network = OSM_Network(_links, self.osm_node_dict)
        return _network
