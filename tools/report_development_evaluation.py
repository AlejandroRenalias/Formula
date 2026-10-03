"""Read-only pooled diagnostics for the three approved development races."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

from src.evaluation.breakdown import attach_cutoff_features, no_stop_breakdowns, breakdown_table
from src.evaluation.diagnostics import metrics, metric_tables
from src.evaluation.offline import network_blocked
from src.evaluation.snapshot import load_dataset
from tools.evaluate_bahrain import read_predictions, save_predictions

SOURCES = {"bahrain_2021": "bahrain_2021_pit_split",
           "spain_2022": "spain_2022_pit_split", "france_2022": "france_2022_pit_split"}


def actual_neutralization(data, row):
    """Outcome-only status label; never passed to snapshots or predictions."""
    times = {int(r["NumberOfLaps"]): r["Time"] for r in data["laps"] if r["Driver"] == row["driver_number"]}
    cutoff, target = times[row["lap"]], times[row["target_lap"]]
    status = sorted(data["track_status"], key=lambda r:r["Time"])
    previous = [r for r in status if r["Time"] <= cutoff]
    initial = previous[-1]["Status"] if previous else "1"
    return str(initial) in {"4","6","7"} or any(
        cutoff < r["Time"] <= target and str(r["Status"]) in {"4","6","7"} for r in status)


def reference_table(current, previous):
    lines = ["| Horizon | Stop group | N reference/current | Mean bias s | Median error s | MAE s | Mean error/lap s | Coverage |",
             "| --- | --- | ---: | --- | --- | --- | --- | --- |"]
    for h, values in current.items():
        for group in ("all", "without_stop", "with_stop"):
            a = previous[h] if group == "all" else previous[h]["by_subject_pit_stop"][group]
            b = values if group == "all" else values["by_subject_pit_stop"][group]
            if not a["n"] or not b["n"]: continue
            cells = [f"{a[k]:+.3f} / {b[k]:+.3f}" for k in
                     ("bias_s", "median_error_s", "mae_s", "mean_error_per_lap_s")]
            cells.append(f"{100*a['coverage']:.1f}% / {100*b['coverage']:.1f}%")
            lines.append(f"| {h} | {group} | {a['n']}/{b['n']} | " + " | ".join(cells) + " |")
    return lines


def run(output):
    output = Path(output); output.mkdir(parents=True, exist_ok=True)
    all_rows, per_race, manifests, snapshots, inputs, exclusion_counts = [], {}, {}, {}, {}, {}
    with network_blocked():
        for race, folder in SOURCES.items():
            root = Path("docs/evaluation") / folder
            manifest = json.loads((root/"manifest.json").read_text())
            data, digest = load_dataset(Path("data/cache/evaluation")/race/"session.json")
            if digest != manifest["dataset_sha256"]: raise ValueError("Race dataset changed")
            records = [json.loads(s) for s in Path(manifest["snapshot_path"]).read_text().splitlines()]
            rows = attach_cutoff_features(read_predictions(root/"predictions.csv"), records, race)
            rows = [{**row,"horizon_has_actual_neutralization":actual_neutralization(data,row)} for row in rows]
            if len(rows) != manifest["scored_predictions"]: raise ValueError("Prediction count changed")
            for record in records:
                if record["config"]["pit_in_lap_fraction"] != .5: raise ValueError("Mixed pit allocation models")
                if any(t > record["audit"]["cutoff_session_s"] for t in record["audit"]["parameter_source_session_s"].values()):
                    raise ValueError("Future parameter source")
            exclusions = json.loads((root/"exclusions.json").read_text())
            exclusion_counts[race] = Counter((e.get("scope","target"),e["reason"]) for e in exclusions)
            manifests[race], per_race[race], snapshots[race] = manifest, rows, records
            all_rows.extend(rows)
            for file in (root/"predictions.csv",root/"manifest.json",root/"exclusions.json",Path(manifest["snapshot_path"])):
                inputs[str(file)] = hashlib.sha256(file.read_bytes()).hexdigest()
    for name in ("projection.py", "pace_model.py", "tyre_model.py", "pit_loss_model.py", "weather_model.py", "traffic_model.py"):
        path = str(Path("src/calculators")/name)
        hashes = {m["source_sha256"][path] for m in manifests.values()}
        if len(hashes) != 1 or hashlib.sha256(Path(path).read_bytes()).hexdigest() not in hashes:
            raise ValueError("Development models are not identical")
    summaries = {race:metrics(rows) for race,rows in per_race.items()}
    summaries["pooled"] = metrics(all_rows)
    breakdowns = {race:no_stop_breakdowns(rows) for race,rows in per_race.items()}
    breakdowns["pooled"] = no_stop_breakdowns(all_rows)
    green_breakdowns = {race:no_stop_breakdowns([r for r in rows if r["cutoff_track_status"] == "GREEN"])
                        for race,rows in {**per_race,"pooled":all_rows}.items()}
    clear_breakdowns = {race:no_stop_breakdowns([r for r in rows if r["cutoff_track_status"] == "GREEN"
                                                and not r["horizon_has_actual_neutralization"]])
                        for race,rows in {**per_race,"pooled":all_rows}.items()}
    tyre_lines = ["# No-stop cutoff tyre diagnostics: GREEN status only", "",
                  "The engine is unchanged. This supplementary outcome diagnostic removes "
                  "non-GREEN cutoff snapshots to reduce status-persistence confounding. "
                  "It still cannot eliminate future neutralizations, traffic, fuel, driver "
                  "selection or unequal finish horizons. Main-report tyre tables include all statuses."]
    for race,records in green_breakdowns.items():
        tyre_lines += ["",f"## {race}","",*breakdown_table([r for r in records if r["dimension"] != "track_status"])]
    tyre_lines += ["", "# GREEN cutoff and no actual horizon neutralization", "",
        "This second diagnostic also excludes horizons containing actual SC/VSC status (4/6/7). "
        "These future status labels are outcome-side filters only, generated after predictions. "
        "They never enter snapshots, base pace, uncertainty or pit parameters. Temporary yellows "
        "are not excluded; traffic and driver/race/horizon selection remain confounders."]
    for race,records in clear_breakdowns.items():
        tyre_lines += ["",f"## {race}","",*breakdown_table([r for r in records if r["dimension"] != "track_status"])]
    (output/"TYRE_DIAGNOSTICS_GREEN.md").write_text("\n".join(tyre_lines)+"\n",encoding="utf-8")
    lines = ["# Three-race dry development evaluation", "",
        "Bahrain 2021, Spain 2022 and France 2022 only. The committed median anchor, "
        "driver-local pace uncertainty and unestimated 50/50 pit allocation are identical "
        "across races. No fitting, other model changes, held-out/wet runs or UI edits.", "",
        "## Dataset and exclusions", "",
        "| Race | Scheduled laps | Attempted / valid snapshots | Scored predictions | Runtime s | Stride |",
        "| --- | ---: | ---: | ---: | ---: | ---: |"]
    for race,m in manifests.items():
        distance = {"bahrain_2021":56,"spain_2022":66,"france_2022":53}[race]
        lines.append(f"| {race} | {distance} | {m['attempted_snapshots']} / {m['evaluated_snapshots']} | "
                     f"{m['scored_predictions']} | {m['evaluation_runtime_s']:.2f} | {m['lap_stride']} |")
    lines += ["", "Top ten finishers per race; cutoffs from lap 5 through scheduled distance minus 5. "
        "Each race was benchmarked separately; every-lap stride retained where below 30 minutes. "
        "Acquisition used FastF1 3.8.3 once per authorized race; evaluation and this report run "
        "with network connections blocked. Hash-verified normalized and raw caches are local/ignored.", "",
        "| Race | Exclusion scope | Reason | Count |", "| --- | --- | --- | ---: |"]
    for race,counts in exclusion_counts.items():
        lines.extend(f"| {race} | {scope} | {reason} | {n} |" for (scope,reason),n in sorted(counts.items()))
    lines += ["", "| Race | Cutoff status | Valid snapshots |", "| --- | --- | ---: |"]
    for race, records in snapshots.items():
        lines.extend(f"| {race} | {status} | {n} |" for status,n in
                     sorted(Counter(r["state"]["track_status"] for r in records).items()))
    lines += ["", "France acquisition warned about late timing data for SAI around laps 13/14 and a "
        "41 ms recorded session-end discrepancy for VER. The cached original streams/corrected crossing "
        "labels are retained; no retrospective repair is inserted into engine inputs.", "",
        "## Per-race and pooled metrics", "",
        "Error is predicted median minus actual. Error per lap divides each row's error by its "
        "actual horizon length before aggregation. Coverage is inclusive p10-p90, nominally 80%. "
        "Pit/no-pit uses actual subject entry in (cutoff,target], solely on the outcome side. "
        "All snapshots are correlated; final classification selects the survivor cohort. "
        "Pooled metrics concatenate predictions: races with more valid cutoffs receive more weight, "
        "not equal race weights."]
    for race,summary in summaries.items():
        lines += ["",f"### {race}","",*metric_tables(summary)]
    lines += ["", "## Reference to the previous Bahrain-only run", "",
        "Each cell is previous Bahrain pit-split / current. Spain and France have no previous "
        "same-race run. These comparisons are unmatched population references, not model improvements. "
        "The pooled comparison changes race composition while preserving the model."]
    for race in ("spain_2022","france_2022","pooled"):
        lines += ["",f"### {race} versus Bahrain", "", *reference_table(summaries[race],summaries["bahrain_2021"])]
    lines += ["", "## No-stop tyre diagnostics", "",
        "Groups use causal compound and tyre age at cutoff, not future tyre labels. Age bins are "
        "fixed at 0-9, 10-19, 20-29 and 30+ laps; joint compound/age groups help distinguish "
        "changing compound mix. Track-status groups show the unchanged safety-car persistence "
        "assumption separately. Every group reports sample count and row-normalized error. "
        "[GREEN-only supplementary tables](TYRE_DIAGNOSTICS_GREEN.md) reduce cutoff-status "
        "confounding without changing the model or headline metrics. Sparse bins and different "
        "finish-horizon lengths require caution. These are associations, "
        "not fitted degradation estimates or proof that wear alone causes the residuals."]
    for race,records in breakdowns.items():
        lines += ["",f"### {race}","",*breakdown_table(records)]
    lines += ["", "## Findings and limits", "",
        "The pit allocation improves Bahrain's 1-lap pit mean bias from +17.683 to +6.968 s "
        "and its 5-lap pit MAE from 5.935 to 3.736 s; no-stop metrics are nearly unchanged. "
        "The 50/50 share remains unestimated and does not deliver calibrated pit-entry intervals.", "",
        "Spain finish MAE is 16.702 s and coverage 39.7%, versus Bahrain 8.519 s and 47.6%. "
        "France finish MAE is 130.620 s with zero coverage. Its median finish error is -36.519 s "
        "despite mean bias +2.818 s: 418 actuals exceed p90 and 11 are below p10. The 11 "
        "safety-car cutoff snapshots explain the large positive tail; the five worst are "
        "lap-19 SC snapshots with approximately +2,790 to +2,834 s finish error. The unchanged "
        "engine holds observed SC status and last-lap-based rival paces through the entire "
        "remaining race, so this tail is not a tyre-wear signal.", "",
        "Every scored France finish horizon includes a real later neutralization, given "
        "the last allowed cutoff at lap 48. Therefore there are no France no-stop finish "
        "rows in the no-actual-neutralization subset. Widespread negative finish errors "
        "cannot be attributed to wear alone when the unchanged model lacks those future "
        "neutralizations. No actual future status was injected to correct them.", "",
        "Within GREEN-cutoff, non-neutralized no-stop finish horizons, Bahrain HARD mean "
        "error/lap becomes -0.193/-0.750/-0.875 s at age 0-9/10-19/20-29 (n=71/65/8). "
        "Spain SOFT becomes -0.610/-1.134 s at age 0-9/10-19 (n=50/33). These patterns are "
        "consistent with a remaining age-related modeling error, but Spain MEDIUM is "
        "non-monotonic (-0.959/-0.269/-0.462; n=18/18/8), and France's neutralization-free "
        "5/10-lap age groups are also non-monotonic. Wear is a plausible contributor, "
        "not an established sole cause or a justification for fitting a new degradation "
        "coefficient in this slice. Horizon length, race/driver selection and fuel remain "
        "confounders even in the joint compound/age tables.", "",
        "Pooled coverage at 1/5/10/finish is 62.4/43.0/39.3/29.9%, below 80% at every "
        "horizon. Pooled mean finish bias -3.592 s conceals median -11.874 s and MAE "
        "49.102 s. No further model changes or interval tuning are performed."]
    lines += ["", "## Reproduction and artifacts", "",
        "Use the explicit offline evaluation commands in each linked per-race report. "
        "The current legacy CLI names accept only the three approved development races. "
        "Bahrain pit-split predictions are reused unchanged; new cutoff columns are joined "
        "from its saved causal snapshots without predicting again.", "",
        "```powershell", r".\.venv\Scripts\python.exe -m tools.report_development_evaluation", "```", "",
        "- [Bahrain](../bahrain_2021_pit_split/REPORT.md), [Spain](../spain_2022_pit_split/REPORT.md), "
        "[France](../france_2022_pit_split/REPORT.md): counts, every metric, worst predictions and plots.",
        "- [Metrics](metrics.json), [no-stop breakdowns](no_stop_breakdowns.json), "
        "[pooled predictions](predictions.csv), [manifest](manifest.json).", ""]
    save_predictions(all_rows, output)
    for filename, payload in (("metrics.json",summaries),("no_stop_breakdowns.json",breakdowns),("green_no_stop_breakdowns.json",green_breakdowns),("unneutralized_no_stop_breakdowns.json",clear_breakdowns)):
        (output/filename).write_text(json.dumps(payload,indent=2)+"\n",encoding="utf-8")
    (output/"REPORT.md").write_text("\n".join(lines),encoding="utf-8")
    manifest = {"network_blocked": True, "input_sha256":inputs,
                "race_dataset_sha256":{race:m["dataset_sha256"] for race,m in manifests.items()},
                "same_model_hashes_verified":True,"prediction_count":len(all_rows),
                "report_source_sha256":{str(p):hashlib.sha256(p.read_bytes()).hexdigest()
                     for p in (Path(__file__),Path("src/evaluation/breakdown.py"),Path("src/evaluation/diagnostics.py"))}}
    (output/"manifest.json").write_text(json.dumps(manifest,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({race:{h:{k:v for k,v in m.items() if k!="by_subject_pit_stop"}
                        for h,m in summary.items()} for race,summary in summaries.items()},indent=2))


if __name__ == "__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output",default="docs/evaluation/development_2021_2022")
    run(parser.parse_args().output)
