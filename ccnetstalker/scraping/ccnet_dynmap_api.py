from . import liveatlas_api as la
from frozendict import frozendict
import time
from bs4 import BeautifulSoup
from attrs import *

# This should contain useful classes for CCNET ONLY

@define(frozen=True)
class TownSnapshot():
    name: str = field()
    nation: str = field()
    vassal: str = field()
    is_capital: bool = field()
    is_peaceful: bool = field()
    occupier: str = field()
    mayor: str = field()
    residents: tuple = field()
    trusted: tuple = field()
    cultures: tuple = field()
    board: str = field()
    bank: float = field()
    upkeep: float = field()
    resources: frozendict = field()
    foundation_date: time.struct_time = field()

    def get_resource(self, resource):
        return self.resources.get(resource, 0)
  
@define(frozen=True)
class CCNetPlayerSnapshot(la.PlayerSnapshot):
    health: int = field(init=False, default=0)
    armor: int = field(init=False, default=0)
    visible: bool = field(default=lambda self: self.world == "world")

@define
class CCNetMap(la.LiveAtlasMap):

    townlist: frozendict = field(init=False)

    @staticmethod
    def default_map_factory():
        return CCNetMap("https://map.ccnetmc.com/nationsmap/standalone/dynmap_world.json",
                        "https://map.ccnetmc.com/nationsmap/tiles/_markers_/marker_world.json")
    
    @staticmethod
    def custom_map_factory(dynmap, markers):
        return CCNetMap(dynmap, markers)
    
    @staticmethod
    def strip_commas(stringa):
        output=list(stringa)
        while True:
            if "," not in output:
                break
            output.remove(",")
        output = "".join(output)
        return output


    def fetch_players_state(self):
        super().fetch_map_state()
        self.players = (CCNetPlayerSnapshot(p) for p in self.players)

    def fetch_markers(self):
        super().fetch_markers()
        temp_townlist = dict()

        for town in self.markers["sets"]["towny.markerset"]["markers"].values():
            if town["icon"] == "warning":
                continue
            town_object = self.parse_town_desc(town["desc"])
            temp_townlist[town_object.name] = town_object

        self.markers = frozendict(temp_townlist)
        return self.markers

    def parse_town_desc(self, town_desc):
        MONTHS={"Jan":1,
                "Feb":2,
                "Mar":3,
                "Apr":4,
                "May":5,
                "Jun":6,
                "Jul":7,
                "Aug":8,
                "Sep":9,
                "Oct":10,
                "Nov":11,
                "Dec":12}
            
        text_soup = BeautifulSoup(town_desc, "html.parser")
        for br in text_soup("br"):
            br.replace_with("\n")
        text = [s.strip("•â€¢ ") for s in text_soup.get_text().split("\n")]

        if "Member" in text[0]:
            is_capital = False
            nation = text[0][text[0].rfind(" "):]
        elif "Capital" in text[0]:
            is_capital = True
            nation = text[0][text[0].rfind(" "):]
        else:
            is_capital = False
            nation = ""
        text.pop(0)

        vassal = ""
        if "Vassal of " in text[0]:
            vassal = text[0][text[0].rfind(" "):]
            text.pop(0)

        name = text.pop(0)
        occupier_string = text.pop(0)
        occupier = "" if occupier_string[-1] == "-" else occupier_string[occupier_string.index("-")+1:].strip()
        
        mayor_string = text.pop(0)
        mayor = mayor_string[mayor_string.index("-")+1:].strip()

        text.pop(0) #TODO: INVESTIGATE WHY IT'S HERE AND EMPTY

        peaceful_string = text.pop(0)
        is_peaceful = "true" in peaceful_string 
        
        trusted_string = text.pop()
        trusted = tuple(p for p in trusted_string[trusted_string.index("-")+1:].strip().split(", "))
        

        resident_string = text.pop()
        residents = tuple(p for p in resident_string[resident_string.index("-")+1:].strip().split(", "))
        
        resources_string = text.pop() #TODO: check if this works
        resources_list = tuple() if len(resources_string) < 12 else resources_string[12:].split(", ")
        resources = frozendict({r[r.find(" "):]: int(r[:r.find(" ")]) for r in resources_list})
        
        foundation_string = text.pop()
        foundation_string = foundation_string[foundation_string.index("-")+1:]
        foundation_date = None if foundation_string==" Not set" else time.strptime(foundation_string, " %b %d %Y")
        
        upkeep_string = text.pop()
        upkeep = float(CCNetMap.strip_commas(upkeep_string[upkeep_string.index("$")+1:]))
        
        bank_string = text.pop()
        bank = float(CCNetMap.strip_commas(bank_string[bank_string.index("$")+1:]))
        
        board_string = text.pop() #TODO: check if this works
        board = "" if len(board_string) < 8 else board_string[8:]
        
        cultures_string = text.pop() #TODO: check if this works
        cultures = tuple() if len(cultures_string) < 10 else cultures_string[10:].split(", ")
        
        town_object = TownSnapshot(
            name,
            nation,
            vassal,
            is_capital,
            is_peaceful,
            occupier,
            mayor,
            residents,
            trusted,
            cultures,
            board,
            bank,
            upkeep,
            resources,
            foundation_date
        )
        return town_object


        



            