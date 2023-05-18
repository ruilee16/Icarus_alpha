# -*- coding: utf-8 -*-
"""
Created on Fri May 12 12:16:54 2023

@author: ruili
"""

from Icarus_main.Classes.basic_class import IcarusObj, IcarusObjs
from typing import Dict
import dataclasses
from shapely.geometry import LineString


@dataclasses.dataclass
class Node(IcarusObj):
    node_id: int = dataclasses.field(default=None)
    x: float = dataclasses.field(default=None)
    y: float = dataclasses.field(default=None)
    __primary_key__ = 'node_id'


@dataclasses.dataclass
class Link_env:
    link_id: str = dataclasses.field(default=None)
    daymet_id: int = dataclasses.field(default=None)
    mrt_id: int = dataclasses.field(default=None)
    LCZ: int = -1


@dataclasses.dataclass
class Link(IcarusObj):
    link_id: str = dataclasses.field(default=None, init=False)
    node1: int = dataclasses.field(default=0)
    node2: int = dataclasses.field(default=0)
    osm_id: int = dataclasses.field(default=0)
    length: float = dataclasses.field(default=0)
    geometry: LineString = dataclasses.field(default=None)
    env: Link_env = dataclasses.field(default=None)

    __primary_key__ = 'node1, node2'

    def __post_init__(self):
        self.node1, self.node2 = sorted((self.node1, self.node2))
        self.link_id = ','.join([str(self.node1), str(self.node2)])


@dataclasses.dataclass
class Links(IcarusObjs):
    primary_keys: str = dataclasses.field(default='node1, node2', init=False)


@dataclasses.dataclass
class Network:
    links: Dict[str, Link] = dataclasses.field(default=None)
    nodes: Dict[str, Node] = dataclasses.field(default=None)
    crs: int = dataclasses.field(default=4326)
    simplified: bool = dataclasses.field(default=False)



