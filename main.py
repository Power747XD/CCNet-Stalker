import json
import requests
import math


DYNMAP_LINK="https://map.ccnetmc.com/nationsmap/standalone/dynmap_world.json"

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

def check_for_players_in_boundaries(player_data, whitelist, boundaries):
    '''Checks whether any player has moved into any user-defined boundary'''
    for name in player_data["players"]:
        if player_data["players"][name] != None and name in whitelist:
            for boundary in boundaries:
                left_border = boundary["upper_left_corner"]["x"]
                upper_border = boundary["upper_left_corner"]["z"]
                right_border = boundary["lower_right_corner"]["x"]
                lower_border = boundary["lower_right_corner"]["z"]
                if left_border <= player_data["players"][name]["x"] <= right_border and upper_border <= player_data["players"][name]["z"] <= lower_border:
                    print("Player " + name + " has been detected in boundary " + boundary["name"] + " at coordinates " + str(player_data["players"][name]))

def check_for_sky_players(player_data, sky_radar_settings, reference):
    '''Detects player above a config-specified height coordinate.
    '''
    if player_data["timestamp"]==reference:
        return

    for name in player_data["players"]:
        if player_data["players"][name] == None:
            continue
        if player_data["players"][name]["y"] >= sky_radar_settings["y_threshold"]:
            print("Player "+ name + " has been spotted in the sky at\nx: "+ str(player_data["players"][name]["x"]) + "\nz: " + str(player_data["players"][name]["z"]) + "\nHeight: " + str(player_data["players"][name]["y"]))

def calculate_movecraft(past_player_positions, player_data, movecraft_streak_index, mvc_d_settings):
    '''Checks if any players has moved in a straight line. If they have, add the player to movecraft_streak_index or increrase its value by one.
    If the value is greater than the value set in the config, prints the player, their index and their current coordinates.'''
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
    for name in past_player_positions[0]["players"]:
        if mvc_d_settings["targets"]!= None and name not in mvc_d_settings["targets"]:
            continue
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

                deviation_limit = mvc_d_settings["deviation_limit"]

                if (delta_x == deviation_limit and delta_z != deviation_limit) or (delta_x != deviation_limit and delta_z == deviation_limit):
                    if name in movecraft_streak_index:
                        movecraft_streak_index[name] += 1
                    else:
                        movecraft_streak_index[name] = 1
                elif mvc_d_settings["reset_if_still"] and delta_x==0 and delta_z==0:
                    continue
                else:
                    movecraft_streak_index.pop(name, "")
            else:
                movecraft_streak_index.pop(name, "")

    for name in movecraft_streak_index:
        if movecraft_streak_index[name] >= mvc_d_settings["streak_threshold"]:
            print(name + "might be using a vehicle. He moved straight "+ str(movecraft_streak_index[name])+ "time(s)."+"\n"+str(player_data["players"][name]))


def initialize_settings():
    with open("config/settings.json", "r") as settings:
        return json.load(settings)["modules"]

def initialize_players():
    with open("config/settings.json", "r") as w:
        whitelists = json.load(w)["whitelists"]
        for wlist in whitelists:
            whitelists[wlist]=set(whitelists[wlist])
        return whitelists

def initialize_boundaries():
    with open("config/boundaries.json","r") as boundaries:
        return json.load(boundaries)["boundaries"]

def main():

    #Initialization phase

    settings = initialize_settings()
    whitelists = initialize_players()

    if settings["player_detector"]["enabled"]:
        boundaries = initialize_boundaries()

    if settings["sky_radar"]["enabled"]:
        sky_radar_settings={
            "y_threshold": settings["sky_radar"]["y_threshold"],
            "targets":None
        }
        if settings["sky_radar"]["target"]=="WHITELIST":
            sky_radar_settings["targets"]= set(whitelists["sky_radar"])
        

    if settings["movecraft_detector"]["enabled"]:
        past_player_positions = [None, None]
        movecraft_detector_settings={
            "streak_threshold": settings["movecraft_detector"]["streak_threshold"],
            "deviation_limit": settings["movecraft_detector"]["deviation_limit"],
            "reset_if_still": settings["movecraft_detector"]["reset_if_still"],
            "targets": None
        }
        if settings["movecraft_detector"]["target"]=="WHITELIST":
            movecraft_detector_settings["targets"]=set(whitelists["movecraft_detector"])
        movecraft_streak_index = dict()
    
    reference_timestamp=None

    print("The Stalker has been successfully initialized!")
    
    #Running phase

    execution_flag = True

    while execution_flag:
        player_data = filter_players_from_data(fetch_dynmap_data())

        if settings["player_detector"]["enabled"]:
            check_for_players_in_boundaries(player_data, whitelists["player_detector"], boundaries)

        if settings["sky_radar"]["enabled"]:
                check_for_sky_players(player_data, sky_radar_settings, reference_timestamp)

        if settings["movecraft_detector"]["enabled"]:
            calculate_movecraft(past_player_positions, player_data, movecraft_streak_index, movecraft_detector_settings)

        reference_timestamp=player_data["timestamp"]

if __name__=="__main__":
    main()
