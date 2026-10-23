# 资料、模型与工具来源

第六阶段查证于 2026-10-23：[McGraw Hill 第二版出版页](https://www.mheducation.com/highered/product/Design-of-Analog-CMOS-Integrated-Circuits-Razavi.html) 与 [NDL 收录的出版方 JPRO 详细目录](https://ndlsearch.ndl.go.jp/books/R100000137-I62131036100010000000) 交叉确认第 6 章 §6.1～6.7 的全部主要拓扑及 §6.8 EET、§6.9 ZVTC、§6.10 米勒对偶。NDL 条目为原著第二版日译本，来源与版本明确；未声称逐页取得英文原书全文。米勒、节点极点关联、差分被动/主动负载与单/多极点的覆盖映射见[知识覆盖](知识覆盖.md)。

[MIT 6.012 官方 Lecture 21](https://web.mit.edu/6.012/FALL00/www/handouts/lec21.pdf) 用于交叉检查共源频响、输入电流与米勒概念；[官方课程目录](https://web.mit.edu/6.012/) 进一步提供电压增益频响与时间常数课程位置。正文推导、两节点交互、图示与工艺实验独立完成，未复制教材图文。引文只用于来源定位，不以第三方转载全文代替授权资料。

第二版教学组织参考、阅读方式及独立核验原则见 [编辑说明](第二版编辑说明.md)。器件与单级放大器的补充一手资料包括 [MIT 6.012 官方讲义目录](https://ocw.mit.edu/courses/6-012-microelectronic-devices-and-circuits-spring-2009/pages/lecture-notes/) 和 [Clif Fonstad 的单管放大级讲义](https://ocw.mit.edu/courses/6-012-microelectronic-devices-and-circuits-fall-2009/18a2d9a52234f9e962d74b5599759767_MIT6_012F09_lec18.pdf)，用于交叉核对端口模型、体效应与电容近似；没有复制讲义图文。

查证日期：2026-10-21。书籍作为理论主线，不声称已在线取得或逐页核对原书全文。

第三阶段补充查证于 2026-10-22：[McGraw Hill 的第二版出版信息与总目录](https://www.mheducation.com/highered/product/Design-of-Analog-CMOS-Integrated-Circuits-Razavi.html)（ISBN 9780072524932）确认章节顺序；第 4 章按单端/差分、基本差分对及退化、共模、MOS 负载和 Gilbert 单元组织覆盖。[MIT 6.012 Lecture 19 原讲义](https://ocw.mit.edu/courses/6-012-microelectronic-devices-and-circuits-fall-2009/9932f87a7b5ec3d088d0e0836a05c622_MIT6_012F09_lec19.pdf) 用于交叉核对差模/共模分解与半电路思路。正文的符号、推导、数值例子与原理图独立完成；[章节覆盖表](知识覆盖.md) 明确与后续电流镜、共模反馈专题的分界。

第五阶段查证于 2026-10-22：下表的国家图书馆出版目录用于核对第 5 章四个主题，MIT Lecture 20 用于交叉检查有源镜像负载的信号汇合与共模解释。五管 OTA 的完整 KCL、两项工程指标、工艺尺寸选择、原理图与仿真由本项目独立建立，不从第三方读书笔记复制。

| 来源 | 用于什么 | 可追溯信息 |
|---|---|---|
| Behzad Razavi, *Design of Analog CMOS Integrated Circuits*, Second Edition | 第 2～10 章的知识组织；现有正文对应第 2～5 章 | 独立文字、推导和插图，不复制教材内容 |
| [原著第二版日译本的国家图书馆目录](https://ndlsearch.ndl.go.jp/books/R100000137-I62131036100010000000) | 核对第 5 章四个主题的目录顺序 | 来自出版书目，不冒充已取得原书全文 |
| [MIT 6.012，Lecture 20：Two Active Loads](https://ocw.mit.edu/courses/6-012-microelectronic-devices-and-circuits-fall-2009/resources/mit6_012f09_lec20_loads/) | 交叉检查镜像负载的差分到单端转换与共模讨论 | Fonstad，2009；本项目符号、KCL、图示与设计独立组织 |
| [GF180MCU 模型上游固定提交](https://github.com/google/globalfoundries-pdk-libs-gf180mcu_fd_pr/tree/9f992d5a9186d1f7820c58f039c484ad35b2edea) | 原始工艺模型与 Apache-2.0 许可 | [逐文件哈希](../models/manifest.json) |
| [GF180MCU 官方模型说明](https://gf180mcu-pdk.readthedocs.io/en/latest/analog/model_parameters/LV/LV_1.html) | 器件分类、实例参数与模型使用背景 | 文档本身持续变化，具体仿真以固定文件为准 |
| [GF180MCU 文档首页](https://gf180mcu-pdk.readthedocs.io/en/latest/) | Experimental Preview 的状态说明 | 不把公开预览模型当作制造签核 |
| [Berkeley BSIM4](https://bsim.berkeley.edu/models/bsim4/) | 紧凑模型背景与手册入口 | 本项目模型卡 version=4.5，未替换成网页上的其他模型版本 |
| [ngspice 官方下载页](https://ngspice.sourceforge.io/download.html) | 确认 Windows 原生程序分发 | 本次选用官方 47 控制台版本 |
| [ngspice 47 官方发布目录](https://sourceforge.net/projects/ngspice/files/ng-spice-rework/47/) | 下载 `ngspice-47_64.7z` | 47 版，2026-08-11 编译；64 位 GUI/console 包 |
| [ngspice 手册](https://ngspice.sourceforge.io/docs.html) | DC/AC/TRAN、工作点、wrdata 与批处理参数 | 使用发行版 47 为本次基准 |

ngspice 下载 URL：`https://downloads.sourceforge.net/project/ngspice/ng-spice-rework/47/ngspice-47_64.7z`。

本次下载包 SHA-256：

```text
59225971bd68cdd1199443649aa4615a9e6d684933f205ab49006a3942518f5a
```

此哈希来自本次官方来源下载的文件，作为后续复现的锁定值，不是声称上游提供了同算法的签名证明。可执行文件不提交到 Git。版本完整输出记录在 [run.json](../模拟/实验/data/run.json)，Python 依赖记录在 [requirements-lock.txt](../requirements-lock.txt)。

编辑阶段使用本机 pe-plots-paper 技能的 `eeplot` 辅助布局，并用其审图脚本检查印刷尺寸。仓库绘图脚本默认使用自带的独立 Matplotlib 样式，读者不依赖 Codex 技能、个人路径或其辅助库；数值数据相同，排版可能有细微差异。正文 SVG/PNG 的最终审图状态见 [验证记录](VALIDATION.md)。
