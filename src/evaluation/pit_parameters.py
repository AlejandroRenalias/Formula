"""Pit-loss evidence from causal raw lap observations and completed stop pairs."""
import hashlib
import json
import statistics
from functools import lru_cache
from pathlib import Path
from src.calculators.pace_model import PaceModel
from src.calculators.tyre_model import TyreModel

PRIOR_STRENGTH_STOPS=5.


def entry_laps(data,driver,cutoff):
    n=0;in_pit=False;entries=[]
    for e in sorted((e for e in data['events'] if e['Driver']==driver and e['Time']<=cutoff),key=lambda e:e['Time']):
        if isinstance(e.get('NumberOfLaps'),(int,float)):n=max(n,int(e['NumberOfLaps']))
        if 'InPit' in e:
            if e['InPit'] and not in_pit and e['Time']>=data.get('session_start_s',0):
                entries.append((n+1,e['Time']))
            in_pit=bool(e['InPit'])
    return entries


def completed_stop_samples(data,prefixes,cutoff):
    samples=[]
    for driver,prefix in prefixes.items():
        observations=[r for r in prefix['history'] if r.timestamp is not None and r.timestamp.timestamp()<=cutoff]
        history={r.lap_number:r for r in observations}
        clean=PaceModel.filter_clean_laps(observations)
        entries=entry_laps(data,driver,cutoff)
        for index,(lap,entry_time) in enumerate(entries):
            if lap not in history or lap+1 not in history:continue
            a,b=history[lap],history[lap+1]
            exits=[e['Time'] for e in data['events'] if e['Driver']==driver and e.get('InPit') is False
                   and entry_time<e['Time']<=min(cutoff,b.timestamp.timestamp())]
            if not exits:continue
            previous_end=entries[index-1][0]+1 if index else 2
            next_entry=entries[index+1][0] if index+1<len(entries) else float('inf')
            if a.track_status.value!='GREEN' or b.track_status.value!='GREEN':continue
            pre=sorted((r for r in clean if previous_end<r.lap_number<lap),key=lambda r:r.lap_number)[-3:]
            # Following clean laps are allowed ONLY when already observed.
            post=sorted((r for r in clean if lap+1<r.lap_number<=lap+5 and r.lap_number<next_entry and r.compound==b.compound),key=lambda r:r.lap_number)[:3]
            if len(pre)<2:continue
            def base(rows):
                return statistics.median(r.lap_time_s-TyreModel.lap_delta_s(r.compound,r.tyre_age_laps)+.05*r.lap_number for r in rows)
            old=pre[-1]
            in_expected=base(pre)+TyreModel.lap_delta_s(old.compound,old.tyre_age_laps+lap-old.lap_number)-.05*lap
            out_expected=(base(post) if post else base(pre))+TyreModel.lap_delta_s(b.compound,b.tyre_age_laps)-.05*(lap+1)
            in_loss=a.lap_time_s-in_expected;out_loss=b.lap_time_s-out_expected
            # Frozen measurement quality bounds, not selected on evaluation errors.
            if not (0<in_loss<40 and 0<out_loss<40 and 5<in_loss+out_loss<60):continue
            source=max((r.timestamp.timestamp() for r in [a,b,*pre,*post]),default=0.)
            if source>cutoff:raise ValueError('Future pit-loss evidence')
            samples.append({'driver':driver,'in_lap':lap,'out_lap':lap+1,'entry_session_s':entry_time,'exit_session_s':min(exits),
                'source_session_s':source,'in_lap_loss_s':in_loss,'out_lap_loss_s':out_loss,
                'total_loss_s':in_loss+out_loss,'post_clean_anchor_count':len(post)})
    return samples


@lru_cache(maxsize=1)
def load_pit_prior():
    path=Path(__file__).resolve().parents[2]/'data/priors/pit_2019.json'
    blob=path.read_bytes();digest=hashlib.sha256(blob).hexdigest()
    if digest!=path.with_suffix('.sha256').read_text().strip():raise ValueError('Pit prior hash mismatch')
    prior=json.loads(blob)
    if prior['latest_available_year']>=2021:raise ValueError('Pit prior must precede evaluation')
    return prior,digest


def pit_inputs(data,prefixes,cutoff):
    prior,digest=load_pit_prior()
    venue=data.get('race')
    defaults=prior.get('by_venue',{}).get(venue,prior)
    samples=completed_stop_samples(data,prefixes,cutoff)
    n=len(samples);weight=n/(n+PRIOR_STRENGTH_STOPS)
    a=(1-weight)*defaults['in_lap_loss_s']+weight*(statistics.median(r['in_lap_loss_s'] for r in samples) if n else defaults['in_lap_loss_s'])
    b=(1-weight)*defaults['out_lap_loss_s']+weight*(statistics.median(r['out_lap_loss_s'] for r in samples) if n else defaults['out_lap_loss_s'])
    return a+b,a/(a+b),{'sample_count':n,'fallback_used':n==0,'prior_weight':1-weight,
        'latest_source_session_s':max((r['source_session_s'] for r in samples),default=0.),
        'green_total_loss_s':a+b,'in_lap_fraction':a/(a+b),'in_lap_loss_s':a,'out_lap_loss_s':b,
        'prior_year':2019,'prior_venue':venue if venue in prior.get('by_venue',{}) else 'pooled','prior_sha256':digest,'samples':samples}
