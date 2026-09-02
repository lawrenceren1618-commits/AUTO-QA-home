# 强制路径（gate）

Skill 文案是建议；**脚本门禁是强制**。Agent 必须走 `run_autoqa.py`，禁止直接调 `write_qa_sheet.py` / `write_review_docx.py`。

## 状态文件

`output/{产品名}/.autoqa_state.json`

```json
{
  "version": 1,
  "title": "ASHEWIG 迷你花瓶",
  "batch": "ASHEWIG_US",
  "phase": "3",
  "validation": { "passed": false, "qa_json": null },
  "deliver": { "xlsx": null, "docx": null }
}
```

## 阶段产物（缺一项 deliver 会拒绝）

| 进入阶段 | 必须已有 |
|----------|----------|
| 1 | Phase 0 env 通过（`init`） |
| 2 | `dossiers/*.json` ≥ 1 |
| 3 | `gists.json` |
| 4 | `screened.json`（keep 30–45 条） |
| 5 | `{batch}_qa.json` |
| 5b | `validate_qa.py --require-zh` 通过 |
| 6 | xlsx + docx 已写出 |

## 命令（唯一入口）

```bash
# 新批次：建文件夹 + Phase 0→1
python scripts/run_autoqa.py init --title "ASHEWIG 迷你花瓶" --batch ASHEWIG_US

# 看卡在哪
python scripts/run_autoqa.py status --product-dir "output/ASHEWIG 迷你花瓶"

# 产物齐了自动进下一阶段
python scripts/run_autoqa.py advance --product-dir "output/ASHEWIG 迷你花瓶"

# 校验 + 写表 + 写 Word（Phase 5b→6）
python scripts/run_autoqa.py deliver --qa-json "output/ASHEWIG 迷你花瓶/ASHEWIG_US_qa.json"
```

## Agent 在各 Phase 要写什么

1. **Phase 1** — MCP 拉数 → `dossiers/{ASIN}_{MP}.json`
2. **Phase 2** — 中文 gist → `gists.json`
3. **Phase 3** — 筛查 → `screened.json`（每条 `keep` + 分数）
4. **Phase 4–5** — 成稿去重 → `{batch}_qa.json`（含 `question_zh` / `answer_zh`）
5. **Phase 5b–6** — 只许 `deliver`，不许手写 xlsx/docx

## 旧批次（门禁上线前已生成的）

```bash
python scripts/run_autoqa.py bootstrap-legacy --qa-json "output/ASHEWIG 迷你花瓶/ASHEWIG_US_qa.json"
python scripts/run_autoqa.py deliver --qa-json "output/ASHEWIG 迷你花瓶/ASHEWIG_US_qa.json"
```

`bootstrap-legacy` 会补最小 dossier/gists/screened，并标明 `legacy_bootstrap`；新批次不要用。

## 下一步：LangGraph

`gate.py` + `run_autoqa.py` 已是线性状态机。将来可把各 Phase 节点搬进 LangGraph，checkpoint 仍用同一套 `output/{产品名}/` 产物。
