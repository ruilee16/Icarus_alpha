from __future__ import annotations
from dataclasses import dataclass, field, asdict
import dataclasses
from typing import List

from typing import Iterable
from enum import Enum
from abc import ABC, abstractmethod


class TravelMode(Enum):
    WALK = 1
    BIKE = 2
    BUS = 3
    CAR = 4


@dataclass
class IcarusObj(ABC):
    # all IcarusObj need primary keys that would be used in database

    def database_fields(self) -> str:
        """
        return the database fields string
        :returns a string used for create database field. Distinguish the method between one and multiple primary keys.
        """
        return ', '.join([_field.name for _field in dataclasses.fields(self)])


@dataclass
class IcarusObjs(ABC):
    # all IcarusObj need primary keys that would be used in database
    primary_keys: str = field(default=None)
    objects: {} = field(default=None)

    def database_fields(self) -> str:
        """
        return the database fields string
        :returns a string used for create database field. Distinguish the method between one and multiple primary keys.
        """
        if self.primary_keys is None:
            print('please assign primary keys')
        elif self.objects is None:
            print('please add objects')
        else:
            _fields = self.objects[0].database_fields()
            return f"{_fields}, PRIMARY KEY ({self.primary_keys})"


