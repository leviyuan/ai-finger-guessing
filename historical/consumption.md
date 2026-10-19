# 十二模型十轮猜拳样本消耗

- 运行：formal-run-20260918-12x22
- 目标：22 轮、12 席、132 场对局、264 次模型出拳
- 已成功解析的出拳：264；含恢复尝试的调用：271
- 调用状态：completed=264，cancelled=5
- Lodestar 报告总 usage：{"cache_creation_input_tokens": 1276810.0, "cache_read_input_tokens": 5254952.0, "input_tokens": 2441008.0, "output_tokens": 21995.0, "reasoning_output_tokens": 4660.0, "total_tokens": 8284482.0}
- Lodestar 报告总费用：unknown

| 席位 | 模型 / 来源 | 成功出拳 | 调用尝试 | usage 合计 | 费用 |
|---|---|---:|---:|---|---:|
| Claude | claude-opus-5 / packy | 22 | 23 | {"cache_creation_input_tokens": 430787.0, "cache_read_input_tokens": 601979.0, "input_tokens": 42.0, "output_tokens": 248.0, "total_tokens": 1033056.0} | unknown |
| Kimi | kimi-k3 / packy-codex | 22 | 25 | {"cache_read_input_tokens": 215307.0, "input_tokens": 289836.0, "output_tokens": 2291.0, "reasoning_output_tokens": 928.0, "total_tokens": 292127.0} | unknown |
| 腾讯 HY4 | tencent/hy4-preview / openrouter | 22 | 23 | {"cache_creation_input_tokens": 0.0, "cache_read_input_tokens": 475392.0, "input_tokens": 154534.0, "output_tokens": 1371.0, "total_tokens": 631297.0} | unknown |
| Gemini | google/gemini-3.8-flash / openrouter | 22 | 22 | {"cache_creation_input_tokens": 526841.0, "cache_read_input_tokens": 526841.0, "input_tokens": 66447.0, "output_tokens": 443.0, "total_tokens": 1120572.0} | unknown |
| Grok | grok-4.6 / packy-codex | 22 | 22 | {"cache_read_input_tokens": 261248.0, "input_tokens": 521383.0, "output_tokens": 3571.0, "reasoning_output_tokens": 3439.0, "total_tokens": 524954.0} | unknown |
| Qwen | qwen3.8-max-0902 / packy-secondary | 22 | 22 | {"cache_creation_input_tokens": 319182.0, "cache_read_input_tokens": 412162.0, "input_tokens": 25252.0, "output_tokens": 5821.0, "total_tokens": 762417.0} | unknown |
| Meta | meta/muse-spark-1.2 / openrouter | 22 | 22 | {"cache_creation_input_tokens": 0.0, "cache_read_input_tokens": 263756.0, "input_tokens": 399038.0, "output_tokens": 4611.0, "total_tokens": 667405.0} | unknown |
| MiniMax | MiniMax-M3 / packy | 22 | 22 | {"cache_creation_input_tokens": 0.0, "cache_read_input_tokens": 542731.0, "input_tokens": 131541.0, "output_tokens": 1235.0, "total_tokens": 675507.0} | unknown |
| 豆包 | bytedance-seed/seed-2-1-turbo / openrouter | 22 | 22 | {"cache_creation_input_tokens": 0.0, "cache_read_input_tokens": 648912.0, "input_tokens": 40896.0, "output_tokens": 862.0, "total_tokens": 690670.0} | unknown |
| DeepSeek | deepseek-flash / deepseek | 22 | 23 | {"cache_creation_input_tokens": 0.0, "cache_read_input_tokens": 574848.0, "input_tokens": 64710.0, "output_tokens": 532.0, "total_tokens": 640090.0} | unknown |
| GLM | GLM-5.3 / glm | 22 | 22 | {"cache_creation_input_tokens": 0.0, "cache_read_input_tokens": 498048.0, "input_tokens": 174468.0, "output_tokens": 472.0, "total_tokens": 672988.0} | unknown |
| GPT-6 | gpt-6-astra / codex-sub | 22 | 23 | {"cache_read_input_tokens": 233728.0, "input_tokens": 572861.0, "output_tokens": 538.0, "reasoning_output_tokens": 293.0, "total_tokens": 573399.0} | unknown |

原始请求、回复、状态和身份快照位于 raw/formal-run-20260918-12x22/；可从 state.json 继续，不重复已有 response.json。
