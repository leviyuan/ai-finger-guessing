#!/usr/bin/env python3
"""Build editable, deterministic artwork from the published match records."""
import base64
import html
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ROSTER = json.loads((ROOT / "data/roster.json").read_text())["players"]
ROUNDS = [json.loads((ROOT / f"data/rounds/round-{n:02d}.json").read_text()) for n in range(1, 23)]
BRANDS = {
    "qwen": "qwen.svg", "deepseek": "deepseek.svg", "glm": "zai.svg", "gpt": "openai.svg",
    "claude": "claude.svg", "meta": "meta.svg", "kimi": "kimi.svg", "hunyuan": "yuanbao.svg",
    "gemini": "google.svg", "grok": "xai.svg", "minimax": "minimax.svg", "doubao": "doubao-female.jpg",
}
COLORS = {"石头": "#5372c6", "布": "#dd9952", "剪刀": "#6d9c83"}
SYMBOLS = {"石头": "石", "布": "布", "剪刀": "剪"}
EMOJI = {"石头": "✊", "布": "✋", "剪刀": "✌️"}
SERIES = [
    {"id": "01-qwen", "number": "01", "accent": "#7660aa", "tint": "#ece5f6",
     "tag": "当轮记录", "round": "R15 · 千问 × GPT-6", "title": "认真猜变招，<br><em>撞上了石头。</em>",
     "deck": "一段认真推测，遇上一记石头。",
     "insight": "推测得更复杂，不保证这一手更准。",
     "evidence": "千问第 15 轮可读记录 + 双方原始出拳",
     "note": "当时的记录提到对手可能调整；这里概括其判断，不把推测当成事实。"},
    {"id": "02-deepseek", "number": "02", "accent": "#3269b0", "tint": "#e2ebf7",
     "tag": "当轮记录", "round": "R14 · DeepSeek × Claude", "title": "示例写着石头，<br><em>它真的照着出了。</em>",
     "deck": "一个格式示例，也可能影响选择。",
     "insight": "赢了这一手，也要看它为何这样选。",
     "evidence": "DeepSeek 第 14 轮恢复请求、可读记录与结算",
     "note": "该轮记录明确提到沿用示例的石头；这只能说明本轮受到示例影响。"},
    {"id": "03-glm", "number": "03", "accent": "#34745b", "tint": "#e0eee7",
     "tag": "当轮记录", "round": "R12 · GLM × Kimi", "title": "只见过一手，<br><em>也要做个选择。</em>",
     "deck": "知道信息不够，仍要在三种手势里选一个。",
     "insight": "承认不确定，再给出自己的选择。",
     "evidence": "GLM 第 12 轮可读记录 + 第 1、12 轮结算",
     "note": "GLM 提醒自己：只依据一次交手，可能过度解读；最后仍选择了布。"},
    {"id": "04-meta", "number": "04", "accent": "#b46d36", "tint": "#f4e6d4",
     "tag": "赛后自述 × 数据核对", "round": "R03—R22 · Meta",
     "title": "每种都出了，<br><em>就等于随机吗？</em>",
     "deck": "它强调均衡；逐轮顺序里，却藏着一个循环。",
     "insight": "次数均匀，可以来自固定的顺序。",
     "evidence": "Meta 赛后复盘 + 22 轮原始出拳序列",
     "note": "第 3—22 轮严格重复“剪刀 → 布 → 石头”；七次剪刀均获胜是样本事实。"},
    {"id": "05-gpt-claude", "number": "05", "accent": "#ad565b", "tint": "#f3e3e2",
     "tag": "赛后补充 · 不计分", "round": "补充演示 · GPT-6 × Claude",
     "title": "它准备改了，<br><em>对手还在猜旧招。</em>",
     "deck": "同一场比赛，两种判断，最后都选了布。",
     "insight": "新解释发生在赛后，原赛果保持不变。",
     "evidence": "22 轮出拳统计 + GPT-6、Claude 两份补充回答",
     "note": "两份补充回答都选择布；这是赛后不计分演示，不是原赛第 23 轮。"},
]


def brand(key, label):
    background = ' style="background:#222831;border-color:#222831"' if key == "kimi" else ""
    return f'<div class="brand"><span class="logo"{background}><img src="../assets/brands/{BRANDS[key]}" alt=""></span><b>{label}</b></div>'


def hand(move, label=""):
    return f'<div class="hand"><span>{EMOJI[move]}</span><b>{move}</b><small>{label}</small></div>'


def match(left_key, left_name, left_move, right_key, right_name, right_move, result, left_caption="", right_caption=""):
    return f'''<div class="match">
      <div class="side">{brand(left_key,left_name)}{hand(left_move,left_caption)}</div>
      <div class="versus"><span>VS</span><i></i></div>
      <div class="side">{brand(right_key,right_name)}{hand(right_move,right_caption)}</div>
    </div><div class="verdict">{result}</div>'''


def content(n):
    if n == 1:
        return f'''<div class="thought-strip"><span>当轮判断 · 摘要</span><p>千问尝试预测 GPT 会如何调整，<br>最终选择了剪刀。</p><div class="thought-path"><i></i><i></i><i></i></div></div>
          {match("qwen","千问","剪刀","gpt","GPT-6","石头","实际结果：千问负 · GPT-6 胜","推测对手会变招","实际出了石头")}'''
    if n == 2:
        return f'''<div class="code-window"><div class="window-top"><i></i><i></i><i></i><span>当时提示词的格式示例</span></div><div class="code-body">&#123;<span>"move"</span>: <strong>"石头"</strong>&#125;</div><p>记录中明确提到，沿用示例选择石头。</p></div>
          {match("deepseek","DeepSeek","石头","claude","Claude","剪刀","实际结果：DeepSeek 胜 · Claude 负","沿用示例","本轮出拳")}'''
    if n == 3:
        return f'''<div class="memory"><div class="memory-number">01<span>次直接交手</span></div><div class="memory-copy"><span>上次 · 第 1 轮</span><b>Kimi 出石头，GLM 出剪刀</b><p>GLM 知道只凭这一条记录，<br>可能过度解读。</p></div></div>
          {match("glm","GLM","布","kimi","Kimi","布","实际结果：双方出布 · 平局","再次交手选择布","这一轮也选择布")}'''
    if n == 4:
        cells = ""
        seq = [d["moves"]["meta"] for d in ROUNDS]
        for n, move in enumerate(seq[2:], 3):
            cells += f'<div class="sequence-cell" style="--move:{COLORS[move]}"><span>{n:02d}</span><b>{SYMBOLS[move]}</b></div>'
        return f'''<div class="meta-intro">{brand("meta","Meta")}<p>赛后自述强调<br><strong>“高熵、零重复”</strong></p><span class="audit-label">与出拳顺序对照</span></div>
          <div class="cycle"><span>剪刀</span><i>→</i><span>布</span><i>→</i><span>石头</span><i>↺</i></div>
          <div class="sequence-label">第 3—22 轮 · 按时间顺序</div><div class="sequence-grid">{cells}</div>
          <div class="meta-stats"><div><strong>7 / 8 / 7</strong><span>石头 / 布 / 剪刀 · 全场次数</span></div><div><strong>7 / 7</strong><span>七次剪刀 · 七次获胜</span></div></div>'''
    return f'''<div class="gpt-stats"><div><strong>16<span>/22</span></strong><p>正式比赛出石头次数</p></div><div><strong>11<span>轮</span></strong><p>最后连续出石头</p></div></div>
      <div class="postgame"><div class="postgame-card">{brand("gpt","GPT-6")}<p>停止重复石头，<br><b>改用布。</b></p>{hand("布")}</div>
      <div class="postgame-card">{brand("claude","Claude")}<p>押它的石头倾向，<br><b>出布。</b></p>{hand("布")}</div></div>
      <div class="verdict">两份补充回答 · 都选择了布</div>'''


CSS = """
*{box-sizing:border-box}html,body{margin:0;background:#ddd9d3;color:#23272e;font-family:"PingFang SC","Noto Sans CJK SC","Microsoft YaHei",sans-serif}
.poster{width:1200px;height:1500px;position:relative;overflow:hidden;background:#f8f5ee;padding:64px 76px;isolation:isolate;margin:0}
.poster:before{content:"";position:absolute;inset:0;z-index:-1;opacity:.15;background-image:url("data:image/svg+xml,%3Csvg viewBox='0 0 180 180' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='.8' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' opacity='.13' filter='url(%23n)'/%3E%3C/svg%3E")}
.poster:after{content:"";position:absolute;width:620px;height:620px;border:1px solid var(--accent);opacity:.09;right:-360px;top:130px;border-radius:50%;z-index:-1;box-shadow:0 0 0 70px var(--tint),0 0 0 71px var(--accent),0 0 0 140px var(--tint),0 0 0 141px var(--accent)}
header{display:flex;justify-content:space-between;align-items:center;border-top:4px solid #252a31;padding-top:22px}
.masthead{font-size:24px;font-weight:750;letter-spacing:5px}.edition{font-size:18px;color:#6e7176;letter-spacing:2px;display:block;margin-top:8px;font-family:Arial,sans-serif}
.serial{font-family:Arial,sans-serif;color:var(--accent);font-size:62px;font-weight:800;letter-spacing:-3px}.serial small{font-size:24px;color:#7c7d7d;font-weight:400;letter-spacing:0;margin-left:8px}
.meta{margin-top:36px;display:flex;align-items:center;gap:18px;font-size:21px;color:#555d66}.tag{background:var(--accent);color:white;font-size:19px;padding:9px 16px;font-weight:650;border-radius:5px}
h1{font-size:83px;line-height:1.23;font-weight:850;margin:28px 0 18px;letter-spacing:-3px}h1 em{font-style:normal;color:var(--accent)}.deck{font-size:26px;letter-spacing:.3px;color:#62676a;margin:0}
.stage{height:700px;margin-top:36px;position:relative;background:#fffdf8;border:1.5px solid #d9d7d1;border-radius:22px;box-shadow:0 15px 25px #27232206;overflow:hidden}
.thought-strip{background:var(--tint);padding:25px 40px;position:relative;height:207px;border-bottom:1px solid #d9d7d1}.thought-strip>span{color:var(--accent);font-weight:700;font-size:19px;letter-spacing:2px}.thought-strip p{font-size:31px;font-weight:650;line-height:1.5;margin:12px 0}
.thought-path{position:absolute;right:57px;top:40px;width:205px;height:130px}.thought-path i{position:absolute;width:100px;height:60px;border:2px solid var(--accent);border-radius:50%;opacity:.2;transform:rotate(-30deg)}.thought-path i:nth-child(2){left:50px;top:28px}.thought-path i:nth-child(3){left:100px;top:56px}
.match{display:flex;height:398px;padding:28px 48px 0;position:relative}.side{flex:1;display:flex;flex-direction:column;align-items:center;position:relative}.side:after{content:"";position:absolute;top:103px;width:226px;height:226px;background:var(--tint);border-radius:50%;z-index:0;opacity:.75}
.brand{display:flex;align-items:center;gap:12px;font-size:29px;line-height:1;position:relative;z-index:1}.logo{background:white;width:50px;height:50px;display:flex;align-items:center;justify-content:center;border:1px solid #e6e2da;border-radius:13px}.logo img{width:33px;height:33px;object-fit:contain}
.hand{position:relative;z-index:1;display:flex;flex-direction:column;align-items:center}.hand>span{font-family:"Apple Color Emoji","Segoe UI Emoji",sans-serif;font-size:155px;line-height:1.2;margin:20px 0 4px;filter:drop-shadow(0 9px 0 #8d684311)}.hand>b{font-size:38px;font-weight:800}.hand small{font-size:20px;color:#697078;margin-top:8px;min-height:25px}
.versus{width:130px;display:flex;align-items:center;flex-direction:column;padding-top:122px;color:#96918a;font-family:Arial,sans-serif}.versus span{font-size:30px;font-weight:800;letter-spacing:4px}.versus i{width:1px;height:55px;background:#d5cfc4;margin-top:15px}
.verdict{margin:0 38px;background:#293039;color:#fff;border-radius:10px;text-align:center;padding:20px;font-size:27px;line-height:1.15;font-weight:650}
.code-window{height:207px;background:var(--tint);border-bottom:1px solid #d9d7d1;padding:22px 40px}.window-top{display:flex;align-items:center;gap:8px}.window-top>i{width:10px;height:10px;border-radius:50%;background:var(--accent);opacity:.35}.window-top>span{font-size:19px;color:var(--accent);font-weight:700;margin-left:10px}.code-body{font-family:Menlo,Consolas,monospace;font-size:46px;margin-top:17px;letter-spacing:1px}.code-body span{color:#505d6d}.code-body strong{color:var(--accent)}.code-window p{margin:9px 0;font-size:20px;color:#5b6674}
.memory{height:207px;background:var(--tint);display:flex;align-items:center;padding:24px 40px;gap:40px;border-bottom:1px solid #d9d7d1}.memory-number{color:var(--accent);font-size:84px;font-weight:850;font-family:Arial,sans-serif;letter-spacing:-3px}.memory-number span{display:block;font-family:inherit;font-size:19px;letter-spacing:0;font-weight:500;margin-top:0}.memory-copy{border-left:1px solid #adc8ba;padding-left:36px}.memory-copy>span{font-size:18px;color:#527465}.memory-copy>b{display:block;font-size:28px;margin-top:8px}.memory-copy p{font-size:23px;line-height:1.4;color:#52675c;margin:10px 0 0}
.insight{display:flex;gap:18px;align-items:flex-start;margin-top:27px}.insight .mark{font-size:42px;line-height:1;color:var(--accent);font-family:Georgia,serif}.insight strong{font-size:29px;font-weight:800;line-height:1.4}.insight p{font-size:19px;line-height:1.55;margin:8px 0 0;color:#6a6d70}
footer{position:absolute;bottom:44px;left:76px;right:76px;display:flex;justify-content:space-between;align-items:flex-end;border-top:1px solid #cfcac1;padding-top:17px;gap:12px;color:#737777;font-size:15px;line-height:1.65}footer b{display:block;font-weight:550;color:#444d52}footer .url{font-family:Arial,sans-serif;font-size:15px;text-align:right;white-space:nowrap}
.meta-intro{display:flex;align-items:center;gap:26px;padding:30px 38px;border-bottom:1px solid #e2d9ca;background:var(--tint);height:150px}.meta-intro p{margin:0;font-size:24px;line-height:1.5;border-left:1px solid #d4baa0;padding-left:26px}.audit-label{font-size:18px;color:var(--accent);margin-left:auto}
.cycle{display:flex;align-items:center;justify-content:center;gap:28px;margin-top:25px}.cycle span{font-size:36px;font-weight:800}.cycle i{font-size:33px;color:var(--accent);font-style:normal}
.sequence-label{text-align:center;font-size:18px;color:#887a6e;margin:20px 0 14px}.sequence-grid{padding:0 38px;display:grid;grid-template-columns:repeat(10,1fr);gap:12px}.sequence-cell{text-align:center}.sequence-cell>span{display:block;font-size:14px;color:#8e8b85;font-family:Arial,sans-serif;margin-bottom:6px}.sequence-cell>b{display:flex;align-items:center;justify-content:center;border-radius:10px;background:var(--move);color:white;height:65px;font-size:29px}
.meta-stats{display:flex;justify-content:space-around;border-top:1px solid #ded4c8;margin:28px 38px 0;padding-top:20px;text-align:center}.meta-stats strong{display:block;font-family:Arial,sans-serif;font-size:44px;color:var(--accent);letter-spacing:1px}.meta-stats span{display:block;font-size:20px;color:#685f56;margin-top:8px}
.gpt-stats{display:flex;background:var(--tint);height:160px;align-items:center;justify-content:space-around;text-align:center;border-bottom:1px solid #ddc8c7}.gpt-stats strong{font-family:Arial,sans-serif;color:var(--accent);font-size:66px;font-weight:850;letter-spacing:-2px}.gpt-stats strong>span{font-size:30px;letter-spacing:0;margin-left:4px}.gpt-stats p{font-size:20px;margin:4px 0;color:#786365}
.postgame{display:flex;gap:0;height:450px;padding:27px 40px 0}.postgame-card{width:50%;display:flex;flex-direction:column;align-items:center}.postgame-card+.postgame-card{border-left:1px solid #e6dcd9}.postgame-card>p{text-align:center;font-size:25px;line-height:1.5;margin:16px 0 0}.postgame-card>p b{color:var(--accent)}.postgame-card .hand>span{font-size:115px;margin:12px 0 0}.postgame-card .hand>b{font-size:29px}.postgame-card .hand>small{display:none}
"""


def build_cards():
    pages = []
    for n, c in enumerate(SERIES, 1):
        pages.append(f'''<section class="poster" id="{c['id']}" style="--accent:{c['accent']};--tint:{c['tint']}">
        <header><div><div class="masthead">AI 猜拳 · 对局档案</div><span class="edition">THE RPS RECORDS / SEPTEMBER 2026</span></div><div class="serial">{c['number']}<small>/ 05</small></div></header>
        <div class="meta"><span class="tag">{c['tag']}</span><span>{c['round']}</span></div>
        <h1>{c['title']}</h1><p class="deck">{c['deck']}</p>
        <div class="stage">{content(n)}</div>
        <div class="insight"><span class="mark">↳</span><div><strong>{c['insight']}</strong><p>{c['note']}</p></div></div>
        <footer><div><b>{c['evidence']}</b>图中文字为摘要；原始记录与完整说明见仓库。</div><div class="url">github.com/leviyuan/<br><b>ai-finger-guessing</b></div></footer>
        </section>''')
    target = ROOT / "design"
    target.mkdir(exist_ok=True)
    (target / "series.html").write_text('<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>AI 猜拳 · 对局档案</title><style>' + CSS + '</style><body>' + "".join(pages) + "</body></html>")
    (target / "series.json").write_text(json.dumps(SERIES, ensure_ascii=False, indent=2) + "\n")


def text(x, y, value, size=22, fill="#293039", weight=400, **kwargs):
    extra = " ".join(f'{k.replace("_","-")}="{v}"' for k,v in kwargs.items())
    return f'<text x="{x}" y="{y}" font-size="{size}" fill="{fill}" font-weight="{weight}" {extra}>{html.escape(str(value))}</text>'


def profile(p):
    seq = [d["moves"][p["key"]] for d in ROUNDS]
    scores = [0] + [d["scores_after"][p["key"]] for d in ROUNDS]
    counts = Counter(seq)
    result = []
    for d in ROUNDS:
        m = next(m for m in d["matches"] if p["id"] in [m["a_id"],m["b_id"]])
        a = "a" if p["id"] == m["a_id"] else "b"
        result.append(m[a+"_result"])
    wdl = Counter(result)
    logo = ROOT / "assets/brands" / BRANDS[p["key"]]
    mime = "image/jpeg" if logo.suffix == ".jpg" else "image/svg+xml"
    image = base64.b64encode(logo.read_bytes()).decode()
    parts = ['<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="530" viewBox="0 0 1200 530"><style>text{font-family:"PingFang SC","Noto Sans CJK SC","Microsoft YaHei",sans-serif}</style><rect width="1200" height="530" rx="24" fill="#f8f5ee"/>',
             f'<rect x="40" y="35" width="65" height="65" rx="17" fill="{chr(35)+"222831" if p["key"]=="kimi" else "white"}"/><image x="51" y="46" width="43" height="43" href="data:{mime};base64,{image}"/>',
             text(125,65,p["short_name"],32,weight=750), text(125,95,p["model"],16,fill="#68717b"),
             text(1150,70,f'{scores[-1]:+d}',46,weight=800,text_anchor="end"),
             text(1150,98,f'{wdl["胜"]} 胜 / {wdl["负"]} 负 / {wdl["平"]} 平',18,fill="#68717b",text_anchor="end"),
             text(42,151,"22 轮出拳 · 每格一轮",20,weight=650)]
    for i,m in enumerate(seq):
        x=42+i*50.8
        parts += [f'<rect x="{x:.1f}" y="170" width="42" height="48" rx="8" fill="{COLORS[m]}"/>',
                  text(x+21,202,SYMBOLS[m],25,"white",700,text_anchor="middle"),
                  text(x+21,242,f"{i+1:02d}",12,"#7b838b",text_anchor="middle")]
    parts.append(text(42,291,"累计积分 · 每轮结束后",20,weight=650))
    y0, dy, step = 391, 9, 50.8
    for val in [-6,0,6]:
        y=y0-val*dy
        parts.extend([f'<line x1="57" y1="{y}" x2="1135" y2="{y}" stroke="#d9d9d3" stroke-dasharray="4 5"/>',
                      text(43,y+4,f'{val:+d}',12,"#8d9498",text_anchor="end")])
    points=" ".join(f'{63+i*step:.1f},{y0-v*dy}' for i,v in enumerate(scores[1:]))
    parts.append(f'<polyline points="{points}" fill="none" stroke="#3d555f" stroke-width="3" stroke-linejoin="round"/>')
    for i,v in enumerate(scores[1:]):
        parts.append(f'<circle cx="{63+i*step:.1f}" cy="{y0-v*dy}" r="3.6" fill="#3d555f"/>')
    parts += [text(42,496,f'石头 {counts["石头"]} 次     布 {counts["布"]} 次     剪刀 {counts["剪刀"]} 次',19,fill="#596970"),
              text(1150,496,"来源：正式 22 轮结算记录",17,"#79858a",text_anchor="end"),"</svg>"]
    out=ROOT/"assets/profiles";out.mkdir(parents=True,exist_ok=True)
    (out/f'{p["key"]}.svg').write_text("".join(parts))


if __name__ == "__main__":
    build_cards()
    for player in ROSTER:
        profile(player)
    print("Built 5 editable case posters and 12 data-driven profile charts.")
