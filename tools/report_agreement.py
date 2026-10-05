"""Report saved agreement calls/matches only; never re-run decisions."""
import json
from pathlib import Path
import statistics
from tools.agreement_inputs import RACES,ROOT,sha

PHASES=('5-14','15-29','30+')
def mean_available(v):
    vv=[x for x in v if x is not None];return statistics.mean(vv) if vv else None

def pooled_counts(rows):
    sumkeys=('valid_cutoffs','box_cutoffs','alerts','left_censored_alerts','total_team_stops','observable_team_stops',
             'unobservable_team_stops','partial_stop_windows','tp_precision','tp_recall','fp','fn','stay_finish_available','stay_finish_wins')
    r={k:sum(x[k] for x in rows) for k in sumkeys}
    for name,num,den in (('precision','tp_precision','alerts'),('recall','tp_recall','observable_team_stops'),
        ('box_rate','box_cutoffs','valid_cutoffs'),('stay_finish_win_fraction_all','stay_finish_wins','valid_cutoffs'),
        ('stay_finish_win_fraction_available','stay_finish_wins','stay_finish_available')):
        r[name]=r[num]/r[den] if r[den] else None
    r['raw_box_precision']=sum((x['raw_box_precision'] or 0)*x['box_cutoffs'] for x in rows)/r['box_cutoffs'] if r['box_cutoffs'] else None
    r['equal_race_precision']=mean_available([x['precision'] for x in rows]);r['equal_race_recall']=mean_available([x['recall'] for x in rows])
    return r

def pooled_time(rows):
    n=sum(r['n'] for r in rows)
    result={'n':n,'mean_laps':sum((r['mean_laps'] or 0)*r['n'] for r in rows)/n if n else None,
        'mae_laps':sum((r['mae_laps'] or 0)*r['n'] for r in rows)/n if n else None,
        'equal_race_mean_laps':mean_available([r['mean_laps'] for r in rows]),
        'equal_race_mae_laps':mean_available([r['mae_laps'] for r in rows]),
        'equal_race_median_laps':mean_available([r['median_laps'] for r in rows])}
    for k in ('early_2_to_10','within_1','late_2_to_10','minus_1','zero','plus_1'):result[k]=sum(r[k] for r in rows)
    return result

def fmt(v,percent=False):return 'NA' if v is None else f'{100*v:.1f}%' if percent else f'{v:+.2f}'
def run():
    races={r:json.loads((ROOT/r/'metrics.json').read_text()) for r in RACES}
    pools={}
    for name,rr in (('development',RACES[:3]),('held_out',RACES[3:])):
        pool={'all':pooled_counts([races[r]['all'] for r in rr]),
            'phase':{ph:pooled_counts([races[r]['phase'][ph] for r in rr]) for ph in PHASES},
            'thirds':{ph:pooled_counts([races[r]['thirds'][ph] for r in rr]) for ph in ('1','2','3')},'timing':{},'directional':{}}
        for t in ('0','1','10'):
            pool['timing'][t]={view:pooled_time([races[r]['timing'][t][view] for r in rr]) for view in ('all','uncensored','censored')}
            for view in ('by_alert_phase','by_team_phase'):
                pool['timing'][t][view]={ph:pooled_time([races[r]['timing'][t][view][ph] for r in rr]) for ph in PHASES}
            for key in ('post_observed_matches','unmatched_alerts','unmatched_observable_stops'):pool['timing'][t][key]=sum(races[r]['timing'][t][key] for r in rr)
        pool['directional']['causal_stratum']=pooled_counts([races[r]['directional']['causal_stratum'] for r in rr])
        for view in ('wide_early_uncensored','wide_stratum_uncensored'):pool['directional'][view]=pooled_time([races[r]['directional'][view] for r in rr])
        pool['exact']=pooled_counts([races[r]['exact'] for r in rr]);pools[name]=pool
    (ROOT/'metrics.json').write_text(json.dumps({'races':races,'pools':pools},indent=2)+'\n')
    b=json.loads((ROOT/'benchmark.json').read_text());parity=json.loads((ROOT/'prediction_parity.json').read_text())
    lines=['# Decision-engine-v1 agreement evaluation','',
        'Timing agreement only: no disagreement/counterfactual quality analysis. Development and held-out sets remain separate. '
        'No model or threshold fitting to these results. Signed timing = engine alert minus team stop boundary (negative earlier, positive later).', '',
        '## Candidate amendment and frozen prediction parity','',
        'The finish-legal zero-stop candidate was documented and committed/tagged before the first agreement benchmark. '
        'Existing candidates retain their ordering and budget, with one reserved extra slot. No-stop uses no reactive or SC stops. '
        'Immediate target HARD (MEDIUM when on HARD), four-lap deferral grid and two-stop cap remain limitations. '
        'The calibrated prediction profile is unchanged. Actual-plan summaries were checked against all saved accepted prediction fields; '
        'see [prediction_parity.json](prediction_parity.json).', '',
        '## Runtime and cohort','',
        '| Race | Valid calls | Excluded cutoffs | Stride | Projected every-lap s | Scored run s | Reused benchmark calls |',
        '| --- | ---: | ---: | ---: | ---: | ---: | ---: |']
    for r in RACES:
        m=json.loads((ROOT/r/'manifest.json').read_text());bm=b['timings'][r]
        lines.append(f"| {r} | {m['valid_cutoffs']} | {m['excluded_cutoffs']} | {m['stride']} | {bm['predicted_every_lap_runtime_s']:.1f} | {m['runtime_s']:.1f} | {m['benchmark_reused']} |")
    lines+=['','Benchmark selection was recorded before calls: phase maximum candidates, per-race minimum candidates, and France ongoing SC. '
        'The three full-wrapper parity states matched call, recommendation, ranking, candidate means, margins and confidence exactly. '
        'All runs blocked network access and hash-verified cached inputs. Benchmark calls are reused, not scored twice. '
        'Run timings exclude full-wrapper parity overhead.', '',
        'All physical subject stops are labels, including same-compound stops. A stop is recall-observable only if its +/-1 window intersects a valid cutoff. '
        'Missing cutoffs break alert episodes; the first BOX in an observed segment is left-censored. '
        'Repeated adjacent BOX calls collapse to their first call. Primary matches maximize chronological one-to-one cardinality within +/-1, '
        'then minimize absolute distance, then prefer earlier alerts. No sliding persistent alerts to the actual stop.', '',
        '## Primary +/-1-lap event agreement','',
        '| Race/set | Alerts | Observable stops | TP | FP | FN | Precision | Recall | Equal-race precision | Equal-race recall |',
        '| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |']
    combined={**races,**pools}
    for name,m in combined.items():
        a=m['all'];lines.append(f"| {name} | {a['alerts']} | {a['observable_team_stops']} | {a['tp_precision']} | {a['fp']} | {a['fn']} | {fmt(a['precision'],True)} | {fmt(a['recall'],True)} | {fmt(a.get('equal_race_precision'),True)} | {fmt(a.get('equal_race_recall'),True)} |")
    for name,m in combined.items():
        lines+=['',f'## {name}: phase and no-stop wins','',
            '| Phase | Calls | BOX rate | Alerts | Observable stops | Matched alerts/stops | Precision | Recall | Stay-finish available | Wins | Wins / all | Wins / available |',
            '| --- | ---: | ---: | ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: |']
        for ph,a in m['phase'].items():
            lines.append(f"| {ph} | {a['valid_cutoffs']} | {fmt(a['box_rate'],True)} | {a['alerts']} | {a['observable_team_stops']} | {a['tp_precision']}/{a['tp_recall']} | {fmt(a['precision'],True)} | {fmt(a['recall'],True)} | {a['stay_finish_available']} | {a['stay_finish_wins']} | {fmt(a['stay_finish_win_fraction_all'],True)} | {fmt(a['stay_finish_win_fraction_available'],True)} |")
        lines+=['','Precision phase belongs to the alert; recall phase belongs to the team stop. Matched counts can differ across a phase boundary.', '',
            '| Timing view | Matched N | Mean laps | Median laps | MAE laps | -1 / 0 / +1 | Earlier 2-10 | Later 2-10 |',
            '| --- | ---: | ---: | ---: | ---: | --- | ---: | ---: |']
        for t in ('1','10'):
            for view in ('all','uncensored','censored'):
                x=m['timing'][t][view]
                lines.append(f"| +/-{t} {view} | {x['n']} | {fmt(x['mean_laps'])} | {fmt(x.get('median_laps'))} | {fmt(x['mae_laps'])} | {x['minus_1']}/{x['zero']}/{x['plus_1']} | {x['early_2_to_10']} | {x['late_2_to_10']} |")
        a=m['all'];exact=m['exact'];lines+=['',f"Exact-lap precision/recall: {fmt(exact['precision'],True)} / {fmt(exact['recall'],True)}. Raw per-cutoff BOX precision: {fmt(a['raw_box_precision'],True)} (repeated alerts allowed). "
            f"Unobservable stops: {a['unobservable_team_stops']}; partial stop windows: {a['partial_stop_windows']}; left-censored alerts: {a['left_censored_alerts']}. "
            f"Primary matches after the stop was observed: {m['timing']['1']['post_observed_matches']}. "
            f"Wide diagnostic unmatched alerts/stops: {m['timing']['10']['unmatched_alerts']}/{m['timing']['10']['unmatched_observable_stops']}."]
    lines+=['','## Registered later-early-call hypothesis','',
        'The expected direction was not changed after the cliff diagnosis: pessimistic fresh-compound costs predict later first BOX alerts, '
        'lower early stop recall and fewer early BOX calls. The registered causal stratum is cutoff laps 5-14, immediate target wear prior weight >=0.5, '
        'and current tyre age +4 <= cliff. It uses no actual future compounds. Absolute finish bias alone need not change relative action costs.', '',
        '| Race/set | Stratum cutoffs | BOX rate | Alerts | Observable stops | Precision | Recall | Wide early uncensored N / mean | Wide stratum uncensored N / mean |',
        '| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |']
    for name,m in combined.items():
        x=m['directional']['causal_stratum'];e=m['directional']['wide_early_uncensored'];s=m['directional']['wide_stratum_uncensored']
        lines.append(f"| {name} | {x['valid_cutoffs']} | {fmt(x['box_rate'],True)} | {x['alerts']} | {x['observable_team_stops']} | {fmt(x['precision'],True)} | {fmt(x['recall'],True)} | {e['n']} / {fmt(e['mean_laps'])} | {s['n']} / {fmt(s['mean_laps'])} |")
    lines+=['','Primary timing is tolerance-truncated. The fixed +/-10 diagnostic remains subject to unmatched events and censoring; '
        'it does not assign arbitrary far-away alerts to teams. Adjacent cutoffs and driver/race events are correlated; '
        'no independent-trial significance claim. Empty denominators are NA.', '',
        '## Saved evidence','',
        'Full unmodified projection outputs are compressed in each race `raw_calls.jsonl.gz`; `calls.jsonl` preserves causal audit fields, '
        'candidate means and call summaries. `matching_audit.json` contains episodes, outcome-only stop labels and every 0/1/10-lap match/unmatched index. '
        '`metrics.json` includes scheduled-distance thirds, per-phase timing, censoring and equal-race timing summaries. '
        'Per-race manifests seal input/output hashes and snapshot exclusions. See [benchmark.json](benchmark.json), '
        '[metrics.json](metrics.json), [manifest.json](manifest.json) and the [protocol](../AGREEMENT_PLAN.md).']
    (ROOT/'REPORT.md').write_text('\n'.join(lines)+'\n')
if __name__=='__main__':run()
