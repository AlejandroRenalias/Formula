"""Acquire only Bahrain 2021 into the local FastF1 and normalized caches."""
import hashlib
import json
from pathlib import Path
import argparse

import fastf1
import pandas as pd
from fastf1 import _api


def records(frame):
    frame = pd.DataFrame(frame).copy()
    for column in frame:
        if pd.api.types.is_timedelta64_dtype(frame[column]):
            frame[column] = frame[column].dt.total_seconds()
    return json.loads(frame.to_json(orient="records"))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--offline", action="store_true", help="Re-export only already cached FastF1 data")
    args = parser.parse_args()
    root = Path("data/cache/evaluation/bahrain_2021")
    root.mkdir(parents=True, exist_ok=True)
    fastf1.Cache.enable_cache("data/cache")
    fastf1.Cache.offline_mode(args.offline)
    session = fastf1.get_session(2021, "Bahrain", "R")
    session.load(telemetry=False, weather=True, laps=True, messages=False)
    app = _api.timing_app_data(session.api_path)
    # Preserve packet timestamps BEFORE FastF1's full-session lap corrections.
    response = _api.fetch_page(session.api_path, "timing_data")
    events = []
    for timestamp, packet in response:
        for driver, update in packet.get("Lines", {}).items():
            fields = {k: update[k] for k in
                      ("NumberOfLaps", "Position", "InPit", "Retired", "Stopped", "LastLapTime")
                      if k in update}
            if fields:
                events.append({"Time": pd.Timedelta(timestamp).total_seconds(),
                               "Driver": driver, **fields})
    # Corrected crossings are a coordinate/label channel, never pace/tyre features.
    lap_timing, _ = _api.timing_data(session.api_path)
    payload = {
        "schema_version": 1, "year": 2021, "race": "Bahrain", "scheduled_laps": 56,
        "session_start_s": session.session_start_time.total_seconds(),
        "fastf1_version": fastf1.__version__, "api_path": session.api_path,
        "laps": records(lap_timing), "events": events,
        "tyres": records(app), "weather": records(session.weather_data),
        "track_status": records(session.track_status),
        "actual_tyres": records(session.laps[["DriverNumber", "LapNumber", "Compound", "TyreLife", "Stint"]]),
        "drivers": records(session.results[["DriverNumber", "Abbreviation", "TeamName"]]),
        "results": records(session.results[["DriverNumber", "Abbreviation", "Position", "Status", "Laps"]]),
    }
    blob = json.dumps(payload, indent=2, allow_nan=False).encode()
    (root / "session.json").write_bytes(blob)
    digest = hashlib.sha256(blob).hexdigest()
    (root / "session.sha256").write_text(digest + "\n", encoding="utf-8")
    print(json.dumps({"path": str(root / "session.json"), "sha256": digest,
                      "rows": {k: len(payload[k]) for k in ("laps", "events", "tyres", "weather", "track_status")}}))


if __name__ == "__main__":
    main()
