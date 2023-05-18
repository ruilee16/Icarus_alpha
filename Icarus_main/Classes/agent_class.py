from Icarus_main.Classes.basic_class import IcarusObj, IcarusObjs
from typing import Tuple
import dataclasses


@dataclasses.dataclass
class Agent(IcarusObj):
    agent_id: int = dataclasses.field(default=None)
    activities: dict = dataclasses.field(default=None)
    trips: dict = dataclasses.field(default=None)
    routed: bool = dataclasses.field(default=False)
    # def update_trip(self, trip):
    # self.trips[trip.trip_id] = trip
    __primary_key__ = ['agent_id']


@dataclasses.dataclass
class Event(IcarusObj):
    agent_id: int = dataclasses.field(default=None)
    has_AC: bool = dataclasses.field(default=True)
    start_time: int = dataclasses.field(default=None)
    duration: int = dataclasses.field(default=None)
    end_time: int = dataclasses.field(default=None)
    heat_exposure: float = dataclasses.field(default=None)  # exposure per second

    def __post_init__(self):
        if self.start_time is not None and self.end_time is not None:
            self.duration = int(self.end_time - self.start_time)
        elif self.start_time is not None and self.duration is not None:
            self.end_time = int(self.start_time + self.duration)
        elif self.end_time is not None and self.duration is not None:
            self.start_time = int(self.end_time - self.duration)
        else:
            print('not enough time data')


@dataclasses.dataclass
class Activity(Event):
    activity_id: int = dataclasses.field(default=None)
    location: Tuple = dataclasses.field(default=None)
    __primary_key__ = ['agent_id', 'activity_id']
    __dict_key__ = 'activity_id'


@dataclasses.dataclass
class Trip(Event):
    trip_id: int = dataclasses.field(default=None)
    start_location: Tuple = dataclasses.field(default=None)
    end_location: Tuple = dataclasses.field(default=None)
    travel_mode: str = dataclasses.field(default=None)
    __primary_key__ = ['agent_id', 'trip_id']
    __dict_key__ = 'trip_id'

