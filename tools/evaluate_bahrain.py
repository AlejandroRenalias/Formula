"""Run the approved Bahrain-only dry conditional prediction slice offline."""
import argparse
from collections import Counter
import csv
import hashlib
import json
import os
from pathlib import Path
import platform
from importlib.metadata import version
import statistics
import subprocess
import time
import shutil

from src.evaluation.diagnostics import enrich_rows, metrics, metric_tables, comparison_tables
from src.evaluation.offline import network_blocked
from src.evaluation.prediction import actual_plan, predict, score_targets
from src.evaluation.snapshot import ExcludedSnapshot, build_snapshot, load_dataset

DEFAULT_DATA = Path("data/cache/evaluation/bahrain_2021/session.json")
DEFAULT_OUTPUT = Path("docs/evaluation/bahrain_2021_pit_split")


def evaluate_one(data, driver, lap):
    snapshot = build_snapshot(data, driver, lap)
    treatment = actual_plan(data, driver, snapshot.audit["cutoff_session_s"], lap)
    predictions = predict(snapshot, treatment)
    rows, exclusions = score_targets(data, driver, snapshot, predictions)
    record = {"driver_number": driver, "lap": lap,
              "state": snapshot.state.model_dump(mode="json"),
              "config": snapshot.config.model_dump(mode="json"), "audit": snapshot.audit,
              "actual_subject_plan": [s.model_dump(mode="json") for s in treatment.dry_stops]}
    return rows, exclusions, record


def plots(rows, output):
    os.environ.setdefault("MPLCONFIGDIR", str(Path("data/cache/matplotlib").resolve()))
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(2, 2, figsize=(11, 8), layout="constrained")
    for axis, horizon in zip(axes.flat, ("1", "5", "10", "finish")):
        group = [r for r in rows if r["horizon"] == horizon]
        actual = [r["actual_s"] for r in group]
        predicted = [r["median_s"] for r in group]
        axis.scatter(actual, predicted, s=12, alpha=.5, color="#2563a6")
        bounds = [min(actual + predicted), max(actual + predicted)]
        axis.plot(bounds, bounds, "--", color="#555555", linewidth=1)
        axis.set(title=f"{horizon} {'laps ahead' if horizon != 'finish' else 'horizon'} (n={len(group)})",
                 xlabel="Actual elapsed time (s)", ylabel="Predicted median (s)")
        axis.grid(alpha=.2)
    fig.suptitle("Bahrain 2021 — conditional actual subject plan")
    fig.savefig(output / "predicted_vs_actual.png", dpi=160)
    plt.close(fig)
    fig, axis = plt.subplots(figsize=(10, 5), layout="constrained")
    for horizon, color in zip(("1", "5", "10", "finish"), ("#2563a6", "#008878", "#bd6700", "#8d407e")):
        group = [r for r in rows if r["horizon"] == horizon]
        axis.scatter([r["horizon_laps"] for r in group], [r["error_s"] for r in group],
                     s=12, alpha=.35, label=horizon, color=color)
    axis.axhline(0, color="#555555", linestyle="--", linewidth=1)
    axis.set(xlabel="Actual horizon length (laps)", ylabel="Median prediction − actual (s)",
             title="Bahrain 2021 — signed error vs horizon")
    axis.legend(title="Requested horizon")
    axis.grid(alpha=.2)
    fig.savefig(output / "error_vs_horizon.png", dpi=160)
    plt.close(fig)


def explanation(row, record):
    audit, config = record["audit"], record["config"]
    stop_count = sum(s["lap"] < row["target_lap"] for s in record["actual_subject_plan"])
    method = audit.get("base_pace_method", "minimum")
    return (f"Pace anchor: {method}, clean lap(s) {audit.get('base_pace_anchor_laps', [audit['base_pace_anchor_lap']])}; fresh base "
            f"{config['base_pace_s']:.3f}s, cutoff tyre age {audit['subject_tyre_age']}; "
            f"{stop_count} future stop(s) in this horizon. "
            + ("Prediction is too fast. Long-horizon fixed wear/fuel and the clean-lap "
               "anchor can sustain more pace than the driver actually delivered. "
               if row["error_s"] < 0 else
               "Prediction is too slow. Fixed compound wear/cliff and the cutoff pace anchor "
               "can accumulate excessive cost over the horizon. ")
            + "This is a model-based diagnostic, not proof of a single cause.")


def write_report(rows, exclusions, snapshots, manifest, output):
    summary = metrics(rows)
    anchor_method = snapshots[0]["audit"].get("base_pace_method", "minimum")
    added_noise = "pace_uncertainty" in snapshots[0]["audit"]
    uncertainty_text = ("Normal subject-only persistent pace offset (SD=s/sqrt(n)) and independent "
                        "per-lap noise (SD=s), sized from the same driver's last six available clean "
                        "laps after nominal wear/fuel corrections; antithetic paired draws, separate "
                        "seed streams. One clean observation gives zero scatter. No error-based tuning. "
                        if added_noise else "No base-pace uncertainty or per-lap noise. ")
    reproduction = (r".\.venv\Scripts\python.exe -m tools.evaluate_bahrain --output " + output.as_posix()
                    + (" --compare-to " + manifest["compare_to"] if manifest.get("compare_to") else ""))
    by_key = {(r["state"]["subject_driver"]["driver"], r["lap"]): r for r in snapshots}
    worst = sorted(rows, key=lambda r: abs(r["error_s"]), reverse=True)[:5]
    counts = Counter((e.get("scope", "target"), e["reason"]) for e in exclusions)
    lines = ["# Bahrain 2021: dry conditional prediction", "",
        "Bahrain development race only. No race-wide fitting, agreement/disagreement analysis or UI changes.", "",
        f"Prediction source: {manifest.get('prediction_origin', 'fresh offline simulation')}. "
        f"Previous comparison: {manifest.get('compare_to') or 'none'}.", "",
        "## Dataset and runtime", "",
        f"- Top ten: {', '.join(manifest['subjects'])}.",
        f"- Scheduled distance: 56 laps; cutoffs 5–51 inclusive; stride {manifest['lap_stride']}.",
        f"- Attempted snapshots: {manifest['attempted_snapshots']}; evaluated: {len(snapshots)}; "
        f"excluded: {manifest['attempted_snapshots'] - len(snapshots)}.",
        f"- Scored predictions: {len(rows)}; excluded horizon targets: "
        f"{sum(e.get('scope') == 'target' for e in exclusions)}.",
        f"- Benchmark: {len(manifest['benchmark_seconds'])} snapshots, "
        f"mean {statistics.mean(manifest['benchmark_seconds']):.3f}s/snapshot; estimated full "
        f"run {manifest['estimated_full_runtime_s'] / 60:.2f} minutes.",
        f"- Actual evaluation loop: {manifest['evaluation_runtime_s']:.2f}s. "
        + ("Every lap retained because estimated runtime was below 30 minutes."
           if manifest['lap_stride'] == 1 else "Every second lap used because estimated runtime exceeded 30 minutes."),
        "- Entire evaluation ran with socket connections blocked; acquisition was a separate operation.",
        "", "### Exclusions", "", "| Scope | Reason | Count |", "| --- | --- | ---: |"]
    lines += [f"| {scope} | {reason} | {n} |" for (scope, reason), n in sorted(counts.items())]
    lines += ["", "## Accuracy", "",
        "Bias is predicted median minus actual elapsed time: negative means too fast. Coverage "
        "uses inclusive absolute p10–p90 endpoints; nominal target is 80%. Width is the mean "
        "p90 minus p10. Existing uncertainty is reported without post-result widening.", "",
        "| Horizon | N | MAE (s) | Mean bias (s) | Median error (s) | Coverage | Mean width (s) | Below p10 | Above p90 | Interval score (s) |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |"]
    lines += [f"| {h} | {v['n']} | {v['mae_s']:.3f} | {v['bias_s']:+.3f} | "
              f"{v['median_error_s']:+.3f} | {100*v['coverage']:.1f}% | {v['mean_width_s']:.3f} | {v['lower_misses']} | "
              f"{v['upper_misses']} | {v['interval_score_s']:.3f} |" for h, v in summary.items()]
    lines += ["", *metric_tables(summary)]
    if manifest.get("diagnostics_source"):
        lines += ["", "### Baseline interpretation", "",
            "The one-lap mean is misleading: its median error is −0.428s. The 409 "
            "no-stop predictions average −0.432s, while 20 pit-entry horizons average "
            "+17.354s. Charging all stop loss on the in-lap creates a separate large "
            "positive-error group; all 324 one-lap actuals above p90 are in the no-stop group.", "",
            "The roughly −0.4s/lap hypothesis holds approximately for short no-stop "
            "horizons: mean errors/lap are −0.432, −0.493 and −0.475 at 1/5/10 laps. "
            "It is not constant across every horizon: finish averages −0.567s/lap "
            "overall and −0.826s/lap without a future stop. This supports investigating "
            "the optimistic minimum pace anchor, but does not rule out wear/cliff, "
            "fuel, or differing finish-cohort effects. The controlled anchor change "
            "is the next test; these diagnostics alone do not establish causality."]
    if manifest.get("compare_to"):
        previous_rows = read_predictions(Path(manifest["compare_to"]) / "predictions.csv")
        previous = metrics(previous_rows)
        keys = lambda records: {(r["driver_number"], r["lap"], r["target_lap"], r["horizon"]) for r in records}
        if keys(previous_rows) != keys(rows):
            raise ValueError("Comparison predictions have different cohorts")
        lines += ["", *comparison_tables(summary, previous)]
    lines += ["", "Coverage remains below 80%; the model's "
              "uncertainty does not cover all real pace and pit timing variation. These are correlated "
              "snapshots from one development race, not an independent calibration result.", "",
              "![Predicted vs actual](predicted_vs_actual.png)", "",
              "![Signed error vs horizon](error_vs_horizon.png)", "",
              "## Five worst predictions", "",
              "Ranked across all scored horizons by absolute median error; several may "
              "come from the same driver or adjacent cutoffs.", "",
              "| Driver | Cutoff | Target / horizon | Actual (s) | Median (s) | p10–p90 (s) | Error (s) |",
              "| --- | ---: | --- | ---: | ---: | --- | ---: |"]
    for row in worst:
        lines.append(f"| {row['driver']} | {row['lap']} | {row['target_lap']} / {row['horizon']} | "
                     f"{row['actual_s']:.3f} | {row['median_s']:.3f} | "
                     f"{row['p10_s']:.3f}–{row['p90_s']:.3f} | {row['error_s']:+.3f} |")
    lines += [""]
    for i, row in enumerate(worst, 1):
        lines += [f"{i}. **{row['driver']}, cutoff {row['lap']}, {row['horizon']}:** "
                  + explanation(row, by_key[(row["driver"], row["lap"])]), ""]
    lines += ["## Protocol and limitations", "",
        "- Exact cutoff coordinates and actual elapsed labels use FastF1 corrected crossing "
        "Time. Pace/position/pit state uses only earlier raw TimingData packets; tyres use "
        "earlier TimingAppData updates. A LastLapTime received after the crossing is excluded "
        "until its packet arrives, even if this leaves the newest known pace one lap old.",
        "- Gap exception: only rival same-lap crossing Time may follow cutoff, tagged "
        "live_timing_proxy_same_lap_crossing. Its other fields are never read. Missing "
        "crossings use a disclosed stale earlier common-lap gap. This is a retrospective "
        "crossing proxy, not a captured live gap feed.",
        "- Session datetimes are epoch-encoded session-relative clocks, not asserted UTC wall times. "
        "Each snapshot saves exact cutoff seconds, source timestamps and parameter configuration.",
        "- Frozen compound degradation scale 1, fuel 0.05s/lap, pit losses 21.5/12.5/9.5s, "
        f"cliff/traffic/SC defaults. Fresh base pace uses the {anchor_method} of the last six available "
        "clean laps, removing the central observation(s)' nominal compound/wear cost and advancing "
        "fuel effect to cutoff (minimum baseline uses its single fastest observation). "
        "No regression-based degradation or race-wide fitting is used.",
        "- Dry persistence, no forecast; seed 18, 32 shared samples, uniform pit offsets "
        "+/-1.5s and wear multipliers +/-15%. " + uncertainty_text +
        "Random traffic, damage, strategic lift-off, warm-up and future neutralizations remain unmodeled.",
        "- Actual subject stop schedule/compounds are supplied only AFTER constructing "
        "the snapshot, as conditional treatment. Autonomous subject stops are suppressed. "
        "Corrected full-session tyre labels are used only for this actual-plan treatment, "
        "never cutoff features. Rivals retain engine tyre-life stop assumptions, not observed future strategies.",
        "- Pit-in lap K maps to boundary K-1. A frozen 50/50 allocation charges half "
        "the sampled entry-time total on K and the remainder on K+1, for subject and "
        "modeled rival stops. A final-lap stop charges the whole total before finish. "
        "The share is an unestimated neutral default, not fitted to evaluation data. "
        "Fresh tyre timing remains the existing entry-lap approximation; used replacement "
        "tyres are not modeled. Subject snapshots inside the pit are excluded.",
        "- Fixed status persistence follows the existing engine. No actual future status "
        "is injected. Final classification selects subjects outside the engine (survivor bias). "
        "No held-out or wet races were acquired or evaluated by this slice.", "",
        "## Reproduction", "", "From the repository root, after acquiring the authorized race once:", "",
        "```powershell", reproduction, "```", "",
        "The command loads only the hash-verified local normalized cache, blocks network "
        "connections and regenerates this report. A missing/corrupt cache fails rather than "
        "downloading. Acquisition: `python -m tools.acquire_bahrain_evaluation` (Bahrain only).", "",
        "- [Metrics](metrics.json), [predictions](predictions.csv), [exclusions](exclusions.json).",
        "- [Manifest](manifest.json) records source/code hashes, versions, benchmark and defaults.",
        f"- Full state/config/plan audit: local ignored `{manifest['snapshot_path']}`."]
    (output / "REPORT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (output / "metrics.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    (output / "exclusions.json").write_text(json.dumps(exclusions, indent=2) + "\n", encoding="utf-8")


def read_predictions(path):
    with Path(path).open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    for row in rows:
        for k, value in row.items():
            if k in ("driver", "driver_number", "horizon"):
                continue
            if k in ("covered", "contains_subject_pit_stop"):
                row[k] = value == "True"
            elif k in ("lap", "target_lap", "horizon_laps", "subject_pit_stop_count"):
                row[k] = int(value)
            else:
                row[k] = float(value)
    return rows


def save_predictions(rows, output):
    with (output / "predictions.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def diagnostics_only(dataset, output, source):
    """Reuse exact baseline predictions; no calls to snapshot/predict."""
    with network_blocked():
        data, digest = load_dataset(dataset)
        source = Path(source)
        output = Path(output)
        manifest = json.loads((source / "manifest.json").read_text())
        if manifest["dataset_sha256"] != digest:
            raise ValueError("Baseline dataset changed")
        output.mkdir(parents=True, exist_ok=True)
        rows = enrich_rows(data, read_predictions(source / "predictions.csv"))
        snapshot_path = Path(dataset).with_name("snapshots.jsonl")
        snapshots = [json.loads(s) for s in snapshot_path.read_text().splitlines()]
        if len(snapshots) != manifest["evaluated_snapshots"]:
            raise ValueError("Baseline snapshot audit missing or changed")
        manifest.update(prediction_origin="unchanged saved minimum-anchor baseline predictions",
                        compare_to=None, snapshot_path=str(snapshot_path),
                        diagnostics_source=str(source),
                        diagnostics_source_predictions_sha256=hashlib.sha256((source / "predictions.csv").read_bytes()).hexdigest())
        manifest["diagnostics_source_sha256"] = {str(p): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in (Path("src/evaluation/diagnostics.py"), Path("tools/evaluate_bahrain.py"))}
        save_predictions(rows, output)
        for file in ("predicted_vs_actual.png", "error_vs_horizon.png"):
            shutil.copyfile(source / file, output / file)
        exclusions = json.loads((source / "exclusions.json").read_text())
        (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        write_report(rows, exclusions, snapshots, manifest, output)
        print(json.dumps({h: {k: v for k, v in values.items() if k != 'by_subject_pit_stop'}
                          for h, values in metrics(rows).items()}, indent=2))


def run(dataset=DEFAULT_DATA, output=DEFAULT_OUTPUT, compare_to=None):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    with network_blocked():
        data, digest = load_dataset(dataset)
        cohort = sorted((r for r in data["results"] if r["Position"] is not None
                         and 1 <= r["Position"] <= 10), key=lambda r: r["Position"])
        if len(cohort) != 10:
            raise ValueError("Expected ten classified evaluation subjects")
        benchmark = []
        for driver, lap in (("44", 8), ("4", 18), ("22", 40)):
            start = time.perf_counter()
            evaluate_one(data, driver, lap)
            benchmark.append(time.perf_counter() - start)
        planned = 10 * (data["scheduled_laps"] - 9)
        estimate = statistics.mean(benchmark) * planned
        stride = 2 if estimate > 1800 else 1
        print(json.dumps({"benchmark_seconds": benchmark, "estimated_full_runtime_s": estimate,
                          "lap_stride": stride}), flush=True)
        rows, exclusions, snapshots = [], [], []
        started = time.perf_counter()
        for subject in cohort:
            driver = subject["DriverNumber"]
            for lap in range(5, data["scheduled_laps"] - 4, stride):
                try:
                    scores, excluded, record = evaluate_one(data, driver, lap)
                except ExcludedSnapshot as exc:
                    exclusions.append({"scope": "snapshot", "driver": driver,
                                       "lap": lap, "reason": str(exc)})
                    continue
                rows.extend(scores)
                exclusions.extend({"scope": "target", **e} for e in excluded)
                snapshots.append(record)
            print(f"Completed {subject['Abbreviation']}: {len(snapshots)} snapshots so far", flush=True)
        elapsed = time.perf_counter() - started
        if not rows:
            raise ValueError("No valid predictions")
        rows = enrich_rows(data, rows)
        snapshot_path = Path(dataset).with_name(f"snapshots_{output.name}.jsonl")
        snapshot_path.write_text("".join(json.dumps(s, allow_nan=False) + "\n" for s in snapshots), encoding="utf-8")
        sources = [Path("src/calculators/projection.py"), Path("src/calculators/tyre_model.py"),
                   Path("src/calculators/pit_loss_model.py"), Path("src/calculators/pace_model.py"),
                   Path("src/calculators/weather_model.py"), Path("src/calculators/traffic_model.py"),
                   Path("src/core/models.py"), Path("src/core/provenance.py"),
                   *sorted(Path("src/evaluation").glob("*.py")),
                   Path("tools/evaluate_bahrain.py"), Path("tools/acquire_bahrain_evaluation.py")]
        manifest = {"dataset_sha256": digest, "fastf1_version": data["fastf1_version"],
            "python_version": platform.python_version(),
            "library_versions": {p: version(p) for p in ("fastf1", "numpy", "pandas", "pydantic", "matplotlib")},
            "git_base_sha": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
            "source_sha256": {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},
            "benchmark_seconds": benchmark, "estimated_full_runtime_s": estimate,
            "evaluation_runtime_s": elapsed, "lap_stride": stride,
            "subjects": [r["Abbreviation"] for r in cohort],
            "attempted_snapshots": 10 * len(range(5, data["scheduled_laps"] - 4, stride)),
            "evaluated_snapshots": len(snapshots), "scored_predictions": len(rows),
            "base_pace_method": snapshots[0]["audit"].get("base_pace_method", "minimum"),
            "snapshot_path": str(snapshot_path), "compare_to": str(compare_to) if compare_to else None,
            "network_blocked": True, "forecast_mode": "no_forecast_dry_persistence",
            "variable_config_from_pre_cutoff_clean_laps": ["base_pace_s", "base_pace_sigma_s", "lap_noise_sigma_s"],
            "fixed_config_except_base_pace": {k: v for k, v in snapshots[0]["config"].items()
                                             if k not in ("base_pace_s", "base_pace_sigma_s", "lap_noise_sigma_s")}}
        save_predictions(rows, output)
        (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        plots(rows, output)
        write_report(rows, exclusions, snapshots, manifest, output)
        print(json.dumps({h: {k: v for k, v in values.items() if k != 'by_subject_pit_stop'}
                          for h, values in metrics(rows).items()}, indent=2), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATA)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--diagnostics-from", type=Path, help="Reuse saved predictions without model changes")
    parser.add_argument("--compare-to", type=Path, help="Previous enriched report for matched comparisons")
    args = parser.parse_args()
    if args.diagnostics_from:
        diagnostics_only(args.dataset, args.output, args.diagnostics_from)
    else:
        run(args.dataset, args.output, args.compare_to)


if __name__ == "__main__":
    main()
