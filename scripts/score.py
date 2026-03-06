#!/usr/bin/env python3
"""
ClawRecord Scoring Engine v2 — Hamster-style

Core loop: use OpenClaw -> earn XP -> auto-upgrade skill cards -> grow Claw Power.
Daily quests, multi-tier badges, personal records, streak XP multiplier.
"""

import hashlib
import json
import sys
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from utils import DATA_DIR, RAW_DIR, get_text, load_json, save_json, tool_xp, classify_tool


def load_metrics():
    path = RAW_DIR / "metrics.json"
    if not path.exists():
        print("[score] No metrics.json found — run collect.py first")
        sys.exit(1)
    return load_json(path)


def load_config():
    return load_json(DATA_DIR / "config.json")


def load_existing_stats():
    path = DATA_DIR / "user_stats.json"
    if path.exists():
        return load_json(path)
    return None


# ── XP ─────────────────────────────────────────────────────────────

def calc_daily_xp(day_data, config):
    w = config["xp_weights"]
    xp = 0
    xp += day_data["messages"]["user"] * w["message_user"]
    xp += day_data["messages"]["assistant"] * w["message_assistant"]
    for tool_name, count in day_data.get("tool_calls", {}).items():
        xp += tool_xp(tool_name) * count
    turns = day_data.get("max_turns_in_session", 0)
    if turns > w["multi_turn_threshold"]:
        xp += (turns - w["multi_turn_threshold"]) * w["multi_turn_bonus"]
    skills_count = len(day_data.get("skills_used", []))
    xp += skills_count * w["skill_diversity_bonus"]
    return xp


def get_streak_multiplier(streak, config):
    mult = 1.0
    for entry in config.get("streak_multiplier", []):
        if streak >= entry["min_streak"]:
            mult = entry["multiplier"]
    return mult


# ── Streak + HP ────────────────────────────────────────────────────

def calc_streak(daily, hp_config):
    if not daily:
        return 0, hp_config["max"], 0
    dates = sorted(daily.keys())
    today = datetime.utcnow().strftime("%Y-%m-%d")
    active_dates = set()
    for d in dates:
        day = daily[d]
        if day["messages"]["user"] > 0 or day.get("commands", 0) > 0:
            active_dates.add(d)

    hp = hp_config["max"]
    streak_freezes = 0
    check_date = datetime.strptime(dates[0], "%Y-%m-%d")
    end_date = datetime.strptime(max(today, dates[-1]), "%Y-%m-%d")
    consecutive = 0
    last_active = None

    date_cursor = check_date
    while date_cursor <= end_date:
        ds = date_cursor.strftime("%Y-%m-%d")
        if ds in active_dates:
            consecutive += 1
            last_active = date_cursor
            hp = min(hp_config["max"], hp + hp_config["recovery_per_active_day"])
        else:
            if last_active is not None:
                gap = (date_cursor - last_active).days
                if gap > hp_config["decay_after_days"]:
                    hp = max(0, hp - hp_config["decay_amount"])
                if gap > 1 and streak_freezes > 0:
                    streak_freezes -= 1
                elif gap > 1:
                    consecutive = 0
        date_cursor += timedelta(days=1)
        if consecutive >= hp_config["streak_freeze_earn_days"] and consecutive % hp_config["streak_freeze_earn_days"] == 0:
            streak_freezes = min(streak_freezes + 1, hp_config["streak_freeze_max"])

    streak = consecutive
    if hp <= 0:
        streak = 0
    return streak, hp, streak_freezes


# ── Level ──────────────────────────────────────────────────────────

def calc_level(total_xp, levels):
    current_level = levels[0]
    for lv in levels:
        if total_xp >= lv["xp_required"]:
            current_level = lv
        else:
            break
    next_level = None
    for lv in levels:
        if lv["xp_required"] > total_xp:
            next_level = lv
            break
    return current_level, next_level


# ── Skills (Card system) ──────────────────────────────────────────

def calc_skills(daily, config):
    skill_xp = defaultdict(int)
    for date, day in daily.items():
        day_skills = set(day.get("skills_used", []))
        for tool_name, count in day.get("tool_calls", {}).items():
            cat = classify_tool(tool_name)
            skill_xp[cat] += tool_xp(tool_name) * count
        msgs = day["messages"]["user"] + day["messages"]["assistant"]
        if day_skills:
            per = msgs // len(day_skills)
            for s in day_skills:
                skill_xp[s] += per

    skills = {}
    for skill_conf in config["skills"]:
        sid = skill_conf["id"]
        xp = skill_xp.get(sid, 0)
        xp_per_level = skill_conf.get("xp_per_level", 200)
        level = min(xp // xp_per_level, skill_conf["max_level"])
        power = level * skill_conf.get("power_per_level", 20)
        next_xp = (level + 1) * xp_per_level if level < skill_conf["max_level"] else xp
        skills[sid] = {
            "level": level,
            "xp": xp,
            "power": power,
            "next_level_xp": next_xp,
            "max_level": skill_conf["max_level"],
            "group": skill_conf.get("group", "core"),
        }
    return skills


# ── League ─────────────────────────────────────────────────────────

def calc_league(daily, config):
    today = datetime.utcnow().date()
    week_start = today - timedelta(days=today.weekday())
    weekly_xp = 0
    for date_str, day in daily.items():
        try:
            dt = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            continue
        if dt >= week_start:
            weekly_xp += calc_daily_xp(day, config)
    league = config["leagues"][0]
    for lg in config["leagues"]:
        if weekly_xp >= lg["min_weekly_xp"]:
            league = lg
    return league, weekly_xp


# ── Claw Power ─────────────────────────────────────────────────────

def calc_claw_power(total_xp, streak, badge_count, skills, config):
    pw = config.get("claw_power", {})
    avg_skill = 0
    if skills:
        avg_skill = sum(s["level"] for s in skills.values()) / len(skills)
    power = (
        total_xp * pw.get("xp_weight", 1)
        + streak * pw.get("streak_weight", 50)
        + badge_count * pw.get("badge_weight", 100)
        + int(avg_skill * pw.get("avg_skill_weight", 200))
    )
    return power


# ── Personal Records ───────────────────────────────────────────────

def calc_personal_records(daily, config):
    best_daily_xp = 0
    best_daily_messages = 0
    best_daily_tools = 0
    best_session_turns = 0
    best_daily_tokens = 0

    for date, day in daily.items():
        xp = calc_daily_xp(day, config)
        best_daily_xp = max(best_daily_xp, xp)
        msgs = day["messages"]["user"] + day["messages"]["assistant"]
        best_daily_messages = max(best_daily_messages, msgs)
        tools = sum(day.get("tool_calls", {}).values())
        best_daily_tools = max(best_daily_tools, tools)
        turns = day.get("max_turns_in_session", 0)
        best_session_turns = max(best_session_turns, turns)
        tokens = day.get("tokens", {}).get("total", 0)
        best_daily_tokens = max(best_daily_tokens, tokens)

    return {
        "best_daily_xp": best_daily_xp,
        "best_daily_messages": best_daily_messages,
        "best_daily_tools": best_daily_tools,
        "best_session_turns": best_session_turns,
        "best_daily_tokens": best_daily_tokens,
    }


# ── Usage Analytics ────────────────────────────────────────────────

def calc_usage_analytics(metrics):
    """Compute rich usage analytics from collected metrics for UI display."""
    daily = metrics["daily"]
    totals = metrics["totals"]

    model_tokens = totals.get("model_tokens", {})
    provider_tokens = totals.get("provider_tokens", {})
    tokens_total = totals.get("tokens_total", 0)

    model_share = {}
    for m, t in model_tokens.items():
        model_share[m] = round(t / max(tokens_total, 1) * 100, 1)

    provider_share = {}
    for p, t in provider_tokens.items():
        provider_share[p] = round(t / max(tokens_total, 1) * 100, 1)

    daily_trend = []
    for date in sorted(daily.keys()):
        day = daily[date]
        tok = day.get("tokens", {})
        daily_trend.append({
            "date": date,
            "tokens": tok.get("total", 0),
            "tokens_input": tok.get("input", 0),
            "tokens_output": tok.get("output", 0),
            "cache_read": tok.get("cache_read", 0),
            "cost": day.get("cost", 0),
            "messages": day["messages"]["user"] + day["messages"]["assistant"],
            "tool_calls": sum(day.get("tool_calls", {}).values()),
            "models_count": len(day.get("models", [])),
        })

    cache_read_total = totals.get("cache_read", 0)
    cache_hit_rate = round(cache_read_total / max(tokens_total, 1) * 100, 1)

    cost_total = totals.get("cost_total", 0)
    active_days = totals.get("active_days", 1)
    avg_cost_per_day = round(cost_total / max(active_days, 1), 4)
    avg_tokens_per_msg = round(tokens_total / max(totals.get("messages_user", 1) + totals.get("messages_assistant", 1), 1))
    cost_per_1k_tokens = round(cost_total / max(tokens_total / 1000, 0.001), 6)

    tool_usage = defaultdict(int)
    for date, day in daily.items():
        for tool_name, count in day.get("tool_calls", {}).items():
            tool_usage[tool_name] += count
    top_tools = sorted(tool_usage.items(), key=lambda x: x[1], reverse=True)[:10]

    channel_messages = defaultdict(int)
    for date, day in daily.items():
        day_msgs = day["messages"]["user"]
        channels = day.get("channels", [])
        if channels and day_msgs > 0:
            per_ch = day_msgs / len(channels)
            for ch in channels:
                channel_messages[ch] += int(per_ch)

    return {
        "model_tokens": model_tokens,
        "model_share": model_share,
        "provider_tokens": provider_tokens,
        "provider_share": provider_share,
        "daily_trend": daily_trend,
        "cache_hit_rate": cache_hit_rate,
        "cache_read_total": cache_read_total,
        "tokens_total": tokens_total,
        "tokens_input": totals.get("tokens_input", 0),
        "tokens_output": totals.get("tokens_output", 0),
        "cost_total": round(cost_total, 4),
        "cost_input": round(totals.get("cost_input", 0), 4),
        "cost_output": round(totals.get("cost_output", 0), 4),
        "avg_cost_per_day": avg_cost_per_day,
        "avg_tokens_per_msg": avg_tokens_per_msg,
        "cost_per_1k_tokens": cost_per_1k_tokens,
        "unique_models": totals.get("unique_models", []),
        "unique_providers": totals.get("unique_providers", []),
        "unique_channels": totals.get("unique_channels", []),
        "top_tools": [{"name": n, "count": c} for n, c in top_tools],
        "channel_messages": dict(channel_messages),
        "active_days": active_days,
        "total_sessions": totals.get("sessions", 0),
    }


# ── Multi-tier Achievements ───────────────────────────────────────

def check_achievements(metrics, config, total_xp, streak, skills, level_info):
    daily = metrics["daily"]
    totals = metrics["totals"]
    unlocked = []

    total_sessions = totals.get("sessions", 0)
    total_messages = totals.get("messages_user", 0)
    total_tokens = totals.get("tokens_total", 0)
    total_tool_calls = totals.get("tool_calls_total", 0)
    unique_tools = totals.get("unique_tools", [])
    unique_channels = totals.get("unique_channels", [])
    unique_models = totals.get("unique_models", [])

    tool_totals = defaultdict(int)
    max_daily_messages = 0
    max_turns = 0
    hour_message_counts = defaultdict(int)
    comeback_detected = False
    prev_active_date = None

    for date_str in sorted(daily.keys()):
        day = daily[date_str]
        for tool_name, count in day.get("tool_calls", {}).items():
            tool_totals[tool_name.lower()] += count
        msgs = day["messages"]["user"] + day["messages"]["assistant"]
        max_daily_messages = max(max_daily_messages, msgs)
        max_turns = max(max_turns, day.get("max_turns_in_session", 0))
        for h in day.get("hours_active", []):
            hour_message_counts[h] += day["messages"]["user"]
        try:
            dt = datetime.strptime(date_str, "%Y-%m-%d")
            if prev_active_date and msgs > 0:
                if (dt - prev_active_date).days >= 7:
                    comeback_detected = True
            if msgs > 0:
                prev_active_date = dt
        except ValueError:
            pass

    current_level = level_info["level"]

    def get_metric(cond):
        ctype = cond["type"]
        if ctype == "total_sessions":
            return total_sessions
        elif ctype == "total_messages":
            return total_messages
        elif ctype == "total_tokens":
            return total_tokens
        elif ctype == "streak":
            return streak
        elif ctype == "total_tool_calls":
            return total_tool_calls
        elif ctype == "unique_tools":
            return len(unique_tools)
        elif ctype == "unique_channels":
            return len(unique_channels)
        elif ctype == "unique_models":
            return len(unique_models)
        elif ctype == "specific_skill":
            s = skills.get(cond.get("skill", ""), {})
            return s.get("level", 0) if isinstance(s, dict) else s
        elif ctype == "all_skills_level":
            if not skills:
                return 0
            return min(
                (s["level"] if isinstance(s, dict) else s) for s in skills.values()
            )
        elif ctype == "specific_tool":
            tool_key = cond.get("tool", "")
            return sum(v for k, v in tool_totals.items() if tool_key in k)
        elif ctype == "daily_messages":
            return max_daily_messages
        elif ctype == "max_turns":
            return max_turns
        elif ctype == "hour_messages":
            hours = cond.get("hours", [])
            return sum(hour_message_counts.get(h, 0) for h in hours)
        elif ctype == "level":
            return current_level
        elif ctype == "channel_used":
            return 1 if cond.get("channel", "") in unique_channels else 0
        elif ctype == "comeback":
            return 1 if comeback_detected else 0
        return 0

    for badge in config["badges"]:
        cond = badge["condition"]
        tiers = badge.get("tiers", [])
        metric_val = get_metric(cond)

        highest_tier = 0
        for t in tiers:
            if metric_val >= t["value"]:
                highest_tier = t["tier"]

        if highest_tier > 0:
            unlocked.append({
                "id": badge["id"],
                "tier": highest_tier,
                "max_tier": len(tiers),
                "metric": metric_val,
            })

    return unlocked


# ── Daily Quests ───────────────────────────────────────────────────

def generate_daily_quests(daily, config, today_str=None):
    if today_str is None:
        today_str = datetime.utcnow().strftime("%Y-%m-%d")

    dq = config.get("daily_quests", {})
    pool = dq.get("challenge_pool", [])

    seed = int(hashlib.md5(today_str.encode()).hexdigest()[:8], 16)
    import random
    rng = random.Random(seed)

    challenge = rng.choice(pool) if pool else None

    combo_cfg = dq.get("combo", {})
    skill_ids = [s["id"] for s in config["skills"]]
    combo_skills = rng.sample(skill_ids, min(combo_cfg.get("skills_to_activate", 3), len(skill_ids)))

    today_data = daily.get(today_str, {})
    today_msgs = today_data.get("messages", {}).get("user", 0) + today_data.get("messages", {}).get("assistant", 0)
    today_tools = sum(today_data.get("tool_calls", {}).values()) if today_data.get("tool_calls") else 0
    today_turns = today_data.get("max_turns_in_session", 0)
    today_skills_used = set(today_data.get("skills_used", []))
    today_writes = sum(v for k, v in today_data.get("tool_calls", {}).items() if "write" in k.lower() or "edit" in k.lower())
    today_execs = sum(v for k, v in today_data.get("tool_calls", {}).items() if "exec" in k.lower() or "shell" in k.lower() or "bash" in k.lower())
    today_browses = sum(v for k, v in today_data.get("tool_calls", {}).items() if "browse" in k.lower() or "fetch" in k.lower() or "web" in k.lower())

    for tool_name, count in today_data.get("tool_calls", {}).items():
        cat = classify_tool(tool_name)
        today_skills_used.add(cat)

    activated_list = [s for s in combo_skills if s in today_skills_used]
    combo_activated = len(activated_list)
    combo_complete = combo_activated >= len(combo_skills)

    challenge_progress = 0
    challenge_complete = False
    if challenge:
        ct = challenge["type"]
        target = challenge["target"]
        if ct == "messages_today":
            challenge_progress = today_msgs
        elif ct == "tools_today":
            challenge_progress = today_tools
        elif ct == "max_turns":
            challenge_progress = today_turns
        elif ct == "skill_diversity":
            challenge_progress = len(today_skills_used)
        elif ct == "writes_today":
            challenge_progress = today_writes
        elif ct == "exec_today":
            challenge_progress = today_execs
        elif ct == "browse_today":
            challenge_progress = today_browses
        challenge_complete = challenge_progress >= target

    streak_active = today_msgs > 0

    return {
        "date": today_str,
        "combo": {
            "skills": combo_skills,
            "activated": combo_activated,
            "activated_skills": activated_list,
            "total": len(combo_skills),
            "complete": combo_complete,
            "xp_reward": combo_cfg.get("xp_reward", 100),
        },
        "challenge": {
            "id": challenge["id"] if challenge else "none",
            "name": challenge.get("name", {}) if challenge else {},
            "desc": challenge.get("desc", {}) if challenge else {},
            "target": challenge["target"] if challenge else 0,
            "progress": challenge_progress,
            "complete": challenge_complete,
            "xp_reward": challenge.get("xp_reward", 0) if challenge else 0,
        },
        "streak": {
            "active": streak_active,
            "complete": streak_active,
        },
    }


# ── Tasks / Check-ins ─────────────────────────────────────────────

def build_tasks(daily, config):
    tasks = []
    task_id = 1
    for date in sorted(daily.keys()):
        day = daily[date]
        msgs = day["messages"]["user"]
        if msgs == 0:
            continue
        xp = calc_daily_xp(day, config)
        skills_used = day.get("skills_used", [])
        task_type = skills_used[0] if skills_used else "general"
        if xp > 200:
            complexity = "high"
        elif xp > 80:
            complexity = "medium"
        else:
            complexity = "low"
        desc_parts = []
        if msgs > 0:
            desc_parts.append(f"{msgs} messages")
        tc = day.get("tool_calls_total", 0)
        if tc > 0:
            desc_parts.append(f"{tc} tool calls")
        if skills_used:
            desc_parts.append(f"skills: {', '.join(skills_used)}")
        tasks.append({
            "id": task_id, "date": date, "type": task_type,
            "description": " | ".join(desc_parts),
            "xp_gained": xp, "complexity": complexity,
        })
        task_id += 1
    return tasks


def build_check_ins(daily, config):
    check_ins = {}
    for date in sorted(daily.keys()):
        day = daily[date]
        has_activity = day["messages"]["user"] > 0 or day.get("commands", 0) > 0
        xp = calc_daily_xp(day, config) if has_activity else 0
        check_ins[date] = {"checked": has_activity, "tasks_count": day.get("sessions", 0), "xp_gained": xp}
    return check_ins


# ── Public Profile ─────────────────────────────────────────────────

def build_public_profile(user_stats, metrics):
    profile_data = {
        "username": user_stats["username"],
        "level": user_stats["level"],
        "xp": user_stats["xp"],
        "claw_power": user_stats.get("claw_power", 0),
        "weekly_xp": user_stats.get("weekly_xp", 0),
        "streak": user_stats["streak"],
        "badge_count": len(user_stats.get("badges", [])),
        "top_skills": sorted(
            user_stats.get("skills", {}).items(),
            key=lambda x: x[1]["level"] if isinstance(x[1], dict) else x[1],
            reverse=True,
        )[:3],
        "league": user_stats.get("league", {}).get("id", "bronze"),
        "avatar": user_stats.get("avatar", "🥚"),
        "last_updated": datetime.utcnow().isoformat() + "Z",
    }
    raw = json.dumps(profile_data, sort_keys=True, ensure_ascii=False)
    profile_data["signature"] = "sha256:" + hashlib.sha256(raw.encode()).hexdigest()
    profile_data["top_skills"] = [
        {"id": s[0], "level": s[1]["level"] if isinstance(s[1], dict) else s[1]}
        for s in profile_data["top_skills"]
    ]
    return profile_data


# ── Main ───────────────────────────────────────────────────────────

def main():
    config = load_config()
    metrics = load_metrics()
    existing = load_existing_stats()
    daily = metrics["daily"]
    username = existing["username"] if existing else "openclaw-user"
    today = datetime.utcnow().strftime("%Y-%m-%d")

    # Streak + HP
    streak, hp, streak_freezes = calc_streak(daily, config["hp"])
    multiplier = get_streak_multiplier(streak, config)
    print(f"[score] Streak: {streak} days (x{multiplier}), HP: {hp}")

    # XP with streak multiplier
    total_xp = 0
    today_xp = 0
    for date_str, day_data in daily.items():
        day_xp = calc_daily_xp(day_data, config)
        day_streak = streak if date_str == today else 1
        day_mult = get_streak_multiplier(day_streak, config)
        total_xp += int(day_xp * day_mult)
        if date_str == today:
            today_xp = int(day_xp * day_mult)
    print(f"[score] Total XP: {total_xp} (today: +{today_xp})")

    # Level
    level_info, next_level = calc_level(total_xp, config["levels"])
    level_num = level_info["level"]
    print(f"[score] Level: {level_num} — {get_text(level_info['rank'], 'en')}")

    # Skills (card system)
    skills = calc_skills(daily, config)
    sk_str = ", ".join(f"{k}={v['level']}" for k, v in skills.items())
    print(f"[score] Skills: {sk_str}")

    # League (10 tiers)
    league, weekly_xp = calc_league(daily, config)
    print(f"[score] League: {get_text(league['name'], 'en')} (weekly: {weekly_xp})")

    # Multi-tier Achievements
    unlocked = check_achievements(metrics, config, total_xp, streak, skills, level_info)
    print(f"[score] Badges: {len(unlocked)}/{len(config['badges'])} types unlocked")

    badge_count = sum(u["tier"] for u in unlocked)

    # Claw Power
    claw_power = calc_claw_power(total_xp, streak, badge_count, skills, config)
    yesterday_str = (datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%d")
    yesterday_xp = calc_daily_xp(daily.get(yesterday_str, {"messages": {"user": 0, "assistant": 0}}), config)
    print(f"[score] Claw Power: {claw_power}")

    # Personal Records
    records = calc_personal_records(daily, config)
    old_records = (existing or {}).get("personal_records", {})
    records["longest_streak"] = max(streak, old_records.get("longest_streak", 0))
    for k in records:
        records[k] = max(records[k], old_records.get(k, 0))
    print(f"[score] Records: {records}")

    # Daily Quests
    quests = generate_daily_quests(daily, config, today)

    # Usage Analytics
    usage_analytics = calc_usage_analytics(metrics)
    print(f"[score] Usage: {usage_analytics['tokens_total']:,} tokens, "
          f"${usage_analytics['cost_total']:.4f}, "
          f"{len(usage_analytics['unique_models'])} models, "
          f"cache hit {usage_analytics['cache_hit_rate']}%")

    # Build badge list with tier info
    old_badges = {b["id"]: b for b in (existing or {}).get("badges", [])}
    badges = []
    for u in unlocked:
        bid = u["id"]
        badge_conf = next((b for b in config["badges"] if b["id"] == bid), None)
        if not badge_conf:
            continue
        date = old_badges[bid]["date"] if bid in old_badges else today
        current_tier = u["tier"]
        max_tier = u["max_tier"]
        tier_label = ""
        for t in badge_conf.get("tiers", []):
            if t["tier"] == current_tier:
                tier_label = get_text(t["label"], "en")
                break
        next_tier_value = None
        for t in badge_conf.get("tiers", []):
            if t["tier"] == current_tier + 1:
                next_tier_value = t["value"]
                break
        badges.append({
            "id": bid,
            "name": get_text(badge_conf["name"], "en"),
            "icon": badge_conf["icon"],
            "tier": current_tier,
            "max_tier": max_tier,
            "tier_label": tier_label,
            "metric": u["metric"],
            "next_tier_value": next_tier_value,
            "date": date,
        })

    # Tasks + Check-ins
    tasks = build_tasks(daily, config)
    check_ins = build_check_ins(daily, config)

    # Assemble user_stats
    skills_display = {k: v for k, v in skills.items()}
    user_stats = {
        "username": username,
        "level": level_num,
        "xp": total_xp,
        "today_xp": today_xp,
        "xp_to_next_level": next_level["xp_required"] if next_level else total_xp,
        "weekly_xp": weekly_xp,
        "streak": streak,
        "streak_freezes": streak_freezes,
        "streak_multiplier": multiplier,
        "hp": hp,
        "max_hp": config["hp"]["max"],
        "claw_power": claw_power,
        "rank": get_text(level_info["rank"], "en"),
        "avatar": level_info["icon"],
        "league": {"id": league["id"], "icon": league["icon"]},
        "badges": badges,
        "skills": skills_display,
        "personal_records": records,
        "last_check_in": max(daily.keys()) if daily else today,
    }

    save_json(DATA_DIR / "user_stats.json", user_stats)
    save_json(DATA_DIR / "tasks.json", tasks)
    save_json(DATA_DIR / "check_ins.json", check_ins)
    save_json(DATA_DIR / "daily_quests.json", quests)
    save_json(DATA_DIR / "usage_analytics.json", usage_analytics)
    print("[score] Saved user_stats, tasks, check_ins, daily_quests, usage_analytics")

    profile = build_public_profile(user_stats, metrics)
    save_json(DATA_DIR / "public_profile.json", profile)
    print("[score] Generated public_profile.json")


if __name__ == "__main__":
    main()
