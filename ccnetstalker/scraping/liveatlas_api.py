import requests
import json
from frozendict import frozendict
from attrs import *

@define(frozen=True)
class PlayerSnapshot():
    name: str 
    world: str
    x: int 
    y: int 
    z: int 
    health: int
    armor: int
    timestamp: int

    def get_coordinates(self):
        return (self.x, self.y, self.z)

    def has_health_info(self):
        return self.health != 0

@define
class LiveAtlasMap():
    dynmap_url: str = field(on_setattr=setters.frozen)
    markers_url: str = field(on_setattr=setters.frozen)
    map_state: frozendict = field(init=False)
    players: tuple = field(init=False)
    markers: frozendict = field(init=False)

    def fetch_map_state(self):
        temp_state = requests.get(self.dynmap_url).json()
        players = tuple([PlayerSnapshot(p["account"],
                        p["world"],
                        p["x"],
                        p["y"],
                        p["z"],
                        p["health"],
                        p["armor"],
                        temp_state["timestamp"]) for p in temp_state["players"]])
        self.players = players
        del temp_state["players"]
        self.map_state = frozendict(temp_state)

    def fetch_markers(self):
        temp_state = requests.get(self.markers_url).json()
        self.markers = frozendict(temp_state)