# 样例（档案 + 成稿行）

机器读写的完整批次在 `output/{产品名}/{batch}_qa.json`。下面只说明字段长什么样。

## Dossier

```json
{
  "asin": "B0EXAMPLE01",
  "marketplace": "UK",
  "target_language": "en-GB",
  "sources_used": ["asin_detail", "review", "traffic_keyword"],
  "gaps": ["no_aplus_copy"],
  "listing": {
    "title": "(from asin_detail)",
    "features": [],
    "category": "",
    "dimensions": ""
  },
  "pain_points": [
    {
      "topic": "底座不稳",
      "why_buyers_care": "院子地面不平会晃",
      "source": "review"
    }
  ],
  "gists": [
    {
      "intent": "install_level",
      "question_gist": "院子略不平能不能放稳",
      "answer_facts": ["需要相对水平的表面", "可垫平板"],
      "evidence": ["review:2star", "listing:dimensions"],
      "keep": true,
      "drop_reason": null
    }
  ]
}
```

## 成稿一行

```json
{
  "asin": "B0EXAMPLE01",
  "marketplace": "UK",
  "language": "en-GB",
  "question": "Will this sit stably on a slightly uneven patio?",
  "answer": "It needs a reasonably level surface so the unit does not rock while running.",
  "question_zh": "院子略不平，放得稳吗？",
  "answer_zh": "需要相对平整的地面，运行时才不会晃。",
  "note": "安装"
}
```
