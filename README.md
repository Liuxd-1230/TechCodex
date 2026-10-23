# TechCodex

## 从零开始的模电生活

基于拉扎维《模拟 CMOS 集成电路设计》第二版的理解、推导与实验笔记。

从一只 MOS 管的电场与电荷出发，沿着电流路径和端口关系，逐步理解放大、加载、偏置与电路设计的取舍。公式用于解答问题，原理图标明节点如何响应，真实工艺实验留在需要检验判断的位置。

**[打开在线阅读站](https://liuxd-1230.github.io/TechCodex/)** · [在 GitHub 阅读](https://github.com/Liuxd-1230/TechCodex/blob/main/模拟/README.md) · [从源跟随器样章开始](模拟/03-单级放大器/03-源跟随器.md)

### 从哪里开始

| 你现在关心的问题 | 建议入口 |
|---|---|
| 栅极不导电，为什么能控制漏流？ | [第 2 章：电场、电荷与电流](模拟/02-MOS器件.md) |
| 小信号里哪些源要置零，哪些必须保留？ | [3.1 端口与分析方法](模拟/03-单级放大器/01-分析方法.md) |
| 不同负载怎样改变增益和摆幅？ | [3.2 共源级](模拟/03-共源级.md) |
| 增益不到一的电路为什么有用？ | [3.3 源跟随器样章](模拟/03-单级放大器/03-源跟随器.md) |
| 从源端输入为什么会同相放大？ | [3.4 共栅级](模拟/03-单级放大器/04-共栅级.md) |
| 多叠一只管，输出电阻为何能显著提高？ | [3.5 共源共栅](模拟/03-单级放大器/05-共源共栅.md) |
| 两个输入怎样争取同一股电流，又怎样拒绝共同变化？ | [第 4 章：差分放大器](模拟/04-差分放大器/README.md) |
| 怎样选择、设计和验证一份真正能用的偏置电流？ | [第 5 章：电流镜与偏置](模拟/05-电流镜与偏置/README.md) |
| 为什么有很高的直流增益，却跟不上快速变化？ | [第 6 章：频率响应](模拟/06-频率响应/README.md) |

现有正文覆盖第 2～6 章：从 MOS 和单级放大器，经过差分对、电流镜与真实偏置 OTA，再从电荷路径进入各类放大器的频率响应。第 6 章加入米勒交互与保留原偏置的 OTA 频域设计，比较增益、速度、尺寸和功耗。第 7～10 章尚未成稿，具体覆盖与边界见 [知识地图](docs/知识覆盖.md)。

### 教材、暗线与实验

教材知识负责系统解释器件和各类重要拓扑；电路演化把这些方法串起来；实验用于检验或修正某个判断。它们有不同的任务，阅读时不必先安装工艺模型。

已有 Windows 原生 ngspice + GF180MCU 实验、原始 CSV、模型哈希与生成脚本完整保留在 [实验资源](模拟/实验/README.md)。第二版的组织方法与旧版对照见 [编辑说明](docs/第二版编辑说明.md)。

<details>
<summary>我要运行仿真或构建网站</summary>

仿真在 Windows PowerShell 中从仓库根目录运行：

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe scripts/bootstrap.py
.\.venv\Scripts\python.exe scripts/run.py --check
.\.venv\Scripts\python.exe scripts/run_differential.py --check
.\.venv\Scripts\python.exe scripts/check_repo.py
```

无需 WSL、容器或完整的版图工具链。配置、模型与实际验证范围见 [Windows 复现](docs/WINDOWS.md) 和 [模型说明](models/README.md)。网站单独使用 `.venv-site`，见 [构建与发布](docs/网站维护.md)。

</details>

TechCodex 以后也会收录数字电路、Python、PCB、Git、电力电子等技术笔记，模拟系列保存在独立的 `模拟/` 目录。原创文字、代码和自绘图采用 [MIT 许可](LICENSE)；GF180MCU 模型与 MathJax 保留各自 Apache-2.0 许可。未包含教材原图或商业工艺文件。
