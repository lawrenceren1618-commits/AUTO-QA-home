# AutoQA 取数

可信级：评价正文 A；精灵/Sif 结构化字段 B；类目常识 C（只准出问题方向，不准出数字）。

## SellerSprite（主通道）

### `asin_detail`（必调）

`marketplace` + `asin`。常用：`title` `features` `nodeLabelPath` `imageUrl` `zoomImageUrl` `dimensions` `weight` `brand` `price` `skuList` `variationList` `overviews` `badge.ebc` `parent`。

`features` 空：规格 QA 只能用 title/overviews/评价里出现过的数字。

### `keepa_info`（图，可选）

必须 `returnFields`，例如 `imageUrls,title,dimensions,weight,pkgDimensions,pkgWeight`。禁止拉全量趋势。

### `review`（痛点原料 A）

`size` 最大 10。三批各一页：`[1,2]` `[3]` `[4,5]`。用 `title`/`content`/`star` 判断「会问什么」，不要把评价原文贴进 F 列。

### `keyword_miner`（运营打分）

核心词 + `keywordList` 精确表。用 searches / purchaseRate 分层：核心、场景流量、长尾高转化。不要把 purchaseRate 写成账户 CVR。新品 `traffic_keyword` 为空时必须用本工具，并标明无 ASIN 自身流量。

`request.asin` + `request.marketplace`，`trafficKeywordTypes: ["primary"]`，`page=1` `size` 适中（≤20）。只要词面与约束（size / outdoor / for x），不要把 purchaseRate 写成转化率，不要把词表倒进 QA。

## Sif（交叉，不是文案源）

- `ping`：Phase 0  
- `market_get_asin_profile`：US 规格/主图/类目交叉；冲突则该规格不写进回答  
- `market_get_asin_keyword_signals`：US 且需要确认「人在搜什么」时，`topN` 小；只用 top 词名做筛查，禁止把流量诊断段落写进问答

非 US 不要拿 Sif 默认 US 画像写英/西站点 QA。不调 `ads_*`。

## 明确没有

| 缺口 | 行为 |
|------|------|
| A+ 模块文字 | 不编；用户可贴 |
| 插头电压认证未出现在 listing | 不写死 |
| 评价 <3 条 | 异议类 QA 减量，档案记样本不足 |

积分由用户账号承担；调用前可提一句，不隐瞒。
