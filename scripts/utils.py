#!/usr/bin/env python3
"""Shared utilities for ClawRecord scripts."""

import json
import os
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
OUTPUT_DIR = PROJECT_ROOT / "docs"

OPENCLAW_STATE_DIR = Path(
    os.environ.get("OPENCLAW_STATE_DIR", Path.home() / ".openclaw")
)
OPENCLAW_SESSIONS_DIR = OPENCLAW_STATE_DIR / "agents" / "main" / "sessions"
OPENCLAW_LOGS_DIR = OPENCLAW_STATE_DIR / "logs"

TOOL_XP_WEIGHTS = {
    "read": 2, "search": 2, "grep": 2, "glob": 2, "list": 2,
    "write": 5, "edit": 5, "patch": 5, "str_replace": 5,
    "exec": 8, "shell": 8, "bash": 8, "run": 8,
    "browser": 10, "browse": 10, "fetch": 10, "web_search": 10,
}
DEFAULT_TOOL_XP = 3

SKILL_TOOL_MAP = {
    "coding": ["read", "write", "edit", "exec", "shell", "bash", "grep",
               "glob", "lint", "patch", "str_replace", "run"],
    "content": ["text", "generate", "translate", "summarize", "write"],
    "research": ["search", "browse", "fetch", "web_search", "browser"],
    "communication": ["telegram", "email", "message", "notify", "send"],
    "automation": ["cron", "schedule", "workflow", "deploy", "exec", "shell"],
    "data": ["analyze", "chart", "query", "database", "csv", "json"],
}

SKILL_NAME_MAP = {
    "coding": ["cursor-coding", "coding", "code", "cursor"],
    "content": ["content", "writing", "blog", "report"],
    "research": ["research", "search", "browse", "web"],
    "communication": ["telegram", "email", "slack", "whatsapp"],
    "automation": ["cron", "automation", "deploy", "ci", "github"],
    "data": ["data", "analytics", "visualization", "analysis"],
}


def load_json(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(filepath, data, indent=2):
    Path(filepath).parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=indent)


def read_jsonl(filepath):
    """Read a JSONL file, yielding parsed objects. Skips malformed lines."""
    if not Path(filepath).exists():
        return
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                continue


def get_text(obj, lang, default="en"):
    if isinstance(obj, dict):
        return obj.get(lang, obj.get(default, ""))
    return obj


def classify_tool(tool_name):
    """Map a tool name to a skill category."""
    tool_lower = tool_name.lower()
    for skill, tools in SKILL_TOOL_MAP.items():
        if any(t in tool_lower for t in tools):
            return skill
    return "coding"  # default


def classify_skill_name(skill_name):
    """Map an OpenClaw skill name to a category."""
    name_lower = skill_name.lower().replace("-", " ").replace("_", " ")
    for category, keywords in SKILL_NAME_MAP.items():
        if any(kw in name_lower for kw in keywords):
            return category
    return "coding"


def tool_xp(tool_name):
    """Get XP value for a tool call."""
    name_lower = tool_name.lower()
    for key, xp in TOOL_XP_WEIGHTS.items():
        if key in name_lower:
            return xp
    return DEFAULT_TOOL_XP


def iso_date(ts_str):
    """Extract YYYY-MM-DD from an ISO timestamp string."""
    if not ts_str:
        return None
    try:
        return ts_str[:10]
    except Exception:
        return None


def hour_from_iso(ts_str):
    """Extract hour (0-23) from an ISO timestamp string."""
    if not ts_str:
        return None
    try:
        dt = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
        return dt.hour
    except Exception:
        return None
