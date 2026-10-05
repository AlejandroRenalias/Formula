/* Saved records only. Outcome fetches exist solely in the explicit Reveal handler. */
(() => {
  'use strict';
  const $ = id => document.getElementById(id);
  const config = JSON.parse($('historical-config').textContent);
  const base = new URL(config.base, document.baseURI.startsWith('http') ? document.baseURI : document.referrer);
  const url = path => new URL(path, base).href;
  const text = (id, value) => { $(id).textContent = value; };
  const action = call => call === 'BOX_NOW' ? 'BOX' : 'STAY';
  const colours = {Mercedes:'#27f4d2', Ferrari:'#e80020', McLaren:'#ff8000', 'Red Bull Racing':'#3671c6', Alpine:'#0093cc', 'Aston Martin':'#229971'};
  const compound = c => ({HARD:'hard tyres', MEDIUM:'medium tyres', SOFT:'soft tyres', WET:'wet tyres', INTERMEDIATE:'intermediates'}[c] || 'an unknown compound');
  const notes = {'5-14':'Early-race finish projections have large errors. Shorter-horizon green predictions performed better in evaluation.', '15-29':'Finish projections remain uncertain, especially across stops.', '30+':'Shorter remaining distance; pit-transition and compound limitations still apply.', non_green_uncertain:'Neutralisation duration is uncertain; green-only scores do not validate this state.'};
  const tagWords = {neutralisation:'Safety car or VSC around the stop', undercut_cover:'A nearby car stopped within two laps (possible undercut or cover)', compound_outside_candidates:"The team fitted a compound Formula didn't consider", strategy_count:'Different number of stops', late_race:'Formula preferred running to the flag', none_of_the_above:'None of the observable tags'};
  let catalog, record, choice, locked = false, revealed = false, token = 0, controller;
  const emptyTally = () => ({you:0, formula:0, total:0, seen:{}});
  const emptySession = () => ({schema_version:2, modes:{user_first:emptyTally(),formula_first:emptyTally()}});
  const orderKey = () => $('h-show-first').checked ? 'formula_first' : 'user_first';
  const orderLabel = key => key === 'formula_first' ? 'Formula first' : 'Your call first';
  let tally=emptySession();
  try {
    const saved=JSON.parse(sessionStorage.getItem('formula-history-tally'));
    if (saved?.schema_version===2) tally=saved;
    // All previous playback attempts showed Formula first. Never merge them
    // with blind choices when migrating the browser-local session tally.
    else if (saved?.seen) tally.modes.formula_first=saved;
  } catch { /* Start a memory-only session when storage is unavailable. */ }
  $('h-show-first').checked=false;
  function showTally() {
    const key=orderKey(), current=tally.modes[key], other=key==='user_first'?'formula_first':'user_first', previous=tally.modes[other];
    text('h-tally', `${orderLabel(key)} · You agreed with the team ${current.you} of ${current.total}; Formula ${current.formula} of ${current.total}`);
    text('h-other-tally', `${orderLabel(other)}: You ${previous.you} of ${previous.total}; Formula ${previous.formula} of ${previous.total}. Display orders are counted separately.`);
    try { sessionStorage.setItem('formula-history-tally', JSON.stringify(tally)); } catch { /* Memory-only tally if storage is unavailable. */ }
  }
  function state(name) { $('historical-workspace').dataset.state = name; }
  function clear() {
    token++; controller?.abort(); controller = new AbortController();
    record = null; choice = null; locked = false; revealed = false;
    $('h-call-content').hidden = true; $('h-revealed').hidden = true;
    $('h-revealed').replaceChildren(); $('h-next-step').hidden = true;
    $('h-model-details').replaceChildren(); text('h-call','BOX or STAY?');
    $('h-model-summary').replaceChildren();
    text('h-next-prompt','');
    text('h-message',''); text('h-lock-status','');
    $('h-lock').disabled = true; $('h-reveal').disabled = true;
    for (const id of ['h-box','h-stay']) { $(id).disabled = false; $(id).setAttribute('aria-pressed','false'); }
    state('choosing');
  }
  const race = () => catalog.races.find(r => r.key === $('h-race').value);
  function drivers() {
    $('h-driver').replaceChildren(...race().drivers.map(d => new Option(`${d.abbreviation} · ${d.team}`,d.number)));
    $('h-lap').max = race().scheduled_laps - 5;
    $('h-lap').value = Math.min(Math.max(Number($('h-lap').value)||5,5),race().scheduled_laps-5);
    navigation();
  }
  function navigation() {
    const lap=Number($('h-lap').value);
    $('h-prev-lap').disabled=lap<=5;
    $('h-next-lap').disabled=lap>=race().scheduled_laps-5;
  }
  function nearby(r) {
    return {
      ahead:r.field.filter(c=>c.gap_to_subject_s>0).sort((a,b)=>a.gap_to_subject_s-b.gap_to_subject_s).slice(0,3),
      behind:r.field.filter(c=>c.gap_to_subject_s<0).sort((a,b)=>b.gap_to_subject_s-a.gap_to_subject_s).slice(0,3)
    };
  }
  function plan(p, lap) {
    const stops = p.policy.dry_stops;
    if (!stops.length) return 'Stay out to the finish.';
    return stops.map((s,i) => `${i ? 'then ' : s.lap === lap ? 'Box now for ' : 'Stay out, then '}${i || s.lap !== lap ? compound(s.compound)+' after lap '+s.lap : compound(s.compound)}`).join(', ') + '.';
  }
  function svgNode(name, attrs, value) {
    const n = document.createElementNS('http://www.w3.org/2000/svg',name);
    for (const [k,v] of Object.entries(attrs)) n.setAttribute(k,String(v));
    if (value !== undefined) n.textContent = value;
    return n;
  }
  function field(r) {
    return [{...r.subject,tyre_age_laps:r.subject.stint_length_laps,gap_to_subject_s:0},...r.field].sort((a,b)=>a.position-b.position);
  }
  function drawMap(track,r) {
    const svg = $('h-map'); svg.replaceChildren();
    // Pre-race shape, causal pace scale; subject at the line, signed causal gaps.
    const duration = r.subject.last_lap_time_s || track.reference_lap_time_s;
    const scaled = {...track, reference_lap_time_s:duration, time_profile:track.time_profile.map(p=>({...p,time_s:p.time_s*duration/track.reference_lap_time_s}))};
    const xy = p => [330+p.x*350,210-p.y*350];
    svg.append(svgNode('path',{d:track.polyline.map((p,i)=>`${i?'L':'M'}${xy(p).join(',')}`).join(' ')+' Z',fill:'none',stroke:'#536779','stroke-width':7}));
    const labels=[], neighbours=nearby(r);
    const labelled=new Set([r.subject.driver,...neighbours.ahead.map(c=>c.driver),...neighbours.behind.map(c=>c.driver)]);
    for (const car of field(r)) {
      const [x,y] = xy(FormulaCircuit.position(scaled,0,-car.gap_to_subject_s));
      const colour = colours[car.team] || '#aebcc5';
      const dot=svgNode('circle',{cx:x,cy:y,r:car.driver===r.subject.driver?8:5,fill:colour,stroke:'#0d1e32','stroke-width':2,'data-driver':car.driver});
      dot.append(svgNode('title',{},`${car.driver} · ${car.team}`));svg.append(dot);
      if (!labelled.has(car.driver)) continue;
      let lx=x+12,ly=y-8;
      for (let offset=0;offset<160;offset+=18) {
        ly=y-8-offset;
        if (!labels.some(p=>Math.abs(p.x-lx)<34 && Math.abs(p.y-ly)<16)) break;
      }
      labels.push({x:lx,y:ly});
      if (Math.abs(ly-y)>18) svg.append(svgNode('path',{d:`M${x},${y} L${lx-3},${ly-3}`,fill:'none',stroke:colour,'stroke-width':.6,opacity:.5}));
      svg.append(svgNode('text',{x:lx,y:ly,fill:colour,'font-size':13,'paint-order':'stroke',stroke:'#0d1e32','stroke-width':3},car.driver));
    }
  }
  function renderModel(r) {
    // Construct the model DOM only after Lock, unless explicitly opted in.
    const details=$('h-model-details');details.replaceChildren();
    const summary=$('h-model-summary');summary.replaceChildren();
    text('h-call',action(r.call));
    const margin=document.createElement('div');margin.className='margin';margin.id='h-margin';
    const value=document.createElement('span'),context=document.createElement('span');
    value.className='margin-value';value.textContent=`+${r.margin_s.toFixed(1)} s`;
    context.className='margin-context';context.textContent=`${action(r.call)} advantage`;
    margin.append(value,context);summary.append(margin);
    const expected=paragraph('Expected over all samples');expected.className='small muted';summary.append(expected);
    const why=document.createElement('div');why.className='why';
    const preference=r.reliability.model_preference.replaceAll('_',' ');
    const rows=[
      ['h-preference',preference[0].toUpperCase()+preference.slice(1)],
      ['h-confidence',`STAY clearly better ${(r.confidence.stay_clearly_better*100).toFixed(1)}% · BOX clearly better ${(r.confidence.box_clearly_better*100).toFixed(1)}% · Too close ${(r.confidence.too_close_to_call*100).toFixed(1)}%`],
      ['h-reliability','Experimental model. Timing agreement is limited; confidence is model agreement, not accuracy. '+notes[r.reliability.phase_note]],
      ['h-best-box','Best BOX: '+plan(r.best_box,r.lap)],['h-best-stay','Best STAY: '+plan(r.best_stay,r.lap)],
      ['h-finish',`Stay-to-finish option: ${r.stay_to_finish_available?'available':'not finish-legal'}.`]
    ];
    for (const [id,value] of rows) { const p=paragraph(value);p.id=id;why.append(p); }
    details.append(why);
  }
  function render(r) {
    $('historical-workspace').style.setProperty('--team-colour',colours[r.subject.team] || '#aebcc5');
    text('h-driver-chip',`${r.subject.driver} / ${r.subject.team}`);
    text('h-lap-current',r.lap); text('h-lap-total',r.scheduled_laps);
    text('h-race-name',race().name);text('h-call','BOX or STAY?');
    const nearest=nearby(r), ahead=nearest.ahead[0], behind=nearest.behind[0];
    text('h-situation',`Position ${r.subject.position} · ${ahead?`${ahead.driver} ${ahead.gap_to_subject_s.toFixed(1)} s ahead`:'No archived car ahead'} · ${behind?`${behind.driver} ${Math.abs(behind.gap_to_subject_s).toFixed(1)} s behind`:'No archived car behind'}`);
    text('h-instruction',$('h-show-first').checked?'Make your call, then lock before revealing the team.':"Make your call, then lock to see Formula's.");
    if ($('h-show-first').checked) renderModel(r);
    const tyreColour = {SOFT:'#e85656',MEDIUM:'#e4c748',HARD:'#eef1f3',INTERMEDIATE:'#48a269',WET:'#4f9dda'}[r.subject.current_compound] || '#aebcc5';
    $('h-tyre-ring').replaceChildren(svgNode('circle',{cx:50,cy:50,r:39,fill:'none',stroke:tyreColour,'stroke-width':8}),svgNode('text',{x:50,y:58,'text-anchor':'middle',fill:tyreColour,'font-size':24},r.subject.current_compound[0]));
    text('h-tyre-age',`${r.subject.stint_length_laps} laps old`);
    $('h-field').replaceChildren(...field(r).map(c => {
      const tr = document.createElement('tr');
      for (const value of [c.position,c.driver,c.gap_to_subject_s===0?'Subject':`${c.gap_to_subject_s>0?'+':''}${c.gap_to_subject_s.toFixed(1)} s`,`${c.current_compound[0]} / ${c.tyre_age_laps}`]) { const td=document.createElement('td');td.textContent=value;tr.append(td); }
      return tr;
    }));
    text('h-field-note',`Signed gaps relative to ${r.subject.driver}: positive ahead. ${r.field_count} cars archived${r.field_complete?'':'; some rivals unavailable'}.`);
    text('h-version',`Calls: ${r.engine.tag} · ${r.engine.prediction_profile}`);
  }
  async function showCall() {
    clear(); const current = token;
    if (!catalog) return;
    navigation();
    const lap = Number($('h-lap').value);
    if (!Number.isInteger(lap) || lap<5 || lap>race().scheduled_laps-5) { text('h-message','Choose a lap in the permitted range.'); return; }
    const path = `${race().key}/${$('h-driver').value}/${lap}.json`;
    text('h-message','Loading archived decision…');
    try {
      const response = await fetch(url('historical/causal/'+path),{signal:controller.signal});
      if (!response.ok) throw new Error('unavailable');
      const r = await response.json();
      if (token!==current) return;
      const geometry = await fetch(url(`tracks/${race().circuit}.json`),{signal:controller.signal});
      if (!geometry.ok) throw new Error('geometry');
      const track = await geometry.json();
      if (token!==current) return;
      record=r; render(r); drawMap(track,r); text('h-message','');
      $('h-call-content').hidden=false; state($('h-show-first').checked?'call-shown':'situation-shown');
    } catch (e) { if (token===current && e.name!=='AbortError') text('h-message',e.message==='geometry'?'Track asset unavailable.':'No archived decision at this cutoff'); }
  }
  function choose(value) {
    if (!record || locked) return;
    choice=value; $('h-lock').disabled=false;
    $('h-box').setAttribute('aria-pressed',String(value==='BOX')); $('h-stay').setAttribute('aria-pressed',String(value==='STAY'));
  }
  function paragraph(value) { const p=document.createElement('p');p.textContent=value;return p; }
  const stopTyre = c => ({HARD:'hards',MEDIUM:'mediums',SOFT:'softs',WET:'wets',INTERMEDIATE:'intermediates'}[c] || 'an unknown compound');
  function nextStop(next) {
    if (!next) return 'No further stop';
    const n=next.laps_from_cutoff;
    if (n===1) return `The team boxes next lap, for ${stopTyre(next.compound)}`;
    if (n>1) return `The team boxes in ${n} laps, for ${stopTyre(next.compound)}`;
    if (n===0) return `The team boxes this lap, for ${stopTyre(next.compound)}`;
    return `The team's next pit entry follows the boundary ${Math.abs(n)} lap${n===-1?'':'s'} earlier, for ${stopTyre(next.compound)}`;
  }
  async function reveal() {
    if (!locked || !record || revealed || $('h-reveal').disabled) return;
    const current=token, r=record, picked=choice, order=orderKey();
    $('h-reveal').disabled=true;
    try {
      const response=await fetch(url(`historical/outcomes/${r.race_key}/${r.driver_number}/${r.lap}.json`),{signal:controller.signal});
      if (!response.ok) throw new Error('Outcome unavailable');
      const o=await response.json();
      if (token!==current) return;
      if (o.id!==r.id || o.schema_version!==2) throw new Error('Outcome record mismatch');
      const panel=$('h-revealed'); panel.replaceChildren();
      const heading=document.createElement('h2'); heading.textContent='This lap';panel.append(heading);
      const comparison=document.createElement('table');comparison.className='history-comparison';comparison.setAttribute('aria-label','This lap comparison');
      const body=document.createElement('tbody');
      for (const [name,value,agrees] of [['Team',o.team_action_this_lap,true],['Formula',action(r.call),o.formula_agrees_with_team],['You',picked,picked===o.team_action_this_lap]]) {
        const row=document.createElement('tr'),label=document.createElement('th'),call=document.createElement('td'),mark=document.createElement('td');
        label.scope='row';label.textContent=name;call.textContent=value;
        mark.textContent=name==='Team'?'— Reference':agrees?'✓ Agree':'✕ Disagree';
        mark.className=name==='Team'?'muted':agrees?'agreement':'disagreement';
        row.append(label,call,mark);body.append(row);
      }
      comparison.append(body);panel.append(comparison);
      if (o.team_stop_this_lap) panel.append(paragraph(`Box after lap ${o.team_stop_this_lap.boundary_lap} for ${compound(o.team_stop_this_lap.compound)}.`));
      const next=o.next_team_stop;
      panel.append(paragraph(nextStop(next)));
      if (o.near_miss && o.near_miss_stop) panel.append(paragraph(`Close: the team boxed one lap ${o.near_miss_stop.boundary_lap>r.lap?'later':'earlier'}.`));
      if (!o.formula_agrees_with_team || o.near_miss) {
        const why=document.createElement('h3');why.textContent='Why Formula might have missed it';panel.append(why);
        if (!o.stop_disagreement_tags.length) panel.append(paragraph('Not enough data: no unmatched-stop classification.'));
        for (const event of o.stop_disagreement_tags) {
        panel.append(paragraph(`Tags for stop after lap ${o.team_stop.boundary_lap}:`));
        for (const [tag,value] of Object.entries(event.tags)) {
          if (value===true) panel.append(paragraph(tagWords[tag] || tag.replaceAll('_',' ')));
          else if (value===null || event.unknown_tags.includes(tag)) panel.append(paragraph((tagWords[tag] || tag.replaceAll('_',' '))+': not enough data'));
        }
        }
      }
      panel.append(paragraph('Agreement describes the timing choice, not who was right. Accepted ±1 episode matching is a separate evaluation.'));
      const link=document.createElement('a');link.href=url('historical/methodology.html');link.textContent='Methodology and evaluation reports ↗';link.target='_blank';link.rel='noopener';panel.append(link);
      revealed=true; panel.hidden=false; $('h-next-step').hidden=false; state('revealed');
      text('h-next-prompt',next?.laps_from_cutoff===1?'The team boxes next lap. Can you call it?':'');
      $('h-next').disabled=r.lap>=race().scheduled_laps-5;
      const bucket=tally.modes[order];
      if (!bucket.seen[r.id]) { bucket.total++;bucket.you+=Number(picked===o.team_action_this_lap);bucket.formula+=Number(o.formula_agrees_with_team);bucket.seen[r.id]=true;showTally(); }
    } catch (e) { if (token===current && e.name!=='AbortError') { text('h-message',e.message);$('h-reveal').disabled=false; } }
  }
  $('h-show').onclick=showCall;
  $('h-race').onchange=()=>{clear();drivers();}; $('h-driver').onchange=clear; $('h-lap').oninput=showCall;
  $('h-prev-lap').onclick=()=>{if (Number($('h-lap').value)>5){$('h-lap').value=Number($('h-lap').value)-1;showCall();}};
  $('h-next-lap').onclick=()=>{if (Number($('h-lap').value)<race().scheduled_laps-5){$('h-lap').value=Number($('h-lap').value)+1;showCall();}};
  $('h-show-first').onchange=()=>{showTally();if(record)showCall();else clear();};
  $('h-box').onclick=()=>choose('BOX');$('h-stay').onclick=()=>choose('STAY');
  $('h-lock').onclick=()=> { if (!record || !choice || locked) return; locked=true;$('h-box').disabled=true;$('h-stay').disabled=true;$('h-lock').disabled=true;$('h-reveal').disabled=false;text('h-lock-status',`Your call locked: ${choice}`);renderModel(record);text('h-instruction','Your choice is locked. Reveal what the team did.');state('call-locked'); };
  $('h-reveal').onclick=reveal;
  $('h-next').onclick=()=> { if (!revealed) return; if (Number($('h-lap').value)<race().scheduled_laps-5) { $('h-lap').value=Number($('h-lap').value)+1;showCall(); } else { clear();text('h-message','End of archive range.'); } };
  $('h-reset-tally').onclick=()=>{tally=emptySession();showTally();clear();};
  async function mode(historical) {
    $('workspace').hidden=historical;$('error').hidden=historical || !$('error').textContent;$('historical-workspace').hidden=!historical;
    $('mode-synthetic').setAttribute('aria-pressed',String(!historical));$('mode-historical').setAttribute('aria-pressed',String(historical));
    if (!historical) { clear();return; }
    if (!catalog) {
      try {
        const response=await fetch(url('historical/catalog.json'));if (!response.ok) throw new Error();catalog=await response.json();
        $('h-race').replaceChildren(...catalog.races.map(r=>new Option(r.name,r.key)));text('h-archive-note',catalog.selector_label);drivers();
      } catch { text('h-message','Archive unavailable.'); }
    }
  }
  $('mode-synthetic').onclick=()=>mode(false);$('mode-historical').onclick=()=>mode(true);
  showTally();state('choosing');
})();
