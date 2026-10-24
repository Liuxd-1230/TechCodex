import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {readFileSync} from 'node:fs';
import {fileURLToPath} from 'node:url';
import path from 'node:path';
import {chartPoint, DISPLAY_WINDOW_HZ, POINT_INDEX, unityWindowNote} from '../web/assets/demos/ota-frequency.js';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const readJson = relative => JSON.parse(readFileSync(path.join(root, relative), 'utf8'));
const dataPath = 'web/assets/demos/ota-frequency-data.json';
const data = readJson(dataPath);
const runPath = '模拟/实验/频率响应/data/run.json';
const run = readJson(runPath);
const metrics = readJson('模拟/实验/频率响应/data/metrics.json');
const design = readJson('模拟/实验/频率响应/design.json');
const close = (actual, expected, tolerance = 2e-12) => {
  const limit = Math.max(1e-14, Math.abs(expected) * tolerance);
  assert.ok(Math.abs(actual - expected) <= limit, `${actual} differs from ${expected} by more than ${limit}`);
};

assert.equal(data.schema, 1);
assert.equal(data.model_commit, run.model.commit);
assert.equal(data.run_manifest_sha256, createHash('sha256').update(readFileSync(path.join(root, runPath))).digest('hex'));
assert.deepEqual(data.target, design.target);
assert.deepEqual(data.conditions.frequency_Hz, design.frequency_Hz);
assert.equal(data.conditions.points_per_decade, design.points_per_decade);
for (const [relative, expectedHash] of Object.entries(data.source_sha256)) {
  assert.equal(run.sha256[relative], expectedHash, `${relative} hash differs from run manifest`);
  const actual = createHash('sha256').update(readFileSync(path.join(root, relative))).digest('hex');
  assert.equal(actual, expectedHash, `${relative} no longer matches the recorded source hash`);
}

assert.deepEqual(data.groups.load, {baseline: 'ota-1p', candidates: ['ota-unloaded', 'ota-5p']});
assert.deepEqual(data.groups.design, {baseline: 'ota-1p', candidates: ['ota-wide', 'ota-long', 'ota-current']});
assert.deepEqual(Object.keys(data.cases).sort(), ['ota-1p', 'ota-5p', 'ota-current', 'ota-long', 'ota-unloaded', 'ota-wide'].sort());
assert.deepEqual(POINT_INDEX, {frequency: 0, gainDb: 1, phaseDeg: 2});
assert.deepEqual(DISPLAY_WINDOW_HZ, [100, 1e9]);
assert.match(unityWindowNote(data.cases['ota-unloaded'].metrics.unity_Hz),/1\.384 GHz.*图窗右侧/);
assert.equal(unityWindowNote(1e9),'');
assert.equal(unityWindowNote(9.7e6),'');
assert.equal(unityWindowNote(null),'');
assert.deepEqual(chartPoint([123, 4.5, -90], 'gain'), [123, 4.5]);
assert.deepEqual(chartPoint([123, 4.5, -90], 'phase'), [123, -90]);
assert.throws(() => chartPoint([123, 4.5, -90], 'complex'), RangeError);

function interpolateLogCrossing(frequencies, values, level) {
  for (let i = 0; i < values.length - 1; i++) {
    if (values[i] >= level && values[i + 1] < level) {
      const logFrequency = Math.log(frequencies[i]) +
        (level - values[i]) / (values[i + 1] - values[i]) * (Math.log(frequencies[i + 1]) - Math.log(frequencies[i]));
      return Math.exp(logFrequency);
    }
  }
  return null;
}

function interpolateLogY(frequencies, values, frequency) {
  for (let i = 0; i < frequencies.length - 1; i++) {
    if (frequencies[i] <= frequency && frequency <= frequencies[i + 1]) {
      const amount = (Math.log(frequency) - Math.log(frequencies[i])) /
        (Math.log(frequencies[i + 1]) - Math.log(frequencies[i]));
      return values[i] + (values[i + 1] - values[i]) * amount;
    }
  }
  return null;
}

let totalPoints = 0;
for (const [id, record] of Object.entries(data.cases)) {
  for (const key of ['gain_V_V', 'bandwidth_3dB_Hz', 'unity_Hz', 'power_W']) {
    assert.equal(record.metrics[key], metrics[id][key], `${id} ${key} is not copied from metrics.json`);
  }
  assert.equal(record.external_load_F, metrics[id].load_F);

  const csv = readFileSync(path.join(root, record.ac_csv), 'utf8').trim().split(/\r?\n/);
  const columns = csv[0].split(',');
  const frequencyColumn = columns.indexOf('frequency_Hz');
  const realColumn = columns.indexOf('v(o)_real');
  const imagColumn = columns.indexOf('v(o)_imag');
  assert.ok(frequencyColumn >= 0 && realColumn >= 0 && imagColumn >= 0, `${id} AC output columns are missing`);
  const rows = csv.slice(1).map(line => line.split(',').map(Number));
  assert.equal(record.points.length, rows.length, `${id} point count differs from source CSV`);
  assert.deepEqual(record.columns, ['frequency_Hz', 'gain_dB', 'phase_deg_unwrapped']);

  const frequencies = [];
  const dbValues = [];
  const phaseValues = [];
  let previousPrincipal = null;
  let phaseOffset = 0;
  for (let i = 0; i < rows.length; i++) {
    const source = rows[i];
    const point = record.points[i];
    const frequency = source[frequencyColumn];
    const real = source[realColumn];
    const imag = source[imagColumn];
    const magnitude = Math.hypot(real, imag);
    const db = 20 * Math.log10(magnitude);
    const principal = Math.atan2(imag, real);
    if (previousPrincipal !== null) {
      const delta = principal - previousPrincipal;
      if (delta > Math.PI) phaseOffset -= 2 * Math.PI;
      else if (delta < -Math.PI) phaseOffset += 2 * Math.PI;
    }
    const phase = (principal + phaseOffset) * 180 / Math.PI;

    assert.equal(point.length, 3);
    close(point[0], frequency, 0);
    close(point[1], db);
    close(point[2], phase);
    const gainPoint = chartPoint(point, 'gain');
    const phasePoint = chartPoint(point, 'phase');
    close(gainPoint[0], frequency, 0);
    close(gainPoint[1], db);
    close(phasePoint[0], frequency, 0);
    close(phasePoint[1], phase);
    if (i) {
      assert.ok(frequency > frequencies[i - 1], `${id} frequencies are not strictly increasing at row ${i}`);
      assert.ok(Math.abs(phase - phaseValues[i - 1]) <= 180.000001, `${id} phase contains an unwrap jump at row ${i}`);
    }
    frequencies.push(frequency);
    dbValues.push(db);
    phaseValues.push(phase);
    previousPrincipal = principal;
  }

  const calculatedGain = Math.hypot(rows[0][realColumn], rows[0][imagColumn]);
  const bandwidth = interpolateLogCrossing(frequencies, dbValues, dbValues[0] - 10 * Math.log10(2));
  const unity = interpolateLogCrossing(frequencies, dbValues, 0);
  assert.ok(bandwidth && unity, `${id} expected downward bandwidth and unity crossings`);
  close(metrics[id].gain_V_V, calculatedGain, 5e-10);
  close(metrics[id].bandwidth_3dB_Hz, bandwidth, 5e-10);
  close(metrics[id].unity_Hz, unity, 5e-10);
  close(metrics[id].phase_at_unity_deg, interpolateLogY(frequencies, phaseValues, unity), 5e-10);
  totalPoints += rows.length;
}

assert.equal(totalPoints, 6 * 801);
console.log(`PASS: ${Object.keys(data.cases).length} cases, ${totalPoints} dB/phase points checked against raw complex CSV, source hashes, and metrics.`);
