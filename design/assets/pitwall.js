/* All strategy values and copy are precomputed fixture display fields. */
(() => {
  'use strict';
  const $ = id => document.getElementById(id);
  const escape = value => String(value).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const table = (headers, rows) => `<div class="table-scroll"><table class="math-table"><thead><tr>${headers.map(h => `<th>${escape(h)}</th>`).join('')}</tr></thead><tbody>${rows.map(row => `<tr>${row.map(cell => `<td>${escape(cell)}</td>`).join('')}</tr>`).join('')}</tbody></table></div>`;
  const carIcon = colour => `<svg class="field-car" viewBox="0 0 64 32" aria-hidden="true" focusable="false" style="color:${escape(colour)}"><g class="car-tyres"><rect x="11" y="1" width="11" height="7" rx="2"/><rect x="11" y="24" width="11" height="7" rx="2"/><rect x="44" y="2" width="9" height="6" rx="2"/><rect x="44" y="24" width="9" height="6" rx="2"/></g><path class="car-suspension" d="M16 6v20M48 6v20"/><path fill="currentColor" d="M8 11h11l6-3h12l6 5 15 1v4l-15 1-6 5H25l-6-3H8z"/><rect fill="currentColor" x="4" y="6" width="5" height="20" rx="1"/><rect fill="currentColor" x="56" y="4" width="4" height="24" rx="1"/><path class="car-cockpit" d="M27 12h9l4 4-4 4h-9z"/></svg>`;
  let data, example, active = null, track;

  function drawMap(loss = track.ghost_rejoin.pit_loss_s) {
    const display = data.map, geometry = FormulaCircuit;
    const ghost = geometry.rejoin(track, loss);
    const radians = display.rotation_degrees * Math.PI / 180;
    const xy = p => ({x:330 + 480 * (p.x * Math.cos(radians) - p.y * Math.sin(radians)),
                      y:212 - 480 * (p.x * Math.sin(radians) + p.y * Math.cos(radians))});
    const pointAt = distance => xy({x:geometry.interpolate(distance,track.polyline,'distance_m','x'),
                                   y:geometry.interpolate(distance,track.polyline,'distance_m','y')});
    const line = points => points.map((p,i) => `${i?'L':'M'}${p.x},${p.y}`).join(' ');
    const sector = track.rain_overlay;
    const rainPoints = track.polyline.filter(p => p.distance_m > sector.start_distance_m && p.distance_m < sector.end_distance_m).map(xy);
    rainPoints.unshift(pointAt(sector.start_distance_m)); rainPoints.push(pointAt(sector.end_distance_m));
    const subject = track.cars.find(c => c.driver === display.selected_driver);
    const highlight = Array.from({length:81},(_,i) => xy(geometry.position(track,track.leader.distance_m,
      subject.gap_to_leader_s + loss * i/80)));
    const cloud=rainPoints.flatMap(p=>[{x:p.x-22,y:p.y-22},{x:p.x+22,y:p.y+22}]);
    const cross=(a,b,c)=>(b.x-a.x)*(c.y-a.y)-(b.y-a.y)*(c.x-a.x);
    const half=ps=>{const h=[];for(const p of ps){while(h.length>1&&cross(h[h.length-2],h[h.length-1],p)<=0)h.pop();h.push(p);}return h;};
    cloud.sort((a,b)=>a.x-b.x||a.y-b.y);
    const hull=half(cloud).slice(0,-1).concat(half([...cloud].reverse()).slice(0,-1));
    let svg = `<defs><pattern id="rain-hatch" width="9" height="9" patternUnits="userSpaceOnUse"><path d="M0 9L9 0" stroke="#74baff" stroke-opacity=".16"/></pattern><filter id="rain-soft" x="-100%" y="-100%" width="300%" height="300%"><feGaussianBlur stdDeviation="17"/></filter><pattern id="chequer" width="8" height="8" patternUnits="userSpaceOnUse"><rect width="8" height="8" fill="var(--paper)"/><path d="M0 0h4v4H0zM4 4h4v4H4z" fill="var(--ink)"/></pattern></defs>`;
    svg += `<path class="radar-cell" d="${line(hull)}Z"/><path fill="url(#rain-hatch)" d="${line(hull)}Z"/><path class="circuit-track" d="${line(track.polyline.map(xy))}"/><path class="pit-distance" d="${line(highlight)}"/>`;
    const labels = [], sectorLabelBoxes = [];
    const addLabel = (p,text,colour='var(--muted)',kind='marker') => labels.push({...p,text,colour,kind});
    const start = pointAt(track.start_finish.distance_m);
    svg += `<rect x="${start.x-7}" y="${start.y-7}" width="14" height="14" fill="url(#chequer)" stroke="var(--ink)" stroke-width=".7"/>`;

    track.sectors.forEach((sector,i) => {
      const distance = sector.end_distance_m % track.lap_length_m;
      const p = pointAt(distance), before = pointAt((distance-10+track.lap_length_m)%track.lap_length_m), after = pointAt((distance+10)%track.lap_length_m);
      const dx = after.x-before.x, dy = after.y-before.y, length = Math.hypot(dx,dy);
      svg += `<path class="sector-tick" d="M${p.x-dy/length*9} ${p.y+dx/length*9}L${p.x+dy/length*9} ${p.y-dx/length*9}"/>`;
      // S1 is moved along the sector to leave space for the rejoin label.
      const fraction=sector.sector===1?.85:.5;
      const mid=pointAt(sector.start_distance_m+(sector.end_distance_m-sector.start_distance_m)*fraction),angle=Math.atan2(mid.y-212,mid.x-330);
      sectorLabelBoxes.push({x:mid.x+23*Math.cos(angle)-15,y:mid.y+23*Math.sin(angle)-17,w:30,h:23});
      svg+=`<text class="sector-name" x="${mid.x+23*Math.cos(angle)}" y="${mid.y+23*Math.sin(angle)}" text-anchor="middle">${escape(display.sector_labels[i])}</text>`;
    });
    ['pit_entry','pit_exit'].forEach(key => {
      const p=pointAt(track[key].distance_m);
      svg += `<path class="pit-marker" d="M${p.x} ${p.y-5}l5 5-5 5-5-5z"/>`;

    });
    track.cars.forEach(car => {
      const p = xy(car), selected = car.driver === display.selected_driver;
      if (selected) svg += `<circle class="selected-ring" cx="${p.x}" cy="${p.y}" r="12" stroke="${escape(car.team_colour)}"/>`;
      svg += `<circle class="car-dot" data-driver="${escape(car.driver)}" cx="${p.x}" cy="${p.y}" r="${selected?7:5}" fill="${escape(car.team_colour)}"/>`;
      addLabel(p,car.driver,'var(--ink)','car');
    });
    const g = xy(ghost);
    svg += `<circle id="ghost-dot" class="ghost-ring" data-distance="${ghost.distance_m}" data-position="${ghost.position}" cx="${g.x}" cy="${g.y}" r="12" stroke="var(--muted)"/>`;
    addLabel(g,display.ghost_template.replace('{position}',ghost.position),'var(--ink)','ghost');
    for(let i=0;i<14;i++){
      const d=(i+.5)*track.lap_length_m/14,p=pointAt(d),before=pointAt((d-18+track.lap_length_m)%track.lap_length_m),after=pointAt((d+18)%track.lap_length_m);
      if(labels.some(l=>Math.hypot(l.x-p.x,l.y-p.y)<25))continue;
      const angle=Math.atan2(after.y-before.y,after.x-before.x)*180/Math.PI;
      svg+=`<path class="travel-chevron" d="M-4-4L1 0-4 4" transform="translate(${p.x} ${p.y}) rotate(${angle})"/>`;
    }
    const mobile=window.matchMedia('(max-width:450px)').matches, font=mobile?18:14;
    const rainEdge=hull.reduce((a,b)=>b.y<a.y?b:a),rainWidth=display.rain_label.length*(mobile?18:12)*.62;
    const rainX=Math.max(rainWidth/2+8,Math.min(652-rainWidth/2,rainEdge.x));
    const rainY=rainEdge.y-16;
    svg+=`<path class="rain-label-link" d="M${rainEdge.x} ${rainEdge.y}L${rainX} ${rainY+5}"/><text class="radar-label" x="${rainX}" y="${rainY}" text-anchor="middle">${escape(display.rain_label)}</text>`;
    const occupied=[...sectorLabelBoxes,{x:rainX-rainWidth/2,y:rainY-(mobile?18:12),w:rainWidth,h:(mobile?18:12)+5}];
    const overlaps=(a,b)=>a.x<b.x+b.w&&a.x+a.w>b.x&&a.y<b.y+b.h&&a.y+a.h>b.y;
    labels.forEach(p=>{
      const w=p.text.length*font*.62,h=font+5;
      const options=[{x:p.x+18,y:p.y-h/2},{x:p.x-18-w,y:p.y-h/2},{x:p.x-w/2,y:p.y-18-h},{x:p.x-w/2,y:p.y+18},{x:p.x+18,y:p.y+12},{x:p.x-18-w,y:p.y+12}];
      const blocked=r=>occupied.some(o=>overlaps(r,o))||labels.some(o=>o!==p&&overlaps(r,{x:o.x-14,y:o.y-14,w:28,h:28}));
      const rect=options.find(r=>r.x>8&&r.x+w<652&&r.y>40&&r.y+h<410&&!blocked({...r,w,h}))||options[3];
      occupied.push({...rect,w,h});
      svg+=`<text data-map-label="${p.kind}" class="map-label" style="font-size:${font}px" x="${rect.x}" y="${rect.y+font}" fill="${escape(p.colour)}">${escape(p.text)}</text>`;
    });
    const label = ghost.car_ahead ? display.rejoin_template.replace('{position}',ghost.position).replace('{gap}',ghost.gap_to_car_ahead_s.toFixed(1)).replace('{ahead}',ghost.car_ahead)
      : display.clear_rejoin_template.replace('{position}',ghost.position);
    $('circuit').innerHTML=svg;
    $('circuit').setAttribute('aria-label',display.aria_prefix + display.position_summary + '. ' + label + '. ' + display.rain_label);
    $('rejoin-label').textContent=label;
    $('rain-label').textContent=display.rain_label;
  }

  function showView(view) {
    for (const id of ['call','margin','reason','confidence','flip','plan','chief']) $(id).textContent = view[id];
    $('chief-vote').textContent = view.call;
    $('share-items').innerHTML = view.shares.map(s => `<div><div class="share-value">${escape(s.value)}</div><div class="share-label">${escape(s.name)}</div><div class="share-strip"><span style="width:${s.fraction * 100}%"></span></div></div>`).join('');
    $('chart-wrap').classList.toggle('dim', active !== null);
    $('chart-warning').hidden = active === null;
  }

  function drawChart() {
    const chart=data.chart,scenario=chart.scenarios.find(s=>s.id===example);
    const x=lap=>50+(lap-chart.window_start)/(chart.window_end-chart.window_start)*650;
    const y=gain=>275-(gain-scenario.low)/(scenario.high-scenario.low)*235;
    const visible=points=>points.filter(p=>p.lap>=chart.window_start&&p.lap<=chart.window_end);
    const path=points=>visible(points).map((p,i)=>`${i?'L':'M'}${x(p.lap)},${y(p.gain_s)}`).join(' ');
    let svg=scenario.y_ticks.map(v=>`<path class="grid" d="M50 ${y(v)}H700"/><text class="chart-text axis-label" x="38" y="${y(v)+4}" text-anchor="end">${escape(v)}</text>`).join('');
    svg+=chart.window_ticks.map(v=>`<text class="chart-text axis-label" x="${x(v)}" y="299" text-anchor="middle">${escape(v)}</text>`).join('');
    if(scenario.rain_lap!==null)svg+=`<rect class="rain-arrival" x="${x(scenario.rain_lap-.25)}" y="35" width="${x(scenario.rain_lap+.25)-x(scenario.rain_lap-.25)}" height="240"/><text class="chart-text rain-chart-label" x="${x(scenario.rain_lap)+8}" y="52">${escape(scenario.rain_label)}</text>`;
    svg+=`<path d="M${x(chart.cutoff)} 25V280" stroke="var(--muted)" stroke-dasharray="3 5"/><text class="chart-text axis-label" x="50" y="18">Observed</text><text class="chart-text axis-label" x="${x(chart.cutoff)+12}" y="18">Projected examples →</text><path class="observed" d="${path(chart.observed)}"/>`;
    const ends=[];
    scenario.plans.forEach((plan,index)=>{
      const recommended=plan.call===data.base.call,cls=recommended?'stay-line':'box-line';
      const points=plan.laps.map((lap,i)=>({lap,gain_s:plan.gain_s[i]}));
      svg+=`<path data-policy="${escape(plan.policy_id)}" class="${cls}" d="${path(points)}"/>`;
      plan.stops.filter(stop=>stop.charged_on_lap>=chart.window_start&&stop.charged_on_lap<=chart.window_end).forEach(stop=>{
        const i=plan.laps.indexOf(stop.charged_on_lap);
        svg+=`<circle class="stop-dot" cx="${x(stop.charged_on_lap)}" cy="${y(plan.gain_s[i])}" r="4" stroke="${recommended?'var(--accent)':'var(--ink)'}"><title>${escape(plan.call+': '+stop.label+' after lap '+stop.lap+' · '+stop.loss_s+' s pit loss')}</title></circle>`;
      });
      ends.push({call:plan.call,y:y(visible(points).at(-1).gain_s),recommended});
      svg+=`<text data-annotation class="chart-text ${recommended?'accent-text':''}" x="50" y="${335+index*20}">${escape(plan.call+' · '+plan.stop_label)}</text>`;
    });
    ends.sort((a,b)=>a.y-b.y).forEach((p,i,all)=>{
      const near=all.length>1&&Math.abs(all[0].y-all[1].y)<22;
      svg+=`<text class="chart-text direct ${p.recommended?'accent-text':''}" x="712" y="${p.y+(near?(i?16:-8):4)}">${escape(p.call)}</text>`;
    });
    const box=185,stay=box-scenario.finish_margin_s/chart.finish_scale_s*75;
    svg+=`<path class="flag-divider" d="M815 30V275"/><text class="chart-text direct" x="845" y="50">${escape(chart.flag_label)}</text><text class="chart-text axis-label" x="845" y="68">${escape(chart.flag_lap_label)}</text><path class="flag-bracket" d="M845 ${stay}H975M845 ${box}H975M968 ${stay}V${box}"/><text class="chart-text ${data.base.call==='STAY OUT'?'accent-text':''}" x="845" y="${Math.min(stay,box)-10}">STAY OUT</text><text class="chart-text" x="845" y="${Math.max(stay,box)+20}">BOX NOW</text><text class="chart-text direct" x="845" y="245">${escape(scenario.finish_margin_label)}</text><text class="chart-text axis-label" x="845" y="265">${escape(scenario.finish_range_label)}</text><text class="chart-text axis-label" x="845" y="288">Expected · p10–p90</text>`;
    if(chart.flip_lap!==null&&chart.flip_lap<=chart.window_end)svg+=`<text data-annotation class="chart-text axis-label" x="50" y="392">${escape('Call flips after lap '+chart.flip_lap)}</text>`;
    $('fork').innerHTML=svg;
  }

  function sliderChanged(sweep, index) {
    const offBase = index !== sweep.base_index;
    active = offBase ? sweep.assumption : null;
    data.sweeps.forEach(other => {
      const chosen = other.assumption === sweep.assumption ? index : other.base_index;
      const input = document.querySelector(`input[data-assumption="${other.assumption}"]`);
      if (input) { input.value = chosen; $(other.assumption + '-value').textContent = other.points[chosen].label; }
    });
    showView(offBase ? sweep.points[index].display : data.base);
    drawMap(sweep.assumption === 'pit_loss_s' ? sweep.points[index].value : track.ghost_rejoin.pit_loss_s);
  }

  function render(fixture) {
    data = fixture.ui.display;
    track = fixture.track;
    document.documentElement.style.setProperty('--accent',data.map.selected_colour);
    const download = document.querySelector('footer a[download]');
    download.href = URL.createObjectURL(new Blob([JSON.stringify(fixture, null, 2)], {type:'application/json'}));
    $('operating').textContent = data.operating;
    $('operating').style.setProperty('--team-colour',data.map.selected_colour);
    $('lap-current').textContent = data.lap_counter.current;
    $('lap-total').textContent = data.lap_counter.total;
    const tyre = data.current_tyre, circumference = 2*Math.PI*39;
    $('tyre-ring').innerHTML=`<circle class="tyre-base" cx="50" cy="50" r="39" stroke="${escape(tyre.colour)}"/><circle class="tyre-health" cx="50" cy="50" r="39" stroke="${escape(tyre.colour)}" stroke-dasharray="${circumference*tyre.health} ${circumference}" transform="rotate(-90 50 50)"/><text x="50" y="60" text-anchor="middle" fill="${escape(tyre.colour)}">${escape(tyre.letter)}</text>`;
    $('tyre-ring').setAttribute('aria-label',tyre.label+', '+tyre.health_label);
    $('tyre-age').textContent=tyre.label;
    $('circuit-title').textContent=data.map.name;
    $('map-note').textContent=data.map.map_note;
    $('tyres').textContent = data.tyres;
    showView(data.base);
    example = data.chart.scenarios[0].id;
    $('scenario-tabs').innerHTML = data.chart.scenarios.map(s => `<button data-example="${s.id}" aria-pressed="${s.id === example}">${escape(s.label)}<small>Example</small></button>`).join('');
    document.querySelectorAll('[data-example]').forEach(button => button.addEventListener('click', () => {
      example = button.dataset.example;
      document.querySelectorAll('[data-example]').forEach(b => b.setAttribute('aria-pressed', b === button));
      drawChart();
    }));
    const names = {rain_arrival_lap:'Rain arrival lap',pit_loss_s:'Pit loss',safety_car_lap:'Safety car onset'};
    const shown = data.sweeps.filter(s => Object.hasOwn(names, s.assumption));
    $('sliders').innerHTML = shown.map(s => `<div><label class="slider-label" for="${s.assumption}"><span>${names[s.assumption]}</span><output id="${s.assumption}-value">${escape(s.points[s.base_index].label)}</output></label><input id="${s.assumption}" data-assumption="${s.assumption}" type="range" min="0" max="${s.points.length-1}" value="${s.base_index}" step="1"><div class="slider-note">${escape(s.assumption === 'safety_car_lap' ? 'Simplified bunching model' : 'Precomputed points')}</div></div>`).join('');
    shown.forEach(s => $(s.assumption).addEventListener('input', event => sliderChanged(s, Number(event.target.value))));
    $('reset').addEventListener('click', () => sliderChanged(shown[0], shown[0].base_index));
    const colours = Object.fromEntries(track.cars.map(c => [c.team,c.team_colour]));
    $('field').innerHTML = data.field.map(d => `<tr class="${d.selected ? 'selected' : ''}"><td>${escape(d.position)}</td><td><div class="field-driver">${carIcon(colours[d.team] || '#b7c8d8')}<span><span class="driver-code">${escape(d.driver)}</span><span class="driver-team">${escape(d.team)}</span></span></div></td><td>${escape(d.gap)}</td><td><span class="tyre tyre-${escape(d.compound)}">${escape(d.compound[0])}</span></td></tr>`).join('');
    $('policy-table').innerHTML = table(['Policy','Expected remaining time / s','Stop budget','Status'],data.policy_rows.map(p => [p.policy,p.time,p.stops,p.status]));
    $('plan-margin').textContent = 'Plan margin: ' + data.plan_margin + ' between the two best policies overall.';
    $('policy-flips').innerHTML = data.policy_flips.map(p => `<details><summary>${escape(p.assumption.replaceAll('_',' '))}</summary><p>${escape(p.text)}</p></details>`).join('');
    $('sweep-tables').innerHTML = data.sweep_rows.map(s => `<details><summary>${escape(s.assumption.replaceAll('_',' '))} · ${escape(s.status)}</summary><p class="small muted">${escape(s.range)}</p>${table(['Value','Call','Expected call margin / s','Best policy'],s.rows.map(p => [p.value,p.call,p.margin,p.policy]))}</details>`).join('');
    $('rain-timing').textContent = data.rain_timing;
    $('assumption-tags').innerHTML = data.assumptions.map(a => `<div class="assumption"><strong><span class="tag">${escape(a.kind)}</span>${escape(a.name)}</strong><span>${escape(a.value)}</span></div>`).join('');
    $('factor-table').innerHTML = table(['Factor','Weighted points'],data.factor_rows.map(f => [f.factor,f.points]));
    $('radio-lines').innerHTML=data.radio.map(r=>`<div class="radio-line"><strong>${escape(r.role)}</strong><span>${escape(r.text)}</span><span class="vote">${escape(r.vote)}</span></div>`).join('');
    $('raw-radio').innerHTML=table(['Specialist','Vote','Candidate (internal)','Raw reasoning'],data.radio_raw.map(r=>[r.role,r.vote,r.candidate,r.text]));
    drawChart();
    drawMap();
    window.matchMedia('(max-width:450px)').addEventListener('change', () => {
      const sweep=data.sweeps.find(s=>s.assumption==='pit_loss_s');
      drawMap(active === 'pit_loss_s' ? sweep.points[Number($('pit_loss_s').value)].value : track.ghost_rejoin.pit_loss_s);
    });
    $('workspace').hidden = false;
  }

  async function start() {
    try {
      const embedded = document.getElementById('projection-fixture');
      const fixture = embedded ? JSON.parse(embedded.textContent) : await fetch('fixture.json',{cache:'no-store'}).then(response => {
        if (!response.ok) throw new Error('Fixture unavailable');
        return response.json();
      });
      render(fixture);
    } catch (error) { $('error').textContent = 'Could not load the projection fixture. ' + error.message; $('error').hidden = false; }
  }
  start();
})();
