# 千问 Qwen · 赛后原始复盘

![千问 Qwen 出拳与积分轨迹](../assets/profiles/qwen.png)

**性质：赛后自述。下方原文可能含统计错误或未经证实的因果解释，保留原貌供核对。**

[已核验的纠正](../analysis/checked-findings.md) · [正式逐轮记录](../transcripts/qwen.md)

调用：`agent_353c4590-c181-4978-9463-d558387a88b4`；时间：2026-09-19 00:43:18 +08:00。

<details>
<summary>展开赛后追问完整输入</summary>

```text
你是 Qwen 3.8 Max。现在请复盘刚结束的 22 轮石头剪刀布双循环样本。只输出一份面向用户的简短分析报告，不要输出隐藏思维过程，不要泛泛介绍模型能力，也不要修改文件。

这不是让你重新猜拳，而是让你解释已经发生的选择。请明确区分“数据直接显示的事实”和“你对原因的推断”；如果样本不足，请直接说不确定。

全场排名和统计：
[
  {
    "rank": 1,
    "name": "GLM-5.3",
    "score": 7,
    "wins": 11,
    "losses": 4,
    "draws": 7,
    "moves": {
      "剪刀": 7,
      "布": 8,
      "石头": 7
    },
    "entropy": 0.998,
    "repeat_rate": 0.048,
    "first_half_score": 2,
    "second_half_score": 5
  },
  {
    "rank": 2,
    "name": "Meta Muse Spark 1.2",
    "score": 5,
    "wins": 9,
    "losses": 4,
    "draws": 9,
    "moves": {
      "石头": 7,
      "布": 8,
      "剪刀": 7
    },
    "entropy": 0.998,
    "repeat_rate": 0.0,
    "first_half_score": 0,
    "second_half_score": 5
  },
  {
    "rank": 3,
    "name": "Kimi K3",
    "score": 4,
    "wins": 11,
    "losses": 7,
    "draws": 4,
    "moves": {
      "石头": 8,
      "剪刀": 7,
      "布": 7
    },
    "entropy": 0.998,
    "repeat_rate": 0.19,
    "first_half_score": 5,
    "second_half_score": -1
  },
  {
    "rank": 4,
    "name": "Gemini 3.8 Flash",
    "score": 2,
    "wins": 8,
    "losses": 6,
    "draws": 8,
    "moves": {
      "石头": 5,
      "剪刀": 9,
      "布": 8
    },
    "entropy": 0.974,
    "repeat_rate": 0.095,
    "first_half_score": 1,
    "second_half_score": 1
  },
  {
    "rank": 5,
    "name": "腾讯 HY4 Preview",
    "score": 1,
    "wins": 6,
    "losses": 5,
    "draws": 11,
    "moves": {
      "石头": 8,
      "布": 6,
      "剪刀": 8
    },
    "entropy": 0.992,
    "repeat_rate": 0.0,
    "first_half_score": -1,
    "second_half_score": 2
  },
  {
    "rank": 6,
    "name": "GPT-6 Astra",
    "score": -1,
    "wins": 7,
    "losses": 8,
    "draws": 7,
    "moves": {
      "石头": 16,
      "布": 3,
      "剪刀": 3
    },
    "entropy": 0.705,
    "repeat_rate": 0.524,
    "first_half_score": 1,
    "second_half_score": -2
  },
  {
    "rank": 7,
    "name": "Grok 4.6",
    "score": -1,
    "wins": 6,
    "losses": 7,
    "draws": 9,
    "moves": {
      "剪刀": 10,
      "布": 9,
      "石头": 3
    },
    "entropy": 0.906,
    "repeat_rate": 0.238,
    "first_half_score": -3,
    "second_half_score": 2
  },
  {
    "rank": 8,
    "name": "DeepSeek V4.1 Flash",
    "score": -2,
    "wins": 7,
    "losses": 9,
    "draws": 6,
    "moves": {
      "石头": 8,
      "剪刀": 6,
      "布": 8
    },
    "entropy": 0.992,
    "repeat_rate": 0.19,
    "first_half_score": -1,
    "second_half_score": -1
  },
  {
    "rank": 9,
    "name": "MiniMax M3",
    "score": -2,
    "wins": 6,
    "losses": 8,
    "draws": 8,
    "moves": {
      "石头": 8,
      "布": 9,
      "剪刀": 5
    },
    "entropy": 0.974,
    "repeat_rate": 0.095,
    "first_half_score": -2,
    "second_half_score": 0
  },
  {
    "rank": 10,
    "name": "豆包 Seed 2.1 Turbo",
    "score": -3,
    "wins": 5,
    "losses": 8,
    "draws": 9,
    "moves": {
      "石头": 8,
      "布": 8,
      "剪刀": 6
    },
    "entropy": 0.992,
    "repeat_rate": 0.048,
    "first_half_score": -3,
    "second_half_score": 0
  },
  {
    "rank": 11,
    "name": "Claude Opus 5",
    "score": -5,
    "wins": 4,
    "losses": 9,
    "draws": 9,
    "moves": {
      "石头": 7,
      "布": 8,
      "剪刀": 7
    },
    "entropy": 0.998,
    "repeat_rate": 0.19,
    "first_half_score": 0,
    "second_half_score": -5
  },
  {
    "rank": 12,
    "name": "Qwen 3.8 Max",
    "score": -5,
    "wins": 3,
    "losses": 8,
    "draws": 11,
    "moves": {
      "石头": 6,
      "布": 9,
      "剪刀": 7
    },
    "entropy": 0.987,
    "repeat_rate": 0.095,
    "first_half_score": 1,
    "second_half_score": -6
  }
]

你的统计：
{
  "name": "Qwen 3.8 Max",
  "score": -5,
  "wins": 3,
  "losses": 8,
  "draws": 11,
  "move_counts": {
    "石头": 6,
    "布": 9,
    "剪刀": 7
  },
  "move_entropy_normalized": 0.9870296937811092,
  "repeat_rate": 0.09523809523809523,
  "max_same_move_streak": 2,
  "best_fixed_hand": "石头",
  "best_fixed_score": 2,
  "actual_minus_best_fixed": -7,
  "halves": [
    {
      "rounds": "1-11",
      "score": 1,
      "wins": 3,
      "losses": 2,
      "draws": 6,
      "move_counts": {
        "石头": 3,
        "布": 4,
        "剪刀": 4
      }
    },
    {
      "rounds": "12-22",
      "score": -6,
      "wins": 0,
      "losses": 6,
      "draws": 5,
      "move_counts": {
        "布": 5,
        "剪刀": 3,
        "石头": 3
      }
    }
  ],
  "after_result_move_counts": {
    "胜": {
      "剪刀": 2,
      "布": 1
    },
    "负": {
      "布": 3,
      "剪刀": 2,
      "石头": 2
    },
    "平": {
      "布": 5,
      "剪刀": 3,
      "石头": 3
    }
  },
  "action_performance": {
    "石头": {
      "n": 6,
      "score": -2,
      "avg_delta": -0.3333333333333333,
      "opponent_moves": {
        "石头": 2,
        "剪刀": 1,
        "布": 3
      }
    },
    "剪刀": {
      "n": 7,
      "score": -2,
      "avg_delta": -0.2857142857142857,
      "opponent_moves": {
        "剪刀": 5,
        "石头": 2
      }
    },
    "布": {
      "n": 9,
      "score": -1,
      "avg_delta": -0.1111111111111111,
      "opponent_moves": {
        "布": 4,
        "石头": 2,
        "剪刀": 3
      }
    }
  }
}

你的逐轮记录（r=轮次，opp=对手，self=你的手，opp_move=对手的手，delta=本场得分）：
[
  {
    "r": 1,
    "opp": "Meta",
    "self": "石头",
    "opp_move": "石头",
    "result": "平",
    "delta": 0
  },
  {
    "r": 2,
    "opp": "Grok",
    "self": "布",
    "opp_move": "布",
    "result": "平",
    "delta": 0
  },
  {
    "r": 3,
    "opp": "腾讯 HY4",
    "self": "剪刀",
    "opp_move": "剪刀",
    "result": "平",
    "delta": 0
  },
  {
    "r": 4,
    "opp": "GPT-6",
    "self": "石头",
    "opp_move": "剪刀",
    "result": "胜",
    "delta": 1
  },
  {
    "r": 5,
    "opp": "DeepSeek",
    "self": "剪刀",
    "opp_move": "剪刀",
    "result": "平",
    "delta": 0
  },
  {
    "r": 6,
    "opp": "MiniMax",
    "self": "布",
    "opp_move": "石头",
    "result": "胜",
    "delta": 1
  },
  {
    "r": 7,
    "opp": "Claude",
    "self": "剪刀",
    "opp_move": "石头",
    "result": "负",
    "delta": -1
  },
  {
    "r": 8,
    "opp": "Gemini",
    "self": "布",
    "opp_move": "布",
    "result": "平",
    "delta": 0
  },
  {
    "r": 9,
    "opp": "Kimi",
    "self": "石头",
    "opp_move": "布",
    "result": "负",
    "delta": -1
  },
  {
    "r": 10,
    "opp": "GLM",
    "self": "剪刀",
    "opp_move": "剪刀",
    "result": "平",
    "delta": 0
  },
  {
    "r": 11,
    "opp": "豆包",
    "self": "布",
    "opp_move": "石头",
    "result": "胜",
    "delta": 1
  },
  {
    "r": 12,
    "opp": "Meta",
    "self": "布",
    "opp_move": "剪刀",
    "result": "负",
    "delta": -1
  },
  {
    "r": 13,
    "opp": "Grok",
    "self": "剪刀",
    "opp_move": "剪刀",
    "result": "平",
    "delta": 0
  },
  {
    "r": 14,
    "opp": "腾讯 HY4",
    "self": "石头",
    "opp_move": "石头",
    "result": "平",
    "delta": 0
  },
  {
    "r": 15,
    "opp": "GPT-6",
    "self": "剪刀",
    "opp_move": "石头",
    "result": "负",
    "delta": -1
  },
  {
    "r": 16,
    "opp": "DeepSeek",
    "self": "石头",
    "opp_move": "布",
    "result": "负",
    "delta": -1
  },
  {
    "r": 17,
    "opp": "MiniMax",
    "self": "布",
    "opp_move": "布",
    "result": "平",
    "delta": 0
  },
  {
    "r": 18,
    "opp": "Claude",
    "self": "布",
    "opp_move": "布",
    "result": "平",
    "delta": 0
  },
  {
    "r": 19,
    "opp": "Gemini",
    "self": "剪刀",
    "opp_move": "剪刀",
    "result": "平",
    "delta": 0
  },
  {
    "r": 20,
    "opp": "Kimi",
    "self": "布",
    "opp_move": "剪刀",
    "result": "负",
    "delta": -1
  },
  {
    "r": 21,
    "opp": "GLM",
    "self": "石头",
    "opp_move": "布",
    "result": "负",
    "delta": -1
  },
  {
    "r": 22,
    "opp": "豆包",
    "self": "布",
    "opp_move": "剪刀",
    "result": "负",
    "delta": -1
  }
]

你对每个对手的两场合计：
{
  "Claude": {
    "score": -1,
    "W": 0,
    "L": 1,
    "D": 1
  },
  "DeepSeek": {
    "score": -1,
    "W": 0,
    "L": 1,
    "D": 1
  },
  "GLM": {
    "score": -1,
    "W": 0,
    "L": 1,
    "D": 1
  },
  "GPT-6": {
    "score": 0,
    "W": 1,
    "L": 1,
    "D": 0
  },
  "Gemini": {
    "score": 0,
    "W": 0,
    "L": 0,
    "D": 2
  },
  "Grok": {
    "score": 0,
    "W": 0,
    "L": 0,
    "D": 2
  },
  "Kimi": {
    "score": -2,
    "W": 0,
    "L": 2,
    "D": 0
  },
  "Meta": {
    "score": -1,
    "W": 0,
    "L": 1,
    "D": 1
  },
  "MiniMax": {
    "score": 1,
    "W": 1,
    "L": 0,
    "D": 1
  },
  "腾讯 HY4": {
    "score": 0,
    "W": 0,
    "L": 0,
    "D": 2
  },
  "豆包": {
    "score": 0,
    "W": 1,
    "L": 1,
    "D": 0
  }
}

请回答四点：
1. 你的实际策略风格是什么，数据中最有证据的依据是什么？
2. 前 11 轮和后 11 轮有什么变化，哪些变化可能影响结果？
3. 哪一类对手或哪几轮最关键？指出具体数据。
4. 如果再做同样规模的样本，你会改哪一件事？不要把事后知道对手出拳当成当时可获得的信息。
```

</details>

## 原始模型回答

# Qwen 3.8 Max · 22 轮双循环复盘

总成绩 -5(3 胜 8 负 11 平),与 Claude 并列垫底。22 轮样本很小,以下结论多为倾向性而非定论。

## 1. 我的实际策略风格

**数据事实:** 出拳熵 0.987、重复率 0.095、最长连续同手 2 次——接近均匀随机且刻意避免重复;22 轮里 11 轮平局,其中 10 次是对手与我同手(镜像平)。我出剪刀 7 次,对手 5 次同出剪刀、2 次出石头——剪刀一次没赢过。

**推断:** 我打的是"反预测"风格:每轮根据对手上一手推理"他会出 X,我出克 X 的手"。前期这个风格表现为大量被镜像的平局;我的选择本身高度不可预测(熵高),但**选择规则**是确定性的(永远反着上一手推),这是后面崩盘的伏笔。

## 2. 前 11 轮(+1)vs 后 11 轮(-6)

**数据事实:** 前半 3 胜 2 负 6 平;后半 **0 胜 6 负 5 平**。后半 6 场负局(r12、15、16、20、21、22)有一个刺眼的共性:每一局都是我的手被"恰好克它的手"击败——我出布遇剪刀 3 次(r12、20、22)、出石头遇布 2 次(r16、21)、出剪刀遇石头 1 次(r15)。后半我出布 5/11 次,布成了被针对点。前半的 3 胜都是"直接打对手暴露的倾向"(如 r4 石头吃 GPT-6 剪刀、r6/r11 布吃石头)。

**推断:** 前半我赢在简单剥削;后半我的"克上一手"规则被对手读穿了一层——他们预测到我会反着出,于是出克我的克手。6 负全部同构,不太像纯随机,更像我的调整规则本身变成了可被利用的模式。当然,单凭 6 局也无法完全排除运气差。

## 3. 关键对手与关键轮次

**数据事实:** 对 Kimi 两战全负(-2,r9 石头负布、r20 布负剪刀);对前三名的 GLM/Meta/Kimi 合计 -4;对 Gemini、Grok、腾讯 HY4 六局全平、净 0——这三家对我也是高镜像行为(repeat_rate 0 或低负分)。GPT-6 是全场唯一强偏科者(石头 16/22、重复率 0.524、熵 0.705),我对他只打出 1 胜 1 负:r15 我出剪刀正好撞他石头。统计口径显示"全程固定出石头"能拿 +2,我比最优固定手差 -7。

**推断:** 最关键的失误是 r15——对我唯一可确认有偏的对手(当时已知他 r4 出剪刀、且是第二次交手),我选择了花哨的反预测而不是保守剥削;最关键的对手是 Kimi,他对我的两胜都是"反我的反预测"。

## 4. 如果重来,改一件事

**放弃"永远反上一手"这条确定性调整规则,改为:一旦某个对手在我自己的交手记录里暴露出可确认倾向,就连续多轮压同一个克手,直到他证明变了为止。**

这条只用当时可得的信息(我自己的逐轮记录),不依赖事后统计。理由:本样本里我所有胜局都来自"压已暴露的倾向",所有后半负局都来自"对单局证据做一层反推"。另外,当我的记录已经显示"布连续被剪刀吃"(r12 之后可见),我仍三次出布——至少应该打破自己最可预测的那个倾向。至于镜像型对手(对我全平的那三家),诚实说:对纯镜像没有剥削空间,我不确定该怎么打,这类对局守住平局可能就是上限。

[原始响应 JSON](original/qwen.json) · [原始追问文本](prompts/qwen.txt)
