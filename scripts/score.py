#!/usr/bin/env python3
"""
ClawRecord Scoring Engine

Reads raw metrics from data/raw/metrics.json, applies XP formulas,
checks achievements, calculates levels/streaks/skills/leagues, and
outputs user_stats.json, tasks.json, check_ins.json, public_profile.json.
"""

import hashlib
import json
import sys
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from utils import DATA_DIR, RAW_DIR, get_text, load_json, save_json, tool_xp


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


# ── XP Calculation ──────────────────────────────────────────────────

def calc_daily_xp(day_data, config):
    w = config["xp_weights"]
    xp = 0

    xp += day_data["messages"]["user"] * w["message_user"]
    xp += day_data["messages"]["assistant"] * w["message_assistant"]

    for tool_name, count in day_data.get("tool_calls", {}).items():
        xp += tool_xp(tool_name) * count

    turns = day_data.get("max_turns_in_session", 0)
    threshold = w["multi_turn_threshold"]
    if turns > threshold:
        xp += (turns - threshold) * w["multi_turn_bonus"]

    skills_count = len(day_data.get("skills_used", []))
    xp += skills_count * w["skill_diversity_bonus"]

    return xp


# ── Streak ──────────────────────────────────────────────────────────

def calc_streak(daily, hp_config):
    """Calculate current streak and HP from daily activity data."""
    if not daily:
        return 0, hp_config["max"], 0

    dates = sorted(daily.keys())
    today = datetime.utcnow().strftime("%Y-%m-%d")
    active_dates = set()
    for d in dates:
        day = daily[d]
        if day["messages"]["user"] > 0 or day.get("commands", 0) > 0:
            active_dates.add(d)

    streak = 0
    hp = hp_config["max"]
    streak_freezes = 0

    check_date = datetime.strptime(dates[0], "%Y-%m-%d")
    end_date = datetime.strptime(max(today, dates[-1]), "%Y-%m-%d")
    consecutive = 0
    last_active = None
    longest_gap = 0

    date_cursor = check_date
    while date_cursor <= end_date:
        ds = date_cursor.strftime("%Y-%m-%d")
        if ds in active_dates:
            if last_active is not None:
                gap = (date_cursor - last_active).days - 1
                longest_gap = max(longest_gap, gap)
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


# ── Level ───────────────────────────────────────────────────────────

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


# ── Skills ──────────────────────────────────────────────────────────

def calc_skills(daily, config):
    skill_xp = defaultdict(int)
    for date, day in daily.items():
        day_skills = set(day.get("skills_used", []))

        for tool_name, count in day.get("tool_calls", {}).items():
            from utils import classify_tool
            cat = classify_tool(tool_name)
            skill_xp[cat] += tool_xp(tool_name) * count

        msgs_per_skill = (day["messages"]["user"] + day["messages"]["assistant"])
        if day_skills:
            per = msgs_per_skill // len(day_skills)
            for s in day_skills:
                skill_xp[s] += per

    skills = {}
    for skill_conf in config["skills"]:
        sid = skill_conf["id"]
        xp = skill_xp.get(sid, 0)
        xp_per_level = skill_conf.get("xp_per_level", 200)
        level = min(xp // xp_per_level, skill_conf["max_level"])
        skills[sid] = {"level": level, "xp": xp}

    return skills


# ── League ──────────────────────────────────────────────────────────

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


# ── Achievements ────────────────────────────────────────────────────

def check_achievements(metrics, config, total_xp, streak, skills, level_info):
    daily = metrics["daily"]
    totals = metrics["totals"]
    unlocked = []

    # Pre-compute aggregates needed by various conditions
    total_sessions = totals.get("sessions", 0)
    total_messages = totals.get("messages_user", 0)
    total_tokens = totals.get("tokens_total", 0)
    total_tool_calls = totals.get("tool_calls_total", 0)
    unique_tools = totals.get("unique_tools", [])
    unique_channels = totals.get("unique_channels", [])
    unique_models = totals.get("unique_models", [])

    # Per-tool totals
    tool_totals = defaultdict(int)
    for date, day in daily.items():
        for tool_name, count in day.get("tool_calls", {}).items():
            tool_totals[tool_name.lower()] += count

    # Per-day max messages
    max_daily_messages = 0
    max_daily_skills = 0
    max_turns = 0
    error_free_streak = 0
    current_error_free = 0
    hour_message_counts = defaultdict(int)
    weekend_dates = set()
    comeback_detected = False

    sorted_dates = sorted(daily.keys())
    prev_active_date = None
    for date_str in sorted_dates:
        day = daily[date_str]
        msgs = day["messages"]["user"] + day["messages"]["assistant"]
        max_daily_messages = max(max_daily_messages, msgs)
        max_daily_skills = max(max_daily_skills, len(day.get("skills_used", [])))
        max_turns = max(max_turns, day.get("max_turns_in_session", 0))

        if day.get("tool_errors", 0) == 0 and msgs > 0:
            current_error_free += 1
            error_free_streak = max(error_free_streak, current_error_free)
        elif day.get("tool_errors", 0) > 0:
            current_error_free = 0

        for h in day.get("hours_active", []):
            hour_message_counts[h] += day["messages"]["user"]

        try:
            dt = datetime.strptime(date_str, "%Y-%m-%d")
            if dt.weekday() >= 5 and msgs > 0:
                weekend_dates.add(dt.isocalendar()[1])

            if prev_active_date and msgs > 0:
                gap = (dt - prev_active_date).days
                if gap >= 7:
                    comeback_detected = True
            if msgs > 0:
                prev_active_date = dt
        except ValueError:
            pass

    # Cost tracking for budget_hero
    week_costs = []
    for date_str in sorted_dates:
        day = daily[date_str]
        total_msgs = day["messages"]["user"] + day["messages"]["assistant"]
        if total_msgs > 0:
            week_costs.append(day.get("cost", 0) / total_msgs)
    avg_cost_ok = False
    if len(week_costs) >= 7:
        for i in range(len(week_costs) - 6):
            window = week_costs[i:i + 7]
            if all(c < 0.01 for c in window):
                avg_cost_ok = True
                break

    weekend_weeks = sorted(weekend_dates)
    consecutive_weekends = 0
    max_consecutive_weekends = 0
    for i, w in enumerate(weekend_weeks):
        if i == 0 or w == weekend_weeks[i - 1] + 1:
            consecutive_weekends += 1
        else:
            consecutive_weekends = 1
        max_consecutive_weekends = max(max_consecutive_weekends, consecutive_weekends)

    current_level = level_info["level"]

    for badge in config["badges"]:
        cond = badge["condition"]
        ctype = cond["type"]
        met = False

        if ctype == "total_sessions":
            met = total_sessions >= cond["value"]
        elif ctype == "total_messages":
            met = total_messages >= cond["value"]
        elif ctype == "total_tokens":
            met = total_tokens >= cond["value"]
        elif ctype == "streak":
            met = streak >= cond["value"]
        elif ctype == "any_skill_level":
            met = any(s["level"] >= cond["value"] for s in skills.values())
        elif ctype == "all_skills_level":
            met = all(s["level"] >= cond["value"] for s in skills.values()) and len(skills) > 0
        elif ctype == "daily_skills":
            met = max_daily_skills >= cond["value"]
        elif ctype == "specific_skill":
            skill_data = skills.get(cond["skill"], {})
            met = skill_data.get("level", 0) >= cond["value"]
        elif ctype == "total_tool_calls":
            met = total_tool_calls >= cond["value"]
        elif ctype == "unique_tools":
            met = len(unique_tools) >= cond["value"]
        elif ctype == "specific_tool":
            tool_count = sum(v for k, v in tool_totals.items() if cond["tool"] in k)
            met = tool_count >= cond["value"]
        elif ctype == "avg_cost_week":
            met = avg_cost_ok
        elif ctype == "max_turns":
            met = max_turns >= cond["value"]
        elif ctype == "daily_messages":
            met = max_daily_messages >= cond["value"]
        elif ctype == "error_free_days":
            met = error_free_streak >= cond["value"]
        elif ctype == "hour_messages":
            hours = cond.get("hours", [])
            total_in_hours = sum(hour_message_counts.get(h, 0) for h in hours)
            met = total_in_hours >= cond["value"]
        elif ctype == "weekend_streak":
            met = max_consecutive_weekends >= cond["value"]
        elif ctype == "channel_used":
            met = cond["channel"] in unique_channels
        elif ctype == "unique_channels":
            met = len(unique_channels) >= cond["value"]
        elif ctype == "unique_models":
            met = len(unique_models) >= cond["value"]
        elif ctype == "comeback_days":
            met = comeback_detected
        elif ctype == "level":
            met = current_level >= cond["value"]

        if met:
            unlocked.append(badge["id"])

    return unlocked


# ── Tasks / Check-ins ───────────────────────────────────────────────

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
            "id": task_id,
            "date": date,
            "type": task_type,
            "description": " | ".join(desc_parts),
            "xp_gained": xp,
            "complexity": complexity,
        })
        task_id += 1
    return tasks


def build_check_ins(daily, config):
    check_ins = {}
    for date in sorted(daily.keys()):
        day = daily[date]
        has_activity = day["messages"]["user"] > 0 or day.get("commands", 0) > 0
        xp = calc_daily_xp(day, config) if has_activity else 0
        check_ins[date] = {
            "checked": has_activity,
            "tasks_count": day.get("sessions", 0),
            "xp_gained": xp,
        }
    return check_ins


# ── Public Profile ──────────────────────────────────────────────────

def build_public_profile(user_stats, metrics):
    """Generate a public_profile.json with a data integrity signature."""
    profile_data = {
        "username": user_stats["username"],
        "level": user_stats["level"],
        "xp": user_stats["xp"],
        "weekly_xp": user_stats.get("weekly_xp", 0),
        "streak": user_stats["streak"],
        "badge_count": len(user_stats.get("badges", [])),
        "top_skills": sorted(
            user_stats.get("skills", {}).items(),
            key=lambda x: x[1] if isinstance(x[1], int) else x[1].get("level", 0),
            reverse=True,
        )[:3],
        "league": user_stats.get("league", {}).get("id", "bronze"),
        "avatar": user_stats.get("avatar", "🥚"),
        "last_updated": datetime.utcnow().isoformat() + "Z",
    }

    raw = json.dumps(profile_data, sort_keys=True, ensure_ascii=False)
    profile_data["signature"] = "sha256:" + hashlib.sha256(raw.encode()).hexdigest()
    profile_data["top_skills"] = [
        {"id": s[0], "level": s[1] if isinstance(s[1], int) else s[1].get("level", 0)}
        for s in profile_data["top_skills"]
    ]

    return profile_data


# ── Main ────────────────────────────────────────────────────────────

def main():
    config = load_config()
    metrics = load_metrics()
    existing = load_existing_stats()
    daily = metrics["daily"]

    username = existing["username"] if existing else "openclaw-user"

    # XP
    total_xp = sum(calc_daily_xp(d, config) for d in daily.values())
    print(f"[score] Total XP: {total_xp}")

    # Streak + HP
    streak, hp, streak_freezes = calc_streak(daily, config["hp"])
    print(f"[score] Streak: {streak} days, HP: {hp}, Freezes: {streak_freezes}")

    # Level
    level_info, next_level = calc_level(total_xp, config["levels"])
    level_num = level_info["level"]
    print(f"[score] Level: {level_num} — {get_text(level_info['rank'], 'en')}")

    # Skills
    skills = calc_skills(daily, config)
    skills_display = {k: v["level"] for k, v in skills.items()}
    print(f"[score] Skills: {skills_display}")

    # League
    league, weekly_xp = calc_league(daily, config)
    print(f"[score] League: {get_text(league['name'], 'en')} (weekly XP: {weekly_xp})")

    # Achievements
    unlocked = check_achievements(metrics, config, total_xp, streak, skills, level_info)
    print(f"[score] Achievements unlocked: {len(unlocked)}/{len(config['badges'])}")

    # Build badges list with dates
    old_badges = {b["id"]: b for b in (existing or {}).get("badges", [])}
    today = datetime.utcnow().strftime("%Y-%m-%d")
    badges = []
    for bid in unlocked:
        badge_conf = next((b for b in config["badges"] if b["id"] == bid), None)
        if not badge_conf:
            continue
        date = old_badges[bid]["date"] if bid in old_badges else today
        badges.append({
            "id": bid,
            "name": get_text(badge_conf["name"], "en"),
            "icon": badge_conf["icon"],
            "date": date,
        })

    # Tasks + Check-ins
    tasks = build_tasks(daily, config)
    check_ins = build_check_ins(daily, config)

    # User Stats
    user_stats = {
        "username": username,
        "level": level_num,
        "xp": total_xp,
        "xp_to_next_level": next_level["xp_required"] if next_level else total_xp,
        "weekly_xp": weekly_xp,
        "streak": streak,
        "streak_freezes": streak_freezes,
        "hp": hp,
        "max_hp": config["hp"]["max"],
        "rank": get_text(level_info["rank"], "en"),
        "avatar": level_info["icon"],
        "league": {"id": league["id"], "icon": league["icon"]},
        "badges": badges,
        "skills": skills_display,
        "last_check_in": max(daily.keys()) if daily else today,
    }

    save_json(DATA_DIR / "user_stats.json", user_stats)
    save_json(DATA_DIR / "tasks.json", tasks)
    save_json(DATA_DIR / "check_ins.json", check_ins)
    print(f"[score] Updated user_stats.json, tasks.json, check_ins.json")

    # Public profile
    profile = build_public_profile(user_stats, metrics)
    save_json(DATA_DIR / "public_profile.json", profile)
    print(f"[score] Generated public_profile.json")


if __name__ == "__main__":
    main()
