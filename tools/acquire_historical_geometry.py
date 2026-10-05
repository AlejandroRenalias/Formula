"""Gated pre-race Q geometry for evaluated weekends; never load a race session."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from tools.reservation_gate import authorize, guarded_session

ROOT=Path(__file__).resolve().parents[1]
TRACKS={'bahrain':(2021,'Bahrain'),'barcelona':(2022,'Spain'),'barcelona_2023':(2023,'Spain'),'paul_ricard':(2022,'France')}
NAMES={'bahrain':'Bahrain International Circuit','barcelona':'Circuit de Barcelona-Catalunya (2022)','barcelona_2023':'Circuit de Barcelona-Catalunya (2023)','paul_ricard':'Circuit Paul Ricard'}

def geometry(track_id,telemetry,duration,sector1,sector2,source):
    """Static measured loop/time profile; pit markers are approximate configuration."""
    if not (duration>0 and 0<sector1<sector1+sector2<duration):raise ValueError('Invalid lap/sector times')
    t=np.asarray(telemetry['Time'].dt.total_seconds(),dtype=float)
    d=np.asarray(telemetry['Distance'],dtype=float)
    x=np.asarray(telemetry['X'],dtype=float);y=np.asarray(telemetry['Y'],dtype=float)
    good=np.isfinite(t)&np.isfinite(d)&np.isfinite(x)&np.isfinite(y)
    t,d,x,y=t[good],d[good],x[good],y[good]
    order=np.argsort(t);t,d,x,y=t[order],d[order],x[order],y[order]
    keep=np.r_[True,np.diff(t)>0];t,d,x,y=t[keep],d[keep],x[keep],y[keep]
    if len(t)<100 or t[0]>0 or t[-1]<duration:raise ValueError('Telemetry must cover the complete reference lap')
    times=np.linspace(0,duration,501)
    distances=np.interp(times,t,d)-np.interp(0,t,d)
    if np.any(np.diff(distances)<=0):raise ValueError('Distance must be strictly increasing')
    xs=np.interp(times,t,x);ys=np.interp(times,t,y)
    length=float(distances[-1]);cx=(xs.max()+xs.min())/2;cy=(ys.max()+ys.min())/2
    scale=max(float(np.ptp(xs)),float(np.ptp(ys)))
    if scale<=0 or not 3000<length<8000:raise ValueError('Invalid measured track scale')
    xs=(xs-cx)/scale;ys=(ys-cy)/scale
    closure=float(np.hypot(xs[-1]-xs[0],ys[-1]-ys[0]))
    if closure>.03:raise ValueError('Reference lap is not a closed circuit')
    xs[-1]=xs[0];ys[-1]=ys[0]
    bounds=[0,float(np.interp(sector1,t,d)-np.interp(0,t,d)),float(np.interp(sector1+sector2,t,d)-np.interp(0,t,d)),length]
    return {'schema_version':1,'id':track_id,'name':NAMES[track_id],'source':source,
        'lap_length_m':length,'reference_lap_time_s':float(duration),
        'coordinates':{'normalization':'centered, longest extent = 1, aspect preserved','orientation':'FastF1 measured X/Y','closure_adjustment_normalized':closure},
        'polyline':[{'distance_m':float(di),'x':float(xi),'y':float(yi)} for di,xi,yi in zip(distances,xs,ys)],
        'time_profile':[{'distance_m':float(di),'time_s':float(ti)} for di,ti in zip(distances,times)],
        'start_finish':{'distance_m':0.,'kind':'measured'},
        'sectors':[{'sector':i+1,'start_distance_m':bounds[i],'end_distance_m':bounds[i+1],'kind':'measured'} for i in range(3)],
        'pit_entry':{'distance_m':.96*length,'kind':'config','note':'Approximate reference marker, not calibrated pit-lane telemetry'},
        'pit_exit':{'distance_m':.04*length,'kind':'config','note':'Approximate reference marker, not calibrated pit-lane telemetry'}}

def acquire(track_id,offline=False):
    if track_id not in TRACKS:raise ValueError('Only the three evaluated venues are authorized')
    year,event=TRACKS[track_id]
    authorize(year,event,purpose='geometry',session='Q')
    session=guarded_session(year,event,purpose='geometry',session='Q',cache_dir=ROOT/'data/cache',offline=offline)
    q_date=session.event.get_session_date('Q',utc=True)
    race_date=session.event.get_session_date('R',utc=True)
    if q_date>=race_date:raise ValueError('Geometry source is not pre-race')
    session.load(telemetry=True,laps=True,weather=False,messages=True)
    lap=session.laps.pick_accurate().pick_not_deleted().pick_fastest()
    if lap is None or not lap['LapTime'] or lap['PitInTime']==lap['PitInTime'] or lap['PitOutTime']==lap['PitOutTime']:
        raise ValueError('Accurate non-pit qualifying reference required')
    telemetry=lap.get_telemetry()
    import fastf1
    source={'provider':'FastF1','version':fastf1.__version__,'year':year,'event':str(session.event['EventName']),
        'session':'Q','date':q_date.isoformat(),'race_start_date':race_date.isoformat(),'clock':'UTC (FastF1 utc=True)',
        'driver':str(lap['Driver']),'lap_number':int(lap['LapNumber']),
        'selection':'fastest accurate non-deleted non-pit qualifying lap',
        'role':'static pre-race reference geometry and time profile, not cutoff race observations',
        'reservation_gate':'geometry authorized before FastF1/cache access',
        'telemetry_sha256':hashlib.sha256(telemetry[['Time','Distance','X','Y']].to_csv(index=False).encode()).hexdigest()}
    result=geometry(track_id,telemetry,lap['LapTime'].total_seconds(),lap['Sector1Time'].total_seconds(),lap['Sector2Time'].total_seconds(),source)
    target=ROOT/'data/tracks'/f'{track_id}.json'
    target.write_bytes((json.dumps(result,indent=2,allow_nan=False)+'\n').encode('utf-8'))
    print(json.dumps({'track':track_id,'path':str(target),'bytes':target.stat().st_size,'length_m':result['lap_length_m'],'source':source}),flush=True)
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--track',choices=tuple(TRACKS),required=True);p.add_argument('--offline',action='store_true')
    a=p.parse_args();acquire(a.track,a.offline)
