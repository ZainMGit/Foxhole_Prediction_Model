import os
import csv
import requests
from datetime import datetime, timezone
import time

# === Config ===
BASE_URL = "https://war-service-live.foxholeservices.com/api"
DATA_DIR = "./war_data"
INTERVAL = 900  # 15 minutes

def get_current_war_state():
    return requests.get(f"{BASE_URL}/worldconquest/war").json()

def get_map_list():
    return requests.get(f"{BASE_URL}/worldconquest/maps").json()

def get_war_report(map_name):
    response = requests.get(f"{BASE_URL}/worldconquest/warReport/{map_name}")
    return response.json() if response.status_code == 200 else None

def get_csv_paths(war_number):
    per_map_csv = os.path.join(DATA_DIR, f"war_{war_number}.csv")
    summary_csv = os.path.join(DATA_DIR, f"war_{war_number}_summary.csv")
    return per_map_csv, summary_csv

def is_resistance_phase(war_state):
    return war_state.get("resistanceStartTime") is not None and war_state.get("conquestEndTime") is not None

def format_war_time(start_time):
    now = datetime.now(timezone.utc)
    start_dt = datetime.fromtimestamp(start_time / 1000, tz=timezone.utc)
    elapsed = now - start_dt
    days = elapsed.days
    hours, remainder = divmod(elapsed.seconds, 3600)
    minutes = remainder // 60
    return f"{days}d {hours}h {minutes}m"

def get_minutes_since_start(start_time):
    now = datetime.now(timezone.utc)
    start_dt = datetime.fromtimestamp(start_time / 1000, tz=timezone.utc)
    elapsed = now - start_dt
    return int(elapsed.total_seconds() // 60)

def fetch_and_log():
    now = datetime.now(timezone.utc).isoformat()
    war_state = get_current_war_state()
    war_number = war_state.get("warNumber")

    if war_number is None:
        print("❌ ERROR: Could not fetch war number.")
        return

    if is_resistance_phase(war_state):
        print(f"⏸️ War #{war_number} is in resistance phase — skipping log at {now}.")
        return

    conquest_start = war_state.get("conquestStartTime")
    if conquest_start is None:
        print(f"❌ ERROR: No conquest start time found for war #{war_number}.")
        return

    war_time = format_war_time(conquest_start)
    minutes_since_start = get_minutes_since_start(conquest_start)

    per_map_csv, summary_csv = get_csv_paths(war_number)
    os.makedirs(DATA_DIR, exist_ok=True)

    # === Logging per-map stats ===
    per_map_exists = os.path.exists(per_map_csv)
    total_enlistments = 0
    total_colonial_casualties = 0
    total_warden_casualties = 0

    with open(per_map_csv, mode="a", newline="") as f:
        writer = csv.writer(f)
        if not per_map_exists:
            writer.writerow([
                "timestamp", "war_number", "war_time", "minutes_since_war_start", "map_name",
                "day_of_war", "total_enlistments",
                "colonial_casualties", "warden_casualties"
            ])

        maps = get_map_list()
        for map_name in maps:
            report = get_war_report(map_name)
            if isinstance(report, dict):
                writer.writerow([
                    now, war_number, war_time, minutes_since_start, map_name,
                    report.get("dayOfWar"),
                    report.get("totalEnlistments"),
                    report.get("colonialCasualties"),
                    report.get("wardenCasualties")
                ])
                total_enlistments += report.get("totalEnlistments", 0)
                total_colonial_casualties += report.get("colonialCasualties", 0)
                total_warden_casualties += report.get("wardenCasualties", 0)
            else:
                print(f"⚠️ Skipped bad report for map: {map_name}")

    # === Logging overall war summary ===
    summary_exists = os.path.exists(summary_csv)
    with open(summary_csv, mode="a", newline="") as f:
        writer = csv.writer(f)
        if not summary_exists:
            writer.writerow([
                "timestamp", "war_number", "winner", "conquest_start_time",
                "war_time", "minutes_since_war_start",
                "total_maps", "total_enlistments",
                "total_colonial_casualties", "total_warden_casualties"
            ])
        writer.writerow([
            now, war_number, war_state.get("winner"), conquest_start,
            war_time, minutes_since_start,
            len(maps), total_enlistments,
            total_colonial_casualties, total_warden_casualties
        ])

    print(f"✅ Logged war #{war_number} at {now}")

def main():
    while True:
        print("🔁 Fetching and logging war data...")
        try:
            fetch_and_log()
        except Exception as e:
            print("❌ ERROR during logging:", e)
        time.sleep(INTERVAL)

if __name__ == "__main__":
    main()
