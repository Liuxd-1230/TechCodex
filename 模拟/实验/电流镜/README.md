# 电流镜与真实偏置 OTA：复现资源

这里支持 [第 5 章](../../05-电流镜与偏置/README.md) 的设计检查，正文不依赖先运行这些资源。

## 设计输入与数据读法

[design.json](design.json) 先固定电流窗口、误差、功耗和 OTA 标称工作点。先后检查短沟道失败候选、两种长沟道普通镜、经典自偏置共源共栅镜，然后从 40 µA 参考建立 OTA 的电阻偏置。原始展开网表在 `decks/`，完整程序日志在 `logs/`，全部数值在 `data/`，不是从绘图曲线反读数据。

- [metrics.json](data/metrics.json)：设计指标、候选结果、最终尺寸、OTA 工作点/增益、PVT 与启动结果。
- [run.json](data/run.json)：Windows、ngspice 版本及可执行文件哈希、GF180 模型版本、网表和数据逐文件 SHA-256。
- [普通镜 L=1 µm](data/medium.csv) · [共源共栅镜](data/cascode.csv)：交互的两条原始曲线。
- [OTA 网表](decks/ota.cir) · [输出钳位扫描](data/ota-output-compliance.csv) · [大信号输入扫描](data/ota-large-signal.csv) · [上电轨迹](data/ota-startup.csv)。

## 固定条件与端口

仿真使用 Windows 原生 ngspice-47，GF180MCU `nmos_3p3` / `pmos_3p3`，固定模型提交 `9f992d5a9186d1f7820c58f039c484ad35b2edea`，来源及 Apache-2.0 许可见 [模型说明](../../../models/README.md)。默认 VDD=3.3 V、typical、27 °C，全局和局部统计开关均为零。MOS 使用固定 AD=AS=5 µm²、PD=PS=21 µm；它们是已记录的结面积假设，不是版图提取值。

电流镜测试参考电流理想固定 40 µA，VO 从 0.05 到 3.00 V，间隔 10 mV。`internal_V` 对普通镜等于输出电压，对共源共栅镜是 X。工作区分别检查下管 VDS≥VDSAT，以及上管 VO−X≥VDSAT；最大电流误差则仅在事先指定的 0.4–2.6 V 窗口计算。两种条件独立，不能用其中一项替代另一项。

OTA 是五管核心加 MR 与约 60 kΩ 电阻；电阻是理想线性电阻，尚非工艺电阻版图。MR=10/1 µm、MT=20/1 µm、输入两管=10/1 µm，PMOS 两管约 3.708/1 µm。NMOS B 接地，PMOS B 接 VDD。输出正常不接直流负载。只有输出顺从扫描用 Vhold 钳位并记录外部平衡电流；只有上电测试加 1 pF 输出电容。

`ota-op.csv` 的 tail_A 是零伏传感器测得的真实尾支路电流，不用供电电流减参考电流冒充它。供电功耗从 −I(VDD) 得到，含参考支路。1 Hz 的 AC 差模输入为 ±0.5 V（端口归一化），共模输入为两边各 1 V；这是线性化激励，不是给实际电路施加一伏大信号。±0.1 mV DC 差分检查导数，再用独立 gm/gmb/gds 节点模型核对。

## 运行与检查

```powershell
uv run --locked scripts/run_mirrors.py --check
uv run --locked scripts/check_mirrors.py
uv run --locked scripts/plot_mirrors.py
uv run --locked scripts/export_mirror_demo.py
uv run --locked scripts/export_mirror_demo.py --check
uv run --locked scripts/check_repo.py
```

首次建立数据可省略 `--check`；后续保留它，检查是否偏离已提交的 OTA 参考结果。运行器不仅检查进程退出码，还检查有限数值、候选电流容差、标称 OTA 功耗与尾电流、核心管饱和余量、DC/AC 斜率一致和完整模型与三参数节点模型的增益一致。闭式公式另外用 96 组确定性参数的独立节点导纳矩阵交叉检查。

网页只读取已打包的 [预计算数据](../../../web/assets/demos/mirror-data.json)，逐列线性插值。导出时检查来源哈希；不按比例缩放已有曲线来伪造其他尺寸、温度或参考电流。所有生成文本使用 LF，避免 Windows 提交转换破坏哈希。

## 验证范围

PVT 仅为 ss/ff 在 27 °C，以及 typical 在 −20/85 °C 的独立冒烟检查，保持尺寸和电阻不变，不是全组合覆盖，也不是局部器件失配。标称输出目标在某些角或温度下失败，保留了结果；没有重调电阻掩盖漂移。电阻温度系数和工艺偏差尚未加入，不能据此宣称真实参考的温漂指标。

上电检查是一条 1 µs 电源上升、50 µs 观察的轨迹，不是 β 倍增器启动设计，也不构成全条件启动保证。输出/共模边界是有限步长下的 DC 饱和网格，不是失真、带宽、负载驱动或稳定性规格。宽摆幅与调节式共源共栅、β 倍增器的完整工艺实现、统计失配、噪声及寄生版图尚未验证。
