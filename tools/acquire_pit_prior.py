"""Acquire 2019 Bahrain/Spain/France evidence for a pre-evaluation pit prior only."""
import argparse,hashlib,json,statistics
from pathlib import Path
import fastf1
import pandas as pd
from fastf1 import _api
from tools.acquire_bahrain_evaluation import records
from src.evaluation.snapshot import driver_prefix
from src.evaluation.pit_parameters import completed_stop_samples
from tools.reservation_gate import authorize


def run(offline):
    for name in ('Bahrain','Spain','France'):
        authorize(2019, name, purpose='prior')
    fastf1.Cache.enable_cache('data/cache');fastf1.Cache.offline_mode(offline)
    all_samples=[];evidence=[]
    for name in ('Bahrain','Spain','France'):
        session=fastf1.get_session(2019,name,'R');path=session.api_path
        weather=_api.weather_data(path)
        if any(weather['Rainfall']):raise ValueError('Dry prior race required')
        events=[]
        for t,packet in _api.fetch_page(path,'timing_data'):
            for driver,update in packet.get('Lines',{}).items():
                fields={k:update[k] for k in ('NumberOfLaps','Position','InPit','Retired','Stopped','LastLapTime') if k in update}
                if fields:events.append({'Time':pd.Timedelta(t).total_seconds(),'Driver':driver,**fields})
        states=_api.session_status_data(path)
        start=next(pd.Timedelta(t).total_seconds() for t,c in zip(states['Time'],states['Status']) if c=='Started')
        data={'year':2019,'race':name,'session_start_s':start,'events':events,
              'tyres':records(_api.timing_app_data(path)),'track_status':records(_api.track_status_data(path))}
        cutoff=max(e['Time'] for e in events)
        prefixes={d:driver_prefix(data,d,cutoff) for d in {e['Driver'] for e in events}}
        samples=completed_stop_samples(data,prefixes,cutoff)
        for r in samples:r['race']=name
        all_samples.extend(samples);evidence.append({'year':2019,'race':name,'samples':samples})
        root=Path('data/cache/pit_prior')/name.lower();root.mkdir(parents=True,exist_ok=True)
        blob=json.dumps(data,indent=2).encode();(root/'session.json').write_bytes(blob)
        (root/'session.sha256').write_text(hashlib.sha256(blob).hexdigest()+'\n')
        print(name,len(samples),'eligible stops',flush=True)
    if len(all_samples)<10:raise ValueError('Insufficient external completed stops')
    a=statistics.median(r['in_lap_loss_s'] for r in all_samples);b=statistics.median(r['out_lap_loss_s'] for r in all_samples)
    by_venue={}
    for race in evidence:
        rows=race['samples']
        a_venue=statistics.median(r['in_lap_loss_s'] for r in rows)
        b_venue=statistics.median(r['out_lap_loss_s'] for r in rows)
        by_venue[race['race']]={'sample_count':len(rows),'in_lap_loss_s':a_venue,'out_lap_loss_s':b_venue,
            'green_total_loss_s':a_venue+b_venue,'in_lap_fraction':a_venue/(a_venue+b_venue)}
    prior={'latest_available_year':2019,'races':['Bahrain 2019','Spain 2019','France 2019'],
        'by_venue':by_venue,'sample_count':len(all_samples),'in_lap_loss_s':a,'out_lap_loss_s':b,'green_total_loss_s':a+b,
        'in_lap_fraction':a/(a+b),'evidence':evidence}
    blob=(json.dumps(prior,indent=2)+'\n').encode();root=Path('data/priors')
    (root/'pit_2019.json').write_bytes(blob);(root/'pit_2019.sha256').write_text(hashlib.sha256(blob).hexdigest()+'\n')
    print(json.dumps({k:v for k,v in prior.items() if k!='evidence'},indent=2),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--offline',action='store_true');run(p.parse_args().offline)
