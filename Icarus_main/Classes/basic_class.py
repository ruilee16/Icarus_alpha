from __future__ import annotations
import dataclasses
from typing import List
from enum import Enum
from abc import ABC


class TravelMode(Enum):
    WALK = 1
    BIKE = 2
    BUS = 3
    CAR = 4


class ActivityType(Enum):
    Home = 0
    Workplace = 1
    University = 2
    School = 3
    Escorting = 4
    School_escort = 41
    Pure_escort_as_main_purpose_of_the_tour = 411
    Ridesharing_stops_on_commuting_tours = 412
    Other_escort_not_by_same_household_members = 42
    Shopping = 5
    Other_maintenance = 6
    Eating_out = 7
    Breakfast = 71
    Lunch = 72
    Dinner = 73
    Visiting_relatives_or_friends = 8
    Other_discretionary = 9
    At_work = 11
    At_work_business = 12
    At_work_lunch = 13
    At_work_other = 14
    Work_related_business = 15
    ASU_related_trip_to_ASU_MAZs = 16


@dataclasses.dataclass
class IcarusObj(ABC):
    # all IcarusObj need primary keys that would be used in database
    # __primary_key__: str = dataclasses.field(default='')

    def database_fields(self) -> str:
        """
        return the database fields string
        :returns a string used for create database field. Distinguish the method between one and multiple primary keys.
        """
        return ', '.join([_field.name for _field in dataclasses.fields(self)])


@dataclasses.dataclass
class IcarusObjs(ABC):
    # all IcarusObj need primary keys that would be used in database
    primary_keys: str = dataclasses.field(default=None)
    objects: {} = dataclasses.field(default=None)

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
