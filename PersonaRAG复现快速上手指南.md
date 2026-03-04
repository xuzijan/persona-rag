# PersonaRAG 复现快速上手指南

> 按 6 步递进：Fork → 环境隔离 → 跑通示例 → 整理 I/O 与配置 → 统一评估与 AmbiCoding

---

## 论文背景

**论文**：*PersonaRAG: Enhancing Retrieval-Augmented Generation Systems with User-Centric Agents* (arXiv:2407.09394)  
**机构**：University of Passau (PADAS Lab)  
**核心思想**：用多智能体 RAG 框架，根据用户偏好与交互动态调整检索与生成，实现用户中心的问答增强。

**评估场景**：开放域问答（NQ、WebQ、TriviaQA）  

**当前项目**：`xuzijan/persona-rag` 是 `padas-lab-de/ir-rag-sigir24-persona-rag` 的 fork。

---

## Step 1：Fork 到自己仓库

- [x] Fork `padas-lab-de/ir-rag-sigir24-persona-rag` → `xuzijan/persona-rag`（或你的 GitHub 用户名）
- [ ] 在 README 或 commit 中注明 fork 来源与对应 commit
- [ ] `.gitignore` 排除大文件（模型权重、日志等），只同步代码和配置

**建议 .gitignore 新增：**

```gitignore
logs/
metrics/
*.safetensors
*.bin
.poetry/
```

---

## Step 2：环境隔离

每个 baseline 单独环境，避免依赖冲突。

**目录结构：**

```
/root/autodl-tmp/
├── persona-rag/              # 论文 2
│   ├── .venv/ 或 conda env   # persona-rag
│   ├── data/                 # 数据
│   ├── logs/                 # 运行日志
│   └── scripts/
├── experiments/
│   ├── configs/
│   ├── data/
│   ├── eval/
│   └── outputs/
└── ...
```

**PersonaRAG 环境：**

```bash
cd /root/autodl-tmp/persona-rag
conda create -n persona-rag python=3.11 -y
conda activate persona-rag
pip install -e .
```

**配置 API Key：**

```bash
export OPENAI_API_KEY='your-openai-api-key'
export MODEL='gpt-4'
# 可选：LLAMA_API_KEY + LLAMA_API_ENDPOINT、MIXTRAL_API_KEY + MIXTRAL_API_ENDPOINT
```

---

## Step 3：按原作者示例跑通一次

### 3.1 Mock 验证（无需密钥）

```bash
cd /root/autodl-tmp/persona-rag
conda activate persona-rag
python -m scripts.validate_mock --dataset nq --topk 5
```

### 3.2 真实 API 验证

```bash
export OPENAI_API_KEY=sk-xxx
# 方式 A：环境变量
export MODEL=gpt-4
python -m scripts.main run --dataset nq --topk 5

# 方式 B：YAML 配置
python -m scripts.main --config experiments/configs/persona_rag_baseline.yaml run --dataset nq --topk 5
```

### 3.3 构建 CSV 与评估

```bash
# 将 logs 转为 result.csv
python -m scripts.main --config experiments/configs/persona_rag_baseline.yaml build --dataset nq --topk 5

# 评估（需先 build）
python -m scripts.main --config experiments/configs/persona_rag_baseline.yaml evaluate --dataset nq --topk 5
```

### 3.4 论文官方数据与复现

**数据来源**：仓库自带 `data/data_{nq,webq,triviaqa}_sampled.jsonl`

**运行流程**：
```bash
# Mock 验证（1 条样本）
python -m scripts.validate_mock --dataset nq --topk 5

# 真实 API（最多 100 条，每条间隔 5 秒）
python -m scripts.main run --dataset nq --topk 5
python -m scripts.main build --dataset nq --topk 5
python -m scripts.main evaluate --dataset nq --topk 5
```

**论文快速复现**（使用作者提供的 request logs）：
```bash
python -m logs.eval --dataset nq --topk 5
```

---

## Step 4：整理输入输出、重要参数、配置

### 4.1 输入格式（完整）

**run / validate_mock**

| 输入 | 类型 | 说明 | 来源 |
|------|------|------|------|
| 数据文件 | JSONL | 每行一条样本 | `data/data_{dataset}_sampled.jsonl` |
| question | str | 问题 | 数据字段 |
| answers | list[str] | 标准答案（可多个） | 数据字段 |
| passages | list[str] | 检索到的段落（取 top-k） | 数据字段 |
| dataset | str | 数据集名 | `--dataset`（nq / webq / triviaqa） |
| topk | int | 使用的 passage 数量 | `--topk`（3 或 5） |

**单条样本格式：**
```json
{"id": "...", "question": "...", "answers": ["a1", "a2"], "passages": ["p1", "p2", ...]}
```

### 4.2 输出格式（完整）

**run 输出**

| 输出 | 类型 | 说明 |
|------|------|------|
| 单条日志 | JSON | `logs/{MODEL}/{dataset}/top{topk}/{dataset}_idx_{i}.json` |
| 内容 | dict | 各 agent 的 message 列表：cot、user_profile、contextual_retrieval、live_session、document_ranking、feedback、cognitive、vanilla_chatgpt、guideline、vanilla_rag、con、self_rerank |

**build 输出**

| 输出 | 类型 | 说明 |
|------|------|------|
| result.csv | CSV | 各 agent 的 output 与 correctness（True/False） |
| 列 | - | id, {agent}_output, {agent}_correctness, true_answer |

**evaluate 输出**

| 输出 | 类型 | 说明 |
|------|------|------|
| results.json | JSON | 各 baseline 的 F1、EM、PM、Accuracy、BLEU 等 |
| 指标 | - | F1、EM、PM、Accuracy、BLEU-2、Norm_Avg_Sentence_Length、Norm_Avg_Syllables |

### 4.3 重要参数（完整）

| 参数 | 位置 | 默认 | 说明 |
|------|------|------|------|
| MODEL | 环境变量 | - | 模型名：gpt-4、llama3、mixtral |
| OPENAI_API_KEY | 环境变量 | - | OpenAI API 密钥 |
| OPENAI_BASE_URL | 环境变量 | - | Mock 时指向假 API（如 http://127.0.0.1:19999/v1） |
| ENABLE_TRIMMING | 环境变量 | false | 是否启用 context 裁剪 |
| MAX_TOKENS | 环境变量 | 16385 | 最大 token 数 |
| dataset | 命令行 | - | nq / webq / triviaqa |
| topk | 命令行 | - | 3 或 5，检索 passage 数量 |

### 4.4 YAML 配置文件（完整）

**路径**：`experiments/configs/persona_rag_baseline.yaml`

| 字段 | 类型 | 说明 |
|------|------|------|
| `experiment.name` | str | 实验名称 |
| `experiment.seed` | int | 随机种子 |
| `model.handle` | str | 模型名，如 gpt-4、llama3、mixtral |
| `model.temperature` | float | 温度 |
| `model.max_tokens` | int | 最大 token 数 |
| `model.enable_trimming` | bool | 是否启用 context 裁剪 |
| `data.dir` | str | 数据目录 |
| `data.pattern` | str | 数据文件名模式 |
| `data.default_dataset` | str | 默认数据集 |
| `data.default_topk` | int | 默认 topk |
| `logs.dir` | str | 日志目录 |
| `logs.pattern` | str | 日志路径模式 |

**完整示例：**
```yaml
experiment:
  name: persona_rag_paper_repro
  seed: 42

model:
  handle: "gpt-4"
  temperature: 0.2
  max_tokens: 16385
  enable_trimming: false

data:
  dir: "data"
  pattern: "data_{dataset}_sampled.jsonl"
  default_dataset: "nq"
  default_topk: 5

logs:
  dir: "logs"
  pattern: "{model}/{dataset}/top{topk}"
```

**加载方式**：`--config path` 或环境变量 `EXPERIMENT_CONFIG`

### 4.5 环境变量（YAML 未覆盖时）

**必需：**

| 变量 | 说明 |
|------|------|
| `OPENAI_API_KEY` | OpenAI API 密钥（gpt 模型） |
| `MODEL` | 模型名（可由 YAML `model.handle` 设置） |

**可选（Mock 模式）：**

| 变量 | 说明 |
|------|------|
| `OPENAI_BASE_URL` | Mock API 地址，如 `http://127.0.0.1:19999/v1` |

**可选（其他模型）：**

| 变量 | 说明 |
|------|------|
| `LLAMA_API_KEY` + `LLAMA_API_ENDPOINT` | Llama3 |
| `MIXTRAL_API_KEY` + `MIXTRAL_API_ENDPOINT` | Mixtral |

### 4.6 脚本命令行参数

**validate_mock**

| 参数 | 说明 |
|------|------|
| `--dataset` | 数据集（nq / webq / triviaqa），默认 nq |
| `--topk` | passage 数量，默认 5 |
| `--port` | Mock 服务端口，默认 19999 |
| `--config` | YAML 配置路径 |

**scripts.main run / build / evaluate**

| 参数 | 说明 |
|------|------|
| `--config` | YAML 配置路径（需放在子命令前，如 `--config x.yaml run ...`） |
| `--dataset` | 必需，数据集名 |
| `--topk` | 必需，passage 数量 |

---

## Step 5：统一评估与 AmbiCoding 适配

### 5.1 统一输入输出接口

- **统一输入**：`{id, query, context, options?, ...}` 的 dict
- **统一输出**：`{id, pred, ground_truth?, metadata?}` 的 dict
- **统一入口**：`run_baseline("persona_rag", config_path)` 分发到各实现

### 5.2 AmbiCoding 数据集转换

- 明确 AmbiCoding 原始格式
- 为 PersonaRAG 写转换脚本：`AmbiCoding → PersonaRAG 输入格式`（question, answers, passages）
- 转换脚本需可复现（固定 seed、版本）

### 5.3 统一评估脚本

- 输入：各 baseline 的预测结果（统一格式）
- 输出：同一套指标（accuracy、exact match、F1 等）
- 评估逻辑与 baseline 解耦

### 5.4 Prompt Template

**论文/代码中的 Prompt**

- 核心 agent 模板位于 `persona_rag/prompts/prompt.py`：
  - **cot**：链式推理，`{question}` → Reasoning process + Answer
  - **user_profile**：用户偏好分析，`{question, passages, global_memory}`
  - **contextual_retrieval**：上下文检索策略
  - **live_session**：会话动态调整
  - **document_ranking**：文档排序
  - **feedback**：反馈收集
  - **vanilla_chatgpt**：简洁直接回答
  - **vanilla_rag**：基于 passages 的 RAG 回答
  - **con**：阅读笔记 + 相关性讨论 + 答案

**建议**：在单独文件或 YAML 中保存完整 prompt 模板，便于复现与对比。

---

## 数据流简图

```
question + passages → CoT Agent → 推理过程
        ↓
user_profile / contextual_retrieval / live_session / document_ranking / feedback
        ↓
global_memory 更新
        ↓
cognitive / vanilla_chatgpt / guideline / vanilla_rag / con / self_rerank
        ↓
多路输出 → build → result.csv → evaluate → results.json
```

---

## 常见问题

| 问题 | 排查 |
|------|------|
| 找不到 API Key | 检查 `OPENAI_API_KEY` 环境变量 |
| 超参数不生效 | 确认 `--config` 放在子命令前，或设置 `EXPERIMENT_CONFIG` |
| ModuleOrPackageNotFoundError | 在 pyproject.toml 添加 `packages = [{include = "persona_rag"}]` 后 `pip install -e .` |
| Mock 验证失败 | 确认端口 19999 未被占用，或指定 `--port` |
| NLTK 报错 | 运行 `python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords')"` |

---

## 参考链接

- [PersonaRAG 论文](https://arxiv.org/abs/2407.09394)
- [PADAS Lab 原仓库](https://github.com/padas-lab-de/ir-rag-sigir24-persona-rag)
