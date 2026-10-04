"""Pre-cutoff driver-intercept regression with fixed, outcome-independent priors."""
from collections import defaultdict
from math import isfinite
import numpy as np
from src.calculators.pace_model import PaceModel
from src.calculators.tyre_model import TyreModel
from src.core.models import TireCompound
from src.evaluation.pit_parameters import entry_laps

COMPOUNDS=('SOFT','MEDIUM','HARD')
PRIOR_LAPS=60.
SLOPE_PRIOR_LEVERAGE=25.  # pseudo-lap variance: five-lap age/race-lap SD
DEFAULT_TREND=-.05


def clean_groups(data,prefixes,cutoff):
    groups=defaultdict(list);available=defaultdict(list)
    for driver,p in prefixes.items():
        entries=entry_laps(data,driver,cutoff)
        pit_laps={n for lap,_ in entries for n in (lap,lap+1)}
        for r in PaceModel.filter_clean_laps(p['history']):
            if r.timestamp is None or r.timestamp.timestamp()>cutoff or r.lap_number<3 or r.lap_number in pit_laps:continue
            if not isfinite(r.lap_time_s) or r.tyre_age_laps<0 or r.compound.value not in COMPOUNDS:continue
            available[r.compound.value].append(r)
            groups[(driver,sum(lap<r.lap_number for lap,_ in entries),r.compound.value)].append(r)
    rows=[]
    for (driver,stint,c),rs in groups.items():
        if len(rs)>=3 and max(r.tyre_age_laps for r in rs)-min(r.tyre_age_laps for r in rs)>=3:
            rows.extend((driver,stint,r) for r in rs)
    return rows,available


def estimate_joint(data,prefixes,cutoff):
    rows,available=clean_groups(data,prefixes,cutoff)
    defaults={c:TyreModel.get_compound_specs(TireCompound(c)).degradation_base_rate_s_per_lap for c in COMPOUNDS}
    active=[c for c in COMPOUNDS if any(r.compound.value==c for _,_,r in rows)]
    by_driver=defaultdict(list)
    for driver,_,r in rows:by_driver[driver].append(r)
    xs=[];ys=[]
    for rs in by_driver.values():
        x=np.array([[r.tyre_age_laps if r.compound.value==c else 0. for c in active]+[r.lap_number] for r in rs],float)
        y=np.array([r.lap_time_s-TyreModel.get_compound_specs(r.compound).base_pace_delta_s
            -.15*max(0,r.tyre_age_laps-TyreModel.get_compound_specs(r.compound).cliff_lap_threshold) for r in rs])
        xs.append(x-x.mean(axis=0));ys.append(y-y.mean())
    x=np.concatenate(xs) if xs else np.empty((0,len(active)+1));y=np.concatenate(ys) if ys else np.empty(0)
    rank=int(np.linalg.matrix_rank(x)) if x.size else 0
    trend_identified=bool(rows) and rank==len(active)+1
    prior=np.array([defaults[c] for c in active]+([DEFAULT_TREND] if trend_identified else []))
    if not trend_identified:y=y-x[:,-1]*DEFAULT_TREND;x=x[:,:-1]
    penalty=PRIOR_LAPS*SLOPE_PRIOR_LEVERAGE
    fitted=prior.copy();free=list(range(len(prior)))
    while free:
        z=x[:,free];target=y-x@fitted+z@fitted[free]
        fitted[free]=np.linalg.solve(z.T@z+np.eye(len(free))*penalty,z.T@target+penalty*prior[free])
        negative=[i for i in free if i<len(active) and fitted[i]<0]
        if not negative:break
        for i in negative:fitted[i]=0.;free.remove(i)
    latest=max((r.timestamp.timestamp() for _,_,r in rows),default=0.)
    rates=defaults.copy();rates.update({c:float(fitted[i]) for i,c in enumerate(active)})
    trend=float(fitted[-1]) if trend_identified else DEFAULT_TREND
    audits={}
    for c in COMPOUNDS:
        used=[r for _,_,r in rows if r.compound.value==c];fallback=c not in active
        audits[c]={'rate_s_per_lap':rates[c],'default_s_per_lap':defaults[c], 'sample_count':len(used),
            'available_clean_lap_count':len(available[c]),'driver_count':len({d for d,_,r in rows if r.compound.value==c}),
            'fallback_used':fallback,'latest_source_session_s':max((r.timestamp.timestamp() for r in available[c]),default=0.) if fallback else latest,
            'prior_precision':penalty,'joint_sample_count':len(rows),'clipped_to_nonnegative':rates[c]==0.}
    trend_audit={'value_s_per_lap':trend,'default_s_per_lap':DEFAULT_TREND,'sample_count':len(rows) if trend_identified else 0,
        'available_sample_count':len(rows),'driver_count':len(by_driver),'fallback_used':not trend_identified,
        'latest_source_session_s':latest,'design_rank':rank,'design_columns':len(active)+1,'prior_precision':penalty,
        'method':'driver-demeaned joint ridge; fixed compound offsets; nonnegative wear'}
    assert latest<=cutoff
    return rates,audits,trend,trend_audit
