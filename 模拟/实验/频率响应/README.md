# 第 6 章实验：把幅相变化还给具体节点

正文入口：[频率响应](../../06-频率响应/README.md)。这里保留完整数据、展开网表和日志；读正文不必先运行它们。

## 模型、工具与固定条件

继续采用 [官方来源与锁定哈希](../../../models/README.md) 的 GF180MCU 3.3 V NMOS/PMOS，模型提交 `9f992d5a9186d1f7820c58f039c484ad35b2edea`，Apache-2.0；没有商业工艺。Windows 原生 ngspice 47 的 console 版，无 WSL、容器、Cadence 或版图工具依赖。`NGSPICE` 环境变量可选择其他平台的原生可执行文件。

全部 GF180 实验：典型角、27 ℃、VDD 3.3 V，统计全局和失配开关均为 0，AD=AS=5 µm²、PD=PS=21 µm。结几何是第 5 章沿用的固定教学约定，宽度变体也不冒充版图提取。每个网表明确端口、尺寸与激励，模型文件由公共运行器复制到隔离工作目录。

[design.json](design.json) 固定 1 pF、增益 ≥150 V/V、−3 dB 带宽 ≥100 kHz、功耗 ≤0.45 mW，先于频域结果生成。基准参数从已归档的第 5 章 metrics.json 读取，不重新调整。`run_frequency.py` 不调用第 5 章的主程序，也不覆盖其数据。

AC 扫描 1 Hz～10 GHz、每十倍频 80 点。高频端用于看清模型路径，不表示已经验证工艺在 10 GHz 的实际精度。AC CSV 第一列为 Hz，其后依次为各电压的实部、虚部，列名保留端口名并增加 real/imag 后缀；导纳测试电流采用相同约定。端口均注明；没有把电流增益、差分电压增益与单端电压增益混画。

## 各实验回答什么

| 网表前缀 | 激励、终接与目的 |
|---|---|
| `ota-unloaded`, `ota-1p`, `ota-5p` | 保留第 5 章的 MR/RREF 与全部 MOS；理想差分源，右单端自由输出，只改 CL。`unloaded` 使用可忽略的 $10^{-24}$ F 外接电容，器件寄生始终存在 |
| `ota-wide` | 仅输入 W 从 10 变 20 µm，检查跨导、电容和 DC 变化 |
| `ota-long` | M1～M4 的 W、L 同比加倍，尾与参考不变；保持大致 W/L，检验增加输出电阻的速度代价 |
| `ota-current` | 全部 MOS 的 W 加倍、RREF 减半，L 不变；功耗超预算的候选保留 |
| `ota-stiff-bias` | B 加原 DC 值的理想电压源，AC 固定；隔离参考网络动态影响，其余条件不变 |
| `probe-x/o/t/b/input` | 4 个 DC 钳位源只用于提取导纳和输入电流项；重建时撤去钳位，通过 G+sC 求自由节点电压 |
| `cs`, `cg`, `cascode`, `sf` | NMOS 10/1 µm；CS/CG 的参考栅压约 0.900170 V，40 kΩ、1 pF；CS/级联栅前 10 kΩ，级联上栅 1.8 V；CG 为理想源端电压驱动；SF 栅 DC 1.4 V、源端理想 40 µA、栅前 10 kΩ、CL 1 pF |
| `cs/cascode-input-limited` | 上述对应拓扑改为 RS=1 MΩ、CL=0.05 pF；将输入加载变得重要，避免只用一组负载给拓扑排速度名次 |
| `passive-diff` | 输入管 10/1 µm、80 µA 理想尾源、VCM 1.4 V，两只 40 kΩ 与两只 1 pF；CSV 为右输出、左输出、尾电压，激励 $v_{id}=1$ |
| `analytic-cgd`, `analytic-no-cgd` | 独立显式受控源/电阻/电容模型，非 GF180；与 Python 完整两节点公式逐点复数比较，验证交互模型的电气含义 |

## 怎样复现

先按 [Windows 配置](../../../docs/WINDOWS.md) 安装已锁定依赖，仓库根目录运行：

```powershell
.\.venv\Scripts\python.exe scripts/run_frequency.py --check
.\.venv\Scripts\python.exe scripts/check_frequency.py
node scripts/check_frequency_demo.mjs
.\.venv\Scripts\python.exe scripts/draw_frequency.py
.\.venv\Scripts\python.exe scripts/plot_frequency.py
.\.venv\Scripts\python.exe scripts/check_repo.py
.\.venv-site\Scripts\python.exe scripts/book.py build
.\.venv-site\Scripts\python.exe scripts/check_site.py
```

运行器保留失败信息；每次删除预期临时输出以防陈旧文件误通过。`--check` 先与已提交主要增益/带宽比较，容差 0.5%，再写新运行记录；不会根据新结果改变指标。图像只读取归档 CSV，不平滑、拟合或将解析曲线伪装为工艺数据。线性模型与真实模型各自明确标注。

[metrics.json](data/metrics.json) 保存工作点、饱和余量、功耗、带宽和第一次向下 0 dB 穿越。带宽用相邻扫描点的 **dB 对 log(f)** 线性插值，相对 1 Hz 幅度降低 $10\log_{10}2$；它不是极点提取。相位由复数结果 atan2 后连续展开，单位度。反相电路的恒定 180° 与附加相位分开解释；`unity_Hz=null` 表示没有找到穿越，不虚构单位增益频率。

[nodal.json](data/nodal.json) 的 G 单位 S、C 单位 F，顺序 X、O、T、B；输入项为 S 和 F。通过 1/10/100 kHz AC 端口测试提取矩阵，检查其频率一致性，再与未钳位直接 AC 在 30 MHz 以下对照。模态由 $-C^{-1}G$ 特征值求得，并检查稳定性、矩阵可逆与时间常数系数恒等式。左右特征向量参与度支持输出、镜节点和偏置模态的关联；快速模态仍只是当前准静态网络结果。

[run.json](data/run.json) 记录平台、Python/ngspice 版本、可执行文件与模型哈希，以及指标文件、生成脚本、原始网表、日志、CSV 和汇总的 SHA-256。原始 ngspice 输出只规范换行和文件末尾空白，不过滤警告或计算信息。前五章资源保持独立。

## 当前验证边界

已实现全部主要拓扑的标称工艺 AC；CS 解析式与独立 SPICE、SF/CG 节点式、级联三节点式与镜像路径模型用独立数值方程核验。OTA 保留原 DC、体端、参考支路并检查所有核心管饱和，完整导纳重建与直接 AC 对照。交互计算 2525 个控制状态检查 KCL、极点和边界，不代表真实工艺扫描。

未进行第 6 章全 PVT、Monte Carlo、高频 CMRR、版图/封装提取、非准静态模型验收、噪声或闭环稳定性验收；不将 GHz 级模型结果作为芯片保证。EET、ZVTC 高阶递推与米勒对偶只安排深入阅读，没有宣称完成其全部一般证明。静态公式与简化电容用于解释机制，真实器件结果以原生 ngspice 档案为准。
