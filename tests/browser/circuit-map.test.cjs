const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const root = path.resolve(__dirname,'../..');
require(path.join(root,'design/assets/circuit-map.js'));
const map = globalThis.FormulaCircuit;
const fixture = JSON.parse(fs.readFileSync(path.join(root,'tests/fixtures/projection_lap18.json'),'utf8'));
const track = fixture.track;
const close = (a,b) => assert.ok(Math.abs(a-b) < 1e-8,`${a} != ${b}`);

test('browser coordinates match the Python scaled-race fixture for every car',()=>{
  for(const car of track.cars){
    const placed=map.position(track,track.leader.distance_m,car.gap_to_leader_s);
    for(const key of ['distance_m','unwrapped_distance_m','x','y']) close(placed[key],car[key]);
  }
});
test('live rejoin matches the fixture, and zero loss returns to NOR',()=>{
  const ghost=map.rejoin(track,21.5);
  close(ghost.distance_m,track.ghost_rejoin.distance_m);
  assert.equal(ghost.position,3);assert.equal(ghost.car_ahead,'HAM');close(ghost.gap_to_car_ahead_s,3.5);
  close(map.rejoin(track,0).distance_m,track.cars[0].distance_m);
});
test('slider changes move backwards and update neighbouring cars',()=>{
  const cheap=map.rejoin(track,5),costly=map.rejoin(track,45);
  assert.equal(cheap.position,2);assert.equal(cheap.car_ahead,'VER');close(cheap.gap_to_car_ahead_s,1.5);
  assert.equal(cheap.car_behind,'HAM');assert.equal(costly.position,3);
  assert.ok(costly.unwrapped_distance_m < cheap.unwrapped_distance_m);
});
test('a full race-reference lap wraps exactly and retains the deficit',()=>{
  const original=map.position(track,track.leader.distance_m,3.5);
  const wrapped=map.position(track,track.leader.distance_m,3.5+2*track.reference_lap_time_s);
  close(wrapped.distance_m,original.distance_m);
  close(wrapped.unwrapped_distance_m,original.unwrapped_distance_m-2*track.lap_length_m);
});
