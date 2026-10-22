# 第 4 章实验：电流转向与共模路径

[教材正文](../../04-差分放大器/README.md) · [Windows 环境](../../../docs/WINDOWS.md) · [模型来源](../../../models/README.md)

正文只使用两幅曲线：电流怎样从一支路转向另一支路，以及尾管电压变化为何带来共模电流。这里保存完整条件、端口定义、CSV、展开网表和日志。MOS 均为实际 GF180MCU 模型，尚未进行硅片测量。

## 从仓库根目录复现

```powershell
.\.venv\Scripts\python.exe scripts/run_differential.py --check
.\.venv\Scripts\python.exe scripts/plot_differential.py
.\.venv\Scripts\python.exe scripts/check_differential.py
.\.venv\Scripts\python.exe scripts/check_repo.py
```

沿用现有原生 ngspice 47、Python 与模型，无需 WSL、版图工具或额外 Python 包。`--check` 使用已提交指标作 2% 相对误差、1e-7 V/V 绝对误差的参考漂移检查；始终执行更严格的内部一致性检查。首次有意重建基线可不带 `--check`，随后应审阅差异，不能以覆盖旧指标来消除失败。

仿真入口为 [run_differential.py](../../../scripts/run_differential.py)，源模板为 [pair.cir](pair.cir)。每次展开的工作目录位于忽略的 `build/ch04/`；运行器把两份固定模型放到对应目录。归档的展开网表引用相邻模型文件，若要单独运行，也需把模型文件复制到同一工作目录。以下日志的首行记录进程退出码，正文来自实际 ngspice。

## 受控条件

| 项目 | 值 |
|---|---|
| 工艺 | GF180MCU nmos_3p3，固定提交 `9f992d5a9186d1f7820c58f039c484ad35b2edea`，typical |
| 温度与随机项 | 27 °C，sw_stat_global=0、sw_stat_mismatch=0 |
| 电源、输入共模、标称尾电流 | 3.3 V、1.4 V、80 µA |
| 输入管 | 两管 W/L=10/1 µm，体接地 |
| 真实尾管 | W/L=10/0.28 µm，源、体接地，栅压标称约 0.794733 V |
| 负载 | 默认每侧 20 kΩ；不等负载对照为 20.1 kΩ 与 19.9 kΩ |
| 结几何 | 每管 AD=AS=5e-12 m²，PD=PS=21e-6 m；原理图级假设 |
| 差分转向扫描 | 固定 VCM，VID 从 −0.65 到 +0.65 V，步进 2 mV |
| 共模扫描 | 固定 VID=0，VCM 从 0.75 到 3.3 V，步进 5 mV |
| 局部增益 | 1 Hz AC；差模输入 ±0.5 V，共模输入两边各 1 V；AC 数值是线性归一化激励 |
| DC 导数复核 | 在工作点两侧 ±1 mV 作中心差分，分别改变 VID 与 VCM |

真实尾管的栅压先在**理想尾源电路的同一个 T 电压**下按 80 µA 校准，再固定不变。两种尾源的标称输出与 T 电压相差小于 3 µV，避免把不同工作点误当成结构差异。尾管校准本身也是实际网表执行，不使用平方律估算值冒充模型结果。

## 数据与执行记录

| 场景 | 主要数据 | 展开网表与日志 |
|---|---|---|
| 理想尾源、电流转向 | [完整转向 CSV](data/ideal-steering-sweep.csv) | [网表](decks/ideal-steering.cir) · [日志](logs/ideal-steering.txt) |
| 理想尾源、共模 | [共模 CSV](data/ideal-common-sweep.csv) | [网表](decks/ideal-common.cir) · [日志](logs/ideal-common.txt) |
| 真实尾管、共模 | [共模 CSV](data/mos-common-sweep.csv) · [工作点](data/mos-common-op.csv) | [网表](decks/mos-common.cir) · [日志](logs/mos-common.txt) |
| 真实尾管、不等负载 | [共模 CSV](data/mos-unequal-load-sweep.csv) · [差模 AC](data/mos-unequal-load-dm.csv) · [共模 AC](data/mos-unequal-load-cm.csv) | [网表](decks/mos-unequal-load.cir) · [日志](logs/mos-unequal-load.txt) |
| 尾管校准 | [扫描 CSV](data/tail-calibration.csv) · [修正工作点](data/tail-calibration-refine.csv) | [扫描网表](decks/calibrate.cir) · [扫描日志](logs/calibrate.txt) · [修正网表](decks/calibrate-refine.cir) · [修正日志](logs/calibrate-refine.txt) |

其余 OP、AC 与局部 DC 数据也在 `data/`，统一汇总于 [metrics.json](data/metrics.json)。[run.json](data/run.json) 记录工具版本、可执行文件 SHA-256、模型版本、逐文件哈希和检查内容。运行器、模板、展开网表、日志与 CSV 均参与哈希记录，仓库检查器会识别仿真后被改写的文件。

## 怎样读这些数据

`i1_A`、`i2_A` 是通过零伏传感源测得的**外部漏端支路电流**，可直接核对 RD 压降；`is1_A`、`is2_A` 是源端汇入 T 的电流，它们的和才是这里测量的尾端电流。`body_return_A` 是输入管的合计体端回流。实际模型满足漏端电流之和减去源端电流之和等于体端回流，不能强迫四端器件的漏、源传导电流完全相等。

这解释了一个细小但可重复的结果：即使理想尾源固定，标称漏端支路电流仍比 40 µA 略大，单端共模增益约为 +5.03e-4 V/V。该共模响应由完整模型的端口电流变化体现；简化的 gm/gmb/gds 模型忽略体传导电流，给出零。不能把 gmb 与体传导电流混为同一个量。匹配电路的两边仍相同，差分共模响应因对称性抵消。

本章将三个层次分别核对：

- 全部端口的 DC KCL 与尾电流守恒；正负差分输入的交换对称性。
- 完整工艺模型的局部 DC 导数与 1 Hz AC 结果，相对误差小于 0.02% 或绝对误差小于 3e-6 V/V。
- 用 OP 的 gm/gmb/gds 建立独立节点方程，差模结果与完整模型相差小于 0.5%；共模下保留约化预测与完整模型结果，不强求省略体电流后的零值精确成立。

纯解析公式另由 [check_differential.py](../../../scripts/check_differential.py) 使用独立节点盖章检查，包括两倍尾阻抗、负载不对称转换、两种退化连接和 Gilbert 单元。它检查代数与符号，不是工艺仿真，也不是教学有效性的证明。

图 4.1-2 的平方律虚线使用实测零点斜率 $G_{md}=|A_{dd}|/R_D$ 对齐，令 $\beta_{fit}=G_{md}^2/I_T$、$V_{OV,fit}=I_T/G_{md}$；这两个数只是局部形状对照参数。其余数据曲线不作拟合、平滑或抽点。[绘图脚本](../../../scripts/plot_differential.py) 同时输出 SVG 与 PNG。

共模图中的浅色区按照扫描点的 VDS−VDSAT 符号标记。当前实际尾源电路在该离散判据下得到约 1.105～3.230 V 的区间；这不是保证失真、增益误差或 PVT 规格的输入共模范围，更不能直接拿它替代正文中对输入差与输出摆幅的联合检查。

本轮真实工艺实验仅覆盖电阻负载输入对、理想/固定栅 MOS 尾源和确定性负载不等。源极退化、PMOS 输入、MOS 负载与 Gilbert 单元在本章完成解析讲授与适用条件检查，尚未逐一做 GF180MCU 电路仿真；未进行随机失配、噪声、PVT 或版图提取验收。原有第 2、3 章数据与 19 个网表继续独立保留。
