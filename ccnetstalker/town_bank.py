from scraping import ccnet_dynmap_api as ccda
from frozendict import frozendict
import math

def town_taxes(markers_state: frozendict, conf):
    days_list=list()
    for town in markers_state.values():
        try:
            days = math.ceil(town.bank/town.upkeep)
            if days == 0:
                days = 1
        except ZeroDivisionError:
            days = float("+inf")
        days_list.append({"name":town.name,
                          "days":days})
    return days_list

if __name__=="__main__":
    towns = town_taxes(ccda.CCNetMap.default_map_factory().fetch_markers(), None)
    print(sorted(towns, key=lambda i: i["days"]))