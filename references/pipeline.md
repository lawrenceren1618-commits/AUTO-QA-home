# 六段流水线（先设计后执行）

没有 ASIN 时只做 Phase 0。有 ASIN 后严格按序，禁止跳过筛查直接写表。

## Phase 0 — 通道

1. 用户填写 `env/.env`（`SELLERSPRITE_SECRET_KEY` / `SIF_SECRET_KEY`）。
2. 同步到 Windows 用户环境变量（Cursor MCP 只认 `${env:…}`）。
3. 重启 Cursor。Settings → MCP 里 `sellersprite`、`sif` 为已连接。
4. 连通抽检：Sif `ping`；有样例 ASIN 后再打 SellerSprite `asin_detail`（会扣积分）。

缺密钥：停。不要用训练记忆编 listing。

## Phase 1 — 信息载入（先懂产品）

每个 ASIN 建档案 `output/{产品名}/{ASIN}_{MP}_dossier.json`，字段见下文。禁止未载入就写 QA。

载入顺序（够用即止）：

1. **Listing 骨架** — SS `asin_detail`：标题、五点、类目路径、主图、尺寸重量、品牌、变体、`overviews`、`badge.ebc`
2. **图** — SS `keepa_info` 且必须 `returnFields`；看主图/副图里实际出现的配件与形态
3. **买家原文** — SS `review` 差评→中评→好评
4. **这个词/这个 ASIN 人在搜什么** — SS `traffic_keyword`（`trafficKeywordTypes: primary`，一页即可）；US 可加 Sif `market_get_asin_keyword_signals`（`topN` 小，只要 top 词名，不要把流量诊断写进 QA）
5. **US 规格交叉** — 可选 Sif `market_get_asin_profile`；冲突则 QA 不用该数字
6. **A+ 正文** — MCP 没有；用户可贴

档案里必须能回答：这是什么、给谁、关键规格、不能承诺什么、买家已经吵过什么、搜索词在问什么。

Phase 2–3 筛到 **整批 30–40 条**（不是每个 ASIN 30 条）。按变体需要分配，不要平均复制。

`answer_facts` 必须能指回 Phase 1。知识储备只允许补「这类目买家通常会问」的**问题方向**，不允许补规格数字。

## Phase 3 — 筛查（合格才留下）

读 [screening.md](screening.md)。每条 gist 打分：真实口吻 / 买家真会问 / 是否击中本词本类目痛点。只留 Keep。补到 30–40；补不出就少于 30 并在报告说明，禁止灌水。

## Phase 4 — 地区语言

语言跟 **这个 ASIN 的目标站点/人群**，不是把同一批 QA 翻译成很多国语言。读 [language_map.md](language_map.md) 与 [localization.md](localization.md)。用 Phase 3 留下的 gist **用当地常用语重写**，改单位、插头、称呼、生活场景，禁止机翻腔。成稿同时写 `question_zh` / `answer_zh`（中文释义，只给对照稿，不上架）。

## Phase 5 — 去重

- 同语言：问句近义合并
- 跨语言：意思相同只留一条（相近可以，相同不行）

## Phase 5b — 语法 / 用词终审（输出前必做）

读 [language_pass.md](language_pass.md)。逐条用目标语读：残句、冠词、问号、堆词、中式搭配。改完再 `scripts/validate_qa.py --require-zh`。这一遍不过，禁止写 Word 或 xlsx。

## Phase 6 — 两份一起交

合同见 [output.md](output.md) 与 [gate.md](gate.md)。

```bash
python scripts/run_autoqa.py deliver --qa-json "output/{产品名}/{batch}_qa.json"
```

产品文件夹名用这次产品名（JSON `title`）。模板是 `templates/点赞、QA.xlsx`，不要往根目录再写填好的副本。同一批不要再复制第二份表。

## Dossier 最小结构

```json
{
  "asin": "B0XXXXXXXXX",
  "marketplace": "UK",
  "target_language": "en-GB",
  "sources_used": ["asin_detail", "review", "traffic_keyword"],
  "gaps": ["no_aplus_copy"],
  "listing": { "title": "", "features": [], "category": "", "dimensions": "" },
  "pain_points": [
    { "topic": "", "why_buyers_care": "", "source": "review|keyword|listing" }
  ],
  "gists": [
    {
      "intent": "fit",
      "question_gist": "",
      "answer_facts": [],
      "evidence": [],
      "keep": true,
      "drop_reason": null
    }
  ]
}
```
