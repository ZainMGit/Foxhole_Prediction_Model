import requests
import time
import csv
import os
from datetime import datetime

BASE = "https://war-service-live.foxholeservices.com/api"
MAPS_URL = f"{BASE}/worldconquest/maps"
DYNAMIC_URL = f"{BASE}/worldconquest/maps/{{}}/dynamic/public"
WAR_URL = f"{BASE}/worldconquest/war"
POLL_INTERVAL = 2.5  # seconds

FOLDER = "live_war_events"
os.makedirs(FOLDER, exist_ok=True)  # ✅ Ensure folder exists

icon_type_lookup = {
    18: "Shipyard",
    33: "Storage Facility",
    34: "Factory",
    35: "Garrison Station",
    45: "Relic Base",
    56: "Town Base 1",
    57: "Town Base 2",
    58: "Town Base 3"
}

previous_state = {}
csv_file = None
current_war_number = None

def get_war_info():
    response = requests.get(WAR_URL)
    response.raise_for_status()
    data = response.json()
    return data["warId"], data["warNumber"]

def get_active_maps():
    return requests.get(MAPS_URL).json()

def get_dynamic_map(map_name):
    return requests.get(DYNAMIC_URL.format(map_name)).json()

def icon_category(icon_type):
    return icon_type_lookup.get(icon_type, "Unknown")

def unique_key(item):
    return (item["iconType"], round(item["x"], 5), round(item["y"], 5))

def get_csv_path(war_number):
    return os.path.join(FOLDER, f"foxhole_events_war_{war_number}.csv")

def initialize_csv(war_number):
    global csv_file
    csv_file = get_csv_path(war_number)
    if not os.path.exists(csv_file):
        with open(csv_file, mode="w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(["Timestamp", "War ID", "War Number", "Map", "Icon Type", "Icon Category", "Team"])

def log_event(war_id, war_number, map_name, icon_type, icon_cat, team):
    with open(csv_file, mode="a", newline="") as file:
        writer = csv.writer(file)
        writer.writerow([
            datetime.now().isoformat(),
            war_id,
            war_number,
            map_name,
            icon_type,
            icon_cat,
            team
        ])

def run_tracker():
    global current_war_number

    war_id, war_number = get_war_info()
    current_war_number = war_number
    initialize_csv(war_number)
    maps = get_active_maps()
    print(f"📡 Tracking {len(maps)} maps for War {war_number} ({war_id})\n")

    for map_name in maps:
        previous_state[map_name] = {}

    while True:
        try:
            new_war_id, new_war_number = get_war_info()
            if new_war_number != current_war_number:
                print(f"⚠️ Detected new war: {new_war_number} (was {current_war_number})")
                current_war_number = new_war_number
                initialize_csv(new_war_number)
        except Exception as e:
            print(f"❌ Could not refresh war info: {e}")

        for map_name in maps:
            try:
                data = get_dynamic_map(map_name)
                current = {}

                for item in data.get("mapItems", []):
                    k = unique_key(item)
                    team = item["teamId"]
                    current[k] = team

                    if k in previous_state[map_name]:
                        prev_team = previous_state[map_name][k]
                        if prev_team != team:
                            cat = icon_category(item["iconType"])
                            print(f"[{datetime.now()}] {map_name}: iconType {item['iconType']} ({cat}) at ({item['x']:.3f},{item['y']:.3f}) changed {prev_team} → {team}")
                            log_event(new_war_id, new_war_number, map_name, item["iconType"], cat, team)

                previous_state[map_name] = current

            except Exception as e:
                print(f"❌ Error on {map_name}: {e}")

        time.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    run_tracker()
