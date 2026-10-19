#!/usr/bin/env python3
"""Render illustrated Markdown from the public export; no private files needed."""
import json
from collections import Counter
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BT = chr(96)
ROSTER = json.loads((ROOT / "data/roster.json").read_text())["players"]
ROUNDS = [json.loads((ROOT / f"data/rounds/round-{n:02d}.json").read_text()) for n in range(1, 23)]
CALLS = [json.loads(s) for s in (ROOT / "evidence/calls.jsonl").read_text().splitlines()]
NATIVE = [json.loads(s) for s in (ROOT / "evidence/participant-turns.jsonl").read_text().splitlines()]
SUMMARY = json.loads((ROOT / "data/summary.json").read_text())
COVERAGE = json.loads((ROOT / "evidence/coverage.json").read_text())
BY_RUN = {c["run_id"]: c for c in CALLS}
CALL_LINE = {c["run_id"]: i for i, c in enumerate(CALLS, 1)}
LABELS = {"claude":"Claude","kimi":"Kimi","hunyuan":"腾讯 HY4","gemini":"Gemini","grok":"Grok",
          "qwen":"千问 Qwen","meta":"Meta","minimax":"MiniMax","doubao":"豆包","deepseek":"DeepSeek","glm":"GLM","gpt":"GPT-6"}


def write(name, text):
    p=ROOT/name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("\n".join(line.rstrip() for line in text.rstrip().splitlines())+"\n")


def code(text, language="text"):
    fence=BT*3
    while fence in text:
        fence+=BT
    return fence+language+"\n"+text.rstrip()+"\n"+fence+"\n"


def details(title, text):
    return "<details>\n<summary>"+title+"</summary>\n\n"+text.strip()+"\n\n</details>\n"


def date(value):
    if not value:
        return "未保存"
    dt=datetime.fromisoformat(value.replace("Z","+00:00"))
    return dt.astimezone(timezone(timedelta(hours=8))).strftime("%Y-%m-%d %H:%M:%S +08:00")


def groups(rid):
    return [g for g in NATIVE if g["accepted_run_id"]==rid]


def readable(rid):
    seen=set()
    values=[]
    for group in groups(rid):
        for entry in group["visible_reasoning"]:
            if entry["text"] not in seen:
                seen.add(entry["text"])
                values.append(entry)
    return values


def make_transcripts():
    index=["# 十二个模型的完整逐轮记录\n",
           "每页包含 22 轮完整请求、原始最终输出、能够恢复的通道可读思考/摘要，以及逐轮结算。输入可展开阅读，未保存的内容明确留空。\n",
           "| 模型 | 正式出拳 | 有可读思考/摘要的轮数 | 完整记录 |\n|---|---:|---:|---|"]
    for p in ROSTER:
        k=p["key"]
        index.append(f'| {LABELS[k]} | 22 | {COVERAGE[k]["readable_reasoning_count"]} | [{p["model"]}]({k}.md) |')
        page=[f'# {LABELS[k]} · 22 轮完整记录\n',
              f'![{LABELS[k]} 出拳与积分轨迹](../assets/profiles/{k}.png)\n',
              f'历史请求型号：{BT}{p["model"]}{BT}；预设 effort：{BT}{p["effort"]}{BT}。通道实际返回字段见每轮原始调用记录。品牌图标仅用于身份展示。\n',
              f'保留 22/22 次正式出拳；其中 {COVERAGE[k]["readable_reasoning_count"]}/22 轮有能够读取的思考文字或摘要。空白不等于没有进行推理，也不能用 reasoning token 数补出文字。\n',
              "这些可读字段来自当时调用通道的保存记录，可能是摘要，不是对模型完整内部过程的声明。英文原文保留；案例图中的中文是编辑概括。\n",
              "[返回模型目录](README.md) · [规则与方法](../METHOD.md) · [字段说明](../DATA_GUIDE.md)\n",
              "轮次导航："+ " · ".join(f'[R{n:02d}](#round-{n:02d})' for n in range(1,23))+"\n"]
        for d in ROUNDS:
            n=d["round"]
            response=next(r for r in d["responses"] if r["player_key"]==k)
            rid=response["run_id"]
            call=BY_RUN[rid]
            match=next(m for m in d["matches"] if p["id"] in [m["a_id"],m["b_id"]])
            a,b=("a","b") if p["id"]==match["a_id"] else ("b","a")
            page += [f'<a id="round-{n:02d}"></a>\n\n## 第 {n:02d} 轮\n',
                     f'**{LABELS[k]}：{match[a+"_move"]} · {match[b+"_name"]}：{match[b+"_move"]} → {match[a+"_result"]}（本轮 {match[a+"_delta"]:+d}；累计 {d["scores_after"][k]:+d}）**\n',
                     f'时间：{date(call["started_at"] or call["created_at"])}；状态：{BT}{call["status"]}{BT}。\n',
                     f'调用编号：{BT}{rid}{BT}。 [本次请求与返回](../evidence/calls.jsonl#L{CALL_LINE[rid]}) · [本轮原始结算](../data/rounds/round-{n:02d}.json)\n',
                     details("展开完整输入（原始提示词）",code(call["prompt"]))]
            reasons=readable(rid)
            if reasons:
                body=[]
                for r in reasons:
                    label="调用通道返回的可读思考文字" if r["kind"]=="channel_returned_thinking" else "调用通道返回的思考摘要"
                    body.append(f'**{label}**\n\n'+code(r["text"]))
                page.append(details("展开当时保存的可读思考 / 摘要","\n".join(body)))
            else:
                page.append("**可读思考：未能从现存记录恢复本轮的非空文字。** 原始出拳仍完整保留。\n")
            page+=["**原始最终输出**\n",code(call["output"],"json")]
        if k in ["claude","glm","meta","qwen"]:
            page.append(f'## 赛后材料\n\n[模型自我复盘](../reviews/{k}.md) · [不计分补充回答](../probe/README.md#{k})\n')
        else:
            page.append(f'## 赛后材料\n\n[不计分补充回答](../probe/README.md#{k})\n')
        write(f"transcripts/{k}.md","\n".join(page))
    write("transcripts/README.md","\n".join(index))


CASES = [
    {"id":"01-qwen","title":"千问：认真猜变招，撞上了石头","kind":"当轮可读记录","model":"qwen","round":15,
     "summary":"第 15 轮，千问根据此前与 GPT-6 的交手尝试预测对方的调整，最终选择剪刀。GPT-6 实际出了石头，千问输掉这一局。",
     "point":"这里能确认的是：千问当时进行了对手预测，而且这次预测没有赢。不能据此判断它整体更强或更弱，也不能证明 GPT 知道千问在想什么。",
     "facts":[("千问","剪刀","负，−1"),("GPT-6","石头","胜，+1")],
     "editorial":"一段认真推测，遇上一记石头。",
     "extra":"上一次交手是第 4 轮：千问石头胜 GPT-6 剪刀。第 15 轮的记录包含对对手可能调整的推测，图中文字只概括这一判断。"},
    {"id":"02-deepseek","title":"DeepSeek：示例写着石头，它真的照着出了","kind":"当轮可读记录","model":"deepseek","round":14,
     "summary":"第 14 轮的恢复请求使用石头作为 JSON 格式示例。DeepSeek 留下的可读记录明确提到沿用这个示例，最终输出石头；Claude 同轮出剪刀，DeepSeek 获胜。",
     "point":"这是提示词示例影响选择的具体证据。它说明这一轮受到示例影响，不能外推为所有石头都由示例造成，也不能把这次获胜当成高水平博弈的证明。",
     "facts":[("DeepSeek","石头","胜，+1"),("Claude","剪刀","负，−1")],
     "editorial":"一个格式示例，也可能影响选择。",
     "extra":"该轮先有一次取消记录，之后恢复。未采用请求与采用请求均在 evidence/calls.jsonl 中，只有最终采用的返回进入比分。全部 264 次正式请求都含石头格式示例，公开版保留原样，不事后修饰为中性示例。"},
    {"id":"03-glm","title":"GLM：只见过一手，也要做个选择","kind":"当轮可读记录","model":"glm","round":12,
     "summary":"第 12 轮，GLM 再次面对 Kimi。它只有一次直接交手信息：第 1 轮 Kimi 石头胜自己的剪刀。可读记录承认基于一个样本可能过度解读，最后仍选择布；Kimi 也出布，平局。",
     "point":"这段呈现信息有限时的决策和不确定性。它不能说明 GLM 已经掌握 Kimi 的稳定规律。",
     "facts":[("GLM","布","平，0"),("Kimi","布","平，0")],
     "editorial":"知道信息不够，仍要在三种手势里选一个。",
     "extra":"GLM 在这组 22 轮数据中最终得分 +7，但本案例发生的第 12 轮是平局。冠军身份与这一次判断是否有效应分别看待。"},
    {"id":"04-meta","title":"Meta：每种都出了，就等于随机吗","kind":"赛后自述与数据核对","model":"meta","round":None,
     "summary":"Meta 在赛后复盘中强调高熵、零重复。重新逐轮核对后，第 3—22 轮严格按剪刀、布、石头的周期重复；全场石头 7 次、布 8 次、剪刀 7 次，其中七次剪刀全部获胜。",
     "point":"边际次数接近均匀，仍然可以对应高度规律的顺序。高熵、零重复本身不能证明不可预测。七次剪刀全胜只是该样本的事实，不是未来胜率。",
     "facts":[("全场手势次数","石头 7 / 布 8 / 剪刀 7","共 22 次"),("第 3—22 轮","剪刀 → 布 → 石头循环","20 轮"),("七次剪刀","全部获胜","7 胜 / 7 次")],
     "editorial":"次数均匀，可以来自固定的顺序。",
     "extra":"这是对赛后自述进行核对，不是把赛后解释还原为比赛当时的思考。原复盘照录，明确可核验的纠正见 analysis/checked-findings.md。"},
    {"id":"05-gpt-claude","title":"GPT 与 Claude：它准备改了，对手还在猜旧招","kind":"赛后补充演示，不计分","model":"gpt","round":None,
     "summary":"GPT-6 在正式 22 轮中出了 16 次石头，最后连续 11 轮出石头。赛后不计分补问中，GPT 表示停止重复、改用布；Claude 则针对 GPT 的石头倾向选择布。两份补充回答都选择布。",
     "point":"这里能展示两种公开解释如何指向同一手势。补问时已有赛后统计，信息条件与原赛不同；它不是原赛第 23 轮，不改变原始积分。",
     "facts":[("GPT-6 正式比赛","石头 16 / 22","最后连续 11 轮石头"),("GPT-6 补充回答","布","不计分"),("Claude 补充回答","布","不计分")],
     "editorial":"同一场比赛，两种判断，最后都选了布。",
     "extra":"当前保存的 GPT 原赛记录没有可读思考正文。本文没有用赛后补问替原赛补写思考，也不声称两份回答来自原比赛中同一局对话。"},
]


def make_cases():
    overview=["# 五个值得展开的案例\n",
              "五张图采用同一套版式。图中文字为编辑概括；前三张引用当轮可读记录，第四张核对赛后自述，第五张来自赛后不计分补充演示。\n"]
    for c in CASES:
        body=[f'# {c["title"]}\n',f'**资料性质：{c["kind"]}。**\n',
              f'![{c["title"]}](../assets/series/{c["id"]}.png)\n',
              "## 记录说了什么\n",c["summary"]+"\n",
              "| 对象 | 出拳 / 数据 | 结果 / 范围 |\n|---|---|---|"]
        body += ["| "+" | ".join(row)+" |" for row in c["facts"]]
        body += ["\n## 可以说明什么\n",c["point"]+"\n",c["extra"]+"\n","## 原始材料\n"]
        if c["round"]:
            n=c["round"];k=c["model"]
            r=next(r for r in ROUNDS[n-1]["responses"] if r["player_key"]==k)
            rid=r["run_id"]
            body += [f'- [第 {n} 轮完整输入、可读思考与输出](../transcripts/{k}.md#round-{n:02d})',
                     f'- [本轮结算 JSON](../data/rounds/round-{n:02d}.json)',
                     f'- [调用原始记录](../evidence/calls.jsonl#L{CALL_LINE[rid]})，编号 {BT}{rid}{BT}\n']
        elif c["model"]=="meta":
            body += ["- [Meta 完整逐轮记录](../transcripts/meta.md)",
                     "- [Meta 原始赛后复盘](../reviews/meta.md)",
                     "- [重新核验的发现与纠正](../analysis/checked-findings.md)\n"]
        else:
            body += ["- [GPT-6 正式 22 轮记录](../transcripts/gpt.md)",
                     "- [GPT-6 补充回答](../probe/README.md#gpt)",
                     "- [Claude 补充回答](../probe/README.md#claude)\n"]
        body += ["## 图文编辑说明\n",f'图中主叙事“{c["editorial"]}”是编辑概括。它不是从原文逐字截取的引语。模型名称和真实型号按当时记录保留。\n',
                 "[返回首页](../README.md) · [五图合集](../HIGHLIGHTS.md)"]
        write(f'cases/{c["id"]}.md',"\n".join(body))
        overview += [f'## {c["title"]}\n',f'**{c["kind"]}**\n',c["summary"]+"\n",
                     f'![{c["title"]}](assets/series/{c["id"]}.png)\n',
                     f'[查看原始材料与解释范围](cases/{c["id"]}.md)\n']
    write("HIGHLIGHTS.md","\n".join(overview))


def make_reviews():
    intro=["# 赛后复盘 · 四个模型\n",
           "正式 22 轮结束后，对前两名和末两名追问。输入含排名及其逐轮记录、统计。以下回答是赛后自述，不是原比赛的当轮思考；其中有可以核验的错误，原文照录。\n",
           "[已核验的纠正](../analysis/checked-findings.md)\n"]
    for f in sorted((ROOT/"reviews/original").glob("*.json")):
        d=json.loads(f.read_text());k=d["model_key"];c=BY_RUN[d["run_id"]]
        body=[f'# {LABELS[k]} · 赛后原始复盘\n',
              f'![{LABELS[k]} 出拳与积分轨迹](../assets/profiles/{k}.png)\n',
              "**性质：赛后自述。下方原文可能含统计错误或未经证实的因果解释，保留原貌供核对。**\n",
              "[已核验的纠正](../analysis/checked-findings.md) · [正式逐轮记录](../transcripts/"+k+".md)\n",
              f'调用：{BT}{d["run_id"]}{BT}；时间：{date(c["started_at"] or c["created_at"])}。\n',
              details("展开赛后追问完整输入",code(c["prompt"])),
              "## 原始模型回答\n",d["output"]+"\n",
              f'[原始响应 JSON](original/{k}.json) · [原始追问文本](prompts/{k}.txt)']
        write(f"reviews/{k}.md","\n".join(body))
        intro.append(f'- [{LABELS[k]} 复盘]({k}.md)')
    write("reviews/README.md","\n".join(intro))
    body=["# 赛后补充演示 · 十二份解释性回答\n",
          "**全部不计分。** 原始目录名中的 round-23 只是制作时的编号，不代表正式比赛扩展到第 23 轮。它不改变 22 轮、132 场、264 次正式出拳。\n",
          "补问要求给出不超过 80 字的可审计理由、一句结论和一手。输入增加了赛后排名、各自统计与最近八轮，因此不能当作原赛当轮思考。下面保留每条完整请求与响应。\n",
          "![GPT 与 Claude 的补充回答](../assets/series/05-gpt-claude.png)\n"]
    for p in ROSTER:
        k=p["key"];d=json.loads((ROOT/f"probe/original/{k}.json").read_text());c=BY_RUN[d["run_id"]]
        body += [f'<a id="{k}"></a>\n\n## {LABELS[k]}\n',
                 f'历史型号：{BT}{d["model"]}{BT}；调用：{BT}{d["run_id"]}{BT}。\n',
                 f'**理由：**{d["reason"]}\n\n**结论：**{d["conclusion"]}\n\n**选择：{d["move"]}；不计分。**\n',
                 details("展开完整输入",code(c["prompt"])),
                 details("展开原始最终输出",code(c["output"],"json")),
                 f'[完整响应 JSON](original/{k}.json)\n']
    write("probe/README.md","\n".join(body))


def main_docs():
    phases=SUMMARY["phase_counts"]
    rows=[]
    for r in SUMMARY["ranking"]:
        rank=1+sum(x["score"]>r["score"] for x in SUMMARY["ranking"])
        rows.append(f'| {rank} | [{LABELS[r["model_key"]]}](transcripts/{r["model_key"]}.md) | {r["score"]:+d} | {r["wins"]} | {r["losses"]} | {r["draws"]} |')
    readme=[
        "# AI 猜拳 · 对局档案\n",
        "十二个模型，二十二轮双循环。这里公开这条视频背后保存下来的请求、返回、可读思考记录、对局数据和制作说明。\n",
        "![五个案例系列图](assets/series/overview.png)\n",
        "**22 轮 · 132 场 · 264 次正式出拳 · 5 张案例图 · 12 份完整逐轮记录**\n",
        "本场记录来自 2026 年 9 月 18—19 日。公开整理时间见提交历史。它是一组娱乐和调用观察样本，不是模型综合能力排名；模型名称、调用通道与 effort 保留当时记录。\n",
        "## 从哪里开始\n",
        "- 想快速看故事：[五图合集](HIGHLIGHTS.md)。\n- 想看完整对话：[十二模型逐轮记录](transcripts/README.md)。\n- 想核对过程：[规则与方法](METHOD.md)、[资料来源与缺失](PROVENANCE.md)、[字段说明](DATA_GUIDE.md)。\n- 想自己算分：[132 场 CSV](data/matches.csv)、[264 次出拳 CSV](data/moves.csv)、[验证脚本](tools/verify.py)。\n",
        "## 五个案例\n",
        "| 图 | 看点 | 资料性质 |\n|---|---|---|",
    ]
    for c in CASES:
        readme.append(f'| {c["id"].split("-")[0]} | [{c["title"]}](cases/{c["id"]}.md) | {c["kind"]} |')
    readme += ["\n前三张使用当轮保存的可读记录；第四张对照赛后自述与实际序列；第五张是赛后补充演示，不计入原赛。图中文字是编辑概括，原文在对应模型页面。\n",
               "## 本场结果\n",
               "| 同分并列名次 | 模型 | 得分 | 胜 | 负 | 平 |\n|---:|---|---:|---:|---:|---:|",
               *rows,
               "\n本表按分数并列，不用同分时的排列顺序推断强弱。每两个模型交手两次；赢 +1、输 −1、平 0。\n",
               "## 公开范围\n",
               f'归档中共找到 **{len(CALLS)} 次相关调用**：{phases["official"]} 次计分出拳、{phases["review"]} 次赛后复盘、{phases["probe"]} 次不计分补问、{phases["not_selected"]} 次失败或取消请求。后者也保留，见 [失败与恢复记录](RECOVERY.md)。\n',
               "每次正式出拳的完整提示词和最终返回都在。思考字段的保留程度因通道而异，见 [覆盖率](evidence/coverage.json)；未返回、被隐藏或没有保存的部分不会补写。整理时发现的旧复盘错误，集中在 [已核验的发现](analysis/checked-findings.md)。\n",
               "## 本地核验\n",
               code("python3 tools/verify.py","sh"),
               "无需 API Key、模型账号或网络。脚本从原始返回重新结算，检查轮次、配对、积分、CSV、案例事实、资料覆盖和文件校验值。\n",
               "重新生成 Markdown 与图表：\n",
               code("python3 tools/build_docs.py\npython3 tools/build_visuals.py\nnpm ci\nnode tools/render_cards.cjs","sh"),
               "PNG 图片由 HTML/CSS 与真实数据确定性绘制，1600 × 2000。渲染需要 Chrome/Chromium 与中文字体；可以通过 CHROME_PATH 指定浏览器。没有重新调用参赛模型，也没有生成新的比赛结果。\n",
               "## 资料与使用说明\n",
               "- [字段与目录说明](DATA_GUIDE.md)\n- [来源、缺失与证据边界](PROVENANCE.md)\n- [脱敏说明](REDACTIONS.md)\n- [赛后原始复盘](reviews/README.md)\n- [不计分补充回答](probe/README.md)\n- [历史视频网页与验收记录](video/README.md)\n- [品牌素材来源及许可](assets/brands/sources.json)\n",
               "代码按仓库原有 [MIT License](LICENSE) 发布。第三方商标、图标、模型输出的权利归属不因本仓库的代码许可而改变；品牌素材的来源与适用说明单独列出。"]
    write("README.md","\n".join(readme))

    write("METHOD.md", f"""# 规则与方法

## 这组数据是什么

正式资料为 2026 年 9 月 18 日完成的十二模型二十二轮双循环：每轮六场，每两个模型交手两次，每个模型出拳 22 次。赢 +1、输 −1、平 0；一场双方得分之和为 0。

原始任务写明它是检查调用消耗的研究样本，不代表模型能力评测。赛后视频用真实记录呈现比赛；早期十席模拟样片不属于这里的正式 264 次出拳。

## 模型实际看到什么

每次提示词说明当前身份、对手、轮次、规则和双方累计分数，附带该模型自己的历史逐局记录，以及它与当前对手此前的直接交手记录。

这不等于给它对手与其他所有模型交手的完整记录。本轮对手尚未揭示的选择不会写入该轮提示词。每份实际输入均保存在 [调用记录](evidence/calls.jsonl)，能够逐一核对。

## 调用与结算

保存的执行器按一组对手两席并发提交，六组依次调度。全部十二席返回后统一结算这一轮，再进入下一轮。视频中六组同时揭拳是展示安排，不表示十二个请求在完全相同的时刻到达服务商。

解析器从最终输出中取最后一个合法的单字段 JSON 对象，move 只能是石头、剪刀、布。这里公开全部原始输出，因此可以核对是否存在额外文字或多个候选对象。详见 [执行器](source/formal_run_12x22.py)。

运行过程中有目标轮数变更和会话恢复，实际提示词中可能写 10、100、20、24 或 22 轮。最终采用前 22 轮完整结算记录，保留历史提示词，不把分母事后改写成 22。找到的失败/取消请求见 [恢复记录](RECOVERY.md)。

## 提示词中的已知影响因素

全部 264 次正式请求都使用 {BT}{{"move":"石头"}}{BT} 作为输出格式示例。DeepSeek 第 14 轮留下的可读文字明确提及按此示例选择石头。这个事实会影响对结果的解释，公开版保留它。

原提示词要求最终只返回手势、禁止附加解释。部分通道另外保存了可读 thinking 字段或思考摘要，部分没有。可读文字的多少不能跨通道直接用作推理能力或投入量的指标。

## 身份与配置

[历史阵容快照](data/roster.json)记录请求型号、调用源和预设 effort；[逐次调用记录](evidence/calls.jsonl)另存通道报告的型号、provider 和 effort。这里没有重新调用或升级模型。

这些字段是本地调用通道的报告，不是服务商签名的身份认证。不同渠道的同名 effort 不等价；使用品牌图标不代表通过相应消费端 App 进行比赛。

## 赛后资料

四份自我复盘和十二份解释性补问都发生在正式比赛之后。补问提供了赛后统计与最近八轮，因此拥有与原赛不同的信息条件。全部单独收录，不计分，不为原赛补写思考。

## 统计与呈现

本仓库核验的是本样本的事实：出拳、胜负、积分和可观察的顺序。22 轮、每个对手两次不足以证明稳定策略、心理人格或模型综合强弱。

图片中的中文摘要是编辑文字，不标为逐字引语。原视频的角色弹幕也属于节目化改写，不作为模型原话证据。五张新图使用确定性 HTML/CSS 排版和数据图表；没有用新模型调用补出历史内容。

本页描述归档中可检查的流程，不将本地日志、截图或当前生成的哈希视作独立第三方认证。
""")

    write("DATA_GUIDE.md", """# 字段与目录说明

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
""")

    write("PROVENANCE.md", f"""# 来源、缺失与证据边界

本仓库由当时的猜拳项目文件、Lodestar 调用存档、参赛者原生会话和本机会话数据库整理而成。只抽取本场参赛者与直接相关请求，未公开整个设备的会话库。

## 已保留与核验

- 22 轮、132 场、264 次采用出拳的结算 JSON。
- 264 份正式完整输入和最终输出；已与逐轮 JSON 中的返回逐条比对。
- 4 次赛后复盘与 12 次不计分补充回答。
- 本地检索到的 7 次失败或取消请求。
- 可恢复的参赛者会话字段，精确覆盖见 evidence/coverage.json。
- 五个新案例图、十二份出拳积分图、当时的视频网页与验收资料。

## 没有冒充完整保留的内容

部分底层 JSONL 会话文件已不存在，其中一些内容从会话数据库恢复。部分通道本来只保存摘要、空思考字段或不透明字段。这些差异均保留，不用推理 token 数量或后来问答补成“完整思维过程”。

项目中的旧 MP4、WAV 当前未找到。视频目录保留的是原始网页、计划与当时检查记录；本次没有重新导出或重新验收旧 MP4。旧验收中的 passed 只代表当时那次检查。

287 是本次实际恢复出的相关调用数，不宣称能排除本地存档之外的未保存事件。旧 state.json 的 submitted_attempts 等计数受续跑迁移影响，与成功出拳总数不一致，因此公开汇总从逐轮数据和找到的调用记录重算，原 state.json 留在 historical/。

## 可核对的链条

原始提示词 → run_id 对应返回 → round JSON 中采用的手势 → 胜负与积分 → 原视频计划中的序列。

来源字节保留清单在 evidence/source-files.json；当前公开文件哈希在 SHA256SUMS。哈希可以检测文件与本次清单是否一致，不能单独证明文件历史上从未改动，也不是服务商提供的签名。

## 发布版本

本次以 {SUMMARY["exported_at"]} 的导出快照为基础。公开版提交 SHA 是后续引用的稳定版本；更正使用后续提交并说明，不覆盖历史原文以制造一致。
""")

    write("REDACTIONS.md", """# 公开副本与脱敏说明

导出工具只选择本场参赛者的请求和返回，按字段白名单输出。会话账号 ID、飞书群 ID、消息卡片 ID、本机工作目录、凭据和无关工具步骤不进入公开副本。

原始提示词和模型返回保留；若文本中出现本机用户目录，以 <LOCAL_PATH> 替换，并记录 text_redacted。请求编号、参赛会话编号、真实模型字符串、通道、时间、usage、失败原因和是否采用等比赛相关信息保留。

原生会话只提取与本场请求对应的用户输入、最终回答、通道实际返回的可读思考文字/摘要及出处定位；不导出环境系统消息或组织者的私人推理，不解密不透明字段。

文件哈希分为来源哈希与公开副本哈希。对发生脱敏的文件，两者可能不同，不能混为同一份原始字节。完整项目路径没有写进公开来源清单。

图文中的中文摘要、图形和重算统计属于本次整理；原始英文与中文返回均保留自己的文本，不以翻译覆盖原文。
""")

    lines=["# 失败、取消与恢复记录\n",
           "下列七次请求存在于本地调用存档，但不进入最终 264 次正式出拳。表格只描述保存的状态，不把失败/取消请求算作比赛结果。\n",
           "| 模型 | 原始轮次 | 状态 | 时间（+08:00） | 请求记录 |\n|---|---:|---|---|---|"]
    for c in CALLS:
        if c["phase"]=="not_selected":
            lines.append(f'| {LABELS[c["model_key"]]} | {c["round"]} | {c["status"]} | {date(c["created_at"])} | [{c["run_id"]}](evidence/calls.jsonl#L{CALL_LINE[c["run_id"]]}) |')
    lines.append("\n失败原因、原始恢复提示词、实际返回和会话编号均保留在调用 JSONL 中。正式计分采用哪个返回，以每轮 JSON 的 responses.run_id 为准。")
    write("RECOVERY.md","\n".join(lines))

    write("analysis/checked-findings.md", """# 重新核验的发现与旧资料纠正

本页根据 22 份逐轮 JSON 重新计算。历史分析与模型复盘保留原文；以下更正不回写为模型当时说过的话。

| 项目 | 可复算的事实 | 需要纠正的解释 |
|---|---|---|
| GPT-6 出石头 | 16/22；第 12—22 轮连续 11 次石头 | 赛后补问说“最近 8 轮全是石头”是截取窗口，不是最长连续段 |
| Meta 序列 | 第 3—22 轮严格重复剪刀→布→石头；全场次数 7/8/7 | 手势次数熵高不等于顺序不可预测 |
| Meta 零重复 | Meta 相邻重复为 0，腾讯 HY4 也为 0 | 原复盘说“全场唯一零重复”不成立 |
| GLM 重复位置 | 唯一相邻重复发生在第 11、12 轮，均为布 | 原复盘把重复写在第 19 轮，错误 |
| GLM 收官三手 | 第 20、21、22 轮依次为剪刀、布、石头，均胜 | 原复盘列出的手势顺序不正确 |
| GLM 最后优势 | GLM +7，Meta +5；把 GLM 一场胜改为平仅降到 +6 | 原复盘称任一收官胜变平就失去第一，不成立 |
| Qwen 后半程 | 0 胜、6 负、5 平 | “六负都被相克手势击败”是规则本身，不能据此证明被读穿 |
| 前两名赢后复制旧对手手势 | 合计 19/19；GLM 10/10、Meta 9/9 | 旧行为分析有一处把合计 19/19 误标成 GLM 单独值 |

![Meta 的序列核对](../assets/series/04-meta.png)

## 五个案例的确认结果

- 第 15 轮：千问剪刀负于 GPT-6 石头。
- 第 14 轮：DeepSeek 石头胜 Claude 剪刀，DeepSeek 可读记录明确提到按格式示例选择。
- 第 12 轮：GLM 与 Kimi 都出布，平局；GLM 当轮提到只有一个直接样本。
- Meta 七次剪刀均胜；第 3—22 轮存在严格三步周期。
- 赛后补问 GPT-6 与 Claude 都选择布，不计入正式结果。

这些是样本内事实。对手是否“读心”、为何恰好命中、某策略是否稳定更优，都不能仅凭这组观察确定。
""")

    write("historical/README.md", """# 当时的分析与状态快照

这里保留比赛结束时写下的分析、消耗汇总、结果和运行状态。内容保持原貌，不是本次重新认证的结论。

已知的问题包括：把均匀分布直接解释成不可预测、部分模型复盘中的轮次/手势错误、state.json 中续跑继承的过期计数和停止字段。请与 [重新核验的发现](../analysis/checked-findings.md)、[逐轮原始数据](../data/rounds/) 对照。
""")
    write("source/README.md", """# 当时执行器的来源快照

这些文件用于说明提示词、解析、重试和赛后补问的实际实现。它们保持当时的项目结构依赖，不是脱离原工程就能重跑所有在线模型的一键程序。

本仓库的离线核验入口是 tools/verify.py；文档与图像生成入口是 tools/build_docs.py 和 tools/build_visuals.py。核验不需要原工程、Lodestar 或模型账号。
""")
    write("video/README.md", """# 历史 V8 视频资料

当前保留当时的 [V8 网页](rps-carousel-v8.html)、[视频计划](formal-v8-video-plan.json)、[视频检查](formal-v8-video-check.json) 与 [浏览器检查](formal-v8-browser-check.json)。

V8 为 34 秒、1440 × 2560、30 fps。正式数据是十二席二十二轮；排行段角色弹幕是节目化改写，不是模型逐字原话。

旧 MP4 和 WAV 当前未找到，因此没有将重新生成的文件冒充旧成片。网页可以展示原画面逻辑，但其原始音频文件不在；检查记录中的哈希和解码通过只说明当时版本。
""")
    write("DESIGN.md", """# 系列图设计与复现

五张主图统一为 1600 × 2000 PNG。逻辑画布 1200 × 1500，以 4/3 像素密度渲染；暖白纸色背景、深色正文、统一字级与页眉，每个案例使用一种强调色。

五图分别标明当轮记录、赛后自述核对、赛后不计分演示。叙事摘要、出拳对照、证据来源和仓库地址在固定区域。全部文字与数字通过代码排版，未用新模型生成历史解释或结果。

可编辑源文件为 design/series.html；配置在 design/series.json；生成脚本为 tools/build_visuals.py。十二张 SVG 轨迹图直接从逐轮数据绘制，未手工改点。

品牌素材复用项目已确认的共享品牌目录。千问使用 Qwen 标志，腾讯席位使用元宝，豆包使用已确认女性头像。品牌标识不暗示调用了对应消费端应用。

字体优先使用系统 PingFang SC，回退 Noto Sans CJK SC / Microsoft YaHei。字体文件不随仓库分发；PNG 已固定字形。手势由系统彩色 Emoji 字体绘制。第三方品牌素材来源及许可见 assets/brands/。
""")


if __name__ == "__main__":
    make_transcripts()
    make_cases()
    make_reviews()
    main_docs()
    print("Built 12 illustrated transcripts, 5 cases, 4 reviews, the probe and audit documents.")
