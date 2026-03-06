#!/usr/bin/env python3
"""
ClawRecord Data Collector v2

Reads ALL OpenClaw runtime data — every session JSONL (including .reset files),
sessions.json metadata, hook output, and commands.log — then produces
comprehensive aggregated metrics in data/raw/metrics.json.

Enhanced: provider/model breakdown, cost tracking, cache stats, token splits.
"""

import json
import os
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from utils import (
    OPENCLAW_LOGS_DIR,
    OPENCLAW_SESSIONS_DIR,
    RAW_DIR,
    classify_skill_name,
    classify_tool,
    hour_from_iso,
    iso_date,
    load_json,
    read_jsonl,
    save_json,
)


def empty_daily():
    return {
        "sessions": set(),
        "messages_user": 0,
        "messages_assistant": 0,
        "tool_calls": defaultdict(int),
        "tool_errors": 0,
        "tokens_input": 0,
        "tokens_output": 0,
        "tokens_total": 0,
        "cache_read": 0,
        "cache_write": 0,
        "cost_total": 0.0,
        "cost_input": 0.0,
        "cost_output": 0.0,
        "skills_used": set(),
        "channels": set(),
        "models": set(),
        "providers": set(),
        "model_tokens": defaultdict(int),
        "provider_tokens": defaultdict(int),
        "hours_active": set(),
        "max_turns_in_session": 0,
        "first_message_at": None,
        "last_message_at": None,
    }


def update_timestamp(daily, ts):
    if ts is None:
        return
    if daily["first_message_at"] is None or ts < daily["first_message_at"]:
        daily["first_message_at"] = ts
    if daily["last_message_at"] is None or ts > daily["last_message_at"]:
        daily["last_message_at"] = ts


def find_all_session_files(sessions_dir):
    """Find all JSONL session files including .reset archives."""
    if not sessions_dir.exists():
        return []
    result = []
    for f in sessions_dir.iterdir():
        name = f.name
        if name == "sessions.json" or name.endswith(".lock"):
            continue
        if ".jsonl" in name and f.is_file():
            result.append(f)
    return sorted(result)


def collect_sessions():
    """Parse all session JSONL files and sessions.json metadata."""
    daily_data = defaultdict(empty_daily)

    sessions_index = {}
    sessions_index_path = OPENCLAW_SESSIONS_DIR / "sessions.json"
    if sessions_index_path.exists():
        sessions_index = load_json(sessions_index_path)

    session_skills = {}
    session_channels = {}
    for session_key, meta in sessions_index.items():
        skills_snapshot = meta.get("skillsSnapshot", [])
        for skill in skills_snapshot:
            name = skill.get("name", "") if isinstance(skill, dict) else str(skill)
            if name:
                session_skills.setdefault(session_key, set()).add(
                    classify_skill_name(name)
                )

        channel = "unknown"
        if "telegram" in session_key:
            channel = "telegram"
        elif "whatsapp" in session_key:
            channel = "whatsapp"
        elif "discord" in session_key:
            channel = "discord"
        elif "slack" in session_key:
            channel = "slack"
        elif "webchat" in session_key or session_key.endswith(":main"):
            channel = "webchat"
        origin = meta.get("origin", {})
        if isinstance(origin, dict) and origin.get("surface"):
            channel = origin["surface"]
        session_channels[meta.get("sessionId", "")] = channel
        session_channels[session_key] = channel

    all_files = find_all_session_files(OPENCLAW_SESSIONS_DIR)
    print(f"[collect]   Found {len(all_files)} session files to parse")

    for session_path in all_files:
        session_id = session_path.name.split(".")[0]
        channel = session_channels.get(session_id, "unknown")
        sk_for_session = None
        for sk, meta in sessions_index.items():
            if meta.get("sessionId") == session_id:
                sk_for_session = sk
                break

        turns_in_session = defaultdict(int)

        for record in read_jsonl(session_path):
            rtype = record.get("type", "")

            if rtype == "message":
                msg = record.get("message", {})
                role = msg.get("role", "")
                ts_raw = record.get("timestamp") or msg.get("timestamp")
                if isinstance(ts_raw, (int, float)):
                    ts_str = datetime.utcfromtimestamp(ts_raw / 1000).isoformat() + "Z"
                else:
                    ts_str = str(ts_raw) if ts_raw else None

                date = iso_date(ts_str)
                if not date:
                    continue

                day = daily_data[date]
                if sk_for_session:
                    day["sessions"].add(sk_for_session)
                else:
                    day["sessions"].add(session_id)
                day["channels"].add(channel)
                update_timestamp(day, ts_str)

                hour = hour_from_iso(ts_str)
                if hour is not None:
                    day["hours_active"].add(hour)

                if sk_for_session:
                    for cat in session_skills.get(sk_for_session, set()):
                        day["skills_used"].add(cat)

                if role == "user":
                    day["messages_user"] += 1
                    turns_in_session[date] += 1

                elif role == "assistant":
                    day["messages_assistant"] += 1

                    model = msg.get("model", "")
                    provider = msg.get("provider", "")
                    if model:
                        day["models"].add(model)
                    if provider:
                        day["providers"].add(provider)

                    usage = msg.get("usage", {})
                    tok_in = usage.get("input", 0)
                    tok_out = usage.get("output", 0)
                    tok_total = usage.get("totalTokens", 0)
                    cr = usage.get("cacheRead", 0)
                    cw = usage.get("cacheWrite", 0)

                    day["tokens_input"] += tok_in
                    day["tokens_output"] += tok_out
                    day["tokens_total"] += tok_total
                    day["cache_read"] += cr
                    day["cache_write"] += cw

                    if model:
                        day["model_tokens"][model] += tok_total
                    if provider:
                        day["provider_tokens"][provider] += tok_total

                    cost = usage.get("cost", {})
                    if isinstance(cost, dict):
                        day["cost_total"] += cost.get("total", 0)
                        day["cost_input"] += cost.get("input", 0)
                        day["cost_output"] += cost.get("output", 0)

                    content = msg.get("content", [])
                    if isinstance(content, list):
                        for item in content:
                            if isinstance(item, dict) and item.get("type") == "toolCall":
                                tool_name = item.get("name", "unknown")
                                day["tool_calls"][tool_name] += 1
                                tool_skill = classify_tool(tool_name)
                                day["skills_used"].add(tool_skill)

                elif role in ("tool", "toolResult"):
                    content = msg.get("content", [])
                    if isinstance(content, list):
                        for item in content:
                            if isinstance(item, dict) and item.get("isError"):
                                day["tool_errors"] += 1

        for date, turns in turns_in_session.items():
            daily_data[date]["max_turns_in_session"] = max(
                daily_data[date]["max_turns_in_session"], turns
            )

    return daily_data


def collect_hook_events():
    daily_supplement = defaultdict(lambda: {"commands": 0, "hook_messages": 0})
    hook_log = OPENCLAW_LOGS_DIR / "clawrecord.jsonl"
    for record in read_jsonl(hook_log):
        date = iso_date(record.get("ts"))
        if not date:
            continue
        event = record.get("event", "")
        if event.startswith("command."):
            daily_supplement[date]["commands"] += 1
        elif event.startswith("message."):
            daily_supplement[date]["hook_messages"] += 1
    return daily_supplement


def collect_commands_log():
    daily_commands = defaultdict(int)
    cmd_log = OPENCLAW_LOGS_DIR / "commands.log"
    for record in read_jsonl(cmd_log):
        date = iso_date(record.get("timestamp"))
        if date:
            daily_commands[date] += 1
    return daily_commands


def serialize_daily(daily_data, hook_data, cmd_data):
    all_dates = sorted(
        set(daily_data.keys()) | set(hook_data.keys()) | set(cmd_data.keys())
    )

    daily_out = {}
    totals = {
        "sessions": 0,
        "messages_user": 0,
        "messages_assistant": 0,
        "tool_calls_total": 0,
        "tool_errors_total": 0,
        "tokens_total": 0,
        "tokens_input": 0,
        "tokens_output": 0,
        "cache_read": 0,
        "cache_write": 0,
        "cost_total": 0.0,
        "cost_input": 0.0,
        "cost_output": 0.0,
        "unique_skills": set(),
        "unique_tools": set(),
        "unique_models": set(),
        "unique_providers": set(),
        "unique_channels": set(),
        "model_tokens": defaultdict(int),
        "provider_tokens": defaultdict(int),
        "active_days": 0,
        "first_activity": None,
        "last_activity": None,
    }

    for date in all_dates:
        d = daily_data.get(date, empty_daily())
        h = hook_data.get(date, {})

        tool_calls_dict = dict(d["tool_calls"]) if isinstance(d["tool_calls"], defaultdict) else d["tool_calls"]
        model_tokens_dict = dict(d["model_tokens"]) if isinstance(d["model_tokens"], defaultdict) else d.get("model_tokens", {})
        provider_tokens_dict = dict(d["provider_tokens"]) if isinstance(d["provider_tokens"], defaultdict) else d.get("provider_tokens", {})

        entry = {
            "sessions": len(d["sessions"]),
            "messages": {
                "user": d["messages_user"],
                "assistant": d["messages_assistant"],
            },
            "tool_calls": tool_calls_dict,
            "tool_calls_total": sum(tool_calls_dict.values()),
            "tool_errors": d["tool_errors"],
            "tokens": {
                "input": d["tokens_input"],
                "output": d["tokens_output"],
                "total": d["tokens_total"],
                "cache_read": d.get("cache_read", 0),
                "cache_write": d.get("cache_write", 0),
            },
            "cost": round(d["cost_total"], 6),
            "cost_breakdown": {
                "input": round(d.get("cost_input", 0), 6),
                "output": round(d.get("cost_output", 0), 6),
                "total": round(d["cost_total"], 6),
            },
            "skills_used": sorted(d["skills_used"]),
            "channels": sorted(d["channels"]),
            "models": sorted(d["models"]),
            "providers": sorted(d.get("providers", set())),
            "model_tokens": model_tokens_dict,
            "provider_tokens": provider_tokens_dict,
            "hours_active": sorted(d["hours_active"]),
            "max_turns_in_session": d["max_turns_in_session"],
            "commands": h.get("commands", 0) + cmd_data.get(date, 0),
            "first_message_at": d["first_message_at"],
            "last_message_at": d["last_message_at"],
        }
        daily_out[date] = entry

        has_activity = (
            entry["messages"]["user"] > 0
            or entry["messages"]["assistant"] > 0
            or entry["commands"] > 0
        )
        if has_activity:
            totals["active_days"] += 1
            if totals["first_activity"] is None:
                totals["first_activity"] = date
            totals["last_activity"] = date

        totals["sessions"] += entry["sessions"]
        totals["messages_user"] += entry["messages"]["user"]
        totals["messages_assistant"] += entry["messages"]["assistant"]
        totals["tool_calls_total"] += entry["tool_calls_total"]
        totals["tool_errors_total"] += entry["tool_errors"]
        totals["tokens_total"] += entry["tokens"]["total"]
        totals["tokens_input"] += entry["tokens"]["input"]
        totals["tokens_output"] += entry["tokens"]["output"]
        totals["cache_read"] += entry["tokens"]["cache_read"]
        totals["cache_write"] += entry["tokens"]["cache_write"]
        totals["cost_total"] += entry["cost"]
        totals["cost_input"] += entry["cost_breakdown"]["input"]
        totals["cost_output"] += entry["cost_breakdown"]["output"]
        totals["unique_skills"].update(entry["skills_used"])
        totals["unique_tools"].update(tool_calls_dict.keys())
        totals["unique_models"].update(entry["models"])
        totals["unique_providers"].update(entry["providers"])
        totals["unique_channels"].update(entry["channels"])
        for m, t in model_tokens_dict.items():
            totals["model_tokens"][m] += t
        for p, t in provider_tokens_dict.items():
            totals["provider_tokens"][p] += t

    totals_out = {
        "sessions": totals["sessions"],
        "messages_user": totals["messages_user"],
        "messages_assistant": totals["messages_assistant"],
        "tool_calls_total": totals["tool_calls_total"],
        "tool_errors_total": totals["tool_errors_total"],
        "tokens_total": totals["tokens_total"],
        "tokens_input": totals["tokens_input"],
        "tokens_output": totals["tokens_output"],
        "cache_read": totals["cache_read"],
        "cache_write": totals["cache_write"],
        "cost_total": round(totals["cost_total"], 6),
        "cost_input": round(totals["cost_input"], 6),
        "cost_output": round(totals["cost_output"], 6),
        "unique_skills": sorted(totals["unique_skills"]),
        "unique_tools": sorted(totals["unique_tools"]),
        "unique_models": sorted(totals["unique_models"]),
        "unique_providers": sorted(totals["unique_providers"]),
        "unique_channels": sorted(totals["unique_channels"]),
        "model_tokens": dict(totals["model_tokens"]),
        "provider_tokens": dict(totals["provider_tokens"]),
        "active_days": totals["active_days"],
        "first_activity": totals["first_activity"],
        "last_activity": totals["last_activity"],
    }

    return {
        "collection_timestamp": datetime.utcnow().isoformat() + "Z",
        "daily": daily_out,
        "totals": totals_out,
    }


def main():
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    print("[collect] Reading OpenClaw session data...")
    daily_data = collect_sessions()
    print(f"[collect]   Found data for {len(daily_data)} days from sessions")

    print("[collect] Reading hook events...")
    hook_data = collect_hook_events()
    print(f"[collect]   Found hook data for {len(hook_data)} days")

    print("[collect] Reading commands.log...")
    cmd_data = collect_commands_log()
    print(f"[collect]   Found command data for {len(cmd_data)} days")

    metrics = serialize_daily(daily_data, hook_data, cmd_data)

    output_path = RAW_DIR / "metrics.json"
    save_json(output_path, metrics)
    print(f"[collect] Metrics written to {output_path}")

    t = metrics["totals"]
    print(f"[collect] Summary: {t['active_days']} active days, "
          f"{t['messages_user']} user msgs, "
          f"{t['tool_calls_total']} tool calls, "
          f"{t['tokens_total']:,} tokens, "
          f"${t['cost_total']:.4f} cost")
    print(f"[collect] Models: {t['unique_models']}")
    print(f"[collect] Providers: {t['unique_providers']}")
    print(f"[collect] Channels: {t['unique_channels']}")


if __name__ == "__main__":
    main()
