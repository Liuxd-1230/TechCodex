# 本地教材检索

检索原书、精读邻页，再打开原始页图核对电路。这个工具运行在本机 stdio 上，既不提供网页聊天入口，也不参与阅读站构建。PDF、模型、OCR 文本、向量与页图缓存均留在 `.local/`，不进入 GitHub 或 Pages。

## 安装与路径

项目保持 Python 3.13，依赖统一由根目录 `uv.lock` 锁定。正常仿真和建站不安装 PyTorch：

```powershell
uv sync --locked
uv run --locked scripts/bootstrap.py
uv sync --locked --group site
uv run --locked --group site scripts/book.py build
uv run --locked --group site scripts/check_site.py
```

RAG 使用同一锁文件、单独的可选环境。当前 Windows NVIDIA 机器选择 CUDA 13.0 wheel：

```powershell
$env:UV_PROJECT_ENVIRONMENT = '.venv-rag'
uv sync --locked --extra rag-cuda --group dev
Remove-Item Env:UV_PROJECT_ENVIRONMENT
```

CPU 安装将 `rag-cuda` 换成 `rag-cpu`；两个 extra 互斥。CPU 索引为 PyTorch 官方 CPU wheel 源；CUDA 索引为官方 cu130 源。安装 CUDA wheel 与运行时选择 device 是两件事。CUDA wheel 需要兼容驱动，不用于 macOS；Linux/macOS 的可移植入口是 CPU extra，尚未在这些系统实测。依据：[uv 的 PyTorch 集成文档](https://docs.astral.sh/uv/guides/integration/pytorch/)。

创建私有 `.local/rag.json`，例如：

```json
{
  "pdf": "book.pdf",
  "model": "models/embeddinggemma-2",
  "device": "auto"
}
```

配置内路径相对于配置文件目录；环境变量路径相对于启动目录，支持中文和空格。可用 `TECHCODEX_RAG_CONFIG` 指定其他私有配置，或通过 `TECHCODEX_BOOK_PDF`、`TECHCODEX_EMBED_MODEL`、`TECHCODEX_RAG_DEVICE` 覆盖。默认索引为 `.local/book-rag/book.sqlite3`。

模型目录必须是完整的官方 [google/embeddinggemma-2](https://huggingface.co/google/embeddinggemma-2) Sentence Transformers 快照，包含权重、config、tokenizer、processor、Pooling 与 Normalize 配置。只有一个 Safetensors 文件不能加载。工具只从本地目录离线加载，不自动下载模型、不执行远程代码。可在模型目录的私有 `source.json` 中记录来源及 revision；建库另计算实际文件 SHA256，不以来源声明替代校验。

本次验证使用官方 revision `914f7f89142e33e77833254d9c9b90c3cef7303b`；权重 SHA256 为 `197a32965d4b1105faf060417baa899e193fb73cd401f42ec9295234d5553d79`。已有用户权重复用，没有重复下载。设备模式：

- `auto`：可用 CUDA 优先，支持 BF16 时用 BF16，否则 FP32；无 CUDA 或初始化失败用 CPU FP32。
- `cuda`：要求 CUDA；不可用则明确失败。
- `cpu`：CPU FP32。

不使用 FP16。CUDA OOM 后将整个失败请求以更小 batch 重试一次；自动模式仍失败则卸载 GPU 模型，以 CPU FP32 重算该请求，不拼接半完成结果。模型配置、文件损坏、索引与维度错误会独立报错。日志输出到 stderr。

## 建库与检索

下列命令在仓库根目录执行，直接使用 uv 创建的环境，避免每次启动同步依赖：

```powershell
.venv-rag/Scripts/python.exe -m rag status
.venv-rag/Scripts/python.exe -m rag index
.venv-rag/Scripts/python.exe -m rag search 'Rs 很大时 Cgd 怎样影响栅节点和输出阻抗' --chapter 6
.venv-rag/Scripts/python.exe -m rag search 'Fig. 6.14' --mode keyword
.venv-rag/Scripts/python.exe -m rag read 188 --count 2
.venv-rag/Scripts/python.exe -m rag image 188
```

`index --keyword-only` 可先建立 FTS5。普通 `index` 不执行 OCR，不渲染全书；它只处理 PDF 的文本层或已经准备好的 OCR 缓存。抽取质量差的页面会标记，不进入向量检索。重复建库逐页检查内容与配置，跳过未变化页面和已有向量；更换设备不重建索引。模型或 tokenizer 变化会使向量失效，PDF 变化后旧引用不能继续查询，须显式增量建库。

每个命中包含 PDF 实际页码（从 1 开始）、PDF 提供的印刷页标签、章节、小节、图号/公式号候选、来源 SHA 和邻页建议。PDF 没有标签时保留空值，不猜印刷页码。图号与公式号由抽取文本识别，扫描页的 OCR 可能识错，最终以页图为准。

分块尽量保持 PDF 段落完整，约 1400 字符，短段落少量重叠。扫描版按句末标点组织 OCR 行，保留公式与解释的相邻关系。FTS5 同时保留拉丁变量名、图号别名与中文双字词；向量为 768 维 FP32 存储的归一化结果。混合检索以页面为单位，用 RRF 合并关键词、变量组合与余弦排名，同页不同片段的证据可以合并。精确图号只匹配图号别名；纯变量的 keyword 查询要求这些变量共同出现。章节过滤在检索前限定候选。`keyword`、`semantic` 和 `hybrid` 可分别检查；纯关键词回退会明确提示，不把它称作语义命中。

查询使用官方 `SearchQuery` 指令。文档按官方格式编码为 `title: 实际章节标题 | text: 段落`，不再叠加会引入 `title: none` 的 Document 默认前缀。文本模式关闭视觉和音频塔。依据：[官方模型说明](https://huggingface.co/google/embeddinggemma-2)、[Transformers 模型文档](https://huggingface.co/docs/transformers/model_doc/embedding_gemma2)。

### 扫描版：独立的 MinerU 预处理环境

本次用户提供的中文版 PDF 是扫描版，没有正文文本层。它不能被当作英文原版跨语言检索的验收样本。为扫描版安装独立 OCR 组；这不会改变普通仿真环境：

```powershell
$env:UV_PROJECT_ENVIRONMENT = '.venv-ocr'
uv sync --locked --group ocr --no-default-groups
Remove-Item Env:UV_PROJECT_ENVIRONMENT
$env:MINERU_HOME = Join-Path (Get-Location) '.local/mineru'
.venv-ocr/Scripts/mineru-kit.exe models download --tier basic --small-backend onnx --source huggingface
.venv-ocr/Scripts/python.exe scripts/book_ocr.py verify > .local/mineru/verified.json
.venv-rag/Scripts/python.exe -m rag ocr --start 188 --end 190
.venv-rag/Scripts/python.exe -m rag index
```

OCR 与 RAG 使用不同的 uv 环境，共用一份根锁文件。Windows 的 `.venv-ocr` 不安装 PyTorch，默认强制 ONNX CPU。MinerU 4.0.12 Basic 使用 PP-DocLayoutV2、PP-OCRv6 和 PP-FormulaNet_plus-M，处理版面、文字与公式，不启动 VLM。锁定 DocVortex 0.5.16 是为了避免其后续版本在 Windows 同时安装 DirectML 与 CPU ONNX Runtime 的包覆盖。配置和模型放在私有 `MINERU_HOME`；普通解析强制 `source=local`，缺模型报错，不隐式下载。参考：[MinerU 档位与运行时](https://opendatalab.github.io/MinerU/usage/tiers/)、[离线模型配置](https://opendatalab.github.io/MinerU/usage/model_source/)。

先用 PyMuPDF 检查每页文字层的可读字符、乱码比例和扫描图覆盖情况；可靠文字页直接使用文字层。仅对不可靠页运行 OCR。Basic 每批最多 20 页，初次只验收 PDF 188～190 页（印刷 164～166 页）。已有同档结果跳过。`TECHCODEX_OCR_PYTHON` 可指定另一个 uv OCR 解释器，`TECHCODEX_MINERU_HOME` 可指定私有模型根目录。

普通查询只读缓存，不导入 MinerU 或启动 OCR。解析结果在私有 `book-rag/ocr-mineru/<PDF-SHA>/<tier>/`，每页记录原始 PDF 页码、印刷标签、目录章节、布局块、LaTeX、公式位置、模型哈希和复核状态；`runs/` 保留 MinerU 原始 JSON、Markdown 与裁图。`get_page_image` 始终渲染原始 PDF，不返回 OCR 重排页。旧 RapidOCR 缓存保留作历史后备，搜索结果明确标注来源。

公式 LaTeX 保留模型原样，不用规范化搜索词覆盖下标、符号或括号。解析器没有提供可靠置信分数时记录 `null`，不能填成 100%；公式默认待核对。FTS 单独生成 `C_{\mathrm{GD}} → Cgd` 等检索别名，读页仍返回原文。Basic 已在这三页暴露漏公式、下标及括号问题，因此是否命中图号与公式是否正确分别验收。

对确有问题的少量页面，可显式准备 Standard 模型并升级解析：

```powershell
.venv-ocr/Scripts/mineru-kit.exe models download --tier standard --small-backend onnx --vlm-engine llama-cpp --source huggingface
.venv-rag/Scripts/python.exe -m rag ocr --start 188 --end 190 --tier standard --reason '核对式6.23、6.24与6.30的下标和分式'
.venv-rag/Scripts/python.exe -m rag index
```

Standard/Advanced 每批最多 3 页，必须给出理由，不由查询自动触发。当前升级流程强制本地 llama.cpp CPU，以免抢占 EmbeddingGemma 显存；没有配置远程 VLM 或 LLM 后处理服务。升级结果优先读取，原 Basic 结果仍保留。更高档位也不等于公式正确，仍须核对原图。

本机这三页的解析阶段约为 Basic 31 秒、Standard 349 秒。Standard 恢复了式 6.24 的括号关系与式 6.30 的系数，但仍漏掉式 6.21，且把 `gm1` 识为 `gml`；这些问题保持待复核状态。该结果说明升级应按页使用，不能把更高档位或流畅的 LaTeX 当作正确性证明。

### 导入自行取得的 MinerU 云端结果

将云端 JSON 放入私有 `.local/book-rag/cloud-ocr/`，使用当时上传的分卷 PDF 指定映射：

```powershell
.venv-rag/Scripts/python.exe -m rag import-ocr .local/book-rag/cloud-ocr/result.json --split-pdf .local/pdf-upload/02_Razavi_Ch06-08.pdf --start 181
.venv-rag/Scripts/python.exe -m rag index
```

`--start` 是分卷首页在完整原 PDF 中的实际页码，从 1 开始。导入会核对导出页数、顺序、版面比例，并逐页比对分卷与原 PDF 的渲染图像；页码和章节仍取完整 PDF。只使用 `para_blocks` 的阅读顺序，保留原始 LaTeX、公式位置和图注，不下载 JSON 中的远程图片。原始 JSON 留在私有目录，页记录保存来源校验与映射。

云端导出优先于旧的本地 OCR 缓存，旧结果保留。来源按导出中的版本、backend 与 effort 记录；未提供的具体模型和置信度保持未知，不宣称使用本地 Basic 或 ONNX CPU。公式默认待核对，原始页面图像仍由完整 PDF 渲染。导入与查询均不重新运行 OCR，只有显式 `index` 才更新关键词和向量。

### 少量页面的视觉检索

```powershell
.venv-rag/Scripts/python.exe -m rag index-images 188 189
.venv-rag/Scripts/python.exe -m rag search '共源级的高频小信号电路' --mode visual
```

一次选择最多 20 页，视觉编码仅关闭音频塔。图像向量用于找页，电气连接必须查看原图；视觉编码不可用时，文本索引和原图读取仍是独立功能。不要把只索引两页的视觉排序当作全书质量评测。

## Codex MCP

```powershell
.venv-rag/Scripts/python.exe -m rag install-mcp
codex mcp get techcodex_book
```

安装命令只添加 `techcodex_book` stdio 项，使用当前 uv 环境的解释器和私有配置位置，保留其他服务器设置。更换环境后重新执行。桌面端与 CLI 共用 MCP 配置；已有聊天未重新连接时，在新会话使用。无需公网端口。依据：[Codex 官方 MCP 文档](https://learn.chatgpt.com/docs/extend/mcp?surface=cli)。

四个工具：`search_book`、`read_book_pages`、`get_page_image`、`book_status`。推荐让 Agent 先搜索、读取 1–3 邻页，再调用 `get_page_image` 查看真实 PNG 内容；不是仅获得本地文件路径。启动及状态查询不加载权重，首次语义查询加载后复用。索引不存在时提示先建库，不暗中扫描整本 PDF。

## 检查与边界

```powershell
.venv-rag/Scripts/python.exe -m pytest tests/test_book_rag.py tests/test_book_mcp.py tests/test_book_ocr.py -q
```

测试使用自行生成的短 PDF，不包含原书文字或模型。覆盖增量跳过、符号/中文分词、引用来源变化、页数限制、向量有效性、CUDA 不可用/OOM 注入、配置错误不被误判为 GPU 故障，以及真实 stdio 工具协议和 PNG 内容块。真实权重和私有教材的验收结果另在本机运行，不能用合成测试代替真实检索质量。

针对本次中文版第二版的验收问题可运行 `.venv-rag/Scripts/python.exe scripts/check_book_rag.py`。它检查第 2～7 章和 Rs/Cgd 主问题的前五候选、精确图号、变量检索，并把页码结果保存到私有索引目录。预期 PDF 页码是这个版本的人工验收标尺，其他排版版本需要重新核对，不能套用命中率。另含自编英文短段落的中文查询测试，不能代替英文原版 PDF 的实测。

`.gitignore` 排除 PDF、Safetensors、SQLite、NumPy 向量和 `.local/`。`scripts/book.py` 继续按页面白名单发布，额外拒绝误放入公开资源的 PDF、权重、tokenizer 和索引；站点检查也检查这些后缀。请不要把私有文字导出到 `web/assets`，或将 OCR 内容粘贴成公开教材。
