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
    let svg = `<defs><filter id="rain-soft" x="-100%" y="-100%" width="300%" height="300%"><feGaussianBlur stdDeviation="17"/></filter><pattern id="chequer" width="8" height="8" patternUnits="userSpaceOnUse"><rect width="8" height="8" fill="var(--paper)"/><path d="M0 0h4v4H0zM4 4h4v4H4z" fill="var(--ink)"/></pattern></defs>`;
    svg += `<path class="rain-cell" d="${line(rainPoints)}"/><path class="circuit-track" d="${line(track.polyline.map(xy))}"/><path class="pit-distance-glow" d="${line(highlight)}"/><path class="pit-distance" d="${line(highlight)}"/>`;
    const labels = [];
    const addLabel = (p,text,colour='var(--muted)',kind='marker') => labels.push({...p,text,colour,kind});
    const start = pointAt(track.start_finish.distance_m);
    svg += `<rect x="${start.x-7}" y="${start.y-7}" width="14" height="14" fill="url(#chequer)" stroke="var(--ink)" stroke-width=".7"/>`;
    addLabel(start,display.marker_labels.start_finish);
    track.sectors.forEach((sector,i) => {
      const distance = sector.end_distance_m % track.lap_length_m;
      const p = pointAt(distance), before = pointAt((distance-10+track.lap_length_m)%track.lap_length_m), after = pointAt((distance+10)%track.lap_length_m);
      const dx = after.x-before.x, dy = after.y-before.y, length = Math.hypot(dx,dy);
      svg += `<path class="sector-tick" d="M${p.x-dy/length*9} ${p.y+dx/length*9}L${p.x+dy/length*9} ${p.y-dx/length*9}"/>`;
      addLabel(p,display.sector_labels[i]);
    });
    ['pit_entry','pit_exit'].forEach(key => {
      const p=pointAt(track[key].distance_m);
      svg += `<path class="pit-marker" d="M${p.x} ${p.y-5}l5 5-5 5-5-5z"/>`;
      addLabel(p,display.marker_labels[key]);
    });
    track.cars.forEach(car => {
      const p = xy(car), selected = car.driver === display.selected_driver;
      if (selected) svg += `<circle class="selected-ring" cx="${p.x}" cy="${p.y}" r="12" stroke="${escape(car.team_colour)}"/>`;
      svg += `<circle class="car-dot" data-driver="${escape(car.driver)}" cx="${p.x}" cy="${p.y}" r="${selected?7:5}" fill="${escape(car.team_colour)}"/>`;
      addLabel(p,car.driver,car.team_colour,'car');
    });
    const g = xy(ghost);
    svg += `<circle id="ghost-dot" class="ghost-ring" data-distance="${ghost.distance_m}" data-position="${ghost.position}" cx="${g.x}" cy="${g.y}" r="12" stroke="${escape(display.selected_colour)}"/>`;
    addLabel(g,display.selected_driver+' · BOX',display.selected_colour,'ghost');
    // Dedicated side rails, packed in Y order: label boxes never overlap.
    for (const left of [true,false]) {
      const rail = labels.filter(p => (p.x<330) === left).sort((a,b) => a.y-b.y);
      let previous=30;
      rail.forEach(p => { p.labelY=Math.max(previous+29,Math.min(370,p.y)); previous=p.labelY; });
      for (let i=rail.length-1;i>=0;i--) rail[i].labelY=Math.min(rail[i].labelY,370-(rail.length-1-i)*29);
      rail.forEach(p => {
        const mobile = window.matchMedia('(max-width:450px)').matches;
        const width = p.text.length * (mobile ? 12 : 8.4);
        const anchor=left?Math.max(width+12,Math.min(300,p.x-25)):Math.min(648-width,Math.max(360,p.x+25));
        const elbow=left?anchor+8:anchor-8;
        svg += `<path class="map-leader" d="M${p.x} ${p.y}L${elbow} ${p.labelY}"/><text data-map-label="${p.kind}" class="map-label" x="${anchor}" y="${p.labelY+4}" text-anchor="${left?'end':'start'}" fill="${escape(p.colour)}">${escape(p.text)}</text>`;
      });
    }
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
    const chart = data.chart, scenario = chart.scenarios.find(s => s.id === example);
    const x = lap => 50 + lap / chart.finish * 735;
    const y = gain => 275 - (gain - chart.low) / (chart.high - chart.low) * 235;
    const path = points => points.map((p, i) => `${i ? 'L' : 'M'}${x(p.lap)},${y(p.gain_s)}`).join(' ');
    let svg = chart.y_ticks.map(v => `<path class="grid" d="M50 ${y(v)}H785"/><text class="chart-text axis-label" x="38" y="${y(v)+4}" text-anchor="end">${escape(v)}</text>`).join('');
    svg += chart.x_ticks.map(v => `<text class="chart-text axis-label" x="${x(v)}" y="299" text-anchor="middle">${escape(v)}</text>`).join('');
    svg += `<path d="M${x(chart.cutoff)} 25V280" stroke="var(--muted)" stroke-dasharray="3 5"/><text class="chart-text axis-label" x="50" y="18">Observed</text><text class="chart-text axis-label" x="${x(chart.cutoff)+12}" y="18">Projected examples →</text><path class="observed" d="${path(chart.observed)}"/><circle cx="${x(chart.cutoff)}" cy="${y(0)}" r="4" fill="var(--accent)"/>`;
    const ends = {};
    scenario.plans.forEach((plan, index) => {
      const stay = plan.call === 'STAY OUT';
      const cls = stay ? 'stay-line' : 'box-line';
      const points = plan.laps.map((lap, i) => ({lap, gain_s: plan.gain_s[i]}));
      svg += `<path data-policy="${escape(plan.policy_id)}" class="${cls}" d="${path(points)}"/>`;
      plan.stops.forEach(stop => {
        const i = plan.laps.indexOf(stop.charged_on_lap);
        svg += `<circle class="stop-dot" cx="${x(stop.charged_on_lap)}" cy="${y(plan.gain_s[i])}" r="4" stroke="${stay ? 'var(--accent)' : 'var(--ink)'}"><title>${escape(plan.call + ': ' + stop.label + ' after lap ' + stop.lap + ' · ' + stop.loss_s + ' s pit loss')}</title></circle>`;
      });
      ends[plan.call] = y(plan.gain_s[plan.gain_s.length - 1]);
      svg += `<text data-annotation class="chart-text ${stay ? 'accent-text' : ''}" x="50" y="${335 + index * 20}">${escape(plan.call + ' · ' + plan.stop_label)}</text>`;
    });
    const near = Math.abs(ends['STAY OUT'] - ends['BOX NOW']) < 22;
    svg += `<text class="chart-text direct accent-text" x="798" y="${ends['STAY OUT'] - (near ? 12 : 8)}">STAY OUT</text><text class="chart-text direct" x="798" y="${ends['BOX NOW'] + (near ? 16 : 15)}">BOX NOW</text>`;
    svg += `<path d="M785 ${ends['STAY OUT']}H920M785 ${ends['BOX NOW']}H920M910 ${ends['STAY OUT']}V${ends['BOX NOW']}" fill="none" stroke="var(--muted)"/><text class="chart-text" x="50" y="392">${escape(scenario.group_label + ' · expected margin: ' + scenario.margin_label)}</text>`;
    if (chart.flip_lap !== null) svg += `<path class="grid" d="M${x(chart.flip_lap)} 30V275"/><text data-annotation class="chart-text axis-label" x="590" y="335">${escape('Call flips after lap ' + chart.flip_lap)}</text>`;
    $('fork').innerHTML = svg;
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
    $('radio-lines').innerHTML = data.radio.map(r => `<details><summary><strong>${escape(r.role)}</strong><span>${escape(r.text)}</span><span class="vote">${escape(r.vote)}</span></summary><p>${escape('Legacy scorer candidate: ' + r.candidate + '. ' + r.text)}</p></details>`).join('');
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
