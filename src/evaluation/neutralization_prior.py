"""Frozen pre-evaluation neutralization prior; causal elapsed-duration conditioning."""
import hashlib,json,math,statistics
from functools import lru_cache
from pathlib import Path

@lru_cache(maxsize=1)
def load_prior():
    p=Path(__file__).resolve().parents[2]/"data/priors/neutralization_2019.json"
    blob=p.read_bytes();digest=hashlib.sha256(blob).hexdigest()
    if digest!=p.with_suffix(".sha256").read_text().strip():raise ValueError("Neutralization prior hash mismatch")
    prior=json.loads(blob)
    if prior["latest_available_year"]>=2021:raise ValueError("Prior must precede every evaluation race")
    return prior,digest


def remaining_seconds(prior,kind,elapsed):
    durations=prior[kind.lower()+"_durations_s"]
    surviving=[d-elapsed for d in durations if d>elapsed]
    return statistics.mean(surviving) if surviving else prior["tail_remaining_assumption_s"][kind]


def ongoing_inputs(track,cutoff,status,green_pace):
    prior,digest=load_prior()
    kind="SC" if status.value=="SAFETY_CAR" else "VSC" if status.value=="VSC" else None
    elapsed=remaining=0.;start=cutoff;source=0.
    if kind:
        codes={"4"} if kind=="SC" else {"6","7"}
        prefix=[r for r in track if r["Time"]<=cutoff]
        for r in reversed(prefix):
            if str(r["Status"]) not in codes:break
            start=r["Time"]
        elapsed=cutoff-start;source=start
        remaining=remaining_seconds(prior,kind,elapsed)
        pace=green_pace*prior[kind.lower()+"_pace_multiplier"]
        laps=max(1,math.ceil(remaining/pace))
    else:laps=0
    return laps,{"kind":kind,"onset_session_s":start if kind else None,"elapsed_s":elapsed,
                 "expected_remaining_s":remaining,"expected_remaining_laps":laps,
                 "source_session_s":source,"prior_sha256":digest,"prior_year":2019,
                 "tail_fallback":bool(kind and not any(d>elapsed for d in prior[kind.lower()+"_durations_s"]))}
