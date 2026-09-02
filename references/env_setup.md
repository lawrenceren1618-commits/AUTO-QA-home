# Phase 0 密钥

Cursor 已在用户 `mcp.json` 里接好：

- 卖家精灵：`secret-key=${env:SELLERSPRITE_SECRET_KEY}`
- Sif：`${env:SIF_SECRET_KEY}`

`${env:…}` 读的是 **Windows 用户/系统环境变量**，不是仓库 `env/.env`。所以要填两处。

## 你要做的

1. 打开本仓库 `env/.env`（可从 `env/.env.example` 复制），把密钥贴在等号后（不要引号、不要空格）。
2. 同一对值写进 Windows：设置 → 系统 → 关于 → 高级系统设置 → 环境变量 → 用户变量 → 新建。
3. **完全退出 Cursor 再打开**（只 reload 窗口往往不够）。
4. Cursor Settings → MCP：`sellersprite`、`sif` 应为绿灯。

抽检（密钥配好后）：在对话里让 Agent 调 Sif `ping`。有 ASIN 后再调 `asin_detail`（扣卖家精灵积分）。

不要把密钥发到聊天里。Agent 只确认「已配置/未配置」，不回显密钥内容。

## 本流程会调的 MCP（扣点）

| 源 | 工具 | 用途 |
|----|------|------|
| 精灵 | `asin_detail` | 标题五点类目主图规格 |
| 精灵 | `keepa_info`（限制 returnFields） | 图集 |
| 精灵 | `review` | 评价原文 |
| 精灵 | `traffic_keyword` | 该类目/该 ASIN 搜索痛点 |
| Sif | `ping` | 连通 |
| Sif | `market_get_asin_profile` | 仅 US 规格交叉 |
| Sif | `market_get_asin_keyword_signals` | 仅需 top 词名时，US 痛点交叉 |

不调：Sif `ads_*`、Sorftime（除非用户另说）。
