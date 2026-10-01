/* Offline geometry only. Strategy decisions remain in the projection fixture. */
(() => {
  'use strict';
  const interpolate = (v, points, from, to) => {
    let lo = 0, hi = points.length - 1;
    while (hi - lo > 1) { const mid = (lo + hi) >> 1; if (points[mid][from] <= v) lo = mid; else hi = mid; }
    const a = points[lo], b = points[hi];
    return a[to] + (b[to] - a[to]) * (v - a[from]) / (b[from] - a[from]);
  };
  function position(track, leaderDistance, gap) {
    const length = track.lap_length_m, duration = track.reference_lap_time_s;
    const leaderTurns = Math.floor(leaderDistance / length);
    const leaderTime = leaderTurns * duration + interpolate(leaderDistance - leaderTurns * length, track.time_profile, 'distance_m', 'time_s');
    const time = leaderTime - gap, turns = Math.floor(time / duration), clock = time - turns * duration;
    const distance = interpolate(clock, track.time_profile, 'time_s', 'distance_m');
    return {gap_to_leader_s: gap, distance_m: distance, unwrapped_distance_m: turns * length + distance, lap_offset: turns,
      x: interpolate(distance, track.polyline, 'distance_m', 'x'), y: interpolate(distance, track.polyline, 'distance_m', 'y')};
  }
  function rejoin(track, loss) {
    const subject = track.cars.find(c => c.driver === track.ghost_rejoin.driver);
    const gap = subject.gap_to_leader_s + loss;
    const others = track.cars.filter(c => c.driver !== subject.driver);
    const ahead = others.filter(c => c.gap_to_leader_s < gap).sort((a,b) => b.gap_to_leader_s - a.gap_to_leader_s);
    const behind = others.filter(c => c.gap_to_leader_s >= gap).sort((a,b) => a.gap_to_leader_s - b.gap_to_leader_s);
    return {...position(track, track.leader.distance_m, gap), position: ahead.length + 1, pit_loss_s: loss,
      car_ahead: ahead[0]?.driver ?? null, car_behind: behind[0]?.driver ?? null,
      gap_to_car_ahead_s: ahead.length ? gap - ahead[0].gap_to_leader_s : null,
      gap_to_car_behind_s: behind.length ? behind[0].gap_to_leader_s - gap : null};
  }
  globalThis.FormulaCircuit = {interpolate, position, rejoin};
})();
