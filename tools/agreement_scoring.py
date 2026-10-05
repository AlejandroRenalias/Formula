"""Outcome-only agreement scoring; no model calls or decision inputs."""
from functools import lru_cache
import statistics
from tools.agreement_inputs import phase

PHASES=('5-14','15-29','30+')
def ratio(a,b):return a/b if b else None

def match(alerts,stops,tolerance):
    @lru_cache(None)
    def solve(i,j):
        if i==len(alerts) or j==len(stops):return ()
        options=[solve(i+1,j),solve(i,j+1)]
        if abs(alerts[i]['lap']-stops[j]['lap'])<=tolerance:
            options.append(((i,j),)+solve(i+1,j+1))
        return min(options,key=lambda pairs:(-len(pairs),sum(abs(alerts[a]['lap']-stops[b]['lap']) for a,b in pairs),tuple((alerts[a]['lap'],stops[b]['lap']) for a,b in pairs)))
    return list(solve(0,0))

def episodes(calls,stride=1):
    result=[];previous=None
    for c in sorted(calls,key=lambda c:c['lap']):
        if c['call']=='BOX_NOW' and (previous is None or previous['call']!='BOX_NOW' or c['lap']-previous['lap']!=stride):
            result.append({'lap':c['lap'],'left_censored':previous is None or c['lap']-previous['lap']!=stride,
                           'cutoff_session_s':c['cutoff_session_s'],'directional_stratum':c['directional_stratum']})
        previous=c
    return result

def timing(pairs):
    e=[p['error_laps'] for p in pairs]
    return {'n':len(e),'mean_laps':statistics.mean(e) if e else None,'median_laps':statistics.median(e) if e else None,
            'mae_laps':statistics.mean(map(abs,e)) if e else None,
            'early_2_to_10':sum(x<-1 for x in e),'within_1':sum(abs(x)<=1 for x in e),'late_2_to_10':sum(x>1 for x in e),
            'minus_1':e.count(-1),'zero':e.count(0),'plus_1':e.count(1)}

def counts(calls,alerts,stops,pairs,scope=lambda r:True):
    cs=[c for c in calls if scope(c)]; aa=[a for a in alerts if scope(a)];ss=[s for s in stops if scope(s)]
    mp=sum(scope(p['alert']) for p in pairs);mr=sum(scope(p['stop']) for p in pairs)
    box=[c for c in cs if c['call']=='BOX_NOW']; eligible=[s for s in ss if s['observable']]
    tp=mp; fp=len(aa)-mp;fn=len(eligible)-mr
    return {'valid_cutoffs':len(cs),'box_cutoffs':len(box),'box_rate':ratio(len(box),len(cs)),
        'alerts':len(aa),'left_censored_alerts':sum(a['left_censored'] for a in aa),'total_team_stops':len(ss),
        'observable_team_stops':len(eligible),'unobservable_team_stops':len(ss)-len(eligible),
        'partial_stop_windows':sum(s['partial_window'] for s in eligible),
        'tp_precision':tp,'tp_recall':mr,'fp':fp,'fn':fn,'precision':ratio(tp,len(aa)),'recall':ratio(mr,len(eligible)),
        'f1':ratio(2*tp,2*tp+fp+fn) if tp==mr else None,
        'raw_box_precision':ratio(sum(any(s['driver_number']==c['driver_number'] and abs(c['lap']-s['lap'])<=1 for s in stops) for c in box),len(box)),
        'stay_finish_available':sum(c['stay_to_finish_available'] for c in cs),
        'stay_finish_wins':sum(c['recommended']=='stay_to_finish' for c in cs),
        'stay_finish_win_fraction_all':ratio(sum(c['recommended']=='stay_to_finish' for c in cs),len(cs)),
        'stay_finish_win_fraction_available':ratio(sum(c['recommended']=='stay_to_finish' for c in cs),sum(c['stay_to_finish_available'] for c in cs))}

def score(calls,data,stride=1):
    alerts=[];stops=[];matched={t:[] for t in (0,1,10)};audits=[]
    for driver in sorted({c['driver_number'] for c in calls}):
        cc=[c for c in calls if c['driver_number']==driver]
        aa=[dict(a,driver_number=driver) for a in episodes(cc,stride)]
        ss=[]
        for row in data['laps']:
            if row['Driver']!=driver or not row.get('PitInTime'):continue
            lap=int(row['NumberOfLaps'])-1
            window={lap-1,lap,lap+1};valid={c['lap'] for c in cc}
            ss.append({'lap':lap,'driver_number':driver,'entry_session_s':row['PitInTime'],
                       'observable':bool(window&valid),'partial_window':not window<=valid,
                       'directional_stratum':any(c['directional_stratum'] and c['lap'] in window for c in cc)})
        ss.sort(key=lambda s:s['lap']);eligible=[s for s in ss if s['observable']]
        alerts.extend(aa);stops.extend(ss)
        for t in matched:
            pairs=match(aa,eligible,t)
            detail=[{'alert':aa[i],'stop':eligible[j],'error_laps':aa[i]['lap']-eligible[j]['lap'],
                     'post_observed_stop':aa[i]['cutoff_session_s']>=eligible[j]['entry_session_s']} for i,j in pairs]
            matched[t].extend(detail)
            audits.append({'driver_number':driver,'tolerance_laps':t,'alerts':aa,'all_stops':ss,'matches':detail,
                           'unmatched_alert_indices':[i for i in range(len(aa)) if all(i!=a for a,b in pairs)],
                           'unmatched_eligible_stop_indices':[j for j in range(len(eligible)) if all(j!=b for a,b in pairs)]})
    result={'all':counts(calls,alerts,stops,matched[1]),'phase':{},'thirds':{},'timing':{},'directional':{}}
    for p in PHASES:result['phase'][p]=counts(calls,alerts,stops,matched[1],lambda r:phase(r['lap'])==p)
    total=data['scheduled_laps']
    def third(r):return min(2,3*r['lap']//total)
    for p in range(3):result['thirds'][str(p+1)]=counts(calls,alerts,stops,matched[1],lambda r:third(r)==p)
    for t,pairs in matched.items():
        result['timing'][str(t)]={'all':timing(pairs),'uncensored':timing([p for p in pairs if not p['alert']['left_censored']]),
          'censored':timing([p for p in pairs if p['alert']['left_censored']]),
          'by_alert_phase':{ph:timing([p for p in pairs if phase(p['alert']['lap'])==ph]) for ph in PHASES},
          'by_team_phase':{ph:timing([p for p in pairs if phase(p['stop']['lap'])==ph]) for ph in PHASES},
          'post_observed_matches':sum(p['post_observed_stop'] for p in pairs),
          'unmatched_alerts':len(alerts)-len(pairs),'unmatched_observable_stops':sum(s['observable'] for s in stops)-len(pairs)}
    result['exact']=counts(calls,alerts,stops,matched[0])
    result['directional']['causal_stratum']=counts(calls,alerts,stops,matched[1],lambda r:r['directional_stratum'])
    result['directional']['wide_early_uncensored']=timing([p for p in matched[10] if phase(p['alert']['lap'])=='5-14' and not p['alert']['left_censored']])
    result['directional']['wide_stratum_uncensored']=timing([p for p in matched[10] if p['alert']['directional_stratum'] and not p['alert']['left_censored']])
    return result,audits
