#!/usr/bin/python3

import riotwatcher
import json
import time
import argparse
import os
from jinja2 import Environment, FileSystemLoader
from requests.exceptions import HTTPError

WATCHER = None
REGION  = "euw1"
KEY     = None

def tierToNumber(tier):
    ratingmap = {   'CHALLENGER' : 9000,
                    'GRANDMASTER': 8000,
                    'MASTER'     : 7000,
                    'DIAMOND'    : 6000,
                    'PLATINUM'   : 5000,
                    'GOLD'       : 4000,
                    'SILVER'     : 3000,
                    'BRONZE'     : 2000,
                    'IRON'       : 1000 }
    return ratingmap[tier]

def divisionToNumber(division):
    divisionmap = { "I"   : 400,
                    "II"  : 300,
                    "III" : 200,
                    "IV"  : 100 }
    return divisionmap[division]

def api(iterable):

    players = []
    missing = []
    count = 0
    pTmp = None

    for l in iterable:
        count += 1
        if count > 9:
            time.sleep(1)
        try:
            pTmp = WATCHER.summoner.by_name(REGION, l.strip())
        except HTTPError:
            missing += [l]
            print("Backing off for 2minutes because of Rate Limit")
            time.sleep(120)

        if not pTmp:
            continue

        try:
            pInfo = WATCHER.league.by_summoner(REGION, pTmp["id"])
        except HTTPError:
            missing += [l]
            print("Backing off for 2minutes because of Rate Limit")
            time.sleep(120)

        for queue in pInfo:
            if queue["queueType"] != "RANKED_SOLO_5x5":
                continue
            queue["sorter"] = tierToNumber(queue["tier"]) \
                                + divisionToNumber(queue["rank"]) \
                                + int(queue["leaguePoints"])
            queue.pop("summonerId")
            queue.pop("leagueId")
            players += [dict(queue)]

    return (missing, players)

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='ESE Overlord')
    parser.add_argument('--target-file', required=True)
    args = parser.parse_args()
    
    with open("key.txt","r") as f:
        key = f.read().strip()
        WATCHER = riotwatcher.LolWatcher(key)

    playersAll = []
    with open("players.txt") as f:
        missing, players = api(f)
        missing, playersMissed = api(missing)
        playersAll = playersAll + playersMissed 
        if missing:
            print("Still missing some players:", missing)
    
    players = sorted(playersAll, key=lambda p: p["sorter"], reverse=True)
    with open(args.target_file, "w") as f:
        f.write(json.dumps(players, indent=4))

    os.chmod(args.target_file, 0o644)
    
    env = Environment(loader=FileSystemLoader('.'))
    template = env.get_template('data.html')     
    output = template.render(players=players)
    
    with open(args.target_file + ".html", "w") as f:
        f.write(output)

    os.chmod(args.target_file + ".html", 0o644)

