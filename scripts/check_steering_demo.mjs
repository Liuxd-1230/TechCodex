// Independent implicit tail-node solution checks the explicit teaching model,
// including cutoff, branch swapping, boundary continuity and allowed bias range.
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {squareLaw, processPoint} from '../web/assets/demos/steering-model.mjs';
const data = JSON.parse(readFileSync(new URL('../web/assets/demos/steering-data.json', import.meta.url)));
const close = (a, b, tolerance = 1e-12) => assert.ok(Math.abs(a - b) < tolerance, `${a} != ${b}`);
const params = data.analytic, c = data.conditions;
let cases = 0;
for (let microamps = 40; microamps <= 100; microamps += 10) {
  const tail = microamps * 1e-6;
  for (let millivolts = -650; millivolts <= 650; millivolts += 5) {
    const v = millivolts / 1000;
    const result = squareLaw(v, tail, params, c);
    // Solve KCL directly: each channel is beta/2 max(VGS-VTH,0)^2.
    const branch = (gate, vt) => params.beta_A_V2 / 2 * Math.max(gate - vt - params.threshold_V, 0) ** 2;
    let lo = -2, hi = 2;
    for (let i = 0; i < 65; i++) {
      const t = (lo + hi) / 2;
      if (branch(1.4 + v / 2, t) + branch(1.4 - v / 2, t) > tail) lo = t;
      else hi = t;
    }
    close(result.vt, (lo + hi) / 2);
    close(result.i1, branch(1.4 + v / 2, result.vt));
    close(result.i2, branch(1.4 - v / 2, result.vt));
    close(result.i1 + result.i2, tail);
    close(result.o1, c.VDD_V - c.RD_ohm * result.i1);
    assert.ok(result.valid, 'Controls must stay inside model headroom');
    const reversed = squareLaw(-v, tail, params, c);
    close(result.i1, reversed.i2);
    close(result.vt, reversed.vt);
    cases++;
  }
  const edge = Math.sqrt(2 * tail / params.beta_A_V2);
  const below = squareLaw(edge - 1e-9, tail, params, c);
  const above = squareLaw(edge + 1e-9, tail, params, c);
  close(below.i1, above.i1);
  close(below.vt, above.vt, 2e-9);
  const deltaT = h => squareLaw(h, tail, params, c).vt - squareLaw(0, tail, params, c).vt;
  close(deltaT(.002) / deltaT(.001), 4, 5e-5);
}

for (let index = 0; index < data.rows.length; index++) {
  const row = data.rows[index];
  const p = processPoint(row[0], data);
  close(p.i1, row[1]); close(p.i2, row[2]); close(p.vt, row[5]);
  close(row[8] + row[9], 80e-6);
  close(p.i1 + p.i2 - 80e-6, p.body);
  assert.ok(p.valid, 'GF180 active branch must retain saturation margin');
  const mirrored = processPoint(-row[0], data);
  close(p.i1, mirrored.i2, 2e-12);
  close(p.vt, mirrored.vt, 2e-9);
  if (index) {
    const prev = data.rows[index - 1];
    const mid = processPoint((prev[0] + row[0]) / 2, data);
    close(mid.i1, (prev[1] + row[1]) / 2);
    close(mid.vt, (prev[5] + row[5]) / 2);
  }
}
for (const v of [-.651, .651, NaN, Infinity]) assert.throws(() => processPoint(v, data), RangeError);
console.log(`PASS: ${cases} independent KCL/model/headroom cases; cutoff continuity; quadratic tail motion; 651 GF180 points and 650 interpolated midpoints; no extrapolation.`);
