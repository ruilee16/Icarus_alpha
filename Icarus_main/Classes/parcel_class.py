from Icarus_main.Classes.basic_class import IcarusObj, IcarusObjs
from enum import Enum
import dataclasses


class ParcelType(Enum):
    HOME = 1
    COMMERCIAL = 2


@dataclasses.dataclass
class Parcel(IcarusObj):
    APN: str = dataclasses.field(default=None)
    type: ParcelType = dataclasses.field(default=None)


