"""Read-only cutoff tyre diagnostics, separate from engine inputs and fitting."""
from collections import defaultdict
from src.evaluation.diagnostics import _summary


def age_bucket(age):
    if age < 0:
        raise ValueError("Negative cutoff tyre age")
    return "0-9" if age < 10 else "10-19" if age < 20 else "20-29" if age < 30 else "30+"


def attach_cutoff_features(rows, snapshots, race):
    index = {(r["driver_number"], r["lap"]): r for r in snapshots}
    result = []
    for row in rows:
        snapshot = index[(row["driver_number"], row["lap"])]
        result.append({**row, "race_key": race,
                       "cutoff_tyre_age_laps": snapshot["audit"]["subject_tyre_age"],
                       "cutoff_compound": snapshot["state"]["subject_driver"]["current_compound"],
                       "cutoff_track_status": snapshot["state"]["track_status"]})
    return result


def no_stop_breakdowns(rows):
    groups = defaultdict(list)
    for row in rows:
        if row["contains_subject_pit_stop"]:
            continue
        age = age_bucket(row["cutoff_tyre_age_laps"])
        compound = row["cutoff_compound"]
        for dimension, value in (("age", age), ("compound", compound),
                                 ("compound_and_age", f"{compound}/{age}"),
                                 ("track_status", row["cutoff_track_status"])):
            groups[(row["horizon"], dimension, value)].append(row)
    return [{"horizon": h, "dimension": d, "group": g, **_summary(group)}
            for (h, d, g), group in sorted(groups.items())]


def breakdown_table(records):
    lines = ["| Horizon | Dimension | Cutoff group | N | Mean error/lap s | Median error/lap s | MAE/lap s | Coverage |",
             "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |"]
    for r in records:
        lines.append(f"| {r['horizon']} | {r['dimension']} | {r['group']} | {r['n']} | "
                     f"{r['mean_error_per_lap_s']:+.3f} | {r['median_error_per_lap_s']:+.3f} | "
                     f"{r['mae_per_lap_s']:.3f} | {100*r['coverage']:.1f}% |")
    return lines
