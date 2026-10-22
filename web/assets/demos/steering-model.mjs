// Units throughout: V, A, ohm. Pure functions shared by the UI and numerical checks.
export function squareLaw(vid, tail, parameters, conditions) {
  const beta = parameters.beta_A_V2;
  const threshold = parameters.threshold_V;
  const vcm = conditions.nominal_VCM_V;
  const vov0 = Math.sqrt(tail / beta);
  const edge = Math.SQRT2 * vov0;
  let delta, vt;
  if (Math.abs(vid) <= edge) {
    const u = Math.sqrt(tail / beta - vid * vid / 4);
    delta = beta * vid * u;
    vt = vcm - threshold - u;
  } else {
    delta = Math.sign(vid) * tail;
    vt = vcm + Math.abs(vid) / 2 - threshold - Math.sqrt(2 * tail / beta);
  }
  const i1 = (tail + delta) / 2;
  const i2 = (tail - delta) / 2;
  const o1 = conditions.VDD_V - conditions.RD_ohm * i1;
  const o2 = conditions.VDD_V - conditions.RD_ohm * i2;
  const sat1 = o1 - (vcm + vid / 2 - threshold);
  const sat2 = o2 - (vcm - vid / 2 - threshold);
  return {vid, i1, i2, o1, o2, vt, delta, edge, vov0, body: 0,
    slope: Math.sqrt(beta * tail),
    valid: vt >= 0 && (i1 < 1e-15 || sat1 >= 0) && (i2 < 1e-15 || sat2 >= 0)};
}

export function processPoint(vid, data) {
  const rows = data.rows;
  if (!Number.isFinite(vid) || vid < rows[0][0] || vid > rows.at(-1)[0]) {
    throw new RangeError('Outside the precomputed GF180MCU sweep');
  }
  let lo = 0, hi = rows.length - 1;
  while (hi - lo > 1) {
    const mid = (lo + hi) >> 1;
    if (rows[mid][0] <= vid) lo = mid; else hi = mid;
  }
  const a = rows[lo], b = rows[hi];
  const f = (vid - a[0]) / (b[0] - a[0]);
  const p = a.map((v, i) => v + f * (b[i] - v));
  return {vid, i1: p[1], i2: p[2], o1: p[3], o2: p[4], vt: p[5],
    delta: p[1] - p[2], body: p[10], slope: data.analytic.port_slope_A_V,
    valid: p[5] >= 0 && (p[1] < 8e-7 || p[3] - p[5] >= p[6])
      && (p[2] < 8e-7 || p[4] - p[5] >= p[7])};
}
