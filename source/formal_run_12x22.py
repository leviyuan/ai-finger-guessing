#!/usr/bin/env python3
"""Run a resumable ten-round, twelve-seat RPS sample through Lodestar.

The referee owns pairing, parsing and settlement. Models only choose one legal
gesture from the prompt. Every request, response, status, retry and reported
usage is retained under data/formal-run-20260918-12x22 and raw/....
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import datetime as dt
import hashlib
import json
import subprocess
import sys
import time
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ROSTER_PATH = ROOT / "data/formal-roster-12.json"
DATA_ROOT = ROOT / "data/formal-run-20260918-12x22"
RAW_ROOT = ROOT / "raw/formal-run-20260918-12x22"
WORKSPACE_ROOT = RAW_ROOT / "model-workspaces"
ROUNDS = 22
POLL_SECONDS = 4
ACTIVE_LIMIT_SECONDS = 240
NO_PROGRESS_SECONDS = 150
TERMINAL = {"completed", "failed", "cancelled", "canceled", "needs_input"}
MOVES = ("石头", "剪刀", "布")
BEATS = {"石头": "剪刀", "剪刀": "布", "布": "石头"}


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def sha(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def dump(value) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(dump(value))


def read_json(path: Path, default=None):
    if not path.exists():
        return default
    return json.loads(path.read_text())


def cli(args, stdin: str | None = None, timeout: int = 60):
    proc = subprocess.run(
        ["lodestar-agent", *args],
        input=stdin,
        text=True,
        capture_output=True,
        timeout=timeout,
    )
    stdout = proc.stdout.strip()
    try:
        value = json.loads(stdout) if stdout else {}
    except json.JSONDecodeError:
        value = {"raw_stdout": stdout}
    if proc.returncode:
        value.setdefault("error", proc.stderr.strip() or stdout or f"exit {proc.returncode}")
        value["cli_exit_code"] = proc.returncode
    return value


def roster():
    data = read_json(ROSTER_PATH)
    players = data["players"]
    if len(players) != 12 or [p["id"] for p in players] != list(range(1, 13)):
        raise ValueError("formal-roster-12.json must contain exactly twelve ordered seats")
    return players


def catalog():
    value = cli(["identities", "--json"])
    if value.get("cli_exit_code"):
        raise RuntimeError(f"identity catalog failed: {value.get('error')}")
    return value


def resolve(player):
    """Resolve immediately before each new Lodestar task; no substitution."""
    cat = catalog()
    hits = [
        identity
        for identity in cat.get("identities", [])
        if identity.get("model") == player["model"]
        and identity.get("token_source_id") == player["token_source_id"]
    ]
    if len(hits) != 1:
        raise RuntimeError(
            f"expected one live identity for {player['key']}, found {len(hits)}"
        )
    identity = hits[0]
    if identity.get("status") != "ready":
        raise RuntimeError(f"identity is not ready: {player['key']} {identity.get('status')}")
    if player["effort"] not in identity.get("supported_efforts", []):
        raise RuntimeError(f"effort unavailable for {player['key']}: {player['effort']}")
    return {
        "checked_at": now(),
        "catalog_generation": cat.get("catalog_generation"),
        "identity": identity,
    }


def worker(status):
    workers = status.get("workers") or []
    return workers[0] if workers else status


def run_id(value):
    return value.get("run_id") or value.get("id") or value.get("run", {}).get("run_id")


def session_id(value):
    return value.get("session_id") or worker(value).get("session_id")


def worker_output(value):
    item = worker(value)
    return item.get("output") or value.get("output") or ""


def status_name(value):
    item = worker(value)
    return item.get("status") or value.get("status") or "unknown"


def prompt_for(player, opponent, round_number, prior_rounds, scores):
    opponent_player = next(p for p in roster() if p["id"] == opponent)
    seat_records = []
    opponent_records = []
    for previous in prior_rounds:
        for match in previous["matches"]:
            if match["a_id"] != player["id"] and match["b_id"] != player["id"]:
                continue
            if match["a_id"] == player["id"]:
                self_move, other_move = match["a_move"], match["b_move"]
                other_id = match["b_id"]
                result = match["a_result"]
            else:
                self_move, other_move = match["b_move"], match["a_move"]
                other_id = match["a_id"]
                result = match["b_result"]
            row = {
                "round": previous["round"],
                "opponent": next(p["short_name"] for p in roster() if p["id"] == other_id),
                "self_move": self_move,
                "opponent_move": other_move,
                "result": result,
            }
            seat_records.append(row)
            if other_id == opponent:
                opponent_records.append(row)
    history = "无" if not seat_records else json.dumps(
        seat_records, ensure_ascii=False, separators=(",", ":")
    )
    head_to_head = "无" if not opponent_records else json.dumps(
        opponent_records, ensure_ascii=False, separators=(",", ":")
    )
    return f"""你正在参加一组研究用的石头、剪刀、布样本。你是 {player['name']}（座位 {player['id']}），当前第 {round_number}/{ROUNDS} 轮；本轮对手是 {opponent_player['name']}（座位 {opponent}）。

规则：每轮同时选择一手；石头胜剪刀，剪刀胜布，布胜石头，相同为平局。你只能依据已经结束的前 {round_number - 1} 轮，不知道本轮任何其他座位的选择。你当前累计分数是 {scores[player['key']]}，对手累计分数是 {scores[opponent_player['key']]}。

你和所有对手此前的逐局记录（包含当时对手、双方手势和结果）：{history}
你与本轮对手此前的直接交手记录：{head_to_head}

请只输出一个严格 JSON 对象，不能有 Markdown、解释、额外字段或代码块：{{"move":"石头"}}。move 必须恰好是“石头”“剪刀”“布”之一。这个样本用于检查调用消耗，不代表任何模型能力评测。"""


def recovery_prompt(original: str, reason: str) -> str:
    return f"""上一条响应未被裁判接受（原因：{reason}）。不要解释、不要调用工具、不要改文件。请重新选择同一轮并只输出一个严格 JSON 对象：{{\"move\":\"石头\"}}；move 只能是石头、剪刀、布。
原任务如下：
{original}"""


def parse_move(output: str):
    decoder = json.JSONDecoder()
    candidates = []
    for index, char in enumerate(output):
        if char != "{":
            continue
        try:
            value, end = decoder.raw_decode(output[index:])
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict) and set(value) == {"move"} and value["move"] in MOVES:
            candidates.append((index + end, value["move"]))
    if not candidates:
        raise ValueError("no complete legal JSON move")
    return candidates[-1][1], {
        "mode": "last_legal_json_object",
        "candidate_count": len(candidates),
    }


def attempt_dir(call_dir: Path, number: int) -> Path:
    path = call_dir / f"attempt-{number:02d}"
    path.mkdir(parents=True, exist_ok=True)
    return path


def wait_for_submission(submission, attempt_path: Path):
    rid = run_id(submission)
    if not rid:
        raise RuntimeError("Lodestar response did not contain a run id")
    status_path = attempt_path / "status.json"
    previous = read_json(status_path)
    if previous and status_name(previous) in TERMINAL:
        return previous
    started = time.monotonic()
    last_progress = started
    while True:
        value = cli(["status", rid, "--json"])
        write_json(status_path, value)
        state = status_name(value)
        item = worker(value)
        if item.get("steps"):
            last_progress = time.monotonic()
        if state in TERMINAL:
            return value
        elapsed = time.monotonic() - started
        if elapsed >= ACTIVE_LIMIT_SECONDS or time.monotonic() - last_progress >= NO_PROGRESS_SECONDS:
            cancel = cli(["cancel", rid])
            write_json(attempt_path / "cancel.json", cancel)
            value = cli(["status", rid, "--json"])
            value["local_stop_reason"] = (
                "active_limit_seconds"
                if elapsed >= ACTIVE_LIMIT_SECONDS
                else "no_progress_seconds"
            )
            write_json(status_path, value)
            return value
        time.sleep(POLL_SECONDS)


def dispatch_or_resume(player, round_number, prompt, prior_session, call_dir: Path):
    """Return one parsed response, reusing submitted requests on restart."""
    call_dir.mkdir(parents=True, exist_ok=True)
    existing = read_json(call_dir / "response.json")
    if existing and existing.get("move") in MOVES:
        existing["reused"] = True
        return existing

    original_prompt = prompt
    attempt_number = 1
    while attempt_number <= 2:
        attempt_path = attempt_dir(call_dir, attempt_number)
        submission = read_json(attempt_path / "submission.json")
        if submission is None:
            identity_record = resolve(player)
            identity = identity_record["identity"]
            if prior_session and attempt_number == 1:
                args = [
                    "run", "--session", prior_session, "--identity", identity["id"],
                    "--description", f"猜拳第{round_number}轮：{player['short_name']}",
                    "--effort", player["effort"], "--stdin", "--json", "--no-wait",
                ]
                request_kind = "session_follow_up"
            else:
                workspace = WORKSPACE_ROOT / player["key"]
                workspace.mkdir(parents=True, exist_ok=True)
                args = [
                    "run", "--identity", identity["id"],
                    "--description", f"猜拳第{round_number}轮：{player['short_name']}",
                    "--workdir", str(workspace), "--effort", player["effort"],
                    "--stdin", "--json", "--no-wait",
                ]
                request_kind = "new_session_recovery" if attempt_number > 1 else "new_session"
            request = {
                "created_at": now(),
                "round": round_number,
                "player": player,
                "request_kind": request_kind,
                "session_before": prior_session,
                "identity_resolution": identity_record,
                "prompt_sha256": sha(prompt),
                "prompt": prompt,
                "args_without_prompt": args,
                "attempt": attempt_number,
            }
            write_json(attempt_path / "request.json", request)
            submission = cli(args, stdin=prompt, timeout=70)
            write_json(attempt_path / "submission.json", submission)
            if submission.get("cli_exit_code"):
                write_json(attempt_path / "submission-error.json", submission)
                if attempt_number == 1:
                    prompt = recovery_prompt(original_prompt, "首次提交因传输或容量错误失败")
                    attempt_number += 1
                    time.sleep(5)
                    continue
                raise RuntimeError(f"Lodestar submission failed: {submission.get('error')}")
        status = wait_for_submission(submission, attempt_path)
        write_json(attempt_path / "status.json", status)
        state = status_name(status)
        item = worker(status)
        output = worker_output(status)
        response_meta = {
            "round": round_number,
            "player_key": player["key"],
            "run_id": run_id(submission),
            "session_id": session_id(status) or session_id(submission),
            "status": state,
            "reported_effort": item.get("effort", "unknown"),
            "usage": item.get("usage", status.get("usage", "unknown")),
            "cost_usd": item.get("cost_usd"),
            "duration_ms": item.get("duration_ms"),
            "finish_reason": item.get("finish_reason"),
            "output": output,
            "attempt": attempt_number,
            "reused": False,
        }
        write_json(attempt_path / "response-meta.json", response_meta)
        if state == "completed":
            try:
                move, parser = parse_move(output)
            except ValueError as exc:
                response_meta["parse_error"] = str(exc)
                write_json(attempt_path / "response-meta.json", response_meta)
                if attempt_number == 1 and response_meta.get("session_id"):
                    prompt = recovery_prompt(original_prompt, str(exc))
                    prior_session = response_meta["session_id"]
                    attempt_number += 1
                    continue
                raise RuntimeError(f"{player['key']} round {round_number}: invalid response")
            final = {**response_meta, "move": move, "parser": parser}
            write_json(call_dir / "response.json", final)
            return final
        if attempt_number == 1 and state in {"failed", "cancelled", "canceled"}:
            prompt = recovery_prompt(original_prompt, item.get("error", state))
            prior_session = None
            attempt_number += 1
            time.sleep(5)
            continue
        raise RuntimeError(f"{player['key']} round {round_number} ended with {state}")
    raise RuntimeError(f"{player['key']} round {round_number} exhausted recovery")


def make_schedule():
    arrangement = list(range(1, 13))
    schedule = []
    for round_number in range(1, ROUNDS + 1):
        pairs = [[arrangement[index], arrangement[-1 - index]] for index in range(6)]
        schedule.append({"round": round_number, "layout": arrangement[:], "pairs": pairs})
        arrangement = [arrangement[0], arrangement[-1], *arrangement[1:-1]]
    flattened = [tuple(sorted(pair)) for item in schedule for pair in item["pairs"]]
    expected_unique = min(ROUNDS, 11) * 6
    if len(flattened) != ROUNDS * 6 or len(set(flattened)) != expected_unique:
        raise AssertionError("twelve-seat schedule has an invalid pair count")
    return schedule


def result_for(a_move: str, b_move: str):
    if a_move == b_move:
        return "平", 0, 0
    if BEATS[a_move] == b_move:
        return "胜", 1, -1
    return "负", -1, 1


def prior_rounds():
    return [
        read_json(DATA_ROOT / f"round-{number:02d}.json")
        for number in range(1, ROUNDS + 1)
        if (DATA_ROOT / f"round-{number:02d}.json").exists()
    ]


def fresh_state(players):
    return {
        "run_id": "formal-run-20260918-12x22",
        "created_at": now(),
        "status": "running",
        "rounds_requested": ROUNDS,
        "players": players,
        "schedule": make_schedule(),
        "rounds_completed": 0,
        "scores": {p["key"]: 0 for p in players},
        "sessions": {},
        "successful_moves": 0,
        "submitted_attempts": 0,
        "recovery_attempts": 0,
    }


def load_or_create_state(players):
    state_path = DATA_ROOT / "state.json"
    state = read_json(state_path)
    if state is None:
        state = fresh_state(players)
        write_json(state_path, state)
        return state
    if state.get("run_id") != "formal-run-20260918-12x22":
        raise ValueError("existing state belongs to another run")
    if [p["key"] for p in state.get("players", [])] != [p["key"] for p in players]:
        raise ValueError("existing state roster differs; do not mix ten-seat and twelve-seat data")
    return state


def normalize_state_from_rounds(state):
    rounds = prior_rounds()
    if rounds:
        state["rounds_completed"] = max(r["round"] for r in rounds)
        last = rounds[-1]
        state["scores"] = last["scores_after"]
        for response in last["responses"]:
            if response.get("session_id"):
                state["sessions"][response["player_key"]] = response["session_id"]
    return state


def usage_numbers(value):
    aliases = {
        "prompt_tokens": "input_tokens",
        "completion_tokens": "output_tokens",
        "total_tokens": "total_tokens",
        "input_tokens": "input_tokens",
        "output_tokens": "output_tokens",
        "reasoning_tokens": "reasoning_tokens",
        "reasoning_output_tokens": "reasoning_output_tokens",
        "cached_tokens": "cached_tokens",
        "cache_creation_input_tokens": "cache_creation_input_tokens",
        "cache_read_input_tokens": "cache_read_input_tokens",
    }
    result = defaultdict(float)
    if isinstance(value, dict):
        for key, item in value.items():
            if isinstance(item, (int, float)) and key in aliases:
                result[aliases[key]] += item
    return dict(result)


def write_consumption(state, players):
    final_records = []
    attempt_records = []
    for number in range(1, ROUNDS + 1):
        for player in players:
            response = read_json(
                DATA_ROOT / "calls" / f"round-{number:02d}" / player["key"] / "response.json"
            )
            if response:
                final_records.append(response)
            call_dir = RAW_ROOT / "rounds" / f"round-{number:02d}" / player["key"]
            for attempt in sorted(call_dir.glob("attempt-*/response-meta.json")):
                meta = read_json(attempt)
                if meta:
                    meta["call_dir"] = str(attempt.parent.relative_to(RAW_ROOT))
                    attempt_records.append(meta)
    totals = defaultdict(float)
    by_model = {}
    for player in players:
        rows = [r for r in attempt_records if r.get("player_key") == player["key"]]
        final_rows = [r for r in final_records if r.get("player_key") == player["key"]]
        numbers = defaultdict(float)
        for row in rows:
            for key, value in usage_numbers(row.get("usage")).items():
                numbers[key] += value
                totals[key] += value
        costs = [
            r.get("cost_usd")
            for r in rows
            if isinstance(r.get("cost_usd"), (int, float))
        ]
        by_model[player["key"]] = {
            "name": player["name"],
            "model": player["model"],
            "token_source_id": player["token_source_id"],
            "effort": player["effort"],
            "successful_turns": len(final_rows),
            "attempts_including_recovery": len(rows),
            "recovery_attempts": max(0, len(rows) - len(final_rows)),
            "reported_usage_sum": dict(numbers),
            "reported_cost_usd_sum": sum(costs) if costs else "unknown",
            "reported_cost_entries": len(costs),
            "statuses": sorted({str(r.get("status", "unknown")) for r in rows}),
        }
    numeric_costs = [
        r["cost_usd"] for r in attempt_records if isinstance(r.get("cost_usd"), (int, float))
    ]
    report = {
        "run_id": state["run_id"],
        "generated_at": now(),
        "roster": "data/formal-roster-12.json",
        "sample": {
            "rounds": ROUNDS,
            "seats": 12,
            "matches": ROUNDS * 6,
            "model_turns": ROUNDS * 12,
        },
        "successful_model_turns": len(final_records),
        "attempts_including_recovery": len(attempt_records),
        "recovery_attempts": max(0, len(attempt_records) - len(final_records)),
        "completed_attempts": sum(
            row.get("status") == "completed" for row in attempt_records
        ),
        "cancelled_attempts": sum(
            row.get("status") in {"cancelled", "canceled"} for row in attempt_records
        ),
        "reported_usage_total": dict(totals),
        "reported_cost_usd_total": sum(numeric_costs) if numeric_costs else "unknown",
        "by_model": by_model,
        "note": "usage/cost 只采用 Lodestar 返回字段；未返回的费用保持 unknown，不用价格猜算。",
    }
    write_json(DATA_ROOT / "consumption.json", report)
    lines = [
        "# 十二模型十轮猜拳样本消耗",
        "",
        f"- 运行：{state['run_id']}",
        f"- 目标：{ROUNDS} 轮、12 席、{ROUNDS * 6} 场对局、{ROUNDS * 12} 次模型出拳",
        f"- 已成功解析的出拳：{len(final_records)}；含恢复尝试的调用：{len(attempt_records)}",
        f"- 调用状态：completed={report['completed_attempts']}，cancelled={report['cancelled_attempts']}",
        f"- Lodestar 报告总 usage：{json.dumps(dict(totals), ensure_ascii=False, sort_keys=True)}",
        f"- Lodestar 报告总费用：{report['reported_cost_usd_total']}",
        "",
        "| 席位 | 模型 / 来源 | 成功出拳 | 调用尝试 | usage 合计 | 费用 |",
        "|---|---|---:|---:|---|---:|",
    ]
    for player in players:
        row = by_model[player["key"]]
        usage = json.dumps(row["reported_usage_sum"], ensure_ascii=False, sort_keys=True)
        lines.append(
            f"| {player['short_name']} | {player['model']} / {player['token_source_id']} | "
            f"{row['successful_turns']} | {row['attempts_including_recovery']} | {usage} | "
            f"{row['reported_cost_usd_sum']} |"
        )
    lines += [
        "",
        "原始请求、回复、状态和身份快照位于 raw/formal-run-20260918-12x22/；可从 state.json 继续，不重复已有 response.json。",
    ]
    (DATA_ROOT / "consumption.md").write_text("\n".join(lines) + "\n")
    return report


def write_results_summary(state, players):
    rounds = [
        read_json(DATA_ROOT / f"round-{number:02d}.json")
        for number in range(1, ROUNDS + 1)
        if (DATA_ROOT / f"round-{number:02d}.json").exists()
    ]
    if len(rounds) != ROUNDS:
        return None
    scores = rounds[-1]["scores_after"]
    ranking = sorted(
        [
            {
                "rank": 0,
                "player_key": player["key"],
                "name": player["name"],
                "score": scores[player["key"]],
                "wins": sum(
                    match["a_result"] == "胜"
                    for item in rounds
                    for match in item["matches"]
                    if match["a_id"] == player["id"]
                )
                + sum(
                    match["b_result"] == "胜"
                    for item in rounds
                    for match in item["matches"]
                    if match["b_id"] == player["id"]
                ),
                "losses": sum(
                    match["a_result"] == "负"
                    for item in rounds
                    for match in item["matches"]
                    if match["a_id"] == player["id"]
                )
                + sum(
                    match["b_result"] == "负"
                    for item in rounds
                    for match in item["matches"]
                    if match["b_id"] == player["id"]
                ),
                "draws": sum(
                    match["a_result"] == "平"
                    for item in rounds
                    for match in item["matches"]
                    if match["a_id"] == player["id"]
                )
                + sum(
                    match["b_result"] == "平"
                    for item in rounds
                    for match in item["matches"]
                    if match["b_id"] == player["id"]
                ),
            }
            for player in players
        ],
        key=lambda row: (-row["score"], -row["wins"], row["name"]),
    )
    for rank, row in enumerate(ranking, start=1):
        row["rank"] = rank
    summary = {
        "run_id": state["run_id"],
        "generated_at": now(),
        "rounds": ROUNDS,
        "matches": ROUNDS * 6,
        "model_turns": ROUNDS * 12,
        "zero_sum_each_round": all(item["zero_sum"] for item in rounds),
        "final_scores": scores,
        "ranking": ranking,
    }
    write_json(DATA_ROOT / "results-summary.json", summary)
    lines = [
        "# 十二模型十轮猜拳结果",
        "",
        f"- 10 轮、60 场、120 次出拳；每轮结算零和：{summary['zero_sum_each_round']}",
        "",
        "| 名次 | 席位 | 分数 | 胜 | 负 | 平 |",
        "|---:|---|---:|---:|---:|---:|",
    ]
    for row in ranking:
        lines.append(
            f"| {row['rank']} | {row['name']} | {row['score']} | "
            f"{row['wins']} | {row['losses']} | {row['draws']} |"
        )
    (DATA_ROOT / "results-summary.md").write_text("\n".join(lines) + "\n")
    return summary


def run():
    players = roster()
    DATA_ROOT.mkdir(parents=True, exist_ok=True)
    RAW_ROOT.mkdir(parents=True, exist_ok=True)
    WORKSPACE_ROOT.mkdir(parents=True, exist_ok=True)
    state = normalize_state_from_rounds(load_or_create_state(players))
    write_json(DATA_ROOT / "schedule.json", state["schedule"])
    write_json(DATA_ROOT / "roster-snapshot.json", {"captured_at": now(), "players": players})
    by_id = {p["id"]: p for p in players}
    for schedule_item in state["schedule"]:
        number = schedule_item["round"]
        round_path = DATA_ROOT / f"round-{number:02d}.json"
        if round_path.exists():
            continue
        previous = [
            read_json(DATA_ROOT / f"round-{n:02d}.json")
            for n in range(1, number)
            if (DATA_ROOT / f"round-{n:02d}.json").exists()
        ]
        scores_before = dict(state["scores"])
        responses = []
        moves = {}
        for a_id, b_id in schedule_item["pairs"]:
            jobs = []
            for seat_id, opponent_id in ((a_id, b_id), (b_id, a_id)):
                player = by_id[seat_id]
                prompt = prompt_for(player, opponent_id, number, previous, state["scores"])
                call_dir = DATA_ROOT / "calls" / f"round-{number:02d}" / player["key"]
                prior_session = state["sessions"].get(player["key"])
                jobs.append((player, call_dir, prompt, prior_session))
            with ThreadPoolExecutor(max_workers=2) as pool:
                futures = {
                    pool.submit(
                        dispatch_or_resume,
                        player,
                        number,
                        prompt,
                        prior_session,
                        RAW_ROOT / "rounds" / f"round-{number:02d}" / player["key"],
                    ): (player, call_dir)
                    for player, call_dir, prompt, prior_session in jobs
                }
                completed = []
                for future, (player, call_dir) in futures.items():
                    completed.append((player, call_dir, future.result()))
            for player, call_dir, response in sorted(completed, key=lambda item: item[0]["id"]):
                write_json(call_dir / "response.json", response)
                responses.append(response)
                moves[player["key"]] = response["move"]
                if response.get("session_id"):
                    state["sessions"][player["key"]] = response["session_id"]
                state["submitted_attempts"] += response.get("attempt", 1)
                state["recovery_attempts"] += max(0, response.get("attempt", 1) - 1)
                print(
                    f"round {number}/{ROUNDS} {player['short_name']}: "
                    f"{response['move']} ({response.get('status')})",
                    flush=True,
                )
        score_after = dict(scores_before)
        matches = []
        for a_id, b_id in schedule_item["pairs"]:
            a = by_id[a_id]
            b = by_id[b_id]
            result, a_delta, b_delta = result_for(moves[a["key"]], moves[b["key"]])
            score_after[a["key"]] += a_delta
            score_after[b["key"]] += b_delta
            matches.append(
                {
                    "a_id": a_id,
                    "b_id": b_id,
                    "a_name": a["short_name"],
                    "b_name": b["short_name"],
                    "a_move": moves[a["key"]],
                    "b_move": moves[b["key"]],
                    "a_result": result,
                    "b_result": "平" if result == "平" else ("负" if result == "胜" else "胜"),
                    "a_delta": a_delta,
                    "b_delta": b_delta,
                }
            )
        round_record = {
            **schedule_item,
            "completed_at": now(),
            "scores_before": scores_before,
            "scores_after": score_after,
            "moves": moves,
            "matches": matches,
            "responses": responses,
            "zero_sum": sum(score_after.values()) == 0,
        }
        write_json(round_path, round_record)
        state["scores"] = score_after
        state["rounds_completed"] = number
        state["successful_moves"] = number * len(players)
        write_json(DATA_ROOT / "state.json", state)
        print(f"round {number}/{ROUNDS} settled; scores={score_after}", flush=True)
    state["status"] = "completed" if state["rounds_completed"] == ROUNDS else "running"
    state["finished_at"] = now() if state["status"] == "completed" else None
    write_json(DATA_ROOT / "state.json", state)
    report = write_consumption(state, players)
    write_results_summary(state, players)
    print(json.dumps(report, ensure_ascii=False, indent=2), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--reset",
        action="store_true",
        help="refuse reset; prevents accidental duplicate calls",
    )
    args = parser.parse_args()
    if args.reset:
        raise SystemExit(
            "Reset is disabled; move the existing run aside explicitly if a new sample is intended."
        )
    try:
        run()
    except KeyboardInterrupt:
        print("interrupted; state and per-call statuses were retained", file=sys.stderr)
        raise


if __name__ == "__main__":
    main()
