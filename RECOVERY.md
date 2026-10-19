# 失败、取消与恢复记录

下列七次请求存在于本地调用存档，但不进入最终 264 次正式出拳。表格只描述保存的状态，不把失败/取消请求算作比赛结果。

| 模型 | 原始轮次 | 状态 | 时间（+08:00） | 请求记录 |
|---|---:|---|---|---|
| Claude | 1 | cancelled | 2026-09-18 12:40:25 +08:00 | [agent_d638d89a-5ece-4ea0-a1dc-1eb75565f587](evidence/calls.jsonl#L1) |
| Kimi | 11 | failed | 2026-09-18 16:59:14 +08:00 | [agent_56ecf69a-35fa-485e-b851-b3c082ba2a5d](evidence/calls.jsonl#L123) |
| GPT-6 | 12 | cancelled | 2026-09-18 17:04:16 +08:00 | [agent_4b3855e2-d1eb-4636-8ded-9cf6b9bca982](evidence/calls.jsonl#L136) |
| 腾讯 HY4 | 12 | cancelled | 2026-09-18 17:08:08 +08:00 | [agent_406f0e25-376e-4ab0-b785-1591fbd526dd](evidence/calls.jsonl#L140) |
| DeepSeek | 14 | cancelled | 2026-09-18 17:35:20 +08:00 | [agent_d656fb60-4f70-401c-a4d9-f435b0c7aa3c](evidence/calls.jsonl#L162) |
| Kimi | 15 | failed | 2026-09-18 17:45:31 +08:00 | [agent_16da112a-0e13-4314-a69b-d7d1128e9b5b](evidence/calls.jsonl#L183) |
| Kimi | 21 | cancelled | 2026-09-18 19:31:23 +08:00 | [agent_09d1209e-7386-40c4-bda3-6bd0d46af564](evidence/calls.jsonl#L249) |

失败原因、原始恢复提示词、实际返回和会话编号均保留在调用 JSONL 中。正式计分采用哪个返回，以每轮 JSON 的 responses.run_id 为准。
