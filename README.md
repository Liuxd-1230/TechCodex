# TechCodex

把技术问题写清楚，也把验证它的方法留下来。

TechCodex 是一个持续维护的中文技术知识库。第一个系列是 [《从零开始的模电生活》](模拟/README.md)：基于拉扎维《模拟 CMOS 集成电路设计》第二版的理解、推导与实验笔记。后续数字电路、Python、PCB、Git、电力电子等主题将各自组织，不共用模拟电路专属的目录结构。

这里关心的是：拿到一个陌生电路时，怎样先预测行为，再找到决定性能的器件和节点，最后用实验检查判断。公式、原理图、真实工艺仿真和分析放在一起阅读。

## 目前可以读什么

| 内容 | 状态 |
|---|---|
| [MOS 器件：先认识工作点](模拟/02-MOS器件.md) | 第一篇正文；转移特性、输出特性、体效应、gm/Id 与长度实验已运行 |
| [单级放大器：共源级专题](模拟/03-共源级.md) | 共源级、源极退化与频率响应预告已验证；第 3 章其余拓扑待续 |
| 第 4～10 章 | 尚未撰写；见 [实施路线](docs/PLAN.md) |

这是首批可发布内容，**完整系列仍在建设**。不会把章节提纲算作正文，也不会把仿真器能加载模型等同于电路设计已经完成。

## 复现实验

在 Windows PowerShell 中，从仓库根目录执行：

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe scripts/bootstrap.py
.\.venv\Scripts\python.exe scripts/run.py --check
.\.venv\Scripts\python.exe scripts/plot__device_cs__paper.py
.\.venv\Scripts\python.exe scripts/draw_schematics.py
.\.venv\Scripts\python.exe scripts/check_repo.py
```

不需要激活虚拟环境，不需要 WSL、容器、完整版图工具链或商业 PDK。首次安装 ngspice 需要联网；固定版本的 GF180MCU 模型已经随仓库保存，仿真本身可离线运行。

详见 [Windows 环境与复现](docs/WINDOWS.md)、[模型来源与限制](models/README.md)、[实验说明](模拟/实验/README.md) 和 [验证记录](docs/VALIDATION.md)。其他系统使用原生 ngspice 和相同 Python 脚本；当前实际验收平台为 Windows x86-64。

## 仓库结构

```text
模拟/              系列首页、文章、图和独立实验资源
models/            开源模型、上游许可证和版本/哈希清单
scripts/           安装、仿真、绘图、原理图和检查脚本
docs/              实施路线、环境、来源和验收记录
```

正文、代码和自绘图见 [MIT 许可证](LICENSE)。GF180MCU 原始模型保留 [Apache-2.0 许可证](models/gf180mcu/LICENSE)。本文不包含教材原图或商业工艺模型。
