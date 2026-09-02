---
name: autoqa
description: >-
  Generates 30–40 realistic Amazon community Q&As for a product family
  (total rows, not per ASIN unless asked). Frames answers by saying what
  the product is (避重就轻). Always writes two files under output/: a vendor
  Excel for posting, and a bilingual Word doc for the user to check errors.
  Use when the user mentions AutoQA, 上QA, 社区问答, 服务商QA, Amazon Q&A,
  生成QA, 中英对照, or filling SHEET QA.
---

# AutoQA

给服务商上社区问答：先载入真实产品信息，再起草 → 按痛点筛查 → 按站点语言落地 → 去重校对 → **语法用词终审** → 同时交出 **两份**：服务商表格（上架用）+ 中英对照 Word（给你核对对错）。同一批产品 **一共 30–40 条**，按变体需要分配，**不要六套平均复制**。

没有 ASIN 时只做 Phase 0（密钥/通道）。禁止用记忆编商品。

**生成物只进 `output/{产品名}/`。** 任务完成后用这次产品名新建文件夹（JSON `title`，如 `ASHEWIG 迷你花瓶`），这一批文件都放进去，不要散落在 `output/` 根下。

| 文件 | 给谁 | 用途 |
|------|------|------|
| `output/{产品名}/{batch}_qa.xlsx` | 服务商 | 上架用，只有站点原文问/答 |
| `output/{产品名}/{batch}_qa_review.docx` | 你 | 中英对照，核对意思和用词有没有错 |

不要再复制 vendor / 服务商 / 运营判断 等额外表格。不要往仓库根目录写填好的表。

完整顺序与档案格式：[references/pipeline.md](references/pipeline.md)  
**强制门禁**：[references/gate.md](references/gate.md) — 必须走 `run_autoqa.py`，禁止直接写 xlsx/docx。

## 唯一入口（Agent 必用）

```bash
python scripts/run_autoqa.py init --title "{产品名}" --batch {BATCH_ID}
python scripts/run_autoqa.py status --product-dir "output/{产品名}"
python scripts/run_autoqa.py advance --product-dir "output/{产品名}"
python scripts/run_autoqa.py deliver --qa-json "output/{产品名}/{batch}_qa.json"
```

禁止跳过 `init` / 产物文件 / `deliver` 直接调用 `write_qa_sheet.py` 或 `write_review_docx.py`（脚本会拒绝）。

## Phase 0 — 密钥（无 ASIN 也要做完）

用户填写 `env/.env`，并按 [references/env_setup.md](references/env_setup.md) 写进 Windows 用户环境变量后重启 Cursor。

Agent：只检查 MCP 是否已连接（Sif `ping`）。**永远不要打印密钥。** 未连通就停，列出缺的是精灵还是 Sif。

## 有 ASIN 之后（禁止跳步写表）

```
- [ ] Phase 1 档案：listing + 图 + 评价 + 流量词
- [ ] Phase 2 中文 gist 候选 36–45
- [ ] Phase 3 筛查 Keep → 30–40
- [ ] Phase 4 目标站点母语成稿（同时写 question_zh / answer_zh）
- [ ] Phase 5 错别字 + 同义/跨语言去重
- [ ] Phase 5b 语法/用词终审（必做，见 language_pass.md）
- [ ] Phase 6 建 `output/{产品名}/`，两份一起写：服务商表 xlsx + 中英对照 Word
```

### Phase 1 信息载入

细节：[references/data_sources.md](references/data_sources.md)

| 目的 | 工具 | 失败 |
|------|------|------|
| 标题、五点、类目、主图、尺寸重量、变体、`overviews`、有无 A+（仅 Y/N） | SS `asin_detail` | 该 ASIN 停 |
| 图集 | SS `keepa_info` + `returnFields` | 只用主图 |
| 评价原文 | SS `review` 1–2★ → 3★ → 4–5★ | 少做异议 QA，档案标无评 |
| 该 ASIN 搜索约束/痛点词 | SS `traffic_keyword`（primary，1 页） | 用 `keyword_miner` 打类目词，并标明无自身流量 |
| 核心词 / 长尾高转化 | SS `keyword_miner`（核心词 + 精确词表） | 只靠 listing 用词，分数降一档 |
| US 规格/词交叉 | Sif `market_get_asin_profile` / `market_get_asin_keyword_signals` | 非 US 跳过 |
| A+ 文案 | 无 MCP | 用户未贴则不当事实引用 |

知识储备只许提供「这类目常问什么方向」，不许填规格。

### Phase 2 草稿

[references/qa_generation.md](references/qa_generation.md) + [references/seller_persona.md](references/seller_persona.md)。以对应站点资深运营身份，结合 MCP 核心词/流量词/长尾高转化词打 listing 分、再写 QA。先写 gist，不要一上来灌 35 条。

### Phase 3 筛查

[references/screening.md](references/screening.md)。三条：像真人、买家真会问、击中本词本类目痛点。总分不够就 Drop。禁止灌水凑 30。

### Phase 4–5 语言与去重

语言跟 **这个产品的目标站点人群**，不是一套稿多国翻译。[references/localization.md](references/localization.md) + [references/language_map.md](references/language_map.md)。

相近可以（都关于尺寸但场景不同）；意思相同（含不同语言同一 intent+同一答案）只留一条。

成稿必须同时有 **站点原文** 和 **中文释义**（`question`/`answer` + `question_zh`/`answer_zh`）。中文是给你核对意思的，不上架。

成稿后、任何输出前，再过 [references/language_pass.md](references/language_pass.md)：语法、问号、残句、堆词、中式英语/西语。不过这一遍不得写 Word 或表。

### Phase 6 交付（表格给服务商，文档给你核对）

格式见 [references/output.md](references/output.md) 与 [references/gate.md](references/gate.md)。**只许**：

```bash
python scripts/run_autoqa.py deliver --qa-json "output/{产品名}/{batch}_qa.json"
```

内部顺序：校验 → 写 xlsx → 写 docx → 更新 `.autoqa_state.json` phase=6。

- **xlsx**：给服务商上架。列合同见 [references/sheet_contract.md](references/sheet_contract.md)。Q/A 框：无 1.2.3、无「问题/答案」字样。回答 **1–2 句**。`操作时间` 空。按 ASIN 连排。中文释义 **不进表**。
- **docx**：给你检查核对。中文 + 站点原文对照；你改完告诉我，再改 JSON 并重出这两份。

## 不能犯的错（短名单）

1. 编尺寸/电压/配件/认证/A+ 正文
2. 编评价或把评价整段改成回答
3. 把核心大词写成「这是什么产品」式 QA
4. 广告腔、禁用词、竞品名；**答句是热心买家不是卖家**（禁止联系我们 / we'll take care）；**避重就轻**：先说产品是什么、怎么用；透明写水晶感清玻璃；染色可以说喷涂（核心工艺）但只点一次，不要让客户盯着喷涂；问答里不要写套装尺寸百分比对照
5. 未做语法用词终审就输出；未筛查就写 xlsx；一条产品线默认总共 30–40 行，禁止每个 ASIN 复制一套
6. US 数据直接当 UK/ES 结论
7. 回显 `env/.env` / secret-key
8. 在 `output/{产品名}/` 之外写生成文件；为同一批再复制第二份 xlsx

## 输入缺口

| 缺 | 行为 |
|----|------|
| 密钥未通 | 停在 Phase 0 |
| ASIN | 停，等粘贴 |
| 站点 | 问一次，禁止默认全美 |
| 语言 | 用该站点默认语言 |

工作簿模板：`templates/点赞、QA.xlsx`。不改 sheet「点赞表」，不改 QA 的 `J1:M5` 红字说明。填好的服务商表只写到 `output/{产品名}/{batch}_qa.xlsx`。
