import json
import requests
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

def check_for_players_in_boundaries(player_data, tracked_players, boundaries):
    for name in player_data["players"]:
        if player_data["players"][name] != None and name in tracked_players:
            for boundary in boundaries:
                left_border = boundary["upper_left_corner"]["x"]
                upper_border = boundary["upper_left_corner"]["z"]
                right_border = boundary["lower_right_corner"]["x"]
                lower_border = boundary["lower_right_corner"]["z"]
                #border_type = boundary["type"]
                if left_border <= player_data["players"][name]["x"] <= right_border and upper_border <= player_data["players"][name]["z"] <= lower_border:
                    print("Player " + name + " has been detected in boundary " + boundary["name"] + " at coordinates " + str(player_data["players"][name]))

def check_for_sky_players(player_data, y_threshold, tracked_players=None):
    '''Detects player above a config-specified height coordinate.
    
    The sky_player_detector has two types of targets:
    "ALL" reports ALL players above y_threshold;
    "WHITELIST" reports ONLY players specified in players.json
    '''
    for name in player_data["players"]:
        if player_data["players"][name] == None:
            continue
        if player_data["players"][name]["y"] >= y_threshold:
            if tracked_players == None or name in tracked_players:
                print(name, player_data["players"][name])

def calculate_movecraft(past_player_positions, player_data, movecraft_streak_index, streak_threshold):
    
    #Fills past_player_positions with two sets of player coordinates
    assert len(past_player_positions) < 3
    if past_player_positions[0]==None:
        past_player_positions[0]=player_data
        return
    elif past_player_positions[0]["timestamp"] == player_data["timestamp"]:
        return
    else:
        if past_player_positions[1]==None:
            past_player_positions[1] = player_data
            return
        elif past_player_positions[1]["timestamp"]==player_data["timestamp"]:
            return
        
        elif past_player_positions[1]["timestamp"]!=player_data["timestamp"]:
            past_player_positions[0], past_player_positions[1] = past_player_positions[1], player_data

    #check if any player has moved in an exact straight line
    assert past_player_positions[0]["timestamp"]!=past_player_positions[1]["timestamp"]
    

    for name in past_player_positions[0]["players"]:
        if name in past_player_positions[1]["players"]:

            detected_in_0 = name in past_player_positions[0]["players"] and past_player_positions[0]["players"][name] != None
            detected_in_1 = name in past_player_positions[1]["players"] and past_player_positions[1]["players"][name] != None   

            if detected_in_0 and detected_in_1:
                x_0=past_player_positions[0]["players"][name]["x"]
                x_1=past_player_positions[1]["players"][name]["x"]
                z_0=past_player_positions[0]["players"][name]["z"]
                z_1=past_player_positions[1]["players"][name]["z"]
                delta_x = x_0 - x_1
                delta_z = z_0 - z_1

                if (delta_x == 0 and delta_z != 0) or (delta_x != 0 and delta_z == 0):
                    if name in movecraft_streak_index:
                        movecraft_streak_index[name] += 1
                    else:
                        movecraft_streak_index[name] = 1
                else:
                    movecraft_streak_index.pop(name, "")
            else:
                movecraft_streak_index.pop(name, "")

    for name in movecraft_streak_index:
        if movecraft_streak_index[name] >= streak_threshold:
            print(name + "might be using a vehicle. He moved straight "+movecraft_streak_index[name]+ "time(s)")



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

    #Initialization phase

    settings = initialize_settings()

    if settings["modules"]["player_detector"]["enabled"]:
        tracked_players = initialize_players()
        boundaries = initialize_boundaries()

    if settings["modules"]["sky_players_detector"]["enabled"]:
        y_threshold = settings["modules"]["sky_players_detector"]["y_threshold"]
        if settings["modules"]["sky_players_detector"]["target"] == "WHITELIST":
            tracked_players = initialize_players()

    if settings["modules"]["movecraft_detector"]["enabled"]:
        past_player_positions = [None, None]
        streak_threshold = settings["modules"]["movecraft_detector"]["streak_threshold"]
        movecraft_streak_index = dict()
    
    #Running phase

    execution_flag = True

    while execution_flag:
        player_data = filter_players_from_data(fetch_dynmap_data())

        if settings["modules"]["player_detector"]["enabled"]:
            check_for_players_in_boundaries(player_data, tracked_players, boundaries)

        if settings["modules"]["sky_players_detector"]["enabled"]:
            if settings["modules"]["sky_players_detector"]["target"] == "WHITELIST":
                check_for_sky_players(player_data, y_threshold, tracked_players)
            else: 
                check_for_sky_players(player_data, y_threshold)

        if settings["modules"]["movecraft_detector"]["enabled"]:
            calculate_movecraft(past_player_positions, player_data, movecraft_streak_index, streak_threshold)

if __name__=="__main__":
    main()
