# 输出：服务商表 + 核对用 Word

所有生成文件只进 `output/{产品名}/`。服务商原表模板在 `templates/点赞、QA.xlsx`，不要往根目录再写填好的副本。

**任务完成后必须新建本次产品文件夹。** 文件夹名用这次产品名（JSON `title`，去掉 `\ / : * ? " < > |`）。这一批的 JSON、服务商表、核对 Word 都放进该文件夹，不要留在 `output/` 根目录。同一产品再改稿，仍写入同一文件夹并覆盖同名文件。

终审通过后 **两份一起写**，不要拆成「先 Word 再等确认才出表」。

| 文件 | 给谁 | 里面是什么 |
|------|------|------------|
| `output/{产品名}/{batch}_qa.xlsx` | 服务商 | 站点原文问/答，按 [sheet_contract.md](sheet_contract.md) |
| `output/{产品名}/{batch}_qa_review.docx` | 你 | 中英对照，方便检查意思、语法、避重就轻有没有错 |

```bash
python scripts/run_autoqa.py deliver --qa-json "output/{产品名}/{batch}_qa.json"
```

禁止直接调用 `write_qa_sheet.py` / `write_review_docx.py`。

## 服务商表

只有上架要用的列。中文释义、listing 分数、运营判断都不要写进去。同一批只这一份 xlsx，禁止再复制 `*_vendor.xlsx` / `*_服务商.xlsx`。

## 核对用 Word

每一条同时有：

| 内容 | 谁用 |
|------|------|
| 中文问 / 中文答（`question_zh` / `answer_zh`） | 你核对意思 |
| 站点问 / 站点答（`question` / `answer`） | 与服务商表同一套原文 |

西语条目标「西」，仍配中文释义。中文不上架。你在 Word 里发现错误后告诉 Agent，回写 JSON，再重出这两份到同一产品文件夹。

JSON `output/{产品名}/{batch}_qa.json` 是机器源，不要另存多份。
