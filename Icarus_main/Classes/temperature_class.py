from Icarus_main.Classes.basic_class import IcarusObj
from typing import Dict
import dataclasses


@dataclasses.dataclass
class MRT(IcarusObj):
    mrt_id: int = dataclasses.field(default=None)
    mrt_temp: Dict[int: float] = dataclasses.field(default=None)
    __primary_key__ = 'link_id'


@dataclasses.dataclass
class Daymet(IcarusObj):
    daymet_id: int = dataclasses.field(default=None)
    daymet_temp: Dict[int: float] = dataclasses.field(default=None)
    __primary_key__ = 'daymet_id'
