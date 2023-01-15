import json
import requests
import os
import math


DYNMAP_LINK="https://map.ccnetmc.com/nationsmap/standalone/dynmap_world.json"

ENABLE_PREDICTORS = True
ENABLE_TRACKERS = True

 #If it becomes false, the program ends

def fetch_dynmap_data():
    '''Fetches data from the dynamic map URL and returns it in a dict() object'''

    raw_dynmap_data=requests.get(url=DYNMAP_LINK)
    dynmap_data=raw_dynmap_data.json()
    #This is A LOT of data, and most of it is garbage.
    data_timestamp=raw_dynmap_data.headers["last-modified"]
    dynmap_data["timestamp"]=data_timestamp 
    #The "timestamp" field in the Response is hard to work with
    #The response header's timestamp is used instead, because it's more understandable
    return dynmap_data

def filter_players_from_data(data):
    '''Filters players information from fetch_player_data() and returns it in a dict() object.

    The returned data amounts to:
    -Timestamp of the response;
    -Account name of every visible player;
    -Horizontal and Vertical coordinates of every visible player.
    '''
    player_data=dict()
    for player in data["players"]:
        name = player["account"] #Gets player's account name (Not /nick name)
        x = int(math.floor(player["x"])) #Gets player's x coordinate
        y = int(math.floor(player["y"])) #Gets player's y coordinate - THIS IS THE VERTICAL AXIS
        z = int(math.floor(player["z"])) #Gets player's z coordinate
        if x!=0 and z!=0:
            #Pairs up a player's account name with its coordinate at that timestamp
            #Default values for non-visible players are x:0, y:64, z:0
            #Non-visible players' coordinates are None.
            player_data[name]={ "x":x, "y":y, "z":z}
        else:
            player_data[name]=None
    stripped_data={
        "players":player_data,
        "timestamp":data["timestamp"]}
    return stripped_data
# Q: Why are fetch_dynmap_data() and strip_dynmap_data() different functions?
# A: Data stripped by strip_dynmap_data() might me useful in the future for features not yet designed.

def check_for_detected_players(player_data, tracked_players, boundaries):
    for name in player_data["players"]:
        if player_data["players"][name] != None and name in tracked_players:
            for boundary in boundaries:
                left_border = boundary["upper_left_corner"]["x"]
                upper_border = boundary["upper_left_corner"]["z"]
                right_border = boundary["lower_right_corner"]["x"]
                lower_border = boundary["lower_right_corner"]["z"]
                border_type = boundary["type"]
                if left_border <= player_data["players"][name]["x"] <= right_border and upper_border <= player_data["players"][name]["z"] <= lower_border:
                    print("Player " + name + " has been detected in boundary " + boundary["name"] + " at coordinates " + str(player_data["players"][name]))


def initialize_settings():
    with open("config/settings.json", "r") as settings:
        return json.load(settings)

def initialize_boundaries():
    with open("config/boundaries.json","r") as boundaries:
        return json.load(boundaries)["boundaries"]

def initialize_players():
    with open("config/players.json", "r") as tracked_players:
        return set(json.load(tracked_players)["single_players"])

def main():

    settings = initialize_settings()

    if settings["modules"]["player_detector"]["enabled"]:
        tracked_players = initialize_players()
        boundaries = initialize_boundaries()
    
    execution_flag = True
    
    #TODO: Read config from json files
    #TODO: Accept keyword arguments
    #TODO: Initialize

    while execution_flag:
        player_data = filter_players_from_data(fetch_dynmap_data())
        if settings["modules"]["player_detector"]["enabled"]:
            check_for_detected_players(player_data, tracked_players, boundaries)


main()
