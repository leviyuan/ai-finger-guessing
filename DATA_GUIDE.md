# 字段与目录说明

| 路径 | 格式 | 内容 |
|---|---|---|
| transcripts/ | Markdown | 十二个模型逐轮完整输入、可读思考/摘要、最终输出、结果，配出拳与积分图 |
| cases/、HIGHLIGHTS.md | Markdown + PNG | 五个案例的图、摘要、证据链接与解释范围 |
| data/rounds/ | 原始 JSON | 22 份逐轮结算，保持来源文件字节不变 |
| data/matches.csv | UTF-8 CSV | 每场一行，132 行 |
| data/moves.csv | UTF-8 CSV | 每席每轮一行，264 行，含调用编号 |
| data/leaderboard.csv、summary.json | CSV / JSON | 从逐轮记录重新汇总的本场统计 |
| evidence/calls.jsonl | JSON Lines | 287 次相关调用，一行一次，包含完整输入与最终返回 |
| evidence/participant-turns.jsonl | JSON Lines | 从原生会话或会话数据库恢复的参赛者回合，可读字段与出处 |
| evidence/coverage.json | JSON | 各模型哪些正式轮次存在可读思考或摘要 |
| reviews/ | Markdown + JSON + TXT | 四份赛后复盘及输入原文 |
| probe/ | Markdown + JSON | 十二份赛后不计分补充回答 |
| historical/ | 原始 Markdown / JSON | 当时写下的旧分析和汇总，未经事后改写；有已知错误 |
| analysis/checked-findings.md | Markdown | 本次重新核对的事实与旧资料纠正 |
| source/ | Python / JavaScript | 当时执行器与视频构建相关代码的快照 |
| video/ | HTML / JSON | 当时 V8 网页、展示计划与验收记录 |
| tools/ | Python / JavaScript | 公开资料导出、文档生成、绘图和离线核验工具 |
| SHA256SUMS | 文本 | 本次公开文件的 SHA-256 清单 |

## 调用记录

- run_id：当时的请求编号，用于串联输入、输出、逐轮结算。
- phase：official 为计分出拳；review 为赛后复盘；probe 为不计分补问；not_selected 为找到的未采用请求。
- requested_model / reported_model：请求阵容所用型号，与调用通道报告的型号分别保留。
- token_source_id / provider：调用来源与入口，不据此暗示消费端客户端。
- requested_effort / reported_effort：预设与通道报告分别保留。
- session_id：当时参赛者的会话编号。用于审计关联，不含会话密钥。
- prompt / output：本次保存的完整输入与最终输出。
- source_*_sha256：来源内容的哈希；text_redacted 标明相关文本是否脱敏。
- status / error / usage / timestamps：本地保存的实际状态和用量，缺失项为 null，不估造费用。

## 会话可读字段

participant-turns.jsonl 的 visible_reasoning 只保存通道实际返回的非空可读文字：

- channel_returned_thinking：原生日志里保存的可读 thinking 字段。
- channel_returned_summary：会话数据库保存的公开思考摘要。

这些字段可能不完整，不能视作整个内部思考过程。opaque_reasoning_blocks 只计数不透明字段，不解密或填补内容。GPT 的已存原赛思考字段为空，不用赛后解释替代。

accepted_run_id 只有在会话、轮次和原始输出能够匹配正式记录时才填写。source_locator 保存来源文件名与行号，或数据库条目编号；去除了本机私人路径。

## 时间和对局编号

JSON 中时间保留 UTC / 来源时区表达，Markdown 显示北京时间（+08:00）。正式轮次为 1—22；probe 的历史编号 23 是制作命名，不是第 23 轮正式比赛。

Markdown 作为阅读版统一换行并清理行末空格；精确请求与返回文本以调用 JSONL 的 prompt / output 字段及对应哈希为准。

## 离线验证

运行 python3 tools/verify.py。脚本只读取本仓库，重新解析出拳与结算并核对 CSV、覆盖率、重点案例、相对链接和哈希。它不重新调用模型，不承诺重跑模型能获得相同出拳。
