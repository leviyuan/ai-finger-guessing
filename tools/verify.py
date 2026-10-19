#!/usr/bin/env python3
"""Offline audit of the public sample. Standard library only; no model calls."""
import argparse
import csv
import hashlib
import json
import re
import struct
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from pathlib import Path
from urllib.parse import unquote

ROOT=Path(__file__).resolve().parents[1]
BEATS={"石头":"剪刀","剪刀":"布","布":"石头"}


def read(p):
    return json.loads(p.read_text())


def lines(p):
    return [json.loads(s) for s in p.read_text().splitlines() if s.strip()]


def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def parse_move(output):
    found=[]
    decoder=json.JSONDecoder()
    for i,c in enumerate(output):
        if c!="{":
            continue
        try:
            d,_=decoder.raw_decode(output[i:])
        except ValueError:
            continue
        if isinstance(d,dict) and set(d)=={"move"} and d["move"] in BEATS:
            found.append(d["move"])
    assert found,"No legal move in raw output"
    return found[-1]


def files():
    return sorted(p for p in ROOT.rglob("*") if p.is_file() and not any(
        x in [".git","node_modules",".local","__pycache__"] for x in p.relative_to(ROOT).parts
    ) and p.name not in [".DS_Store","SHA256SUMS"] and p.suffix not in [".pyc",".zip"])


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--write-manifest",action="store_true")
    args=ap.parse_args()
    roster=read(ROOT/"data/roster.json")["players"]
    assert len(roster)==12
    by_key={p["key"]:p for p in roster}
    by_id={p["id"]:p for p in roster}
    calls=lines(ROOT/"evidence/calls.jsonl")
    by_run={c["run_id"]:c for c in calls}
    assert len(by_run)==len(calls)
    phases=Counter(c["phase"] for c in calls)
    assert phases=={"official":264,"review":4,"probe":12,"not_selected":7}
    for c in calls:
        assert "chatId" not in c and "codexAccountId" not in c
        if not c["text_redacted"]:
            assert hashlib.sha256(c["prompt"].encode()).hexdigest()==c["source_prompt_sha256"]
            assert hashlib.sha256(c["output"].encode()).hexdigest()==c["source_output_sha256"]
    scores={k:0 for k in by_key}
    pair_counts=Counter()
    history=defaultdict(list)
    sequence=defaultdict(list)
    expected_matches=[]
    expected_moves=[]
    accepted_ids=set()
    rounds=[]
    examples=0
    for n in range(1,23):
        d=read(ROOT/f"data/rounds/round-{n:02d}.json")
        rounds.append(d)
        assert d["round"]==n and len(d["matches"])==6 and len(d["responses"])==12
        assert d["scores_before"]==scores and set(d["moves"])==set(by_key)
        assert sorted(sum(d["pairs"],[]))==sorted(by_id)
        responses={r["player_key"]:r for r in d["responses"]}
        assert len(responses)==12
        for k,r in responses.items():
            c=by_run[r["run_id"]]
            assert c["phase"]=="official" and c["round"]==n and c["model_key"]==k
            assert c["status"]=="completed" and c["included_in_official_score"]
            assert c["output"].strip()==r["output"].strip()
            assert parse_move(c["output"])==r["move"]==d["moves"][k]
            assert c["session_id"]==r["session_id"]
            match=re.search(r"当前第\s*(\d+)\s*/\s*(\d+)\s*轮",c["prompt"])
            assert match and int(match[1])==n
            marker="你和所有对手此前的逐局记录（包含当时对手、双方手势和结果）："
            segment=c["prompt"].split(marker,1)[1].splitlines()[0].strip()
            actual=[] if segment=="无" else json.loads(segment)
            assert actual==history[k],f"Prompt history mismatch: {k} R{n}"
            own_score=re.search(r"你当前累计分数是 (-?\d+)",c["prompt"])
            assert own_score and int(own_score[1])==scores[k]
            examples += '{"move":"石头"}' in c["prompt"]
            accepted_ids.add(r["run_id"])
            sequence[k].append(r["move"])
        delta={k:0 for k in by_key}
        for m in d["matches"]:
            a,b=by_id[m["a_id"]],by_id[m["b_id"]]
            ma,mb=d["moves"][a["key"]],d["moves"][b["key"]]
            gain=0 if ma==mb else (1 if BEATS[ma]==mb else -1)
            assert (m["a_move"],m["b_move"],m["a_delta"],m["b_delta"])==(ma,mb,gain,-gain)
            assert m["a_result"]=={1:"胜",0:"平",-1:"负"}[gain]
            assert m["b_result"]=={1:"负",0:"平",-1:"胜"}[gain]
            delta[a["key"]]+=gain
            delta[b["key"]]-=gain
            pair_counts[tuple(sorted((a["id"],b["id"])))]+=1
            expected_matches.append({"round":n,**m})
            for p,o,side,other in [(a,b,"a","b"),(b,a,"b","a")]:
                history[p["key"]].append({
                    "round":n,"opponent":o["short_name"],"self_move":m[side+"_move"],
                    "opponent_move":m[other+"_move"],"result":m[side+"_result"]})
        scores={k:scores[k]+delta[k] for k in scores}
        assert d["scores_after"]==scores and sum(scores.values())==0
        for r in d["responses"]:
            p=by_key[r["player_key"]]
            m=next(m for m in d["matches"] if p["id"] in [m["a_id"],m["b_id"]])
            a,b=("a","b") if p["id"]==m["a_id"] else ("b","a")
            expected_moves.append({
                "round":n,"model_key":p["key"],"model":p["model"],"opponent":m[b+"_name"],
                "move":r["move"],"opponent_move":m[b+"_move"],"result":m[a+"_result"],
                "delta":m[a+"_delta"],"score_after":scores[p["key"]],"run_id":r["run_id"]})
    assert len(accepted_ids)==264 and len(pair_counts)==66 and set(pair_counts.values())=={2}
    assert examples==264
    for name,expected in [("matches",expected_matches),("moves",expected_moves)]:
        with (ROOT/f"data/{name}.csv").open(encoding="utf-8-sig") as f:
            actual=list(csv.DictReader(f))
        assert actual==[{k:str(v) for k,v in row.items()} for row in expected],name+" CSV mismatch"
    summary=read(ROOT/"data/summary.json")
    assert summary["phase_counts"]==phases
    for row in summary["ranking"]:
        own=[x for x in expected_moves if x["model_key"]==row["model_key"]]
        results=Counter(x["result"] for x in own)
        assert row["score"]==scores[row["model_key"]]
        assert (row["wins"],row["losses"],row["draws"])==(results["胜"],results["负"],results["平"])
    native=lines(ROOT/"evidence/participant-turns.jsonl")
    coverage=read(ROOT/"evidence/coverage.json")
    for k in by_key:
        groups=[g for g in native if g["model_key"]==k and g["accepted_run_id"]]
        actual=sorted({g["round"] for g in groups if g["visible_reasoning"]})
        assert actual==coverage[k]["rounds_with_readable_reasoning"]
        for group in groups:
            c=by_run[group["accepted_run_id"]]
            assert c["session_id"]==group["session_id"] and c["round"]==group["round"]
            assert any(s.strip()==c["output"].strip() for s in group["responses"])
    for p in sorted((ROOT/"reviews/original").glob("*.json"))+sorted((ROOT/"probe/original").glob("*.json")):
        d=read(p);c=by_run[d["run_id"]]
        assert c["output"].strip()==d.get("output",d.get("raw_output","")).strip()
        if d.get("prompt_sha256"):
            assert hashlib.sha256(c["prompt"].encode()).hexdigest()==d["prompt_sha256"]
    assert rounds[14]["moves"]["qwen"]=="剪刀" and rounds[14]["moves"]["gpt"]=="石头"
    assert rounds[13]["moves"]["deepseek"]=="石头" and rounds[13]["moves"]["claude"]=="剪刀"
    assert rounds[11]["moves"]["glm"]==rounds[11]["moves"]["kimi"]=="布"
    assert all(sequence["meta"][i]==["剪刀","布","石头"][(i-2)%3] for i in range(2,22))
    scissors=[x for x in expected_moves if x["model_key"]=="meta" and x["move"]=="剪刀"]
    assert len(scissors)==7 and all(x["result"]=="胜" for x in scissors)
    assert sequence["gpt"].count("石头")==16 and sequence["gpt"][11:]==["石头"]*11
    assert sequence["gpt"][10]!="石头"
    for key in ["gpt","claude"]:
        assert read(ROOT/f"probe/original/{key}.json")["move"]=="布"
    originals=read(ROOT/"evidence/source-files.json")
    for f in originals:
        if f["byte_preserved"]:
            assert digest(ROOT/f["public_path"])==f["sha256"],f["public_path"]
    link_count=0
    for f in ROOT.rglob("*.md"):
        parts=f.relative_to(ROOT).parts
        if any(x in [".git","node_modules",".local","historical"] for x in parts):
            continue
        value=re.sub(chr(96)*3+r"[\s\S]*?"+chr(96)*3,"",f.read_text())
        for target in re.findall(r"!?\[[^\]]*\]\(([^)\n]+)\)",value):
            target=target.strip().split(" ",1)[0].split("#",1)[0]
            if not target or re.match(r"^[a-z]+:",target):
                continue
            assert (f.parent/unquote(target)).exists(),f"Broken link in {f}: {target}"
            link_count+=1
    for name in ["01-qwen","02-deepseek","03-glm","04-meta","05-gpt-claude"]:
        data=(ROOT/f"assets/series/{name}.png").read_bytes()
        assert data[:8]==b"\x89PNG\r\n\x1a\n" and struct.unpack(">II",data[16:24])==(1600,2000)
    for p in roster:
        svg=ET.parse(ROOT/f'assets/profiles/{p["key"]}.svg')
        line=svg.find("{http://www.w3.org/2000/svg}polyline")
        coordinates=[tuple(map(float,xy.split(","))) for xy in line.attrib["points"].split()]
        expected=[(round(63+i*50.8,1),391-d["scores_after"][p["key"]]*9) for i,d in enumerate(rounds)]
        assert coordinates==expected,"Score chart geometry mismatch"
        png=(ROOT/f'assets/profiles/{p["key"]}.png').read_bytes()
        assert struct.unpack(">II",png[16:24])==(1600,707)
    for f in files():
        if f.suffix in [".md",".json",".jsonl",".txt",".html",".csv",".py",".cjs"]:
            value=f.read_text()
            assert not re.search(r"/Users/[A-Za-z0-9._-]+/",value),f"Private absolute path: {f}"
            assert not re.search(r"\b(?:sk-proj-|sk-ant-|ghp_|github_pat_)[A-Za-z0-9_-]{20,}",value),f"Secret-shaped value: {f}"
    report={"status":"passed","official_rounds":22,"matches":132,"accepted_moves":264,
            "pairings":66,"meetings_per_pair":2,"related_calls":len(calls),"calls_by_phase":dict(phases),
            "verified_prompt_histories":264,"verified_raw_returns":264,"score_sum":sum(scores.values()),
            "case_claims":5,"poster_pngs_1600x2000":5,"profile_svgs":12,"checked_markdown_links":link_count,
            "source_files_byte_preserved":sum(f["byte_preserved"] for f in originals),
            "private_path_and_secret_pattern_scan":"passed"}
    (ROOT/"checks").mkdir(exist_ok=True)
    (ROOT/"checks/verification.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
    manifest=ROOT/"SHA256SUMS"
    if args.write_manifest:
        manifest.write_text("".join(f"{digest(p)}  {p.relative_to(ROOT)}\n" for p in files()))
    else:
        assert manifest.exists(),"Run with --write-manifest for a new release"
        expected=dict((name,h) for h,name in (line.split("  ",1) for line in manifest.read_text().splitlines()))
        assert expected=={str(p.relative_to(ROOT)):digest(p) for p in files()},"Published file manifest mismatch"
    print(json.dumps(report,ensure_ascii=False))


if __name__=="__main__":
    main()
