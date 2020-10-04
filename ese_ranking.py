#!/usr/bin/python3

import riotwatcher
import json
import argparse
import os
from jinja2 import Environment, FileSystemLoader

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

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='ESE Overlord')
    parser.add_argument('--target-file', required=True)
    args = parser.parse_args()
    
    with open("key.txt","r") as f:
        key = f.read().strip()
        WATCHER = riotwatcher.LolWatcher(key)

    players = []
    with open("players.txt") as f:
        for l in f:
            pTmp = WATCHER.summoner.by_name(REGION, l.strip())
            if not pTmp:
                continue
            pInfo = WATCHER.league.by_summoner(REGION, pTmp["id"])
            for queue in pInfo:
                if queue["queueType"] != "RANKED_SOLO_5x5":
                    continue
                queue["sorter"] = tierToNumber(queue["tier"]) \
                                    + divisionToNumber(queue["rank"]) \
                                    + int(queue["leaguePoints"])
                queue.pop("summonerId")
                queue.pop("leagueId")
                players += [dict(queue)]
    
    players = sorted(players, key=lambda p: p["sorter"], reverse=True)
    with open(args.target_file, "w") as f:
        f.write(json.dumps(players, indent=4))

    os.chmod(args.target_file, 0o644)
    
    env = Environment(loader=FileSystemLoader('.'))
    template = env.get_template('data.html')     
    output = template.render(players=players)
    
    with open(args.target_file + ".html", "w") as f:
        f.write(output)

    os.chmod(args.target_file + ".html", 0o644)

