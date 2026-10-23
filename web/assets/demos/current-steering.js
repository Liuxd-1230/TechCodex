import {squareLaw, processPoint} from './steering-model.mjs';

// Each demo owns its state. The textbook remains complete without this module.
const root = document.querySelector('[data-demo="current-steering"]');
if (root) enhance(root).catch(() => {
  root.hidden = true;
  const message = root.nextElementSibling;
  message.hidden = false;
  message.textContent = '交互数据暂时无法载入；请继续阅读下方静态图与推导，或刷新本页重试。';
});

async function enhance(root) {
  const response = await fetch(new URL('./steering-data.json', import.meta.url));
  if (!response.ok) throw new Error('Demo data unavailable');
  const data = await response.json();
  if (data.schema !== 1 || data.rows.length !== 651) throw new Error('Unknown dataset');
  const c = data.conditions;
  const vidControl = root.querySelector('#steering-vid');
  const tailControl = root.querySelector('#steering-tail');
  const compareControl = root.querySelector('#steering-compare');
  const viewControl = root.querySelector('#steering-view');
  const fields = Object.fromEntries([...root.querySelectorAll('[data-field]')]
    .map(el => [el.dataset.field, el]));
  const curves = Object.fromEntries([...root.querySelectorAll('[data-curve]')]
    .map(el => [el.dataset.curve, el]));
  let source = root.querySelector('[name="steering-source"]:checked').value;
  let analyticTail = Number(tailControl.value);
  const fmt = (v, digits = 3) => (Math.abs(v) < .5 * 10 ** -digits ? 0 : v).toFixed(digits);
  const current = value => value > 0 && value < 1e-8
    ? `${fmt(value * 1e9, 2)} nA` : `${fmt(value * 1e6, 2)} µA`;
  const text = (key, value) => { fields[key].textContent = value; };
  let extent = .65, low = 0, high = 100;
  const x = v => 57 + (v + extent) / (2 * extent) * 406;
  const y = current => 235 - (current * 1e6 - low) / (high - low) * 200;
  const point = (v, mode, tail) => mode === 'analytic'
    ? squareLaw(v, tail * 1e-6, data.analytic, c) : processPoint(v, data);
  const path = (mode, branch, tail) => Array.from({length: 651}, (_, i) => {
    const v = Number((-extent + i * 2 * extent / 650).toFixed(9));
    return `${i ? 'L' : 'M'}${fmt(x(v), 2)} ${fmt(y(point(v, mode, tail)[branch]), 2)}`;
  }).join('');

  function drawCurves() {
    const tail = source === 'analytic' ? analyticTail : 80;
    for (const branch of ['i1', 'i2']) curves[branch].setAttribute('d', path(source, branch, tail));
    const compare = tail === 80 && compareControl.checked;
    compareControl.disabled = tail !== 80;
    for (const [index, branch] of ['i1', 'i2'].entries()) {
      curves[`other${index + 1}`].setAttribute('d', compare
        ? path(source === 'analytic' ? 'process' : 'analytic', branch, 80) : '');
    }
    text('legend', compare
      ? `实线：${source === 'analytic' ? '平方律' : 'GF180'}；同色虚线：${source === 'analytic' ? 'GF180' : '平方律'}，均为 80 µA。圆点是当前工作点。`
      : `实线：当前模型的 I1、I2。${tail !== 80 ? 'GF180 数据仅对应 80 µA，此时不叠加。' : '需要比较时，在“模型选择与曲线对照”中勾选叠加。'}`);
    root.querySelectorAll('[data-y-tick]').forEach(el => {
      el.textContent = String(low + Number(el.dataset.yTick) * (high - low) / 4);
    });
    text('x-left', String(-extent * 1000)); text('x-right', String(extent * 1000));
    text('plot-description', `当前横轴为 ±${extent * 1000} 毫伏，纵轴 ${low} 至 ${high} 微安，固定刻度。两实线对应左右支路；${compare ? '虚线为另一模型在 80 微安时的对照。' : '未叠加另一模型。'}竖线与圆点标出当前工作点。`);
  }

  function update() {
    const vid = Number(vidControl.value) / 1000;
    const tail = source === 'analytic' ? analyticTail : 80;
    const p = point(vid, source, tail);
    const zero = point(0, source, tail);
    const tailShift = (p.vt - zero.vt) * 1000;
    const tailSpan = Math.max(
      Math.abs(point(extent, source, tail).vt - zero.vt),
      Math.abs(point(-extent, source, tail).vt - zero.vt)
    );
    const haloOpacity = .08 + .27 * (tailSpan ? Math.min(1, Math.abs(tailShift) / tailSpan) : 0);
    const tangent = p.slope * vid;
    const compression = Math.abs(vid) < 1e-12 ? 0 : 100 * (1 - p.delta / tangent);
    text('vid', `${Number(vidControl.value) > 0 ? '+' : ''}${vidControl.value} mV`);
    vidControl.setAttribute('aria-valuetext', `${vidControl.value} 毫伏，固定平均输入 1.4 伏`);
    text('vi1', `VI1 ${fmt(1.4 + vid / 2)} V`);
    text('vi2', `VI2 ${fmt(1.4 - vid / 2)} V`);
    text('o1', `VO1 ${fmt(p.o1)} V`);
    text('o2', `VO2 ${fmt(p.o2)} V`);
    text('i1', `I1 ${current(p.i1)}`);
    text('i2', `I2 ${current(p.i2)}`);
    text('vt', `T ${fmt(p.vt)} V`);
    text('it', `IT ${tail} µA`);
    text('circuit-description', `电阻负载 NMOS 差分对。两管体端各自接地，不与公共源节点 T 短接。箭头均向下，粗细表示漏电流大小。${source === 'analytic' ? '平方律实时计算' : 'GF180 预计算数据插值'}：输入 VI1 ${fmt(1.4 + vid / 2)} 伏、VI2 ${fmt(1.4 - vid / 2)} 伏；I1 ${current(p.i1)}、I2 ${current(p.i2)}；VO1 ${fmt(p.o1)} 伏、VO2 ${fmt(p.o2)} 伏；T ${fmt(p.vt)} 伏。理想尾源 ${tail} 微安。`);
    text('branch-balance', `I1 + I2 = ${current(p.i1 + p.i2)} · IT = ${tail} µA · T−T₀ = ${tailShift > 0 ? '+' : ''}${fmt(tailShift, 1)} mV`);
    fields['tail-halo'].setAttribute('opacity', fmt(haloOpacity, 3));
    text('tail', `${tail} µA`);
    tailControl.value = String(tail);
    tailControl.disabled = source === 'process';
    tailControl.setAttribute('aria-valuetext', `${tail} 微安`);
    text('tail-note', source === 'process'
      ? 'GF180 只有 80 µA 的预计算数据，尾电流已锁定。切回平方律可调节；不会将固定数据缩放成新的 SPICE 结果。'
      : '保持 β、阈值、VCM 和 RD 不变，调节 40–100 µA。先比较中央斜率，再比较接近全转向时所需的输入差。');
    text('source', source === 'analytic'
      ? '当前：平方律准静态计算 · 固定 β、阈值 · 理想尾源 · 非 SPICE'
      : '当前：GF180MCU / ngspice-47 · 固定 80 µA · DC 预计算点间线性插值');
    for (const branch of ['i1', 'i2']) {
      const arrow = root.querySelector(`[data-current="${branch}"]`);
      arrow.style.strokeWidth = String(.7 + 4 * p[branch] / (100e-6));
      arrow.style.opacity = p[branch] < 1e-9 ? '.2' : '1';
      const dot = root.querySelector(`[data-dot="${branch}"]`);
      dot.setAttribute('cx', x(vid));
      dot.setAttribute('cy', y(p[branch]));
    }
    fields.cursor.setAttribute('d', `M${x(vid)} 35V235`);
    text('readout', `ΔI = ${fmt(p.delta * 1e6, 2)} µA　·　VOD = ${fmt(p.o1 - p.o2)} V${extent < .1 ? `　·　零点 dΔI/dVID = ${fmt(p.slope * 1000, 4)} mS` : ''}`);
    let observation;
    if (vid === 0) {
      observation = `观察：两边各分约 ${fmt(p.i1 * 1e6, 2)} µA。试着向右移，再向左移同样距离：电流互换，T 的变化方向是否也互换？`;
    } else {
      const stronger = vid > 0 ? '左' : '右';
      const weaker = vid > 0 ? '右' : '左';
      observation = `观察：${stronger}支路电流增加，${stronger}输出下降；${weaker}支路让出电流，${weaker}输出升高。`;
      if (source === 'analytic' && Math.abs(vid) >= p.edge) {
        observation += ` 平方律已到单管导通段；全转向边界约 ±${fmt(p.edge * 1000, 0)} mV，继续加大输入不会增加 ΔI。`;
      } else {
        observation += ` 相对零点切线，电流差压缩 ${fmt(compression, 1)}%。${Math.abs(vid) <= .020 ? 'T 的移动很小，因为它在零点附近从二次项开始变化。' : 'T 已升高；“差模时 T 不动”只适用于平衡点附近的一阶分析。'}`;
      }
      if (source === 'process' && Math.abs(vid) > .4) {
        observation += ' 弱支路仍有微小电流，真实器件没有平方律式的突然截止。';
      }
    }
    if (!p.valid) observation += ' 当前点不满足导通管的饱和余量，不能沿用饱和区解释。';
    // Debounce only screen-reader narration; visuals and numerical values update immediately.
    clearTimeout(update.announcement);
    text('observation', observation);
    update.announcement = setTimeout(() => text('announcement', observation), 180);
    text('parameters', `解析校准值：β = ${fmt(data.analytic.beta_A_V2 * 1000, 4)} mA/V²；VTH = ${fmt(data.analytic.threshold_V, 4)} V。标称端口斜率 d(I1−I2)/dVID = ${fmt(data.analytic.port_slope_A_V * 1000, 4)} mS。仅在 80 µA 时对齐标称点；改变尾电流后不重新拟合。`);
  }

  vidControl.addEventListener('input', update);
  compareControl.addEventListener('change', drawCurves);
  function applyView() {
    const small = viewControl.value === 'small';
    extent = small ? .04 : .65; low = small ? 15 : 0; high = small ? 65 : 100;
    vidControl.min = String(-extent * 1000); vidControl.max = String(extent * 1000);
    vidControl.value = String(Math.max(-extent * 1000, Math.min(extent * 1000, Number(vidControl.value))));
    text('range-left', `−${extent * 1000} mV · 右支路占优`);
    text('range-right', `+${extent * 1000} mV · 左支路占优`);
    drawCurves(); update();
  }
  viewControl.addEventListener('change', applyView);
  tailControl.addEventListener('input', () => {
    analyticTail = Number(tailControl.value);
    drawCurves();
    update();
  });
  root.querySelectorAll('[name="steering-source"]').forEach(input => input.addEventListener('change', () => {
    source = input.value;
    drawCurves();
    update();
  }));
  root.querySelector('[data-action="zero"]').addEventListener('click', () => {
    vidControl.value = '0';
    update();
  });
  // Browsers may restore form values on reload/back. Derive the first graph
  // from those visible controls too, rather than assuming HTML defaults.
  applyView();
  root.hidden = false;
  root.nextElementSibling.hidden = true;
  // Fragment links arrive before the initially hidden demo can be scrolled to.
  if (location.hash === '#steering-title') root.scrollIntoView({block:'start'});
}
