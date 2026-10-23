# 可复现实验

[系列首页](../README.md) · [安装步骤](../../docs/WINDOWS.md) · [模型说明](../../models/README.md)

第二版把详细参数与误差统计留在实验阅读路径。原有分析和结果完整保存在 [首版器件笔记](首版器件笔记.md) 与 [首版共源级笔记](首版共源级笔记.md)；按教材顺序阅读可从 [第 2 章](../02-MOS器件.md) 和 [第 3 章](../03-单级放大器/README.md) 开始。

第 4 章新增 [差分对实验](差分对/README.md)，包括同工作点的理想/真实尾源比较、电流转向和不等负载的共模转换。它使用独立入口 `scripts/run_differential.py --check`，原有入口和数据保持独立。

第 5 章的 [电流镜与 OTA 实验](电流镜/README.md) 先固定设计指标，比较普通/共源共栅镜，再实现电阻参考的五管 OTA 核心。入口是 `scripts/run_mirrors.py --check`，包括工作区、DC/AC 增益、少量 PVT 与一条上电轨迹。

第 6 章的 [频率响应实验](频率响应/README.md) 保留第 5 章基准，研究 OTA 的负载、节点导纳、尺寸和电流取舍；同时独立验证 CS/SF/CG/cascode 与电阻负载差分对。实时米勒解析交互与真实 GF180 数据分开，原始复数 AC、完整网表和日志全部保留。

从根目录执行 `python scripts/run.py --check`，脚本自动定位仓库、展开模板并调用原生 ngspice。这里的 `python` 应为已安装依赖的项目虚拟环境解释器；完整 Windows 命令见安装步骤。

| 源文件 | 测试条件与输出 | 用途 |
|---|---|---|
| [v0-device.cir](v0-device.cir) | W=10 µm，L=0.28/1/2 µm；VDS=1.65 V，VGS=0.3～1.5 V，步进 5 mV | 转移特性、gm/ID、gm/gds；中心差分核对 gm |
| [v0-output.cir](v0-output.cir) | W/L=10/1 µm；VGS=0.8/0.9/1.1/1.3 V；VDS=0～3.3 V，步进 10 mV | 输出曲线；中心差分核对 gds |
| [v0-body.cir](v0-body.cir) | VGS=0.9 V、VDS=1.65 V 固定；VSB=0～0.8 V，步进 10 mV | 隔离体效应，检查阈值方向 |
| [v1-common-source.cir](v1-common-source.cir) | VDD=3.3 V、VG=0.9 V、RD=39 kΩ、CL=2 pF、RS=0/1 kΩ | 偏置、低频 AC、DC 斜率、瞬态 |
| [run.py 中的 PVT 网表生成](../../scripts/run.py) | NMOS/PMOS 同时测试，typical/ff/ss × −40/27/125 °C | 兼容性冒烟测试，非放大器全 PVT 验收 |

除表中专门变化的量外，主线采用 typical、27 °C、随机开关为 0；MOS 结几何见 [符号约定](../约定.md)。PVT 冒烟器件采用子电路默认结面积和周长（零），只测试偏置电流，因此不拿它们做电容或带宽比较。

## 数据怎样回到文章

`data/*.csv` 是实际仿真的数字结果。`metrics.json` 是若干工作点和测量汇总，`run.json` 记录工具版本、模型哈希、网表哈希和默认条件。工作点记录并非随机生成，也不是解析公式构造的曲线。

`run.py --check` 在写入新汇总前，将主要参考指标与已经提交的数据比较，容许 2% 的跨版本数值变化；同时始终执行更严格的内部物理检查：gm/gds 与有限差分相差小于 1%，KCL/AC/DC 的低频增益相差小于 0.3%。跨版本门限不能代替工作点与物理一致性检查。运行前的参考 `metrics.json` 必须存在。

CS 的低频增益取 10 Hz AC 输出实部，因为输入 AC=1、理想输入源阻抗为 0。−3 dB 频率相对于低频增益幅值定义，在 80 点/十倍频的对数频率扫描上作相邻点插值。瞬态为 1 mV、10 kHz 正弦，步长上限 0.2 µs、总时长 0.4 ms。暂不由该瞬态报告 THD 或最大摆幅。

运行 [绘图脚本](../../scripts/plot__device_cs__paper.py) 得到 SVG 和 600 dpi PNG。正文引用 SVG，PNG 用于视觉检查。除 `cs-bode` 的红色虚线以外，数据曲线均来自 ngspice；该虚线是明确标注的 Rout·CL 解析近似。没有对数据进行平滑、拟合或抽点。

原理图由 [draw_schematics.py](../../scripts/draw_schematics.py) 确定性生成，节点名称与网表一致。它们是可缩放的原创教学图，不是版图或制造交付文件。

第 7 章的 [噪声实验](噪声/README.md) 使用同一 OTA 的真实 `.noise`，校准单边谱单位，保留源分解、失败候选及追加面积方案。积分边界、输入端口、模型设置和 Windows 复现均有独立记录。
