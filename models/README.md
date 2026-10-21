# 工艺模型与来源

当前使用 GF180MCU 公开原始模型，不安装完整 PDK。

| 项目 | 本次选择 |
|---|---|
| 上游 | [google/globalfoundries-pdk-libs-gf180mcu_fd_pr](https://github.com/google/globalfoundries-pdk-libs-gf180mcu_fd_pr) |
| 提交 | `9f992d5a9186d1f7820c58f039c484ad35b2edea` |
| 原始文件 | `models/ngspice/design.ngspice`、`models/ngspice/sm141064.ngspice` |
| 许可 | [Apache-2.0](gf180mcu/LICENSE)，保留原始版权头 |
| 模型 | 3.3 V NMOS/PMOS，`level=54`，BSIM4；模型卡 `version=4.5` |
| 实例 | `X1 d g s b nmos_3p3 w=10u l=1u ...` |
| 主线条件 | typical、27 °C、无随机全局变化及失配 |
| 验证平台 | Windows x86-64 原生 ngspice 47 |

上游仓库目前已归档。本项目固定提交，保留完整的这两份模型文件，不重排分档、不抽取一个简化 `.model` 替代原文件。[manifest.json](manifest.json) 列出逐文件 SHA-256；`fetch_models.py` 可从固定提交重新取得并核对内容。Git 对该目录关闭文本换行转换，避免 Windows 检出改变原始字节。

`design.ngspice` 默认把 `sw_stat_global`、`sw_stat_mismatch` 都设为 1。本项目在 include/lib 之后显式覆盖为 0，保持确定性。没有直接改上游文件。将来 Monte Carlo 实验会作为独立实验打开相应开关并记录种子、样本数和统计定义。

这里的 `nmos_3p3` 是上游子电路，内部 MOS 名为 `m0`。工作点使用 `@m.x1.m0[gm]` 等访问，而不是把子电路名当作原生 MOS 参数对象。3.3 V NMOS 模型最短 L 为 0.28 µm；不能因为工艺名称是 180 nm 就自动使用 0.18 µm。

`vth`、`vdsat`、gm 和结电容等是工作点相关的模型输出，不是对所有电压都固定的器件常数。BSIM4 仍然是紧凑模型；本次测试检查了模型加载和若干偏导、电路行为，没有重新验证其硅片相关性，也没有做流片签核。[官方 PDK 文档](https://gf180mcu-pdk.readthedocs.io/en/latest/) 本身也标注为 Experimental Preview。

本次没有使用 SMIC 或其他商业工艺文件。若将来由用户提供合法且授权允许的模型，应放入默认忽略的 `private-models/`，单独检查授权范围与分发限制；不通过未授权渠道下载，不把私有模型提交到公开仓库。`.gitignore` 只是默认防线，公开前仍需检查暂存文件。
