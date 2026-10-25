# Windows 环境与复现

[返回首页](../README.md) · [实验说明](../模拟/实验/README.md)

## 本次检测记录

2026-10-21，Windows x86-64，PowerShell。当前工作目录最初为空，没有覆盖已有仓库。Git 2.48.1.windows.1、Python 3.13.12、pip 25.3、GitHub CLI、Node.js、CMake 已存在；PATH 与常见安装位置未发现 ngspice。Python 原环境有 NumPy、SciPy，但没有 Matplotlib 和 py7zr。本项目创建独立 `.venv` 安装依赖，没有改全局 Python。

另外检测到了 TeX Live 和 Poppler，仅用于编辑阶段的图形印刷尺寸检查，读者复现实验不依赖它们。没有安装 Magic、KLayout、Xschem、OpenROAD 或整套 PDK 构建工具；原生 ngspice 可直接运行目前需要的模型。

环境按 Windows 配置，不使用 MacPorts 路径，也不要求 WSL。

## 从干净检出开始

前提是 Python 3.13 x64 可用。先用 `python --version` 检查，避免误用 Windows 商店的占位命令。在仓库根目录执行：

```powershell
uv sync --locked
uv run --locked scripts/bootstrap.py
uv run --locked scripts/run.py --check
uv run --locked scripts/plot__device_cs__paper.py
uv run --locked scripts/draw_schematics.py
uv run --locked scripts/check_repo.py
```

`pyproject.toml` 固定 NumPy 2.5.4、Matplotlib 3.11.2 和 py7zr 1.1.4；仓库只有一个 `uv.lock`。原 pip 快照保存在[历史记录](../模拟/实验/requirements-v1.txt)，仅用于追溯旧实验环境。`uv sync --locked` 按锁文件安装基础环境；运行脚本无需激活环境，也不需要修改 PowerShell 执行策略。当前 Python 版本由 `.python-version` 固定为 3.13.12，uv 会使用兼容的现有 Python。基础环境不包含 PyTorch、Transformers 或模型文件。需要本地 RAG 时，按[可选 RAG 环境说明](RAG.md)明确选择 CPU 或 CUDA 安装；配置遵循 [uv 的 PyTorch 索引指南](https://docs.astral.sh/uv/guides/integration/pytorch/)，两种 extra 不能同时启用。

`bootstrap.py` 先验证仓库内模型 SHA-256，再依次检查 `NGSPICE`、本项目 `.tools/Spice64/bin/ngspice_con.exe` 与 PATH。如果已安装则复用；否则下载官方 ngspice 47 Windows 64 位压缩包，核对 SHA-256 后解压到 `.tools/`。不修改系统 PATH、注册表或用户 `.spiceinit`。压缩包来源和实测 SHA 见 [来源记录](SOURCES.md)。

如果要使用已有的原生版本：

```powershell
$env:NGSPICE = 'C:\tools\ngspice\bin\ngspice_con.exe'
uv run --locked scripts/run.py --check
```

以上是路径示例，请按本机位置填写。`NGSPICE` 传入可执行文件的完整路径，不含额外命令参数；含空格的路径也由 Python 参数数组安全传递。不要把 GUI 启动器或未经验证的第三方封装误作控制台程序。已安装版本会记录在每次输出的 `run.json` 中；当前基准来自 ngspice 47。

## 为什么要复制到 build

原始 GF180MCU 模型内部使用相对文件名再次调用自身的 `.lib` 分区。运行器为每个实验创建 `build/<case>/`，把模型的两份原始文件与展开后的 ASCII 网表放在一起，再将该目录设为工作目录。这样不需要改上游 `.lib` 路径，不需要硬编码个人安装位置。

包含 `@LENGTH@`、`@VG@`、`@RS@` 的源网表是模板。可直接执行的具体网表保存在每个 `build/<case>/run.cir`。脱离 Python 运行时，应将它与 `design.ngspice`、`sm141064.ngspice` 放在同一目录，在该目录执行：

```powershell
& 'C:\tools\ngspice\bin\ngspice_con.exe' -n -b run.cir
```

`-n` 忽略个人初始化文件，避免别处设置的单位缩放或兼容模式影响结果。本次上游文件在 ngspice 47 默认模式下已经通过测试，没有额外开启 PSpice/LTspice 兼容模式。尺寸使用 `w=10u l=1u`，不同时设置 `scale=1u`，以免重复缩放。

RS=0 的版本在展开后使用 0 V 理想电压源连接源极与地，表示理想短路；避免 ngspice 把零电阻自动调整为一个极小电阻。CSV、脚本和记录统一使用 LF 换行，模型文件则按原始字节保留，防止系统换行差异破坏数据哈希。

## 输出与故障定位

`build/` 保存各次日志、完整网表和 ngspice 的文本输出，属于可重新生成的本地文件。公开的基准数据及测量定义见 [实验说明](../模拟/实验/README.md)，`run.py` 会重新生成这些数据；实验前建议先提交自己的修改，完成后用 `git diff` 检查差异。

运行器检查退出码、典型错误文字、输出文件存在性、有限数值和物理一致性。每次运行前先删除该次预期的输出，避免上次残留文件被误认为成功。错误日志仍保留供诊断，不自动修改模型参数或放松收敛精度。

若 `--check` 失败，先看 `build/<case>/ngspice.log`。模型校验失败应检查换行转换或本地改动；不可直接更新哈希来绕过。网络下载失败可手工从官方来源取得同名压缩包放到 `.cache/`，哈希检查仍然执行。

其他系统可安装原生 ngspice 后运行同一 Python 脚本。当前未实际验收 Linux/macOS，也未保证所有旧版 ngspice 都具有相同误差。项目主目录含中文，已在本次 Windows 原生运行中验证；对包含特殊字符的其他路径尚未逐一测试。
