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
os.makedirs(FOLDER, exist_ok=True)

icon_type_lookup = {
    18: "Shipyard",
    33: "Storage Facility",
    34: "Factory",
    35: "Garrison Station",
    45: "Relic Base",
    56: "Town Base 1",
    57: "Town Base 2",
    58: "Town Base 3",
    28: "Observation Tower"
}

previous_state = {}
csv_file = None
current_war_number = None

def get_war_info():
    r = requests.get(WAR_URL)
    r.raise_for_status()
    data = r.json()
    return (
        data["warId"],
        data["warNumber"],
        int(data["conquestStartTime"]),
        data.get("resistanceStartTime"),
        data.get("conquestEndTime")
    )

def is_resistance_phase(resistance_start, conquest_end):
    return resistance_start is not None and conquest_end is not None

def format_war_time(conquest_start_unix_ms):
    now = datetime.utcnow()
    delta = now - datetime.utcfromtimestamp(conquest_start_unix_ms / 1000)
    days = delta.days
    hours, remainder = divmod(delta.seconds, 3600)
    minutes = remainder // 60
    return f"{days}d {hours:02}h {minutes:02}m"

def get_minutes_since_war_started(conquest_start_unix_ms):
    now_unix = int(time.time())  # current time in seconds
    start_unix = conquest_start_unix_ms // 1000
    elapsed_sec = now_unix - start_unix
    return elapsed_sec // 60

def get_active_maps():
    r = requests.get(MAPS_URL)
    r.raise_for_status()
    return r.json()

def get_dynamic_map(map_name):
    r = requests.get(DYNAMIC_URL.format(map_name))
    r.raise_for_status()
    return r.json()

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
            writer.writerow([
                "Timestamp",
                "War Time",
                "Minutes Since War Start",
                "War ID",
                "War Number",
                "Map",
                "Icon Type",
                "Icon Category",
                "Team"
            ])

def log_event(war_id, war_number, war_time, minutes_since_start, map_name, icon_type, icon_cat, team):
    with open(csv_file, mode="a", newline="") as file:
        writer = csv.writer(file)
        writer.writerow([
            datetime.now().isoformat(),
            war_time,
            minutes_since_start,
            war_id,
            war_number,
            map_name,
            icon_type,
            icon_cat,
            team
        ])

def run_tracker():
    global current_war_number

    war_id, war_number, conquest_start, resistance_start, conquest_end = get_war_info()
    if is_resistance_phase(resistance_start, conquest_end):
        print("🛑 War is in resistance phase. Logging halted.")
        return

    current_war_number = war_number
    initialize_csv(war_number)

    maps = get_active_maps()
    print(f"📡 Tracking {len(maps)} maps for War {war_number} ({war_id})\n")

    for map_name in maps:
        previous_state[map_name] = {}

    while True:
        try:
            war_id, war_number, conquest_start, resistance_start, conquest_end = get_war_info()

            if is_resistance_phase(resistance_start, conquest_end):
                print("🛑 War entered resistance phase. Logging stopped.")
                break

            if war_number != current_war_number:
                print(f"⚠️ New war detected: {war_number} (was {current_war_number})")
                current_war_number = war_number
                initialize_csv(war_number)
                for map_name in maps:
                    previous_state[map_name] = {}

        except Exception as e:
            print(f"❌ Error refreshing war info: {e}")
            time.sleep(POLL_INTERVAL)
            continue

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
                            war_time = format_war_time(conquest_start)
                            minutes_since = get_minutes_since_war_started(conquest_start)
                            print(f"[{datetime.now()}] {map_name}: iconType {item['iconType']} ({cat}) at ({item['x']:.3f},{item['y']:.3f}) changed {prev_team} → {team}")
                            log_event(war_id, war_number, war_time, minutes_since, map_name, item["iconType"], cat, team)

                previous_state[map_name] = current

            except Exception as e:
                print(f"❌ Error on {map_name}: {e}")

        time.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    run_tracker()
