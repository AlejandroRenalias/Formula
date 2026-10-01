/* All strategy values and copy are precomputed fixture display fields. */
(() => {
  'use strict';
  const $ = id => document.getElementById(id);
  const escape = value => String(value).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const table = (headers, rows) => `<div class="table-scroll"><table class="math-table"><thead><tr>${headers.map(h => `<th>${escape(h)}</th>`).join('')}</tr></thead><tbody>${rows.map(row => `<tr>${row.map(cell => `<td>${escape(cell)}</td>`).join('')}</tr>`).join('')}</tbody></table></div>`;
  let data, example, active = null;

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
  }

  function render(fixture) {
    data = fixture.ui.display;
    const download = document.querySelector('footer a[download]');
    download.href = URL.createObjectURL(new Blob([JSON.stringify(fixture, null, 2)], {type:'application/json'}));
    $('operating').textContent = data.operating;
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
    const colours = {McLaren:'#ff9b45','Red Bull':'#7d9cff',Mercedes:'#52dfce',Ferrari:'#ff6573'};
    $('field').innerHTML = data.field.map(d => `<tr class="${d.selected ? 'selected' : ''}"><td>${escape(d.position)}</td><td><span class="team-mark" style="--team-colour:${colours[d.team] || '#b7c8d8'}"></span><span class="driver-code">${escape(d.driver)}</span><span class="driver-team">${escape(d.team)}</span></td><td>${escape(d.gap)}</td><td><span class="tyre tyre-${escape(d.compound)}">${escape(d.compound[0])}</span></td></tr>`).join('');
    $('policy-table').innerHTML = table(['Policy','Expected remaining time / s','Stop budget','Status'],data.policy_rows.map(p => [p.policy,p.time,p.stops,p.status]));
    $('plan-margin').textContent = 'Plan margin: ' + data.plan_margin + ' between the two best policies overall.';
    $('policy-flips').innerHTML = data.policy_flips.map(p => `<details><summary>${escape(p.assumption.replaceAll('_',' '))}</summary><p>${escape(p.text)}</p></details>`).join('');
    $('sweep-tables').innerHTML = data.sweep_rows.map(s => `<details><summary>${escape(s.assumption.replaceAll('_',' '))} · ${escape(s.status)}</summary><p class="small muted">${escape(s.range)}</p>${table(['Value','Call','Expected call margin / s','Best policy'],s.rows.map(p => [p.value,p.call,p.margin,p.policy]))}</details>`).join('');
    $('rain-timing').textContent = data.rain_timing;
    $('assumption-tags').innerHTML = data.assumptions.map(a => `<div class="assumption"><strong><span class="tag">${escape(a.kind)}</span>${escape(a.name)}</strong><span>${escape(a.value)}</span></div>`).join('');
    $('factor-table').innerHTML = table(['Factor','Weighted points'],data.factor_rows.map(f => [f.factor,f.points]));
    $('radio-lines').innerHTML = data.radio.map(r => `<details><summary><strong>${escape(r.role)}</strong><span>${escape(r.text)}</span><span class="vote">${escape(r.vote)}</span></summary><p>${escape('Legacy scorer candidate: ' + r.candidate + '. ' + r.text)}</p></details>`).join('');
    drawChart();
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
