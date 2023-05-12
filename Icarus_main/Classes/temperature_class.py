from Icarus_main.Classes.basic_class import IcarusObj, IcarusObjs
from typing import Dict
import dataclasses


@dataclasses.dataclass
class MRT(IcarusObj):
    mrt_id: int = dataclasses.field(default=None)
    mrt_temp: Dict[int: float] = dataclasses.field(default=None)


@dataclasses.dataclass
class MRTs(IcarusObjs):
    primary_keys: str = dataclasses.field(default='mrt_id', init=False)
    objects: {} = dataclasses.field(default=None, init=False)


@dataclasses.dataclass
class Daymet(IcarusObj):
    daymet_id: int = dataclasses.field(default=None)
    daymet_temp: Dict[int: float] = dataclasses.field(default=None)


@dataclasses.dataclass
class Daymets(IcarusObjs):
    primary_keys: str = dataclasses.field(default='daymet_id', init=False)