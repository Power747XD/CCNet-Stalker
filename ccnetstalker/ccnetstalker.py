from config import RunnableUnit
from scraping import ccnet_dynmap_api as ccda
from pathlib import Path
import json
import time

def sky_radar(config, feed):
    for player in feed:
        if player.y >= config.attributes["y_threshold"]:
            print(player.name + " Sky")

def player_detector(config, feed):
    for boundary in config.boundaries:
        for player in feed:
            if boundary.left_border < player.x < boundary.right_border and \
                boundary.upper_border < player.z < boundary.lower_border:
                print(player.name, boundary.name)

def movecraft_radar(config, feed, past, streak):
    if past == None:
        past = feed
        return
    elif past[0].timestamp==feed[0].timestamp:
        return
    
    streak_threshold = config.attributes["streak_threshold"]
    deviation_limit = config.attributes["deviation_limit"]
    reset_if_still = config.attributes["reset_if_still"]
    filtered_feed = filter(lambda x: x in config.whitelist, feed)
    updated_streak = dict()
    
    for c_player in filtered_feed:
        player_found = False
        for p_player in past:
            if c_player.name==p_player.name:
                player_found = True
                delta_x = abs(p_player.x-c_player.x)
                delta_z = abs(p_player.z-c_player.z)
                if delta_x == 0 and delta_z==0:
                    if reset_if_still:
                        streak.pop(p_player.name, "")
                    continue
                elif (delta_x < deviation_limit and delta_z > deviation_limit) or \
                     (delta_x > deviation_limit and delta_z < deviation_limit):
                    if c_player.name in streak.keys():
                        streak[c_player.name] += 1
                    else:
                        streak[c_player.name] = 1
                break
        if not player_found:
            streak.pop(p_player.name, "")

    for name in streak.keys():
        if streak[name] > streak_threshold:
            print(name + "might be using a vehicle. He moved straight " + streak[name] +  " times.")


def main():
    p = Path(__file__).parents[1].joinpath("config")
    with open(p.joinpath("settings.json"), "r") as f:
        all_conf = json.loads(f.read())["modules"]
    
    tasks_list = []
    tasks_list.append(RunnableUnit(sky_radar, all_conf["sky_radar"]))
    tasks_list.append(RunnableUnit(player_detector, all_conf["player_detector"]))
    tasks_list.append(RunnableUnit(movecraft_radar, all_conf["movecraft_radar"]))

    datafeed = ccda.CCNetMap.default_map_factory()
    datafeed.fetch_markers()

    start_time = time.monotonic()
    interval = 5 #in seconds

    while True:
        datafeed.fetch_map_state()
        tasks_list[0].run(datafeed.players)
        tasks_list[1].run(datafeed.players)

        past_players = None
        movecraft_streaks = dict()
        tasks_list[2].run(datafeed.players, past_players, movecraft_streaks)

        print("Tick completed!\n")

        time.sleep(max(0, interval - (time.monotonic() - start_time) % interval))

main()
