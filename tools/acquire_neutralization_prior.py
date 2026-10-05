"""Acquire only 2019 dry-race neutralization evidence, before all evaluation cutoffs."""
import argparse, hashlib, json, statistics
from pathlib import Path
import fastf1
import pandas as pd
from fastf1 import _api
from tools.reservation_gate import authorize

RACES = ["Australia","Bahrain","China","Azerbaijan","Spain","Monaco","Canada","France",
         "Austria","Great Britain","Hungary","Belgium","Italy","Singapore","Russia","Japan",
         "Mexico","United States","Brazil","Abu Dhabi"]

def kind(code):
    return "SC" if str(code)=="4" else "VSC" if str(code) in {"6","7"} else None


def run(offline=False):
    for name in RACES:
        authorize(2019, name, purpose='prior')
    fastf1.Cache.enable_cache("data/cache");fastf1.Cache.offline_mode(offline)
    sc, vsc, ratios = [], [], {"SC":[],"VSC":[]}
    evidence, exposure, included = [], 0., []
    event_counts={"SC":0,"VSC":0}
    for name in RACES:
        session=fastf1.get_session(2019,name,"R")
        path=session.api_path
        weather=_api.weather_data(path)
        if any(weather["Rainfall"]):
            evidence.append({"race":name,"excluded":"any rainfall station sample"});continue
        status=_api.track_status_data(path)
        statuses=[(pd.Timedelta(t).total_seconds(),str(c)) for t,c in zip(status["Time"],status["Status"])]
        statuses.sort()
        laps,_=_api.timing_data(path)
        states=_api.session_status_data(path)
        started=[pd.Timedelta(t).total_seconds() for t,c in zip(states["Time"],states["Status"]) if c=="Started"]
        start=started[0]
        finish=laps.loc[laps["NumberOfLaps"]==laps["NumberOfLaps"].max(),"Time"].min().total_seconds()
        valid=laps[laps["LapTime"].notna() & laps["PitInTime"].isna() & laps["PitOutTime"].isna() & (laps["NumberOfLaps"]>2)]
        def classification(a,b):
            initial=next((c for t,c in reversed(statuses) if t<=a),"1")
            codes=[initial]+[c for t,c in statuses if a<t<b]
            ks=[kind(c) for c in codes]
            return initial if all(c=="1" for c in codes) else ks[0] if ks[0] and all(k==ks[0] for k in ks) else None
        green={}
        for driver,rows in valid.groupby("Driver"):
            values=[r.LapTime.total_seconds() for r in rows.itertuples() if classification((r.Time-r.LapTime).total_seconds(),r.Time.total_seconds())=="1"]
            if values:green[driver]=statistics.median(values)
        reference=statistics.median(green.values())
        for r in valid.itertuples():
            k=classification((r.Time-r.LapTime).total_seconds(),r.Time.total_seconds())
            if k in ratios and r.Driver in green:ratios[k].append(r.LapTime.total_seconds()/green[r.Driver])
        segments=[]
        for i,(t,c) in enumerate(statuses):
            a=max(start,t); b=min(finish,statuses[i+1][0] if i+1<len(statuses) else finish)
            if b<=a:continue
            k=kind(c)
            if k:
                if segments and segments[-1]["kind"]==k and abs(segments[-1]["end"]-a)<1e-6:segments[-1]["end"]=b
                else:segments.append({"kind":k,"start":a,"end":b})
            elif c in {"1","2"}:exposure+=(b-a)/reference
        for e in segments:
            duration=e["end"]-e["start"]
            event_counts[e["kind"]]+=1
            e["right_censored"] = abs(e["end"]-finish)<1e-6
            if not e["right_censored"]:
                (sc if e["kind"]=="SC" else vsc).append(duration)
        included.append(name)
        evidence.append({"race":name,"api_path":path,"green_pace_s":reference,"episodes":segments,
                         "status":statuses,"green_driver_count":len(green)})
        print(name,"episodes",len(segments),flush=True)
    if not sc or not vsc or not ratios["SC"] or not ratios["VSC"]:raise ValueError("Insufficient external prior evidence")
    prior={"schema_version":1,"year":2019,"latest_available_year":2019,"included_races":included,
           "excluded_wet_race": "Germany omitted in advance; any rainy station session also excluded",
           "green_lap_exposure":exposure,"sc_event_count":event_counts["SC"],"vsc_event_count":event_counts["VSC"],
           "sc_probability_per_green_lap":event_counts["SC"]/exposure,"vsc_probability_per_green_lap":event_counts["VSC"]/exposure,
           "sc_durations_s":sc,"vsc_durations_s":vsc,
           "duration_censoring":"Right-censored finish episodes count as onsets, not completed durations",
           "sc_pace_multiplier":statistics.median(ratios["SC"]),
           "vsc_pace_multiplier":statistics.median(ratios["VSC"]),
           "pace_ratio_sample_counts":{k:len(v) for k,v in ratios.items()},
           "tail_remaining_assumption_s":{"SC":90.,"VSC":30.},"race_evidence":evidence}
    root=Path("data/priors");root.mkdir(parents=True,exist_ok=True)
    blob=(json.dumps(prior,indent=2)+"\n").encode()
    (root/"neutralization_2019.json").write_bytes(blob)
    (root/"neutralization_2019.sha256").write_text(hashlib.sha256(blob).hexdigest()+"\n")
    print(json.dumps({k:v for k,v in prior.items() if k not in ("race_evidence","sc_durations_s","vsc_durations_s")},indent=2))

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--offline",action="store_true");run(p.parse_args().offline)
