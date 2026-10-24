export const POINT_INDEX = Object.freeze({frequency: 0, gainDb: 1, phaseDeg: 2});
export const DISPLAY_WINDOW_HZ = Object.freeze([100, 1e9]);
export function chartPoint(point, quantity) {
  const valueIndex = quantity === 'gain' ? POINT_INDEX.gainDb :
    quantity === 'phase' ? POINT_INDEX.phaseDeg : null;
  if (valueIndex === null) throw new RangeError('Unknown OTA plot quantity');
  return [point[POINT_INDEX.frequency], point[valueIndex]];
}

const root = typeof document === 'undefined' ? null : document.querySelector('[data-demo="ota-frequency"]');
const NS = 'http://www.w3.org/2000/svg';
const field = name => root.querySelector(`[data-ota-frequency="${name}"]`);

async function start() {
  const response = await fetch(root.dataset.payload);
  if (!response.ok) throw new Error('OTA frequency data unavailable');
  const data = await response.json();
  if (data.schema !== 1) throw new Error('Unsupported OTA frequency data');

  const purpose = root.querySelector('#ota-frequency-purpose');
  const candidateSelect = root.querySelector('#ota-frequency-candidate');
  const grid = field('grid');
  const baselineGain = field('baseline-gain');
  const selectedGain = field('candidate-gain');
  const baselinePhase = field('baseline-phase');
  const selectedPhase = field('candidate-phase');
  const xMin = Math.log10(DISPLAY_WINDOW_HZ[0]);
  const xMax = Math.log10(DISPLAY_WINDOW_HZ[1]);
  const plot = {left: 78, right: 582, gainTop: 48, gainBottom: 265, phaseTop: 345, phaseBottom: 560};
  const x = frequency => plot.left + (Math.log10(frequency) - xMin) / (xMax - xMin) * (plot.right - plot.left);
  const yGain = value => plot.gainBottom - (value + 60) / 120 * (plot.gainBottom - plot.gainTop);
  const yPhase = value => plot.phaseTop + (0 - value) / 180 * (plot.phaseBottom - plot.phaseTop);
  const path = (points, y) => points.map((point, index) => `${index ? 'L' : 'M'}${x(point[0]).toFixed(2)} ${y(point[1]).toFixed(2)}`).join(' ');

  function svgElement(name, attrs = {}, value = '') {
    const element = document.createElementNS(NS, name);
    for (const [key, val] of Object.entries(attrs)) element.setAttribute(key, String(val));
    if (value) element.textContent = value;
    return element;
  }

  function addGridLine(y, x0 = plot.left, x1 = plot.right) {
    grid.append(svgElement('line', {x1: x0, x2: x1, y1: y, y2: y, class: 'ota-frequency-grid'}));
  }

  function addLabel(value, xPos, yPos, anchor = 'middle') {
    grid.append(svgElement('text', {x: xPos, y: yPos, 'text-anchor': anchor}, value));
  }

  function buildGrid() {
    grid.replaceChildren();
    for (const db of [60, 40, 20, 0, -20, -40, -60]) {
      const y = yGain(db);
      addGridLine(y);
      addLabel(String(db), plot.left - 10, y + 6, 'end');
    }
    for (const degrees of [0, -45, -90, -135, -180]) {
      const y = yPhase(degrees);
      addGridLine(y);
      addLabel(String(degrees), plot.left - 10, y + 6, 'end');
    }
    for (const xPos of [plot.left, plot.right]) {
      grid.append(svgElement('line', {x1: xPos, x2: xPos, y1: plot.gainTop, y2: plot.gainBottom, class: 'ota-frequency-grid'}));
      grid.append(svgElement('line', {x1: xPos, x2: xPos, y1: plot.phaseTop, y2: plot.phaseBottom, class: 'ota-frequency-grid'}));
    }
    for (const [index, [frequency, label]] of [[1e2, '100'], [1e3, '1k'], [1e4, '10k'], [1e5, '100k'], [1e6, '1M'], [1e7, '10M'], [1e8, '100M'], [1e9, '1G']].entries()) {
      const xPos = x(frequency);
      grid.append(svgElement('line', {x1: xPos, x2: xPos, y1: plot.gainTop, y2: plot.gainBottom, class: 'ota-frequency-grid'}));
      grid.append(svgElement('line', {x1: xPos, x2: xPos, y1: plot.phaseTop, y2: plot.phaseBottom, class: 'ota-frequency-grid'}));
      const labelElement = svgElement('text', {x: xPos, y: plot.phaseBottom + 23, 'text-anchor': 'middle', class: index % 2 ? 'ota-frequency-mobile-hide' : ''}, label);
      grid.append(labelElement);
    }
    for (const [y0, y1] of [[plot.gainTop, plot.gainBottom], [plot.phaseTop, plot.phaseBottom]]) {
      grid.append(svgElement('line', {x1: plot.left, x2: plot.left, y1: y0, y2: y1, class: 'ota-frequency-axis'}));
      grid.append(svgElement('line', {x1: plot.left, x2: plot.right, y1, y2: y1, class: 'ota-frequency-axis'}));
    }
    addLabel('开环增益 / dB', plot.left, 30, 'start');
    addLabel('开环连续展开相位 / °', plot.left, 327, 'start');
    addLabel('频率 / Hz · 对数坐标', (plot.left + plot.right) / 2, 614);
  }

  function formatHz(value) {
    if (!Number.isFinite(value)) return '未穿越';
    if (value >= 1e9) return `${(value / 1e9).toFixed(2)} GHz`;
    if (value >= 1e6) return `${(value / 1e6).toFixed(2)} MHz`;
    if (value >= 1e3) return `${(value / 1e3).toFixed(2)} kHz`;
    return `${value.toFixed(2)} Hz`;
  }

  function formatLoad(value) {
    if (value === 0) return '无外接';
    if (value >= 1e-12) return `${(value / 1e-12).toFixed(value % 1e-12 ? 2 : 0)} pF`;
    return `${(value / 1e-15).toFixed(0)} fF`;
  }

  function formatPower(value) {
    return `${(value * 1e3).toFixed(3)} mW`;
  }

  function populateCandidates(groupId, requestedId) {
    const group = data.groups[groupId];
    candidateSelect.replaceChildren();
    for (const id of group.candidates) {
      const option = document.createElement('option');
      option.value = id;
      option.textContent = data.cases[id].label;
      candidateSelect.append(option);
    }
    candidateSelect.value = group.candidates.includes(requestedId) ? requestedId : group.candidates[0];
  }

  function setPath(element, points, quantity, scale) {
    element.setAttribute('d', path(points.map(point => chartPoint(point, quantity)), scale));
  }

  function update() {
    const group = data.groups[purpose.value];
    const base = data.cases[group.baseline];
    const selected = data.cases[candidateSelect.value];
    if (!base || !selected) throw new Error('Selected OTA case is missing');
    setPath(baselineGain, base.points, 'gain', yGain);
    setPath(selectedGain, selected.points, 'gain', yGain);
    setPath(baselinePhase, base.points, 'phase', yPhase);
    setPath(selectedPhase, selected.points, 'phase', yPhase);

    field('label').textContent = selected.label;
    field('load').textContent = formatLoad(selected.external_load_F);
    field('gain').textContent = `${selected.metrics.gain_V_V.toFixed(2)} V/V`;
    field('bandwidth').textContent = formatHz(selected.metrics.bandwidth_3dB_Hz);
    field('unity').textContent = formatHz(selected.metrics.unity_Hz);
    field('power').textContent = formatPower(selected.metrics.power_W);
    field('change').textContent = selected.change + (selected.deck_load_note ? ` ${selected.deck_load_note}` : '');
    field('chart-desc').textContent = `曲线显示窗口为 100 Hz 至 1 GHz；原始开环 AC 扫描为 1 Hz 至 10 GHz，全部频点保留，窗口外部分由图框裁切。上图显示 ${base.label} 的蓝色虚线与 ${selected.label} 的绿色实线开环增益 dB；下图显示同两条复数响应按频率递增展开的开环相位，不是闭环相位裕度。所选负载为 ${formatLoad(selected.external_load_F)}。`;

    const target = data.target;
    if (purpose.value === 'load') {
      if (selected.external_load_F === 0) {
        field('observation').textContent = `无外接 CL 时仍有器件寄生，−3 dB 带宽为 ${formatHz(selected.metrics.bandwidth_3dB_Hz)}；这是技术对照，不是目标负载工况。`;
      } else if (selected.external_load_F === base.external_load_F) {
        field('observation').textContent = `当前候选与 ${base.label} 使用相同负载；−3 dB 带宽为 ${formatHz(selected.metrics.bandwidth_3dB_Hz)}。`;
      } else {
        const bandwidthResult = selected.metrics.bandwidth_3dB_Hz < target.minimum_3dB_bandwidth_Hz
          ? `低于 ${formatHz(target.minimum_3dB_bandwidth_Hz)} 目标`
          : `达到 ${formatHz(target.minimum_3dB_bandwidth_Hz)} 目标`;
        field('observation').textContent = `CL 从 ${formatLoad(base.external_load_F)} 变为 ${formatLoad(selected.external_load_F)} 后，低频增益近似不变，−3 dB 带宽为 ${formatHz(selected.metrics.bandwidth_3dB_Hz)}，${bandwidthResult}。`;
      }
    } else {
      const failures = [];
      if (selected.metrics.gain_V_V < target.minimum_dc_gain_V_V) failures.push(`增益低于 ${target.minimum_dc_gain_V_V} V/V`);
      if (selected.metrics.bandwidth_3dB_Hz < target.minimum_3dB_bandwidth_Hz) failures.push(`带宽低于 ${formatHz(target.minimum_3dB_bandwidth_Hz)}`);
      if (selected.metrics.power_W > target.maximum_supply_power_W) failures.push(`功耗 ${formatPower(selected.metrics.power_W)} 超过 ${formatPower(target.maximum_supply_power_W)}`);
      field('observation').textContent = failures.length
        ? `${selected.label}：${failures.join('；')}。曲线和指标来自这一尺寸与偏置的独立 AC 仿真。`
        : `${selected.label} 在 1 pF 标称条件下满足增益、带宽和功耗目标；此结果不代表 PVT 或版图后保证。`;
    }
  }

  if (!data.groups.load || !data.groups.design) throw new Error('Incomplete OTA candidate manifest');
  buildGrid();
  populateCandidates(purpose.value, candidateSelect.value);
  purpose.addEventListener('change', () => {
    populateCandidates(purpose.value, '');
    update();
  });
  candidateSelect.addEventListener('change', update);
  update();
  root.hidden = false;
  root.nextElementSibling.hidden = true;
  field('provenance').textContent = `${data.source} · ${data.conditions.corner} · ${data.conditions.temperature_C} °C · open-loop AC`;
  if(location.hash==='#ota-frequency-title')requestAnimationFrame(()=>root.scrollIntoView({block:'start',behavior:'instant'}));
}

if (root) start().catch(() => {
  root.hidden = true;
  const fallback = root.nextElementSibling;
  if (fallback?.classList.contains('ota-frequency-loading')) {
    fallback.hidden = false;
    fallback.textContent = '交互数据暂不可用；本节原有频响图、候选表和节点矩阵推导仍可阅读。';
  }
});
