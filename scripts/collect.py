#!/usr/bin/env python3
"""
ClawRecord Data Collector

Reads OpenClaw runtime data (session JSONLs, hook output, commands.log)
and produces aggregated metrics in data/raw/metrics.json.

This is the single source of truth for the scoring engine.
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
    tool_xp,
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
        "cost_total": 0.0,
        "skills_used": set(),
        "channels": set(),
        "models": set(),
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


def collect_sessions():
    """Parse all session JSONL files and sessions.json metadata."""
    daily_data = defaultdict(empty_daily)

    sessions_index_path = OPENCLAW_SESSIONS_DIR / "sessions.json"
    if not sessions_index_path.exists():
        print(f"[collect] sessions.json not found at {sessions_index_path}")
        return daily_data

    sessions_index = load_json(sessions_index_path)
    session_skills = {}

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
        elif "webchat" in session_key or session_key.endswith(":main"):
            channel = "webchat"

        session_file = meta.get("sessionFile")
        if not session_file:
            continue

        session_path = OPENCLAW_SESSIONS_DIR / session_file
        if not session_path.exists():
            continue

        turns_in_session = defaultdict(int)

        for record in read_jsonl(session_path):
            if record.get("type") != "message":
                continue

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
            day["sessions"].add(session_key)
            day["channels"].add(channel)
            update_timestamp(day, ts_str)

            hour = hour_from_iso(ts_str)
            if hour is not None:
                day["hours_active"].add(hour)

            for cat in session_skills.get(session_key, set()):
                day["skills_used"].add(cat)

            if role == "user":
                day["messages_user"] += 1
                turns_in_session[date] += 1

            elif role == "assistant":
                day["messages_assistant"] += 1

                usage = msg.get("usage", {})
                day["tokens_input"] += usage.get("input", 0)
                day["tokens_output"] += usage.get("output", 0)
                day["tokens_total"] += usage.get("totalTokens", 0)
                cost = usage.get("cost", {})
                day["cost_total"] += cost.get("total", 0) if isinstance(cost, dict) else 0

                model = msg.get("model", "")
                if model:
                    day["models"].add(model)

                content = msg.get("content", [])
                if isinstance(content, list):
                    for item in content:
                        if isinstance(item, dict) and item.get("type") == "toolCall":
                            tool_name = item.get("name", "unknown")
                            day["tool_calls"][tool_name] += 1
                            tool_skill = classify_tool(tool_name)
                            day["skills_used"].add(tool_skill)

            elif role == "tool":
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
    """Parse clawrecord.jsonl hook output for supplementary data."""
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
    """Parse commands.log for session command data."""
    daily_commands = defaultdict(int)
    cmd_log = OPENCLAW_LOGS_DIR / "commands.log"

    for record in read_jsonl(cmd_log):
        date = iso_date(record.get("timestamp"))
        if date:
            daily_commands[date] += 1

    return daily_commands


def serialize_daily(daily_data, hook_data, cmd_data):
    """Convert collected data to JSON-serializable format."""
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
        "cost_total": 0.0,
        "unique_skills": set(),
        "unique_tools": set(),
        "unique_models": set(),
        "unique_channels": set(),
        "active_days": 0,
        "first_activity": None,
        "last_activity": None,
    }

    for date in all_dates:
        d = daily_data.get(date, empty_daily())
        h = hook_data.get(date, {})

        tool_calls_dict = dict(d["tool_calls"]) if isinstance(d["tool_calls"], defaultdict) else d["tool_calls"]

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
            },
            "cost": round(d["cost_total"], 6),
            "skills_used": sorted(d["skills_used"]),
            "channels": sorted(d["channels"]),
            "models": sorted(d["models"]),
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
        totals["cost_total"] += entry["cost"]
        totals["unique_skills"].update(entry["skills_used"])
        totals["unique_tools"].update(tool_calls_dict.keys())
        totals["unique_models"].update(entry["models"])
        totals["unique_channels"].update(entry["channels"])

    totals_out = {
        **totals,
        "cost_total": round(totals["cost_total"], 6),
        "unique_skills": sorted(totals["unique_skills"]),
        "unique_tools": sorted(totals["unique_tools"]),
        "unique_models": sorted(totals["unique_models"]),
        "unique_channels": sorted(totals["unique_channels"]),
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
    print(
        f"[collect] Summary: {metrics['totals']['active_days']} active days, "
        f"{metrics['totals']['messages_user']} user messages, "
        f"{metrics['totals']['tool_calls_total']} tool calls"
    )


if __name__ == "__main__":
    main()
