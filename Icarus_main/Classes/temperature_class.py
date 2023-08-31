from Icarus_main.Classes.basic_class import IcarusObj
from typing import Dict
import dataclasses


@dataclasses.dataclass
class Point:
    uuid: int = dataclasses.field(default=None)
    x: float = dataclasses.field(default=None)
    y: float = dataclasses.field(default=None)
    x_id: int = dataclasses.field(default=None)
    y_id: int = dataclasses.field(default=None)


@dataclasses.dataclass
class MRT(IcarusObj):
    mrt_id: int = dataclasses.field(default=None)
    mrt_temp: Dict = dataclasses.field(default=None)
    __primary_key__ = 'link_id'


@dataclasses.dataclass
class Daymet(IcarusObj):
    daymet_id: int = dataclasses.field(default=None)
    daymet_temp: Dict = dataclasses.field(default=None)
    __primary_key__ = 'daymet_id'
