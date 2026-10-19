#!/usr/bin/env python3
"""Ask every seat for a concise, auditable rationale before one non-scoring move."""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / "data/formal-run-20260918-12x22"
ANALYSIS = json.loads((RUN / "analysis.json").read_text())
ROSTER = json.loads((ROOT / "data/formal-roster-12.json").read_text())["players"]
STATE = json.loads((RUN / "state.json").read_text())
RAW = ROOT / "raw/formal-run-20260918-12x22/probe-round-23"
OUT = RUN / "model-reviews/probe-round-23"
MOVES = {"石头", "剪刀", "布"}
PAIRINGS = [[1, 12], [2, 11], [3, 10], [4, 9], [5, 8], [6, 7]]
TERMINAL = {"completed", "failed", "cancelled", "canceled", "needs_input"}


def now():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def dump(value):
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def write(path: Path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(dump(value))


def read(path: Path, default=None):
    if not path.exists():
        return default
    return json.loads(path.read_text())


def cli(args, prompt=None, timeout=60):
    p = subprocess.run(
        ["lodestar-agent", *args],
        input=prompt,
        text=True,
        capture_output=True,
        timeout=timeout,
    )
    try:
        value = json.loads(p.stdout) if p.stdout.strip() else {}
    except json.JSONDecodeError:
        value = {"raw_stdout": p.stdout}
    if p.returncode:
        value["cli_exit_code"] = p.returncode
        value["error"] = p.stderr.strip() or p.stdout.strip()
    return value


def worker(value):
    return (value.get("workers") or [value])[0]


def status(value):
    w = worker(value)
    return w.get("status") or value.get("status") or "unknown"


def run_id(value):
    return value.get("run_id") or value.get("id") or value.get("run", {}).get("run_id")


def output(value):
    w = worker(value)
    return w.get("output") or value.get("output") or ""


def resolve(player):
    catalog = cli(["identities", "--json"])
    hits = [
        x for x in catalog.get("identities", [])
        if x.get("model") == player["model"]
        and x.get("token_source_id") == player["token_source_id"]
        and x.get("status") == "ready"
    ]
    if len(hits) != 1:
        raise RuntimeError(f"identity resolution failed for {player['key']}: {len(hits)} hits")
    identity = hits[0]
    if player["effort"] not in identity.get("supported_efforts", []):
        raise RuntimeError(f"effort unavailable for {player['key']}: {player['effort']}")
    return {"checked_at": now(), "catalog_generation": catalog.get("catalog_generation"), "identity": identity}


def prompt_for(player):
    own = ANALYSIS["metrics_by_key"][player["key"]]
    ranking = [
        {
            "rank": row["rank"],
            "name": row["name"],
            "score": row["score"],
            "wins": row["wins"],
            "losses": row["losses"],
            "draws": row["draws"],
        }
        for row in ANALYSIS["ranking"]
    ]
    opponent_map = {a: b for a, b in PAIRINGS}
    opponent_map.update({b: a for a, b in PAIRINGS})
    opponent = opponent_map[player["id"]]
    opponent_player = next(p for p in ROSTER if p["id"] == opponent)
    recent = [
        {
            "round": x["round"],
            "opponent": x["opponent"],
            "self": x["move"],
            "opponent_move": x["opponent_move"],
            "result": x["result"],
        }
        for x in own["records"][-8:]
    ]
    return f"""这是一个不计分的解释性探针，不会改写 22 轮正式赛果，也不会进入视频。
你是 {player['name']}。如果现在继续做一场演示，你的对手是 {opponent_player['name']}。

请先给出一个不超过 80 字的“可审计理由”：只能引用你在这条消息和已有历史会话里看到的统计或逐局记录，不要输出隐藏思维过程。
再给出一句不超过 30 字的“结论”。
最后选择一手。只输出严格 JSON，不要 Markdown、不要额外字段：
{{"reason":"简短理由","conclusion":"一句结论","move":"石头"}}

全场最终排名：
{json.dumps(ranking, ensure_ascii=False)}

你的统计：
{json.dumps({k: own[k] for k in ['name','score','wins','losses','draws','move_counts','move_entropy_normalized','repeat_rate','halves','best_fixed_hand','best_fixed_score','actual_minus_best_fixed']}, ensure_ascii=False)}

你最近 8 轮：
{json.dumps(recent, ensure_ascii=False)}

请把这次选择当作“解释后再行动”的探针，不要声称这是能力评测。"""


def parse_response(raw):
    decoder = json.JSONDecoder()
    candidates = []
    for i, ch in enumerate(raw):
        if ch != "{":
            continue
        try:
            value, end = decoder.raw_decode(raw[i:])
        except json.JSONDecodeError:
            continue
        if (
            isinstance(value, dict)
            and set(value) == {"reason", "conclusion", "move"}
            and isinstance(value["reason"], str)
            and isinstance(value["conclusion"], str)
            and value["move"] in MOVES
        ):
            candidates.append((i + end, value))
    if not candidates:
        raise ValueError("no complete JSON with reason/conclusion/move")
    return candidates[-1][1]


def wait(submission, attempt_path):
    rid = run_id(submission)
    if not rid:
        raise RuntimeError("missing run id")
    status_path = attempt_path / "status.json"
    start = time.monotonic()
    while True:
        value = cli(["status", rid, "--json"])
        write(status_path, value)
        if status(value) in TERMINAL:
            return value
        if time.monotonic() - start > 300:
            cancel = cli(["cancel", rid])
            write(attempt_path / "cancel.json", cancel)
            raise TimeoutError(f"probe timeout: {rid}")
        time.sleep(5)


def main():
    RAW.mkdir(parents=True, exist_ok=True)
    OUT.mkdir(parents=True, exist_ok=True)
    by_key = {p["key"]: p for p in ROSTER}
    for key in [p["key"] for p in ROSTER]:
        player = by_key[key]
        output_path = OUT / f"{key}.json"
        if output_path.exists():
            print(f"{key}: reused", flush=True)
            continue
        call_path = RAW / key / "attempt-01"
        call_path.mkdir(parents=True, exist_ok=True)
        prompt = prompt_for(player)
        identity = resolve(player)
        request = {
            "created_at": now(),
            "kind": "non_scoring_reasoned_probe",
            "round_label": 23,
            "player": player,
            "identity_resolution": identity,
            "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(),
            "prompt": prompt,
            "session_before": STATE["sessions"].get(key),
        }
        write(call_path / "request.json", request)
        args = [
            "run",
            "--session",
            STATE["sessions"][key],
            "--identity",
            identity["identity"]["id"],
            "--description",
            f"{player['short_name']} 解释性探针",
            "--effort",
            player["effort"],
            "--stdin",
            "--json",
            "--no-wait",
        ]
        submission = cli(args, prompt=prompt, timeout=70)
        write(call_path / "submission.json", submission)
        if submission.get("cli_exit_code"):
            raise RuntimeError(f"{key} submission failed: {submission}")
        result = wait(submission, call_path)
        w = worker(result)
        raw = output(result)
        meta = {
            "player_key": key,
            "run_id": run_id(submission),
            "session_id": w.get("session_id"),
            "status": status(result),
            "model": w.get("model"),
            "effort": w.get("effort"),
            "usage": w.get("usage"),
            "cost_usd": w.get("cost_usd"),
            "duration_ms": w.get("duration_ms"),
            "raw_output": raw,
        }
        try:
            parsed = parse_response(raw)
            meta.update(parsed)
        except ValueError as exc:
            meta["parse_error"] = str(exc)
        write(call_path / "response-meta.json", meta)
        write(output_path, meta)
        print(f"{key}: {status(result)} move={meta.get('move', '?')}", flush=True)


if __name__ == "__main__":
    main()
