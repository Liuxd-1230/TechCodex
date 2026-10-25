# 噪声实验：从谱密度到可检查的 OTA 预算

本实验服务于[第 7 章](../../07-噪声/README.md)，保留 `.op`、AC、真实 `.noise`、完整源分解与失败候选。没有随机瞬态测量，也没有硅片精度保证。

## 条件与证据

- 平台：Windows，原生 ngspice 47，实际噪声求解日志使用 SPARSE 1.3；Python 及 NumPy 版本沿用仓库锁定环境。
- 模型：[官方 GF180MCU](https://github.com/google/gf180mcu-pdk) 3.3 V NMOS/PMOS，提交 `9f992d5a9186d1f7820c58f039c484ad35b2edea`，Apache-2.0；文件与许可见[模型清单](../../../models/manifest.json)。
- 设置：typical、27 °C、VDD=3.3 V、VCM=1.4 V；默认 CL=1 pF。NMOS 体接地，PMOS 体接电源。没有商业工艺模型。
- 端口：理想 Vdiff，经 +0.5/-0.5 的无噪声受控源驱动两输入。`.noise v(o) Vdiff` 折算到**完整差分电压**，不多乘或少乘二。
- 频率：1 Hz–1 GHz、每十倍频程 100 点；目标带为 100 Hz–100 kHz，另外检查 1 Hz–100 kHz 和 100 Hz–1 MHz。

按实验技能的适用轴，本次属于信号处理/硬件电路教学验证：证据是固定基线、源分解和可复现积分；主要风险是比较条件不一致、单位错误和模型精度外推。流程先固定指标，再运行基准和候选，最后记录失败后的尺寸调整。

[design.json](design.json) 在第一次噪声运行前固定规格；[adjustment.json](adjustment.json) 记录看到失败后追加的面积方案，不改变原指标。所有数据见 [metrics.json](data/metrics.json)，源、网表和运行记录的 SHA-256 见 [run.json](data/run.json)。

## Windows 复现

在仓库根目录运行；Python 环境安装方法见 [Windows 环境](../../../docs/WINDOWS.md)：

```powershell
uv run --locked scripts/run_noise.py --check
uv run --locked scripts/check_noise.py
uv run --locked scripts/plot_noise.py
uv run --locked scripts/build_noise_demo.py
node scripts/check_noise_demo.mjs
uv run --locked --group site scripts/book.py build
uv run --locked --group site scripts/check_site.py
```

`run_noise.py` 复用第 5、6 章已有 OTA 发生器，未改动旧实验。每个候选新求工作点、频响和噪声；`--check` 与此前输入 RMS 比较，容差 0.5%。它先删除本次预期输出，运行失败会停止，避免把旧 CSV 当作新结果。

## 单位校准，先于电路结论

ngspice 默认常见的是 ASD。这里显式使用 `set sqrnoise`，因此 `noise1` 中的 `onoise_spectrum`、`inoise_spectrum` 是 **V²/Hz**，`noise2` 的积分结果是 **V²**；最后才开平方得到 RMS。参阅 [ngspice 官方手册](https://ngspice.sourceforge.io/docs/ngspice-manual.pdf) 的 noise 与 sqrnoise。

用 10 kΩ、1 nF、27 °C 的 RC 电路校准：输入 PSD 应为 $4kTR=1.6576071894\times10^{-16}$ V²/Hz，输出为该值乘单极点模平方。1 Hz–1 MHz 的解析方差为 $4.1018681\times10^{-12}$ V²，仿真为 $4.1017751\times10^{-12}$ V²。有限上下限的 arctan 积分用于比较，没有把它硬当成从零到无穷的 $kT/C$。

每个 OTA 逐频点验证 $S_{out}/|A_v|^2=S_{in}$；可用器件组输出 PSD 之和等于总 PSD。独立 Python 积分与 ngspice 的全扫描积分误差小于 0.3%。采样间采用幂律插值，对白噪声和 $1/f$ 精确；正文和 JS 使用相同积分约定，并用独立解析算例验证。

## 网表与原始资源

| 案例 | 网表 | 频谱 CSV | 全日志 |
|---|---|---|---|
| 基准 | [baseline](decks/baseline.cir) | [spectrum](data/baseline-spectrum.csv) | [log](logs/baseline.txt) |
| 输入宽度 ×2 | [input-width-2x](decks/input-width-2x.cir) | [spectrum](data/input-width-2x-spectrum.csv) | [log](logs/input-width-2x.txt) |
| 全部宽度、电流 ×2 | [all-width-current-2x](decks/all-width-current-2x.cir) | [spectrum](data/all-width-current-2x-spectrum.csv) | [log](logs/all-width-current-2x.txt) |
| 仅负载 5 pF | [baseline-5p](decks/baseline-5p.cir) | [spectrum](data/baseline-5p-spectrum.csv) | [log](logs/baseline-5p.txt) |
| 追加面积方案 | [area-budget](decks/area-budget.cir) | [spectrum](data/area-budget-spectrum.csv) | [log](logs/area-budget.txt) |
| 电阻校准 | [resistor](decks/resistor.cir) | [spectrum](data/resistor-spectrum.csv) | [log](logs/resistor.txt) |

同目录还保存各案例的 `-op.csv`、`-ac.csv` 与 `-totals.csv`。CSV 列名写明单位，原文件不做平滑或删点。绘图源为 [plot_noise.py](../../../scripts/plot_noise.py)，积分源为 [noise_math.py](../../../scripts/noise_math.py)。

## 模型分组与适用范围

当前模型 `fnoimod=1`、`tnoimod=0`。实际可读的每器件总贡献、`.id`、`.1overf` 被保存。正文“闪烁”指 `.1overf`；“非闪烁”是总量减闪烁，包括模型其余机制，并不伪装成长沟道独立源。没有虚构感应栅噪声或互谱数据。电路层面的同源多路径已由 ngspice 传递函数合成。

输入对、PMOS 镜、尾管、参考网络的份额以**逐频率折回输入后的积分方差**计算。不能相加 ASD 或 RMS 百分比。基准的目标频带输入 RMS 为 28.249947 µV；面积方案为 2.588965 µV，后者在同一频带满足 4 µV 目标。其他指标与失效原因见[设计正文](../../07-噪声/06-噪声预算与设计.md)。

面积方案采用显式并联单元，避免超出宽度分箱，以及 wrapper 未转发 `m` 的问题。每个输入支路十个 100/1 µm 单元；PMOS 每只约 37.08/10 µm；尾管与参考不变。每个输入单元 AD=AS=5 µm²、PD=PS=21 µm，因此总寄生几何也增加。兼容性探针保留 [m=1 网表](compatibility/multiplicity-1-run.cir)、[m=10 网表](compatibility/multiplicity-10-run.cir)、[相同工作点](compatibility/multiplicity-10-op.txt)和[超宽 nf 探针的失败日志](compatibility/finger-probe-ngspice.txt)，这些诊断失败没有进入合格结果。单元独立性、共享扩散、版图匹配与面积约束尚未验证。

GF 的[官方低频噪声说明](https://gf180mcu-pdk.readthedocs.io/en/latest/analog/model_parameters/LV/LV_2_3.html)采用指定测试尺寸与偏置，频段 10 Hz–100 kHz。本实验的尺寸与部分频率超出其列出的测试条件。1 GHz 端点用于数学与全扫描积分检查，**不作为工艺实测精度承诺**；目标也只在 typical、27 °C 下检查。未声称 PVT 良率、闭环稳定性或硅片最优设计。

## 交互数据怎样生成

[build_noise_demo.py](../../../scripts/build_noise_demo.py) 先校验运行记录哈希，再直接提取基准的 1 Hz–1 MHz 输入 PSD、闪烁项与非闪烁项，保持每十倍频程 100 点。不改变偏置，不按用户操作任意缩放工艺曲线。

交互的“白噪声”“白噪声 + 1/f”是独立的解析模型，参数固定为 10 nV/√Hz 与 $f_c=1$ kHz。用户只选择数据来源和积分上下限。动画每一帧对当前显示的同一频带重新积分；工艺源切换即时完成，不在不同电路之间制造虚假的插值。无 JS 或数据加载失败时，静态图与完整公式仍在。
