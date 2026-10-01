"""One-off FastF1 exporter; runtime uses the committed JSON, never this script.

Run: python scripts/build_track.py --offline (after populating FastF1 cache).
Pit markers are explicit approximate configuration, not measured telemetry.
"""
import argparse
import json
from pathlib import Path

import fastf1
import numpy as np

ROOT = Path(__file__).resolve().parents[1]


def build(args):
    fastf1.Cache.enable_cache(str(ROOT / "data/cache"))
    if args.offline:
        fastf1.Cache.offline_mode(True)
    session = fastf1.get_session(args.year, "Silverstone", args.session)
    session.load(weather=False, messages=False)
    lap = session.laps.pick_accurate().pick_wo_box().pick_fastest()
    if lap is None:
        raise ValueError("No accurate non-pit reference lap available")
    telemetry = lap.get_telemetry().sort_values("Time").drop_duplicates("Time")
    time = telemetry.Time.dt.total_seconds().to_numpy()
    distance = telemetry.Distance.to_numpy()
    duration = lap.LapTime.total_seconds()
    # Interpolate exact timing-line edges and remove small integration offsets.
    edges = np.unique(np.concatenate(([0.0], time[(time > 0) & (time < duration)], [duration])))
    dist = np.interp(edges, time, distance)
    dist -= dist[0]
    if not np.all(np.diff(dist) > 0):
        raise ValueError("Reference telemetry distance must increase strictly")
    length = float(dist[-1])
    x = np.interp(edges, time, telemetry.X)
    y = np.interp(edges, time, telemetry.Y)
    scale = max(float(np.ptp(x)), float(np.ptp(y)))
    x = (x - (x.min() + x.max()) / 2) / scale
    y = (y - (y.min() + y.max()) / 2) / scale
    # Uniform-distance resampling gives a deterministic few-hundred-point line.
    stations = np.linspace(0, length, args.points)
    px, py = np.interp(stations, dist, x), np.interp(stations, dist, y)
    px[-1], py[-1] = px[0], py[0]  # close timing-line positional measurement seam
    sector_times = [0, lap.Sector1Time.total_seconds(),
                    (lap.Sector1Time + lap.Sector2Time).total_seconds(), duration]
    asset = {
        "schema_version": 1, "id": "silverstone", "name": "Silverstone",
        "source": {"provider": "FastF1", "version": fastf1.__version__, "year": args.year,
                   "event": str(session.event.EventName), "session": args.session,
                   "date": str(session.date), "driver": str(lap.Driver),
                   "lap_number": int(lap.LapNumber), "selection": "fastest accurate non-pit lap",
                   "role": "static reference geometry and pace profile, not cutoff race observations"},
        "lap_length_m": length, "reference_lap_time_s": duration,
        "coordinates": {"normalization": "centered, longest extent = 1, aspect preserved",
                        "y_axis": "FastF1 positive Y; renderer may invert", "closed": True},
        "polyline": [{"distance_m": float(d), "x": float(a), "y": float(b)}
                     for d, a, b in zip(stations, px, py)],
        "time_profile": [{"distance_m": float(d), "time_s": float(t)} for d, t in zip(dist, edges)],
        "start_finish": {"distance_m": 0.0, "kind": "measured"},
        "sectors": [{"sector": i + 1, "start_distance_m": float(np.interp(sector_times[i], edges, dist)),
                     "end_distance_m": float(np.interp(sector_times[i+1], edges, dist)), "kind": "measured"}
                    for i in range(3)],
        "pit_entry": {"distance_m": length * args.pit_entry_fraction, "kind": "config",
                      "note": "Approximate marker; not calibrated to pit-lane telemetry"},
        "pit_exit": {"distance_m": length * args.pit_exit_fraction, "kind": "config",
                     "note": "Approximate marker; not calibrated to pit-lane telemetry"},
    }
    destination = ROOT / "data/tracks/silverstone.json"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(asset, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(f"{destination}: {len(stations)} points, {length:.1f} m, {duration:.3f} s, {lap.Driver}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--year", type=int, default=2024)
    parser.add_argument("--session", default="Q")
    parser.add_argument("--points", type=int, default=301)
    parser.add_argument("--pit-entry-fraction", type=float, default=.96)
    parser.add_argument("--pit-exit-fraction", type=float, default=.04)
    parser.add_argument("--offline", action="store_true")
    args = parser.parse_args()
    if args.points < 3 or not all(0 <= f < 1 for f in (args.pit_entry_fraction, args.pit_exit_fraction)):
        parser.error("Need at least three points and marker fractions in [0, 1)")
    build(args)
