import requests
import pandas as pd
import time
import os

API_KEY = "ae31b5ab-62bd-43a5-9ccc-5b3a1455b7fe"

SQUAD_FILE = r'C:\Users\User\Documents\IPL_predictor\data\squads.csv'
PROGRESS_FILE = r'C:\Users\User\Documents\IPL_predictor\data\squad_with_stats.csv'
FINAL_FILE = r'C:\Users\User\Documents\IPL_predictor\data\squad_with_stats_FINAL.csv'

# Leave a safety buffer under the 100 hits/day limit (2 hits per player)
MAX_PLAYERS_PER_RUN = 45


def get_player_id(name):
    url = "https://api.cricapi.com/v1/players"
    params = {"apikey": API_KEY, "offset": 0, "search": name}
    response = requests.get(url, params=params)
    data = response.json()
    if data.get("data"):
        return data["data"][0]["id"]
    return None


def get_stat(stats_list, fn, matchtype, stat_name):
    for entry in stats_list:
        if (entry["fn"] == fn
                and entry["matchtype"].strip() == matchtype
                and entry["stat"].strip() == stat_name):
            return entry["value"].strip()
    return None


# Step 1: Load your squad file
df_sq = pd.read_csv(SQUAD_FILE)
unique_players = df_sq['player'].unique()
print(f"Total unique players in squad: {len(unique_players)}")

# Step 2: Load existing progress if it exists AND is not empty
if os.path.exists(PROGRESS_FILE) and os.path.getsize(PROGRESS_FILE) > 0:
    df_progress = pd.read_csv(PROGRESS_FILE)
    already_done = set(df_progress['player'])
    print(f"Resuming. Already fetched: {len(already_done)} players.")
else:
    df_progress = pd.DataFrame()
    already_done = set()
    print("Starting fresh.")

# Step 3: Figure out who's left
remaining_players = [p for p in unique_players if p not in already_done]
print(f"Remaining players to fetch: {len(remaining_players)}")

players_today = remaining_players[:MAX_PLAYERS_PER_RUN]
print(f"Fetching {len(players_today)} players in this run...")

new_results = []

for player_name in players_today:
    print(f"Fetching: {player_name}...")

    player_id = get_player_id(player_name)
    if not player_id:
        print(f"  Could not find ID for {player_name}, skipping.")
        new_results.append({"player": player_name})
        time.sleep(1)
        continue

    url = "https://api.cricapi.com/v1/players_info"
    params = {"apikey": API_KEY, "id": player_id}
    response = requests.get(url, params=params)
    data = response.json()

    stats_list = data.get("data", {}).get("stats", [])

    row = {
        "player": player_name,
        "t20_batting_avg": get_stat(stats_list, "batting", "t20", "avg"),
        "t20_bowling_avg": get_stat(stats_list, "bowling", "t20", "avg"),
        "t20_batting_sr": get_stat(stats_list, "batting", "t20", "sr"),
        "t20_bowling_sr": get_stat(stats_list, "bowling", "t20", "sr"),
        "t20_bowling_econ": get_stat(stats_list, "bowling", "t20", "econ"),
        "ipl_batting_avg": get_stat(stats_list, "batting", "ipl", "avg"),
        "ipl_bowling_avg": get_stat(stats_list, "bowling", "ipl", "avg"),
        "ipl_batting_sr": get_stat(stats_list, "batting", "ipl", "sr"),
        "ipl_bowling_sr": get_stat(stats_list, "bowling", "ipl", "sr"),
        "ipl_bowling_econ": get_stat(stats_list, "bowling", "ipl", "econ"),
    }
    new_results.append(row)
    time.sleep(1)

# Step 4: Save progress
df_new = pd.DataFrame(new_results)
df_progress = pd.concat([df_progress, df_new], ignore_index=True)
df_progress.to_csv(PROGRESS_FILE, index=False)

print(f"Saved progress. Total players fetched so far: {len(df_progress)} / {len(unique_players)}")

# Step 5: If everything is fetched, merge with team info and save final file
if len(df_progress) >= len(unique_players):
    print("All players fetched! Merging with squad/team data...")
    df_final = df_sq.merge(df_progress, on="player", how="left")
    df_final.to_csv(FINAL_FILE, index=False)
    print(f"Saved final merged file: {FINAL_FILE}")
else:
    print(f"Run this script again (tomorrow, once your daily API limit resets) "
          f"to continue — {len(unique_players) - len(df_progress)} players left.")