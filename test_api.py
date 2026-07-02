import requests
import json

API_KEY = "ae31b5ab-62bd-43a5-9ccc-5b3a1455b7fe"
player_id = "c61d247d-7f77-452c-b495-2813a9cd0ac4"

url = "https://api.cricapi.com/v1/players_info"
params = {"apikey": API_KEY, "id": player_id}

response = requests.get(url, params=params)
data = response.json()

stats_list = data["data"]["stats"]

# Helper to safely extract a stat, handling the space inconsistency
def get_stat(stats_list, fn, matchtype, stat_name):
    for entry in stats_list:
        if (entry["fn"] == fn 
            and entry["matchtype"].strip() == matchtype 
            and entry["stat"].strip() == stat_name):
            return entry["value"].strip()
    return None

t20_batting_avg = get_stat(stats_list, "batting", "t20", "avg")
t20_bowling_avg = get_stat(stats_list, "bowling", "t20", "avg")
t20_batting_sr = get_stat(stats_list, "batting", "t20", "sr")
t20_bowling_sr = get_stat(stats_list, "bowling", "t20", "sr")
t20_bowling_economy = get_stat(stats_list, "bowling", "t20", "econ")
ipl_batting_avg = get_stat(stats_list, "batting", "ipl", "avg")
ipl_bowling_avg = get_stat(stats_list, "bowling", "ipl", "avg")
ipl_batting_sr = get_stat(stats_list, "batting", "ipl", "sr")
ipl_bowling_sr = get_stat(stats_list, "bowling", "ipl", "sr")
ipl_bowling_economy = get_stat(stats_list, "bowling", "ipl", "econ")

print("----- PLAYER STATS -----")
print("Player Name: ",data["data"]["name"])
print("T20 Batting Avg:", t20_batting_avg)
print("T20 Bowling Avg:", t20_bowling_avg)
print("T20 Batting Strike Rate:", t20_batting_sr)
print("T20 Bowling Strike Rate:", t20_bowling_sr)
print("T20 Bowling Economy:", t20_bowling_economy)
print("IPL Batting Avg:", ipl_batting_avg)
print("IPL Bowling Avg:", ipl_bowling_avg)
print("IPL Batting Strike Rate:", ipl_batting_sr)
print("IPL Bowling Strike Rate:", ipl_bowling_sr)
print("IPL Bowling Economy:", ipl_bowling_economy)