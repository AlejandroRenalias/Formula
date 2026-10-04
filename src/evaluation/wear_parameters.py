"""Causal within-stint, compound-pooled linear wear estimates."""
import statistics
from math import isfinite
from collections import defaultdict
from src.calculators.pace_model import PaceModel
from src.calculators.tyre_model import TyreModel
from src.core.models import TireCompound
from src.evaluation.pit_parameters import entry_laps

SHRINKAGE_CLEAN_LAPS=60.
MIN_STINT_LAPS=3
MIN_AGE_SPAN=3


def estimate_wear(data,prefixes,cutoff):
    groups=defaultdict(list);available=defaultdict(list)
    for driver,prefix in prefixes.items():
        entries=entry_laps(data,driver,cutoff)
        pit_laps={n for lap,_ in entries for n in (lap,lap+1)}
        for r in PaceModel.filter_clean_laps(prefix['history']):
            if r.timestamp is None or r.timestamp.timestamp()>cutoff or r.lap_number<3 or r.lap_number in pit_laps:continue
            if not isfinite(r.lap_time_s) or r.tyre_age_laps<0:continue
            if r.compound not in (TireCompound.SOFT,TireCompound.MEDIUM,TireCompound.HARD):continue
            stint=sum(lap<r.lap_number for lap,_ in entries)
            available[r.compound.value].append(r)
            groups[(r.compound.value,driver,stint)].append(r)
    results={};rates={}
    for compound in (TireCompound.SOFT,TireCompound.MEDIUM,TireCompound.HARD):
        specs=TyreModel.get_compound_specs(compound)
        count=0;xx=xy=0.;used=[];stints=[]
        for (kind,driver,stint),rows in groups.items():
            if kind!=compound.value or len(rows)<MIN_STINT_LAPS:continue
            ages=[r.tyre_age_laps for r in rows]
            if max(ages)-min(ages)<MIN_AGE_SPAN:continue
            # Remove the unchanged nominal cliff term to avoid fitting it twice.
            times=[r.lap_time_s+.05*r.lap_number-.15*max(0,r.tyre_age_laps-specs.cliff_lap_threshold) for r in rows]
            mx,my=statistics.mean(ages),statistics.mean(times)
            sxx=sum((x-mx)**2 for x in ages)
            sxy=sum((x-mx)*(y-my) for x,y in zip(ages,times))
            if sxx<=0:continue
            xx+=sxx;xy+=sxy;count+=len(rows);used.extend(rows)
            stints.append({'driver':driver,'stint_index':stint,'sample_count':len(rows),
                'age_span':max(ages)-min(ages),'latest_source_session_s':max(r.timestamp.timestamp() for r in rows)})
        raw=xy/xx if xx else None
        weight=count/(count+SHRINKAGE_CLEAN_LAPS)
        default=specs.degradation_base_rate_s_per_lap
        rate=default if raw is None else (1-weight)*default+weight*max(0.,raw)
        rows_for_source=used or available[compound.value]
        source=max((r.timestamp.timestamp() for r in rows_for_source),default=0.)
        if source>cutoff:raise ValueError('Future wear parameter source')
        rates[compound.value]=rate
        results[compound.value]={'rate_s_per_lap':rate,'default_s_per_lap':default,'raw_slope_s_per_lap':raw,
            'clipped_to_nonnegative':raw is not None and raw<0,'sample_count':count,'available_clean_lap_count':len(available[compound.value]),
            'qualifying_stint_count':len(stints),'driver_count':len({r['driver'] for r in stints}),
            'fallback_used':raw is None,'prior_weight':1-weight,'latest_source_session_s':source,
            'within_stint_sxx':xx,'within_stint_sxy':xy,'stints':stints}
    return rates,results
