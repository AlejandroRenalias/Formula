"""Outcome-only diagnostics; never used to build state or tune parameters."""
import statistics


def enrich_rows(data, rows):
    labels = {(r["Driver"], int(r["NumberOfLaps"])): r["Time"] for r in data["laps"]}
    result = []
    for row in rows:
        item = dict(row)
        cutoff = labels[(item["driver_number"], item["lap"])]
        target = labels[(item["driver_number"], item["target_lap"])]
        stops = sum(r["Driver"] == item["driver_number"]
                    and r.get("PitInTime") is not None and cutoff < r["PitInTime"] <= target
                    for r in data["laps"])
        item["subject_pit_stop_count"] = stops
        item["contains_subject_pit_stop"] = stops > 0
        item["error_per_lap_s"] = item["error_s"] / item["horizon_laps"]
        result.append(item)
    return result


def _summary(group):
    if not group:
        return {"n": 0}
    interval_scores = [r["width_s"] + 10 * max(0, r["p10_s"] - r["actual_s"])
                       + 10 * max(0, r["actual_s"] - r["p90_s"]) for r in group]
    return {"n": len(group),
        "mae_s": statistics.mean(abs(r["error_s"]) for r in group),
        "bias_s": statistics.mean(r["error_s"] for r in group),
        "median_error_s": statistics.median(r["error_s"] for r in group),
        "mean_error_per_lap_s": statistics.mean(r["error_s"] / r["horizon_laps"] for r in group),
        "median_error_per_lap_s": statistics.median(r["error_s"] / r["horizon_laps"] for r in group),
        "mae_per_lap_s": statistics.mean(abs(r["error_s"]) / r["horizon_laps"] for r in group),
        "coverage": sum(r["covered"] for r in group) / len(group),
        "mean_width_s": statistics.mean(r["width_s"] for r in group),
        "lower_misses": sum(r["actual_s"] < r["p10_s"] for r in group),
        "upper_misses": sum(r["actual_s"] > r["p90_s"] for r in group),
        "interval_score_s": statistics.mean(interval_scores)}


def metrics(rows):
    groups = {}
    for horizon in ("1", "5", "10", "finish"):
        group = [r for r in rows if r["horizon"] == horizon]
        if group:
            groups[horizon] = {**_summary(group), "by_subject_pit_stop": {
                "without_stop": _summary([r for r in group if not r["contains_subject_pit_stop"]]),
                "with_stop": _summary([r for r in group if r["contains_subject_pit_stop"]])}}
    return groups


def metric_tables(summary):
    lines = ["## Median error, pit-stop split and error per lap", "",
        "Signed error is predicted median minus actual. Pit-stop labels use actual subject "
        "pit-entry timestamps in (cutoff, target], solely as outcome diagnostics. All metrics "
        "are split by this label. Error/lap is computed for each prediction, then averaged "
        "or median-aggregated; finish horizons have different lengths.", "",
        "| Horizon | Stops in horizon | N | MAE s | Mean bias s | Median error s | Mean error/lap s | Median error/lap s | MAE/lap s | Coverage | Mean width s | Below p10 | Above p90 | Interval score s |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |"]
    for horizon, values in summary.items():
        for label, v in (("all", values), *values["by_subject_pit_stop"].items()):
            if v["n"] == 0:
                lines.append(f"| {horizon} | {label} | 0 | — | — | — | — | — | — | — | — | — | — | — |")
                continue
            lines.append(f"| {horizon} | {label} | {v['n']} | {v['mae_s']:.3f} | "
                f"{v['bias_s']:+.3f} | {v['median_error_s']:+.3f} | "
                f"{v['mean_error_per_lap_s']:+.3f} | {v['median_error_per_lap_s']:+.3f} | "
                f"{v['mae_per_lap_s']:.3f} | {100*v['coverage']:.1f}% | "
                f"{v['mean_width_s']:.3f} | {v['lower_misses']} | {v['upper_misses']} | "
                f"{v['interval_score_s']:.3f} |")
    return lines


def comparison_tables(current, previous):
    lines = ["## Matched comparison with previous run", "",
        "Same driver/cutoff/target cohort. Entries are previous → current; zero-sample "
        "pit-stop strata are unavailable. No outcome-derived tuning is applied.", "",
        "| Horizon | Stops | N | Mean bias s | Median error s | MAE s | Coverage | Mean width s |",
        "| --- | --- | ---: | --- | --- | --- | --- | --- |"]
    for horizon, values in current.items():
        for label in ("all", "without_stop", "with_stop"):
            a = previous[horizon] if label == "all" else previous[horizon]["by_subject_pit_stop"][label]
            b = values if label == "all" else values["by_subject_pit_stop"][label]
            if a["n"] != b["n"]:
                raise ValueError("Comparison cohort changed")
            if not b["n"]:
                continue
            lines.append(f"| {horizon} | {label} | {b['n']} | {a['bias_s']:+.3f} → {b['bias_s']:+.3f} | "
                f"{a['median_error_s']:+.3f} → {b['median_error_s']:+.3f} | "
                f"{a['mae_s']:.3f} → {b['mae_s']:.3f} | {100*a['coverage']:.1f}% → {100*b['coverage']:.1f}% | "
                f"{a['mean_width_s']:.3f} → {b['mean_width_s']:.3f} |")
    return lines
