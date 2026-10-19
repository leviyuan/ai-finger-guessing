#!/usr/bin/env python3
"""Export this experiment from the author's local records. No model calls."""
import argparse
import csv
import hashlib
import json
import re
import shutil
import sqlite3
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path


def sha(data):
    return hashlib.sha256(data).hexdigest()


def load(path):
    return json.loads(path.read_text())


def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def jsonl(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(x, ensure_ascii=False) + "\n" for x in rows))


def scrub(text):
    if not isinstance(text, str):
        return text
    return re.sub(r"/Users/[^/\s]+/[^\s\"'<>，。；]*", "<LOCAL_PATH>", text)


def normalize(text):
    return text.replace("\\n", "\n").strip()


def iso(value):
    if isinstance(value, (float, int)):
        return datetime.fromtimestamp(value / 1000, timezone.utc).isoformat()
    return value


def write_csv(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(rows)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--destination", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--lodestar", type=Path, default=Path.home() / ".local/share/lodestar")
    parser.add_argument("--claude-projects", type=Path, default=Path.home() / ".claude/projects")
    parser.add_argument("--thread-db", type=Path, default=Path.home() / ".codex/thread_history_1.sqlite")
    args = parser.parse_args()
    src, dst = args.source.resolve(), args.destination.resolve()
    run = src / "data/formal-run-20260918-12x22"
    store = args.lodestar / "agent-runs"
    source_files = []

    def copy(source, target):
        target = dst / target
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        source_files.append({
            "public_path": str(target.relative_to(dst)),
            "source_basename": source.name,
            "sha256": sha(source.read_bytes()),
            "bytes": source.stat().st_size,
            "byte_preserved": True,
        })

    roster_doc = load(run / "roster-snapshot.json")
    roster = roster_doc["players"]
    by_key = {p["key"]: p for p in roster}
    by_id = {p["id"]: p for p in roster}
    model_keys = {p["model"]: p["key"] for p in roster}
    rounds = [load(run / f"round-{n:02d}.json") for n in range(1, 23)]
    accepted = {}
    reference = {}
    for d in rounds:
        copy(run / f"round-{d['round']:02d}.json", f"data/rounds/round-{d['round']:02d}.json")
        for r in d["responses"]:
            accepted[(r["player_key"], d["round"])] = r
            reference[r["run_id"]] = ("official", r["player_key"], d["round"])
    copy(run / "roster-snapshot.json", "data/roster.json")
    copy(run / "schedule.json", "data/schedule.json")
    for f in sorted((run / "model-reviews/responses").glob("*.json")):
        d = load(f)
        reference[d["run_id"]] = ("review", d["model_key"], None)
        copy(f, "reviews/original/" + f.name)
    for f in sorted((run / "model-reviews/prompts").glob("*.txt")):
        copy(f, "reviews/prompts/" + f.name)
    for f in sorted((run / "model-reviews/probe-round-23").glob("*.json")):
        d = load(f)
        reference[d["run_id"]] = ("probe", d["player_key"], 23)
        copy(f, "probe/original/" + f.name)
    for name in ["analysis.md", "analysis.json", "behavior-analysis.md", "behavior-analysis.json",
                 "consumption.md", "consumption.json", "results-summary.md", "results-summary.json", "state.json"]:
        copy(run / name, "historical/" + name)
    for name in ["formal_run_12x10.py", "formal_run_12x22.py", "probe_reasoned_round.py",
                 "build_formal_v4_video.py", "formal_v4_animation_12.js"]:
        source = src / "src" / name
        text = source.read_text()
        safe = scrub(text)
        target = dst / "source" / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(safe)
        source_files.append({"public_path": str(target.relative_to(dst)),
                             "source_basename": name, "sha256": sha(source.read_bytes()),
                             "bytes": source.stat().st_size, "byte_preserved": text == safe})
    for name in ["formal-v8-video-check.json", "formal-v8-browser-check.json", "formal-v8-video-plan.json"]:
        copy(src / "data" / name, "video/" + name)
    copy(src / "output/rps-carousel-v8-varied-danmaku.html", "video/rps-carousel-v8.html")

    # Whitelist public run metadata. Never export account IDs, chat IDs, credentials,
    # command steps, local workspaces or unrelated agent sessions.
    calls = []
    for f in sorted(store.glob("*.json")):
        m = load(f)
        rid = m.get("runId", f.stem)
        workers = m.get("workers") or []
        if not workers:
            continue
        w = workers[0]
        if w.get("model") not in model_keys and rid not in reference:
            continue
        in_project = any("douyin-html-video" in str(m.get(k, "")) for k in ["sessionWorkDir", "workDir"])
        if not in_project and rid not in reference:
            continue
        pf = store / m.get("promptArtifact", rid + ".prompt.txt")
        prompt = pf.read_text() if pf.is_file() else m.get("prompt", "")
        if rid not in reference and "你正在参加一组研究用的石头、剪刀、布样本" not in prompt:
            continue
        key = model_keys.get(w.get("model"))
        match = re.search(r"当前第\s*(\d+)\s*/\s*(\d+)\s*轮", prompt)
        stage, key, number = reference.get(rid, ("not_selected", key, int(match[1]) if match else None))
        of = store / w.get("outputArtifact", "_missing_")
        output = of.read_text() if of.is_file() else w.get("output", "")
        item = {
            "run_id": rid, "phase": stage, "model_key": key, "round": number,
            "included_in_official_score": stage == "official",
            "requested_model": by_key[key]["model"], "reported_model": w.get("model"),
            "requested_effort": by_key[key]["effort"], "reported_effort": w.get("effort"),
            "token_source_id": w.get("tokenSourceId"), "provider": w.get("provider"),
            "session_id": w.get("sessionId"), "status": w.get("status", m.get("status")),
            "created_at": iso(m.get("createdAt")), "started_at": iso(w.get("startedAt")),
            "finished_at": iso(w.get("finishedAt", m.get("finishedAt"))),
            "duration_ms": w.get("durationMs"), "usage": w.get("usage"),
            "cost_usd": w.get("costUsd"), "error": scrub(w.get("error", m.get("error"))),
            "prompt": scrub(prompt), "output": scrub(output),
            "source_prompt_sha256": sha(prompt.encode()),
            "source_output_sha256": sha(output.encode()),
            "source_metadata_sha256": sha(f.read_bytes()),
            "text_redacted": scrub(prompt) != prompt or scrub(output) != output,
        }
        calls.append(item)
    calls.sort(key=lambda x: (x["created_at"] or "", x["run_id"]))
    ids = {x["run_id"] for x in calls}
    assert set(reference) <= ids, "A referenced request is missing"
    for c in calls:
        if c["phase"] == "official":
            r = accepted[(c["model_key"], c["round"])]
            assert c["output"].strip() == r["output"].strip()
    jsonl(dst / "evidence/calls.jsonl", calls)

    # Recover only participant conversation turns. Export readable fields actually
    # returned by the channel; do not decode opaque or encrypted thinking.
    call_by_prompt = defaultdict(list)
    session_to_key = {}
    for c in calls:
        call_by_prompt[normalize(c["prompt"])].append(c)
        if c["session_id"]:
            session_to_key[c["session_id"]] = c["model_key"]
    for r in accepted.values():
        session_to_key[r["session_id"]] = r["player_key"]
    native = []

    def begin(text, key, sid, origin, locator):
        candidates = call_by_prompt.get(normalize(text), [])
        match = re.search(r"当前第\s*(\d+)\s*/\s*(\d+)\s*轮", text)
        if candidates:
            preferred = [x for x in candidates if x["session_id"] == sid] or candidates
            c = preferred[-1]
            phase, number = ("official" if match else c["phase"]), int(match[1]) if match else c["round"]
        elif match:
            phase, number = "official", int(match[1])
        elif "解释性探针" in text:
            phase, number = "probe", 23
        else:
            return None
        return {
            "model_key": key, "session_id": sid, "phase": phase, "round": number,
            "source": origin, "source_locator": locator, "prompt": scrub(text),
            "responses": [], "visible_reasoning": [], "opaque_reasoning_blocks": 0,
            "timestamps": [], "accepted_run_id": None,
        }

    def finish(group):
        if not group:
            return
        if group["phase"] == "official":
            r = accepted.get((group["model_key"], group["round"]))
            if r and r["session_id"] == group["session_id"] and any(
                t.strip() == r["output"].strip() for t in group["responses"]
            ):
                group["accepted_run_id"] = r["run_id"]
        native.append(group)

    for directory in sorted(args.claude_projects.glob("*020-rps-carousel*")):
        key = directory.name.split("model-workspaces-")[-1]
        if key not in by_key:
            continue
        for f in sorted(directory.glob("*.jsonl")):
            sid = f.stem
            if sid not in session_to_key:
                continue
            digest = sha(f.read_bytes())
            group = None
            for line_no, line in enumerate(f.open(), 1):
                d = json.loads(line)
                if d.get("type") == "user":
                    content = d.get("message", {}).get("content", "")
                    text = content if isinstance(content, str) else "\n".join(
                        x.get("text", "") for x in content if isinstance(x, dict)
                    )
                    if text:
                        finish(group)
                        group = begin(text, key, sid, "native_jsonl", {
                            "basename": f.name, "file_sha256": digest, "user_line": line_no,
                        })
                elif d.get("type") == "assistant" and group:
                    if d.get("timestamp"):
                        group["timestamps"].append(d["timestamp"])
                    for block in d.get("message", {}).get("content", []):
                        if not isinstance(block, dict):
                            continue
                        if block.get("type") == "text":
                            group["responses"].append(scrub(block.get("text", "")))
                        elif block.get("type") == "thinking" and block.get("thinking", "").strip():
                            group["visible_reasoning"].append({
                                "kind": "channel_returned_thinking",
                                "text": scrub(block["thinking"].strip()), "source_line": line_no,
                                "timestamp": d.get("timestamp"),
                            })
                        elif block.get("type") == "redacted_thinking":
                            group["opaque_reasoning_blocks"] += 1
            finish(group)

    db = sqlite3.connect(args.thread_db.as_uri() + "?mode=ro", uri=True)
    for sid, key in sorted(session_to_key.items()):
        if key not in ["gpt", "kimi", "grok"]:
            continue
        group = None
        for kind, raw, ordinal, ts in db.execute(
            "SELECT item_type,item_json,rollout_ordinal,created_at_ms FROM thread_items "
            "WHERE thread_id=? AND item_type IN ('userMessage','agentMessage','reasoning') ORDER BY rollout_ordinal",
            (sid,),
        ):
            d = json.loads(raw)
            if kind == "userMessage":
                text = "\n".join(x.get("text", "") for x in d.get("content", []) if isinstance(x, dict))
                finish(group)
                group = begin(text, key, sid, "conversation_database", {
                    "thread_id": sid, "item_id": d.get("id"), "ordinal": ordinal,
                    "item_sha256": sha(raw.encode()),
                })
            elif group and kind == "agentMessage":
                group["responses"].append(scrub(d.get("text", "")))
                group["timestamps"].append(iso(ts))
            elif group and kind == "reasoning":
                summary = d.get("summary") or []
                text = "\n".join(x if isinstance(x, str) else x.get("text", "") for x in summary)
                if text.strip():
                    group["visible_reasoning"].append({
                        "kind": "channel_returned_summary", "text": scrub(text.strip()),
                        "item_id": d.get("id"), "timestamp": iso(ts),
                    })
                # Hidden reasoning content is intentionally not exported.
        finish(group)
    db.close()
    native.sort(key=lambda x: (x["model_key"], x["round"] or 999, x["timestamps"][:1]))
    for n, g in enumerate(native, 1):
        g["evidence_id"] = f"native-{n:04d}"
    jsonl(dst / "evidence/participant-turns.jsonl", native)
    coverage = {}
    for p in roster:
        official = [g for g in native if g["model_key"] == p["key"] and g["accepted_run_id"]]
        reasoned = sorted({g["round"] for g in official if g["visible_reasoning"]})
        coverage[p["key"]] = {
            "official_moves": 22,
            "matched_native_rounds": sorted({g["round"] for g in official}),
            "rounds_with_readable_reasoning": reasoned,
            "readable_reasoning_count": len(reasoned),
            "interpretation": "Readable channel-returned text only; absence does not establish absence of reasoning.",
        }
    dump(dst / "evidence/coverage.json", coverage)

    matches, moves, ranking = [], [], []
    for d in rounds:
        for m in d["matches"]:
            matches.append({"round": d["round"], **m})
        for r in d["responses"]:
            p = by_key[r["player_key"]]
            m = next(m for m in d["matches"] if p["id"] in [m["a_id"], m["b_id"]])
            a, b = ("a", "b") if p["id"] == m["a_id"] else ("b", "a")
            moves.append({
                "round": d["round"], "model_key": p["key"], "model": p["model"],
                "opponent": m[b + "_name"], "move": r["move"],
                "opponent_move": m[b + "_move"], "result": m[a + "_result"],
                "delta": m[a + "_delta"], "score_after": d["scores_after"][p["key"]],
                "run_id": r["run_id"],
            })
    for p in roster:
        own = [m for m in moves if m["model_key"] == p["key"]]
        seq = [m["move"] for m in own]
        results = Counter(m["result"] for m in own)
        distribution = Counter(seq)
        ranking.append({
            "model_key": p["key"], "name": p["short_name"], "model": p["model"],
            "score": sum(m["delta"] for m in own), "wins": results["胜"],
            "losses": results["负"], "draws": results["平"],
            "rock": distribution["石头"], "paper": distribution["布"],
            "scissors": distribution["剪刀"],
            "consecutive_repeats": sum(a == b for a, b in zip(seq, seq[1:])),
        })
    ranking.sort(key=lambda x: (-x["score"], -x["wins"], x["model_key"]))
    write_csv(dst / "data/matches.csv", matches)
    write_csv(dst / "data/moves.csv", moves)
    write_csv(dst / "data/leaderboard.csv", ranking)
    dump(dst / "data/summary.json", {
        "rounds": 22, "matches": 132, "accepted_moves": 264, "ranking": ranking,
        "phase_counts": dict(Counter(c["phase"] for c in calls)),
        "exported_at": datetime.now(timezone.utc).isoformat(),
    })
    dump(dst / "evidence/source-files.json", source_files)
    print(json.dumps({
        "calls": len(calls), "phases": dict(Counter(c["phase"] for c in calls)),
        "participant_turns": len(native),
        "reasoning_rounds": {k: v["readable_reasoning_count"] for k, v in coverage.items()},
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
