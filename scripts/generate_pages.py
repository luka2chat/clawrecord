#!/usr/bin/env python3
"""
ClawRecord Dashboard Generator v3 — Duolingo × Hamster Kombat Inspired

Key design inspirations:
- Duolingo: Learning path, streak system, league progression, achievement tiers
- Hamster Kombat: Daily combo/cipher/mini-game trio, tap-to-earn progression

Features:
- Onboarding path (beginner → intermediate → advanced)
- Share-to-X buttons on every key section
- Enhanced league visualization with promotion zones
- Polished visual design with glassmorphism and animations
"""

import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from utils import DATA_DIR, OUTPUT_DIR, get_text, load_json

OUTPUT_DIR.mkdir(exist_ok=True)

SHARE_HASHTAGS = "ClawRecord,OpenClaw,AI"
SHARE_BASE_URL = "https://twitter.com/intent/tweet"


def share_url(text):
    import urllib.parse
    return f"{SHARE_BASE_URL}?text={urllib.parse.quote(text)}&hashtags={SHARE_HASHTAGS}"


def share_button(text, label, lang, extra_cls=""):
    url = share_url(text)
    btn_label = "𝕏" if lang == "en" else "𝕏"
    return (
        f'<a href="{url}" target="_blank" rel="noopener" '
        f'class="share-btn {extra_cls}" title="{label}">'
        f'<span class="share-icon">{btn_label}</span>'
        f'</a>'
    )


# ── Usage Analytics Panel ─────────────────────────────────────────

def build_usage_analytics(analytics, config, lang):
    ui = {k: get_text(v, lang) for k, v in config["ui_text"].items()}

    tokens_total = analytics.get("tokens_total", 0)
    tokens_input = analytics.get("tokens_input", 0)
    tokens_output = analytics.get("tokens_output", 0)
    cost_total = analytics.get("cost_total", 0)
    cache_hit = analytics.get("cache_hit_rate", 0)
    avg_cost = analytics.get("avg_cost_per_day", 0)
    avg_tok_msg = analytics.get("avg_tokens_per_msg", 0)
    total_sessions = analytics.get("total_sessions", 0)

    def fmt_tokens(n):
        if n >= 1_000_000:
            return f"{n/1_000_000:.1f}M"
        if n >= 1_000:
            return f"{n/1_000:.1f}K"
        return str(n)

    stats_cards = (
        f'<div class="ua-stats">'
        f'<div class="ua-stat">'
        f'<div class="ua-stat-val">{fmt_tokens(tokens_total)}</div>'
        f'<div class="ua-stat-key">Total Tokens</div></div>'
        f'<div class="ua-stat">'
        f'<div class="ua-stat-val">${cost_total:.2f}</div>'
        f'<div class="ua-stat-key">Total Cost</div></div>'
        f'<div class="ua-stat">'
        f'<div class="ua-stat-val">{cache_hit}%</div>'
        f'<div class="ua-stat-key">Cache Hit</div></div>'
        f'<div class="ua-stat">'
        f'<div class="ua-stat-val">${avg_cost:.3f}</div>'
        f'<div class="ua-stat-key">Cost/Day</div></div>'
        f'<div class="ua-stat">'
        f'<div class="ua-stat-val">{fmt_tokens(avg_tok_msg)}</div>'
        f'<div class="ua-stat-key">Tok/Msg</div></div>'
        f'<div class="ua-stat">'
        f'<div class="ua-stat-val">{total_sessions}</div>'
        f'<div class="ua-stat-key">Sessions</div></div>'
        f'</div>'
    )

    colors = ["#22c55e", "#06b6d4", "#6366f1", "#f59e0b", "#f43f5e", "#a855f7", "#ec4899", "#14b8a6"]

    model_share = analytics.get("model_share", {})
    model_tokens_data = analytics.get("model_tokens", {})
    model_items = sorted(model_share.items(), key=lambda x: x[1], reverse=True)
    model_bars = ""
    for i, (model, pct) in enumerate(model_items):
        color = colors[i % len(colors)]
        short_name = model.split("/")[-1] if "/" in model else model
        tok_str = fmt_tokens(model_tokens_data.get(model, 0))
        if pct > 0:
            model_bars += (
                f'<div class="ua-bar-item">'
                f'<div class="ua-bar-label">{short_name}</div>'
                f'<div class="ua-bar-track"><div class="ua-bar-fill" style="width:{pct}%;background:{color}"></div></div>'
                f'<div class="ua-bar-pct">{pct}% ({tok_str})</div>'
                f'</div>'
            )

    provider_share = analytics.get("provider_share", {})
    provider_tokens_data = analytics.get("provider_tokens", {})
    provider_items = sorted(provider_share.items(), key=lambda x: x[1], reverse=True)
    provider_bars = ""
    for i, (provider, pct) in enumerate(provider_items):
        color = colors[(i + 3) % len(colors)]
        tok_str = fmt_tokens(provider_tokens_data.get(provider, 0))
        if pct > 0:
            provider_bars += (
                f'<div class="ua-bar-item">'
                f'<div class="ua-bar-label">{provider}</div>'
                f'<div class="ua-bar-track"><div class="ua-bar-fill" style="width:{pct}%;background:{color}"></div></div>'
                f'<div class="ua-bar-pct">{pct}% ({tok_str})</div>'
                f'</div>'
            )

    top_tools = analytics.get("top_tools", [])
    max_tool_count = max((t["count"] for t in top_tools), default=1)
    tool_bars = ""
    for i, t in enumerate(top_tools[:8]):
        color = colors[i % len(colors)]
        pct = t["count"] / max(max_tool_count, 1) * 100
        tool_bars += (
            f'<div class="ua-bar-item">'
            f'<div class="ua-bar-label">{t["name"]}</div>'
            f'<div class="ua-bar-track"><div class="ua-bar-fill" style="width:{pct:.0f}%;background:{color}"></div></div>'
            f'<div class="ua-bar-pct">{t["count"]:,}</div>'
            f'</div>'
        )

    channel_msgs = analytics.get("channel_messages", {})
    ch_items = sorted(channel_msgs.items(), key=lambda x: x[1], reverse=True)
    ch_max = max(channel_msgs.values(), default=1)
    channel_bars = ""
    ch_icons = {"telegram": "\U0001f4e8", "webchat": "\U0001f4bb", "discord": "\U0001f3ae", "slack": "\U0001f4ac"}
    for i, (ch, count) in enumerate(ch_items):
        icon = ch_icons.get(ch, "\U0001f310")
        pct = count / max(ch_max, 1) * 100
        channel_bars += (
            f'<div class="ua-bar-item">'
            f'<div class="ua-bar-label">{icon} {ch}</div>'
            f'<div class="ua-bar-track"><div class="ua-bar-fill" style="width:{pct:.0f}%;background:{colors[i%len(colors)]}"></div></div>'
            f'<div class="ua-bar-pct">{count}</div>'
            f'</div>'
        )

    trend = analytics.get("daily_trend", [])
    if trend:
        max_tokens = max((d["tokens"] for d in trend), default=1)
        spark_bars = ""
        for d in trend:
            h = max(d["tokens"] / max(max_tokens, 1) * 100, 2) if d["tokens"] > 0 else 2
            spark_bars += (
                f'<div class="ua-spark-bar" style="height:{h:.0f}%" '
                f'title="{d["date"]}: {fmt_tokens(d["tokens"])} tok, ${d["cost"]:.3f}">'
                f'</div>'
            )
        spark_html = (
            f'<div class="ua-sub-title">Daily Token Trend</div>'
            f'<div class="ua-spark">{spark_bars}</div>'
            f'<div class="ua-spark-labels">'
            f'<span>{trend[0]["date"][-5:]}</span>'
            f'<span>{trend[-1]["date"][-5:]}</span></div>'
        )
    else:
        spark_html = ""

    token_split_html = ""
    if tokens_total > 0:
        in_pct = round(tokens_input / max(tokens_total, 1) * 100, 1)
        out_pct = round(tokens_output / max(tokens_total, 1) * 100, 1)
        cache_pct = cache_hit
        token_split_html = (
            f'<div class="ua-sub-title">Token Breakdown</div>'
            f'<div class="ua-split-bar">'
            f'<div class="ua-split-seg" style="width:{in_pct}%;background:#6366f1" title="Input: {in_pct}%"></div>'
            f'<div class="ua-split-seg" style="width:{out_pct}%;background:#22c55e" title="Output: {out_pct}%"></div>'
            f'<div class="ua-split-seg" style="width:{cache_pct}%;background:#06b6d4" title="Cache: {cache_pct}%"></div>'
            f'</div>'
            f'<div class="ua-split-legend">'
            f'<span class="ua-leg"><span class="ua-dot" style="background:#6366f1"></span>Input {in_pct}%</span>'
            f'<span class="ua-leg"><span class="ua-dot" style="background:#22c55e"></span>Output {out_pct}%</span>'
            f'<span class="ua-leg"><span class="ua-dot" style="background:#06b6d4"></span>Cache {cache_pct}%</span>'
            f'</div>'
        )

    return (
        f'{stats_cards}'
        f'<div class="ua-panels">'
        f'<div class="ua-panel">'
        f'<div class="ua-sub-title">\U0001f916 Models</div>'
        f'{model_bars}'
        f'</div>'
        f'<div class="ua-panel">'
        f'<div class="ua-sub-title">\u2601\ufe0f Providers</div>'
        f'{provider_bars}'
        f'</div>'
        f'</div>'
        f'{token_split_html}'
        f'{spark_html}'
        f'<div class="ua-panels">'
        f'<div class="ua-panel">'
        f'<div class="ua-sub-title">\U0001f527 Top Tools</div>'
        f'{tool_bars}'
        f'</div>'
        f'<div class="ua-panel">'
        f'<div class="ua-sub-title">\U0001f4e1 Channels</div>'
        f'{channel_bars}'
        f'</div>'
        f'</div>'
    )


# ── Heatmap ────────────────────────────────────────────────────────

def build_heatmap(check_ins, lang):
    today = datetime.now(timezone.utc).date()
    start = today - timedelta(days=90)
    weekday_offset = start.weekday()
    cells = []
    for i in range(91):
        d = start + timedelta(days=i)
        ds = d.strftime("%Y-%m-%d")
        ci = check_ins.get(ds, {})
        xp = ci.get("xp_gained", 0)
        if xp == 0:
            level = 0
        elif xp < 50:
            level = 1
        elif xp < 150:
            level = 2
        elif xp < 300:
            level = 3
        else:
            level = 4
        row = (weekday_offset + i) % 7
        col = (weekday_offset + i) // 7
        cells.append(
            f'<div class="hm-cell hm-{level}" '
            f'style="grid-row:{row+1};grid-column:{col+1}" '
            f'title="{ds}: {xp} XP"></div>'
        )
    return "".join(cells)


# ── Skill Cards ────────────────────────────────────────────────────

def build_skill_cards(skills_data, config, lang):
    groups = config.get("skill_groups", {})
    grouped = {}
    for s in config["skills"]:
        g = s.get("group", "core")
        grouped.setdefault(g, []).append(s)

    html_parts = []
    for gid, g_conf in groups.items():
        g_name = get_text(g_conf["name"], lang)
        g_icon = g_conf.get("icon", "")
        cards_html = []
        for skill in grouped.get(gid, []):
            sid = skill["id"]
            sdata = skills_data.get(sid, {})
            if isinstance(sdata, dict):
                lvl = sdata.get("level", 0)
                xp = sdata.get("xp", 0)
                power = sdata.get("power", 0)
                next_xp = sdata.get("next_level_xp", skill["xp_per_level"])
                max_lvl = sdata.get("max_level", skill["max_level"])
            else:
                lvl = sdata if isinstance(sdata, int) else 0
                xp = 0
                power = lvl * skill.get("power_per_level", 20)
                next_xp = skill["xp_per_level"]
                max_lvl = skill["max_level"]
            pct = min((xp / max(next_xp, 1)) * 100, 100) if lvl < max_lvl else 100
            s_name = get_text(skill["name"], lang)
            pwr_label = get_text(config["ui_text"].get("power_per_level", {"en": "Power", "zh": "战力"}), lang)
            maxed = " maxed" if lvl >= max_lvl else ""
            cards_html.append(
                f'<div class="sk-card{maxed}">'
                f'<div class="sk-icon">{skill["icon"]}</div>'
                f'<div class="sk-info">'
                f'<div class="sk-name">{s_name}</div>'
                f'<div class="sk-lvl">Lv.{lvl}<span class="sk-max">/{max_lvl}</span></div>'
                f'</div>'
                f'<div class="sk-bar"><div class="sk-fill" style="width:{pct:.0f}%"></div></div>'
                f'<div class="sk-pwr">+{power} {pwr_label}</div>'
                f'</div>'
            )
        html_parts.append(
            f'<div class="sk-group">'
            f'<div class="sk-group-hdr">{g_icon} {g_name}</div>'
            f'<div class="sk-group-cards">{"".join(cards_html)}</div>'
            f'</div>'
        )
    return "".join(html_parts)


# ── Daily Quests ───────────────────────────────────────────────────

def build_daily_quests(quests, config, lang):
    ui = {k: get_text(v, lang) for k, v in config["ui_text"].items()}
    dq_conf = config.get("daily_quests", {})

    combo = quests.get("combo", {})
    combo_name = get_text(dq_conf.get("combo", {}).get("name", {"en": "Daily Combo"}), lang)
    combo_skills = combo.get("skills", [])
    combo_activated = combo.get("activated", 0)
    combo_activated_set = set(combo.get("activated_skills", []))
    combo_total = combo.get("total", 3)
    combo_done = combo.get("complete", False)
    combo_pct = min(combo_activated / max(combo_total, 1) * 100, 100)
    combo_xp = combo.get("xp_reward", 100)

    skill_map = {s["id"]: s for s in config["skills"]}
    combo_pills = ""
    for sid in combo_skills:
        sc = skill_map.get(sid, {})
        icon = sc.get("icon", "")
        name = get_text(sc.get("name", {"en": sid}), lang)
        active = "active" if sid in combo_activated_set else ""
        combo_pills += f'<span class="q-pill {active}">{icon} {name}</span>'

    ch = quests.get("challenge", {})
    ch_name = get_text(ch.get("name", {}), lang) or "Challenge"
    ch_desc = get_text(ch.get("desc", {}), lang) or ""
    ch_target = ch.get("target", 1)
    ch_progress = ch.get("progress", 0)
    ch_done = ch.get("complete", False)
    ch_pct = min(ch_progress / max(ch_target, 1) * 100, 100)
    ch_xp = ch.get("xp_reward", 0)
    if "{n}" in ch_desc:
        ch_desc = ch_desc.replace("{n}", str(ch_target))

    st = quests.get("streak", {})
    st_name = get_text(dq_conf.get("streak", {}).get("name", {"en": "Daily Streak"}), lang)
    st_done = st.get("complete", False)

    def quest_card(title, inner, done, xp_reward, icon_emoji):
        done_cls = " q-done" if done else " q-pulse"
        check = '<span class="q-check">\u2714</span>' if done else ""
        xp_tag = f'<span class="q-xp">+{xp_reward} XP</span>' if xp_reward else ""
        return (
            f'<div class="q-card{done_cls}">'
            f'<div class="q-icon-ring">{icon_emoji}</div>'
            f'<div class="q-hdr">{title}{check}{xp_tag}</div>'
            f'{inner}'
            f'</div>'
        )

    combo_inner = (
        f'<div class="q-pills">{combo_pills}</div>'
        f'<div class="q-bar"><div class="q-fill" style="width:{combo_pct:.0f}%"></div></div>'
        f'<div class="q-stat">{combo_activated}/{combo_total}</div>'
    )
    ch_inner = (
        f'<div class="q-desc">{ch_desc}</div>'
        f'<div class="q-bar"><div class="q-fill" style="width:{ch_pct:.0f}%"></div></div>'
        f'<div class="q-stat">{ch_progress}/{ch_target}</div>'
    )
    st_inner = (
        f'<div class="q-desc">{get_text(dq_conf.get("streak", {}).get("desc", {}), lang)}</div>'
        f'<div class="q-bar"><div class="q-fill" style="width:{"100" if st_done else "0"}%"></div></div>'
    )

    now = datetime.now(timezone.utc)
    midnight = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=timezone.utc)
    remaining = midnight - now
    hours_left = int(remaining.total_seconds() // 3600)
    mins_left = int((remaining.total_seconds() % 3600) // 60)
    timer = f'{ui.get("resets_in", "Resets in")} {hours_left}h {mins_left}m'

    return (
        f'<div class="q-row">'
        f'{quest_card(combo_name, combo_inner, combo_done, combo_xp, "\U0001f3b0")}'
        f'{quest_card(ch_name, ch_inner, ch_done, ch_xp, "\u2694\ufe0f")}'
        f'{quest_card(st_name, st_inner, st_done, 0, "\U0001f525")}'
        f'</div>'
        f'<div class="q-timer">\u23f0 {timer}</div>'
    )


# ── League Bar (Enhanced with progress) ───────────────────────────

def build_league_section(config, current_league_id, weekly_xp, lang):
    ui = {k: get_text(v, lang) for k, v in config["ui_text"].items()}
    leagues = config["leagues"]

    current_idx = 0
    for i, lg in enumerate(leagues):
        if lg["id"] == current_league_id:
            current_idx = i
            break

    next_league = leagues[current_idx + 1] if current_idx + 1 < len(leagues) else None
    current_league = leagues[current_idx]
    current_min = current_league["min_weekly_xp"]
    next_min = next_league["min_weekly_xp"] if next_league else current_min

    if next_league and next_min > current_min:
        progress_pct = min((weekly_xp - current_min) / (next_min - current_min) * 100, 100)
        xp_to_next = max(next_min - weekly_xp, 0)
    else:
        progress_pct = 100
        xp_to_next = 0

    items = []
    for i, lg in enumerate(leagues):
        on = " on" if lg["id"] == current_league_id else ""
        passed = " passed" if i < current_idx else ""
        name = get_text(lg["name"], lang)
        items.append(
            f'<div class="lg-item{on}{passed}">'
            f'<span class="lg-icon">{lg["icon"]}</span>'
            f'<span class="lg-name">{name}</span>'
            f'</div>'
        )

    league_bar_html = "".join(items)

    progress_html = ""
    if next_league:
        next_name = get_text(next_league["name"], lang)
        progress_html = (
            f'<div class="lg-progress">'
            f'<div class="lg-progress-info">'
            f'<span class="lg-progress-label">{ui.get("next_league", "Next League")}: {next_league["icon"]} {next_name}</span>'
            f'<span class="lg-progress-xp">{xp_to_next:,} XP</span>'
            f'</div>'
            f'<div class="lg-progress-bar"><div class="lg-progress-fill" style="width:{progress_pct:.1f}%"></div></div>'
            f'</div>'
        )

    return f'<div class="lg-bar">{league_bar_html}</div>{progress_html}'


# ── Multi-tier Badges ──────────────────────────────────────────────

def build_badges(user_badges, config, lang):
    unlocked_map = {b["id"]: b for b in user_badges}
    tier_styles = config.get("badge_tier_styles", {})

    cat_labels = {
        "milestone":  {"en": "Milestones",  "zh": "\u91cc\u7a0b\u7891"},
        "streak":     {"en": "Streaks",     "zh": "\u8fde\u7eed\u7eaa\u5f55"},
        "skill":      {"en": "Skills",      "zh": "\u6280\u80fd"},
        "tool":       {"en": "Tools",       "zh": "\u5de5\u5177"},
        "efficiency": {"en": "Efficiency",  "zh": "\u6548\u7387"},
        "time":       {"en": "Time",        "zh": "\u65f6\u95f4"},
        "special":    {"en": "Special",     "zh": "\u7279\u6b8a"},
    }

    by_cat = {}
    for badge in config["badges"]:
        cat = badge.get("category", "other")
        by_cat.setdefault(cat, []).append(badge)

    sections = []
    for cat, badges_list in by_cat.items():
        cat_name = get_text(cat_labels.get(cat, {"en": cat}), lang)
        items = []
        for badge in badges_list:
            bid = badge["id"]
            u = unlocked_map.get(bid)
            name = get_text(badge["name"], lang)
            icon = badge["icon"]
            tiers = badge.get("tiers", [])

            if u:
                tier = u.get("tier", 1)
                max_tier = u.get("max_tier", len(tiers))
                metric = u.get("metric", 0)
                next_val = u.get("next_tier_value")
                ts = tier_styles.get(str(tier), {})
                border_cls = ts.get("border", "bronze")
                stars = "\u2b50" * ts.get("stars", tier)
                pct = 100
                if next_val and next_val > 0:
                    cur_tier_val = 0
                    for t in tiers:
                        if t["tier"] == tier:
                            cur_tier_val = t["value"]
                            break
                    progress_range = next_val - cur_tier_val
                    if progress_range > 0:
                        pct = min((metric - cur_tier_val) / progress_range * 100, 100)
                tier_label = u.get("tier_label", "")
                items.append(
                    f'<div class="bdg bdg-{border_cls}" title="{tier_label}">'
                    f'<div class="bdg-icon">{icon}</div>'
                    f'<div class="bdg-name">{name}</div>'
                    f'<div class="bdg-stars">{stars}</div>'
                    f'<div class="bdg-bar"><div class="bdg-fill" style="width:{pct:.0f}%"></div></div>'
                    f'<div class="bdg-tier">T{tier}/{max_tier}</div>'
                    f'</div>'
                )
            else:
                items.append(
                    f'<div class="bdg bdg-locked">'
                    f'<div class="bdg-icon">\U0001f512</div>'
                    f'<div class="bdg-name">{name}</div>'
                    f'</div>'
                )
        sections.append(
            f'<div class="bdg-cat">'
            f'<div class="bdg-cat-title">{cat_name}</div>'
            f'<div class="bdg-grid">{"".join(items)}</div>'
            f'</div>'
        )
    return "".join(sections)


# ── Personal Records ───────────────────────────────────────────────

def build_records(records, config, lang):
    ui = {k: get_text(v, lang) for k, v in config["ui_text"].items()}
    items = [
        ("\u26a1", ui.get("best_daily_xp", "Best Daily XP"), f'{records.get("best_daily_xp", 0):,}'),
        ("\U0001f525", ui.get("longest_streak", "Longest Streak"), f'{records.get("longest_streak", 0)} {ui.get("days", "days")}'),
        ("\U0001f4ac", ui.get("best_session", "Longest Session"), f'{records.get("best_session_turns", 0)} turns'),
        ("\U0001f527", ui.get("best_daily_tools", "Most Tools/Day"), f'{records.get("best_daily_tools", 0)}'),
    ]
    cards = ""
    for icon, label, value in items:
        cards += (
            f'<div class="rec-card">'
            f'<div class="rec-icon">{icon}</div>'
            f'<div class="rec-val">{value}</div>'
            f'<div class="rec-label">{label}</div>'
            f'</div>'
        )
    return cards


# ── Onboarding / Learning Path ────────────────────────────────────

def build_learning_path(user_stats, config, lang):
    ui = {k: get_text(v, lang) for k, v in config["ui_text"].items()}

    level = user_stats.get("level", 1)
    streak = user_stats.get("streak", 0)
    badge_count = len(user_stats.get("badges", []))
    league_id = user_stats.get("league", {}).get("id", "bronze")
    weekly_xp = user_stats.get("weekly_xp", 0)
    total_sessions = user_stats.get("total_sessions", 0)
    total_messages = user_stats.get("total_messages", 0)
    total_tools = user_stats.get("total_tool_calls", 0)

    skills = user_stats.get("skills", {})
    max_skill_level = 0
    for s in skills.values():
        if isinstance(s, dict):
            max_skill_level = max(max_skill_level, s.get("level", 0))
        elif isinstance(s, int):
            max_skill_level = max(max_skill_level, s)

    has_legend = any(b.get("tier", 0) >= 5 for b in user_stats.get("badges", []))
    diamond_leagues = ["diamond"]

    beginner_checks = [
        total_messages >= 1,
        total_tools >= 1,
        total_sessions >= 1,
        badge_count >= 1,
        level >= 3,
    ]
    intermediate_checks = [
        streak >= 7,
        league_id in ["gold", "sapphire", "ruby", "emerald", "amethyst", "pearl", "obsidian", "diamond"],
        badge_count >= 10,
        max_skill_level >= 5,
        True,
    ]
    advanced_checks = [
        True,
        league_id in diamond_leagues,
        has_legend,
        streak >= 30,
        True,
    ]

    beginner_done = sum(beginner_checks)
    intermediate_done = sum(intermediate_checks)
    advanced_done = sum(advanced_checks)

    beginner_tasks = get_text(config["ui_text"].get("path_tasks_beginner", {"en": []}), lang)
    intermediate_tasks = get_text(config["ui_text"].get("path_tasks_intermediate", {"en": []}), lang)
    advanced_tasks = get_text(config["ui_text"].get("path_tasks_advanced", {"en": []}), lang)

    def path_section(title, desc, icon, tasks, checks, done_count, color, is_active):
        total = len(tasks)
        pct = (done_count / max(total, 1)) * 100
        active_cls = " path-active" if is_active else ""
        completed_cls = " path-completed" if done_count >= total else ""

        task_items = ""
        for i, task in enumerate(tasks):
            checked = checks[i] if i < len(checks) else False
            check_cls = "path-task-done" if checked else "path-task-pending"
            check_icon = "\u2705" if checked else "\u2b1c"
            task_items += f'<div class="{check_cls}"><span>{check_icon}</span> {task}</div>'

        return (
            f'<div class="path-stage{active_cls}{completed_cls}" style="--path-color:{color}">'
            f'<div class="path-header">'
            f'<div class="path-icon">{icon}</div>'
            f'<div class="path-info">'
            f'<div class="path-title">{title}</div>'
            f'<div class="path-desc">{desc}</div>'
            f'</div>'
            f'<div class="path-progress-ring">'
            f'<span class="path-progress-text">{done_count}/{total}</span>'
            f'</div>'
            f'</div>'
            f'<div class="path-tasks">{task_items}</div>'
            f'<div class="path-bar"><div class="path-bar-fill" style="width:{pct:.0f}%"></div></div>'
            f'</div>'
        )

    beginner_active = beginner_done < 5
    intermediate_active = beginner_done >= 5 and intermediate_done < 5
    advanced_active = beginner_done >= 5 and intermediate_done >= 5

    return (
        f'<div class="path-container">'
        f'{path_section(ui.get("path_beginner", "Beginner"), ui.get("path_beginner_desc", ""), "\U0001f331", beginner_tasks, beginner_checks, beginner_done, "#22c55e", beginner_active)}'
        f'<div class="path-connector"></div>'
        f'{path_section(ui.get("path_intermediate", "Intermediate"), ui.get("path_intermediate_desc", ""), "\U0001f680", intermediate_tasks, intermediate_checks, intermediate_done, "#f59e0b", intermediate_active)}'
        f'<div class="path-connector"></div>'
        f'{path_section(ui.get("path_advanced", "Advanced"), ui.get("path_advanced_desc", ""), "\U0001f451", advanced_tasks, advanced_checks, advanced_done, "#a855f7", advanced_active)}'
        f'</div>'
    )


# ── Dashboard HTML ─────────────────────────────────────────────────

def generate_dashboard(user_stats, tasks, config, check_ins, quests, analytics, lang):
    ui = {k: get_text(v, lang) for k, v in config["ui_text"].items()}

    level_info = next(
        (l for l in reversed(config["levels"]) if l["level"] <= user_stats["level"]),
        config["levels"][0],
    )
    next_level = None
    for lv in config["levels"]:
        if lv["xp_required"] > user_stats["xp"]:
            next_level = lv
            break
    xp_progress = 0
    if next_level:
        prev_xp = level_info["xp_required"]
        xp_progress = ((user_stats["xp"] - prev_xp) / max(next_level["xp_required"] - prev_xp, 1)) * 100

    lang_links = " ".join(
        f'<a href="{"index.html" if l == "en" else f"index_{l}.html"}" '
        f'class="lang-btn {"active" if l == lang else ""}">{l.upper()}</a>'
        for l in config["supported_languages"]
    )

    league = user_stats.get("league", {})
    league_conf = next(
        (lg for lg in config["leagues"] if lg["id"] == league.get("id")),
        config["leagues"][0],
    )
    league_name = get_text(league_conf["name"], lang)
    weekly_xp = user_stats.get("weekly_xp", 0)
    league_section_html = build_league_section(config, league.get("id", "bronze"), weekly_xp, lang)
    heatmap_html = build_heatmap(check_ins, lang)
    skill_cards_html = build_skill_cards(user_stats.get("skills", {}), config, lang)
    daily_quests_html = build_daily_quests(quests, config, lang)
    badges_html = build_badges(user_stats.get("badges", []), config, lang)
    records = user_stats.get("personal_records", {})
    records_html = build_records(records, config, lang)
    usage_analytics_html = build_usage_analytics(analytics, config, lang)
    learning_path_html = build_learning_path(user_stats, config, lang)

    claw_power = user_stats.get("claw_power", 0)
    today_xp = user_stats.get("today_xp", 0)
    multiplier = user_stats.get("streak_multiplier", 1.0)

    streak_freeze = ""
    sf = user_stats.get("streak_freezes", 0)
    if sf > 0:
        streak_freeze = f' <span class="freeze">\U0001f9ca x{sf}</span>'

    xp_display = f"{user_stats['xp']:,}"
    next_xp_display = f"{next_level['xp_required']:,}" if next_level else xp_display

    unlocked_count = len(user_stats.get("badges", []))
    total_badges = len(config["badges"])

    recent = sorted(tasks, key=lambda t: t["date"], reverse=True)[:8]
    if recent:
        rows = "".join(
            f'<div class="trow">'
            f'<span class="t-date">{t["date"]}</span>'
            f'<span class="t-desc">{t["description"]}</span>'
            f'<span class="t-xp">+{t["xp_gained"]}</span>'
            f'<span class="t-cx cx-{t["complexity"]}">{t["complexity"]}</span>'
            f'</div>'
            for t in recent
        )
        tasks_html = f'<div class="tlist">{rows}</div>'
    else:
        tasks_html = f'<p class="empty">{ui["empty_tasks"]}</p>'

    mult_tag = ""
    if multiplier > 1.0:
        mult_tag = f'<span class="hero-mult">\U0001f680 x{multiplier}</span>'

    rank_name = get_text(level_info["rank"], lang)
    username = user_stats["username"]

    share_profile_text = f"I'm a Lv.{user_stats['level']} {rank_name} on ClawRecord with {claw_power:,} Claw Power! \U0001f43e"
    share_league_text = f"I'm in the {league_conf['icon']} {league_name} league with {weekly_xp:,} weekly XP on ClawRecord! \U0001f3c6"
    share_streak_text = f"I'm on a {user_stats['streak']}-day streak on ClawRecord! \U0001f525"
    share_badge_text = f"I've unlocked {unlocked_count}/{total_badges} achievements on ClawRecord! \U0001f3c5"

    best_xp = records.get("best_daily_xp", 0)
    share_record_text = f"New personal best on ClawRecord: {best_xp:,} XP in one day! \u26a1"

    profile_share = share_button(share_profile_text, ui.get("share_profile", "Share Profile"), lang)
    league_share = share_button(share_league_text, ui.get("share_league", "Share League"), lang)
    badge_share = share_button(share_badge_text, ui.get("share_badge", "Share"), lang)
    record_share = share_button(share_record_text, ui.get("share_record", "Share"), lang)

    og_description = f"Lv.{user_stats['level']} {rank_name} | {claw_power:,} Claw Power | {user_stats['streak']}-day streak"

    return f'''<!DOCTYPE html>
<html lang="{lang}">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{ui["title"]} \u2014 {username}</title>
<meta name="description" content="{og_description}">
<meta property="og:title" content="{ui["title"]} \u2014 {username}">
<meta property="og:description" content="{og_description}">
<meta property="og:type" content="website">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{ui["title"]} \u2014 {username}">
<meta name="twitter:description" content="{og_description}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;700&family=Space+Grotesk:wght@400;500;600;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="styles.css">
</head>
<body>
<div class="noise"></div>
<div class="shell">

<nav class="nav">
  <div class="nav-l">
    <span class="brand">\U0001f43e ClawRecord</span>
    <span class="sep">/</span>
    <span class="nav-user">{username}</span>
  </div>
  <div class="nav-r">
    <span class="pill">{league_conf["icon"]} {league_name}</span>
    {profile_share}
    {lang_links}
  </div>
</nav>

<header class="hero">
  <div class="hero-left">
    <div class="av-ring"><div class="av-inner">{user_stats.get("avatar", level_info["icon"])}</div></div>
    <div class="av-rank">{rank_name}</div>
  </div>
  <div class="hero-center">
    <div class="power-label">{ui.get("claw_power", "Claw Power")}</div>
    <div class="power-num">{claw_power:,}</div>
    <div class="power-delta">+{today_xp} {ui.get("today_gain", "today")} {mult_tag}</div>
    <div class="xp-track">
      <div class="xp-fill" style="width:{xp_progress:.1f}%"></div>
      <span class="xp-label">Lv.{user_stats["level"]} \u2014 {xp_display} / {next_xp_display} XP</span>
    </div>
  </div>
  <div class="hero-stats">
    <div class="hs"><span class="hs-val">{user_stats["level"]}</span><span class="hs-key">{ui["level"]}</span></div>
    <div class="hs"><span class="hs-val">\U0001f525 {user_stats["streak"]}</span>{streak_freeze}<span class="hs-key">{ui["streak"]}</span></div>
    <div class="hs"><span class="hs-val">\u2764\ufe0f {user_stats["hp"]}<small>/{user_stats["max_hp"]}</small></span><span class="hs-key">{ui["hp"]}</span></div>
    <div class="hs"><span class="hs-val">\u26a1 {weekly_xp}</span><span class="hs-key">{ui["weekly_xp"]}</span></div>
  </div>
</header>

<section class="card card-quests">
  <h2>\U0001f3af {ui.get("daily_quests", "Daily Quests")}</h2>
  {daily_quests_html}
</section>

<section class="card card-path">
  <h2>\U0001f5fa\ufe0f {ui.get("onboarding_title", "Your OpenClaw Journey")}</h2>
  {learning_path_html}
</section>

<section class="card card-skills">
  <h2>\U0001f0cf {ui.get("skills_tree", "Skill Cards")}</h2>
  <div class="sk-wall">{skill_cards_html}</div>
</section>

<section class="card card-league">
  <h2>\U0001f3c6 {ui["league"]} <span class="dim">{ui["weekly_xp"]}: {weekly_xp:,}</span>{league_share}</h2>
  {league_section_html}
</section>

<section class="card card-heat">
  <h2>\U0001f4c5 {ui["heatmap"]}</h2>
  <div class="hm-grid">{heatmap_html}</div>
  <div class="hm-legend">
    <span>{ui["less"]}</span>
    <div class="hm-cell hm-0"></div><div class="hm-cell hm-1"></div><div class="hm-cell hm-2"></div><div class="hm-cell hm-3"></div><div class="hm-cell hm-4"></div>
    <span>{ui["more"]}</span>
  </div>
</section>

<section class="card card-usage">
  <h2>\U0001f4ca {ui.get("usage_analytics", "Usage Analytics")}</h2>
  {usage_analytics_html}
</section>

<section class="card card-badges">
  <h2>\U0001f3c5 {ui["achievements"]} <span class="dim">{unlocked_count}/{total_badges}</span>{badge_share}</h2>
  {badges_html}
</section>

<section class="card card-records">
  <h2>\U0001f947 {ui.get("personal_bests", "Personal Bests")}{record_share}</h2>
  <div class="rec-grid">{records_html}</div>
</section>

<section class="card card-tasks">
  <h2>\U0001f4cb {ui["recent_tasks"]}</h2>
  {tasks_html}
</section>

<section class="card card-leaderboard">
  <h2>\U0001f30d {ui.get("leaderboard_title", "Global Leaderboard")}</h2>
  <div class="lb-cta">
    <div class="lb-info">
      <p class="lb-desc">{ui.get("leaderboard_desc", "Compete with OpenClaw users worldwide")}</p>
      <div class="lb-stats-row">
        <div class="lb-stat"><span class="lb-stat-val">{claw_power:,}</span><span class="lb-stat-key">Claw Power</span></div>
        <div class="lb-stat"><span class="lb-stat-val">{league_conf["icon"]} {league_name}</span><span class="lb-stat-key">{ui.get("league", "League")}</span></div>
        <div class="lb-stat"><span class="lb-stat-val">{unlocked_count}</span><span class="lb-stat-key">{ui.get("achievements", "Badges")}</span></div>
      </div>
    </div>
    <div class="lb-actions">
      <a href="https://github.com/luka2chat/clawrecord-leaderboard" target="_blank" class="lb-btn">\U0001f3c6 {ui.get("join_leaderboard", "Join the Leaderboard")}</a>
    </div>
  </div>
</section>

<footer class="foot">
  <p>{ui["last_updated"]}: {datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")}</p>
  <p>Powered by <a href="https://github.com/openclaw/openclaw">OpenClaw</a> &amp; <a href="https://github.com/luka2chat/clawrecord">ClawRecord</a></p>
</footer>

</div>
<script>
document.querySelectorAll('.share-btn').forEach(function(btn){{
  btn.addEventListener('click', function(e){{
    if(navigator.share){{
      e.preventDefault();
      var url = btn.getAttribute('href');
      var params = new URLSearchParams(url.split('?')[1]);
      navigator.share({{title: 'ClawRecord', text: params.get('text') || '', url: window.location.href}}).catch(function(){{}});
    }}
  }});
}});
</script>
</body>
</html>'''


# ── CSS ────────────────────────────────────────────────────────────

def generate_css():
    return """\
:root {
  --bg: #050a18;
  --surface: #0a1128;
  --card: #0d1530;
  --card-hover: #111d40;
  --border: #1a2744;
  --border-glow: rgba(34,197,94,.25);
  --g: #22c55e;
  --g-dim: rgba(34,197,94,.1);
  --g-glow: rgba(34,197,94,.35);
  --g2: #16a34a;
  --indigo: #6366f1;
  --cyan: #06b6d4;
  --text: #f1f5f9;
  --sub: #94a3b8;
  --muted: #475569;
  --danger: #f43f5e;
  --warn: #f59e0b;
  --gold: #fbbf24;
  --purple: #a855f7;
  --r: 18px;
  --r-sm: 12px;
  --font: 'Space Grotesk', system-ui, sans-serif;
  --mono: 'JetBrains Mono', ui-monospace, monospace;
  --glass: rgba(255,255,255,.03);
  --glass-border: rgba(255,255,255,.06);
}
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
body {
  font-family: var(--font); background: var(--bg); color: var(--text);
  line-height: 1.6; min-height: 100vh; overflow-x: hidden;
}
a { color: var(--g); text-decoration: none; transition: color .2s; }
a:hover { color: var(--cyan); }

.noise {
  position: fixed; inset: 0; z-index: 9999; pointer-events: none; opacity: .025;
  background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='.85' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E");
  background-repeat: repeat; background-size: 200px 200px;
}
.shell { max-width: 980px; margin: 0 auto; padding: 20px 24px 40px; }

/* ── Nav ────────────────────────────────── */
.nav {
  display: flex; justify-content: space-between; align-items: center;
  padding: 16px 0; margin-bottom: 24px;
  border-bottom: 1px solid var(--border);
}
.nav-l { display: flex; align-items: center; gap: 8px; }
.brand {
  font-weight: 700; font-size: 1.2em; letter-spacing: -.02em;
  background: linear-gradient(135deg, var(--g), var(--cyan));
  -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;
}
.sep { color: var(--muted); }
.nav-user { color: var(--sub); font-size: .9em; }
.nav-r { display: flex; align-items: center; gap: 10px; }
.pill {
  background: linear-gradient(135deg, var(--card), var(--card-hover));
  padding: 6px 16px; border-radius: 20px;
  font-size: .82em; border: 1px solid var(--border); font-family: var(--mono); font-weight: 600;
}
.lang-btn {
  color: var(--sub); padding: 5px 14px; border: 1px solid var(--border);
  border-radius: var(--r-sm); font-size: .78em; font-weight: 500;
  transition: all .2s; font-family: var(--mono);
}
.lang-btn.active {
  background: var(--g); color: #fff; border-color: var(--g);
  box-shadow: 0 0 14px var(--g-glow);
}
.lang-btn:hover:not(.active) { border-color: var(--g); color: var(--g); }

/* ── Share Button ───────────────────────── */
.share-btn {
  display: inline-flex; align-items: center; justify-content: center;
  width: 32px; height: 32px; border-radius: 50%;
  background: linear-gradient(135deg, #1a1a2e, #16213e);
  border: 1px solid var(--border); color: var(--text);
  font-size: .82em; font-weight: 700; transition: all .25s;
  margin-left: 8px; text-decoration: none; flex-shrink: 0;
}
.share-btn:hover {
  background: linear-gradient(135deg, #1d9bf0, #0d8bd9);
  border-color: #1d9bf0; color: #fff;
  box-shadow: 0 0 16px rgba(29,155,240,.3);
  transform: scale(1.1);
}
.share-icon { font-size: .9em; }

/* ── Hero ───────────────────────────────── */
.hero {
  display: grid; grid-template-columns: auto 1fr auto;
  gap: 28px; align-items: center;
  background: linear-gradient(135deg, var(--card) 0%, rgba(34,197,94,.04) 50%, rgba(99,102,241,.04) 100%);
  padding: 32px; border-radius: var(--r); border: 1px solid var(--border);
  margin-bottom: 24px; position: relative; overflow: hidden;
  backdrop-filter: blur(8px);
}
.hero::before {
  content: ''; position: absolute; inset: 0;
  background: radial-gradient(ellipse at 20% 50%, rgba(34,197,94,.08) 0%, transparent 50%),
              radial-gradient(ellipse at 80% 50%, rgba(99,102,241,.06) 0%, transparent 50%);
  pointer-events: none;
}
.hero::after {
  content: ''; position: absolute; top: -50%; right: -20%; width: 300px; height: 300px;
  background: radial-gradient(circle, rgba(6,182,212,.06) 0%, transparent 70%);
  pointer-events: none;
}
.hero-left { text-align: center; position: relative; z-index: 1; }
.av-ring {
  width: 100px; height: 100px; border-radius: 50%;
  background: conic-gradient(from 0deg, var(--g), var(--cyan), var(--indigo), var(--purple), var(--g));
  padding: 3px; animation: spin 10s linear infinite;
  box-shadow: 0 0 30px rgba(34,197,94,.15);
}
@keyframes spin { to { transform: rotate(360deg); } }
.av-inner {
  width: 100%; height: 100%; border-radius: 50%;
  background: var(--card); display: flex; align-items: center; justify-content: center;
  font-size: 44px;
}
.av-rank {
  margin-top: 8px; font-size: .72em; font-weight: 600; letter-spacing: .06em;
  text-transform: uppercase; font-family: var(--mono);
  background: linear-gradient(90deg, var(--g), var(--cyan));
  -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;
}

.hero-center { min-width: 0; position: relative; z-index: 1; }
.power-label {
  font-size: .75em; font-weight: 600; text-transform: uppercase;
  letter-spacing: .1em; color: var(--sub); font-family: var(--mono);
}
.power-num {
  font-size: 3.4em; font-weight: 700; line-height: 1.05;
  letter-spacing: -.03em; font-family: var(--mono);
  background: linear-gradient(135deg, var(--g), var(--cyan), var(--indigo));
  background-size: 200% 200%; animation: gradientShift 4s ease infinite;
  -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;
}
@keyframes gradientShift {
  0%, 100% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
}
.power-delta {
  font-size: .85em; color: var(--g); font-family: var(--mono); margin-bottom: 12px;
}
.hero-mult {
  display: inline-block; background: linear-gradient(135deg, rgba(245,158,11,.2), rgba(245,158,11,.1));
  color: var(--warn); padding: 2px 10px; border-radius: 12px; font-size: .82em; font-weight: 600;
  margin-left: 6px; border: 1px solid rgba(245,158,11,.2);
}
.xp-track {
  position: relative; height: 24px; border-radius: 12px;
  background: var(--surface); overflow: hidden; border: 1px solid var(--border);
}
.xp-fill {
  height: 100%; border-radius: 12px;
  background: linear-gradient(90deg, #15803d, var(--g), #4ade80);
  box-shadow: 0 0 20px var(--g-glow); transition: width .8s cubic-bezier(.4,0,.2,1);
  position: relative;
}
.xp-fill::after {
  content: ''; position: absolute; top: 0; left: 0; right: 0; height: 50%;
  background: linear-gradient(180deg, rgba(255,255,255,.15) 0%, transparent 100%);
  border-radius: 12px 12px 0 0;
}
.xp-label {
  position: absolute; inset: 0; display: flex; align-items: center; justify-content: center;
  font-size: .7em; font-weight: 600; color: #fff; font-family: var(--mono);
  text-shadow: 0 1px 4px rgba(0,0,0,.6);
}

.hero-stats { display: flex; flex-direction: column; gap: 8px; position: relative; z-index: 1; }
.hs {
  text-align: center; padding: 10px 18px; min-width: 100px;
  background: var(--glass); border-radius: var(--r-sm);
  border: 1px solid var(--glass-border); backdrop-filter: blur(4px);
}
.hs-val { display: block; font-size: 1.15em; font-weight: 700; color: var(--g); font-family: var(--mono); }
.hs-val small { font-size: .7em; color: var(--sub); font-weight: 400; }
.hs-key { display: block; font-size: .65em; color: var(--muted); margin-top: 2px; }
.freeze { font-size: .65em; vertical-align: middle; margin-left: 2px; }

/* ── Cards ──────────────────────────────── */
.card {
  background: linear-gradient(135deg, var(--card) 0%, rgba(13,21,48,.9) 100%);
  border: 1px solid var(--border); border-radius: var(--r);
  padding: 28px; margin-bottom: 20px; transition: all .3s;
  backdrop-filter: blur(4px);
}
.card:hover { border-color: var(--border-glow); box-shadow: 0 4px 24px rgba(0,0,0,.2); }
.card h2 {
  font-size: 1.05em; font-weight: 600; margin-bottom: 20px;
  display: flex; align-items: center; gap: 8px; letter-spacing: -.01em;
}
.dim { color: var(--muted); font-weight: 400; font-size: .85em; margin-left: auto; }

/* ── Daily Quests ─────────────────────────── */
.q-row { display: grid; grid-template-columns: repeat(3, 1fr); gap: 14px; }
.q-card {
  background: var(--surface); border: 1px solid var(--border); border-radius: var(--r-sm);
  padding: 18px; transition: all .3s; position: relative; overflow: hidden;
}
.q-card::before {
  content: ''; position: absolute; top: 0; left: 0; right: 0; height: 3px;
  background: linear-gradient(90deg, var(--g), var(--cyan)); opacity: 0;
  transition: opacity .3s;
}
.q-card:hover::before { opacity: 1; }
.q-card.q-done {
  border-color: var(--g);
  background: linear-gradient(135deg, rgba(34,197,94,.08), rgba(6,182,212,.04));
}
.q-card.q-done::before { opacity: 1; background: var(--g); }
.q-card.q-pulse { animation: pulse 3s ease-in-out infinite; }
@keyframes pulse { 0%,100% { box-shadow: none; } 50% { box-shadow: 0 0 20px rgba(34,197,94,.1); } }
.q-icon-ring {
  font-size: 1.6em; margin-bottom: 10px;
  width: 48px; height: 48px; display: flex; align-items: center; justify-content: center;
  background: var(--glass); border-radius: 50%; border: 1px solid var(--glass-border);
}
.q-hdr {
  font-weight: 600; font-size: .88em; margin-bottom: 10px;
  display: flex; align-items: center; gap: 6px; flex-wrap: wrap;
}
.q-check { color: var(--g); font-weight: 700; }
.q-xp {
  margin-left: auto; font-size: .78em; font-family: var(--mono);
  color: var(--g); font-weight: 600;
  background: rgba(34,197,94,.1); padding: 2px 8px; border-radius: 10px;
}
.q-desc { color: var(--sub); font-size: .8em; margin-bottom: 8px; }
.q-pills { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 10px; }
.q-pill {
  font-size: .7em; padding: 3px 10px; border-radius: 14px;
  background: var(--glass); border: 1px solid var(--glass-border);
  color: var(--muted); font-family: var(--mono); transition: all .2s;
}
.q-pill.active { background: rgba(34,197,94,.12); border-color: var(--g); color: var(--g); }
.q-bar {
  height: 8px; border-radius: 4px; background: rgba(255,255,255,.06); overflow: hidden;
  margin-bottom: 6px;
}
.q-fill {
  height: 100%; border-radius: 4px;
  background: linear-gradient(90deg, var(--g), var(--cyan));
  transition: width .5s; position: relative;
}
.q-fill::after {
  content: ''; position: absolute; top: 0; left: 0; right: 0; height: 50%;
  background: linear-gradient(180deg, rgba(255,255,255,.2) 0%, transparent 100%);
  border-radius: 4px 4px 0 0;
}
.q-stat { font-size: .7em; color: var(--muted); font-family: var(--mono); text-align: right; }
.q-timer {
  text-align: center; margin-top: 14px; font-size: .82em;
  color: var(--warn); font-family: var(--mono); font-weight: 600;
  background: rgba(245,158,11,.06); padding: 8px; border-radius: var(--r-sm);
  border: 1px solid rgba(245,158,11,.12);
}

/* ── Learning Path ──────────────────────── */
.path-container { display: flex; flex-direction: column; gap: 0; }
.path-connector {
  width: 3px; height: 24px; margin: 0 auto;
  background: linear-gradient(180deg, var(--border), var(--glass-border));
}
.path-stage {
  background: var(--surface); border: 1px solid var(--border); border-radius: var(--r-sm);
  padding: 20px; transition: all .3s; position: relative; overflow: hidden;
}
.path-stage::before {
  content: ''; position: absolute; left: 0; top: 0; bottom: 0; width: 4px;
  background: var(--path-color, var(--g)); opacity: .3; transition: opacity .3s;
}
.path-stage.path-active { border-color: var(--path-color, var(--g)); }
.path-stage.path-active::before { opacity: 1; }
.path-stage.path-completed { border-color: rgba(34,197,94,.2); }
.path-stage.path-completed::before { opacity: .6; }
.path-header { display: flex; align-items: center; gap: 14px; margin-bottom: 14px; }
.path-icon {
  font-size: 1.8em; width: 52px; height: 52px; display: flex; align-items: center; justify-content: center;
  background: var(--glass); border-radius: 50%; border: 2px solid var(--glass-border);
  flex-shrink: 0;
}
.path-stage.path-active .path-icon { border-color: var(--path-color, var(--g)); box-shadow: 0 0 16px color-mix(in srgb, var(--path-color) 30%, transparent); }
.path-info { flex: 1; min-width: 0; }
.path-title { font-weight: 600; font-size: 1em; }
.path-desc { font-size: .78em; color: var(--sub); }
.path-progress-ring {
  width: 42px; height: 42px; border-radius: 50%;
  border: 2px solid var(--border); display: flex; align-items: center; justify-content: center;
  font-family: var(--mono); font-size: .7em; font-weight: 600; color: var(--sub); flex-shrink: 0;
}
.path-stage.path-active .path-progress-ring { border-color: var(--path-color); color: var(--path-color); }
.path-stage.path-completed .path-progress-ring { border-color: var(--g); color: var(--g); background: rgba(34,197,94,.08); }
.path-tasks { display: grid; grid-template-columns: 1fr 1fr; gap: 6px 16px; margin-bottom: 12px; font-size: .82em; }
.path-task-done { color: var(--g); }
.path-task-pending { color: var(--muted); }
.path-bar { height: 6px; border-radius: 3px; background: rgba(255,255,255,.06); overflow: hidden; }
.path-bar-fill {
  height: 100%; border-radius: 3px;
  background: linear-gradient(90deg, var(--path-color, var(--g)), color-mix(in srgb, var(--path-color) 70%, var(--cyan)));
  transition: width .5s;
}

/* ── Skill Cards ──────────────────────────── */
.sk-wall { display: flex; flex-direction: column; gap: 18px; }
.sk-group-hdr {
  font-size: .78em; font-weight: 600; color: var(--sub); text-transform: uppercase;
  letter-spacing: .08em; margin-bottom: 10px; font-family: var(--mono);
  padding-bottom: 4px; border-bottom: 1px solid var(--glass-border);
}
.sk-group-cards { display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; }
.sk-card {
  background: var(--surface); border: 1px solid var(--border); border-radius: var(--r-sm);
  padding: 16px; display: grid; grid-template-columns: auto 1fr; gap: 8px 12px;
  align-items: center; transition: all .25s;
}
.sk-card:hover { border-color: rgba(34,197,94,.25); transform: translateY(-2px); box-shadow: 0 4px 16px rgba(0,0,0,.15); }
.sk-card.maxed { border-color: rgba(245,158,11,.3); background: linear-gradient(135deg, var(--surface), rgba(245,158,11,.03)); }
.sk-icon { font-size: 1.8em; grid-row: span 2; }
.sk-info { display: flex; justify-content: space-between; align-items: baseline; }
.sk-name { font-weight: 600; font-size: .88em; }
.sk-lvl { font-family: var(--mono); font-weight: 700; color: var(--g); font-size: .85em; }
.sk-max { font-weight: 400; color: var(--muted); font-size: .8em; }
.sk-bar {
  grid-column: 2; height: 6px; border-radius: 3px; background: rgba(255,255,255,.06);
  overflow: hidden;
}
.sk-fill {
  height: 100%; border-radius: 3px;
  background: linear-gradient(90deg, var(--g), var(--cyan)); transition: width .5s;
  position: relative;
}
.sk-fill::after {
  content: ''; position: absolute; top: 0; left: 0; right: 0; height: 50%;
  background: linear-gradient(180deg, rgba(255,255,255,.2) 0%, transparent 100%);
  border-radius: 3px 3px 0 0;
}
.sk-pwr {
  grid-column: 2; font-size: .7em; color: var(--sub); font-family: var(--mono);
  text-align: right;
}

/* ── League Bar ───────────────────────────── */
.lg-bar { display: flex; gap: 4px; overflow-x: auto; margin-bottom: 16px; }
.lg-item {
  flex: 1; min-width: 60px; text-align: center; padding: 14px 4px;
  border-radius: var(--r-sm); background: var(--surface);
  border: 1px solid var(--border); opacity: .35; transition: all .25s;
}
.lg-item.passed { opacity: .55; }
.lg-item.on {
  opacity: 1; border-color: var(--g);
  box-shadow: 0 0 18px var(--g-dim), inset 0 0 24px var(--g-dim);
  background: linear-gradient(135deg, rgba(34,197,94,.1), rgba(6,182,212,.05));
  transform: scale(1.05);
}
.lg-icon { display: block; font-size: 1.5em; }
.lg-name { display: block; font-size: .6em; color: var(--sub); margin-top: 3px; font-family: var(--mono); }
.lg-progress { background: var(--surface); border: 1px solid var(--border); border-radius: var(--r-sm); padding: 14px; }
.lg-progress-info { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
.lg-progress-label { font-size: .82em; color: var(--sub); font-family: var(--mono); }
.lg-progress-xp { font-size: .82em; font-weight: 600; color: var(--warn); font-family: var(--mono); }
.lg-progress-bar { height: 10px; border-radius: 5px; background: rgba(255,255,255,.06); overflow: hidden; }
.lg-progress-fill {
  height: 100%; border-radius: 5px;
  background: linear-gradient(90deg, var(--g), var(--gold));
  box-shadow: 0 0 12px rgba(251,191,36,.2);
  transition: width .8s cubic-bezier(.4,0,.2,1); position: relative;
}
.lg-progress-fill::after {
  content: ''; position: absolute; top: 0; left: 0; right: 0; height: 50%;
  background: linear-gradient(180deg, rgba(255,255,255,.2) 0%, transparent 100%);
  border-radius: 5px 5px 0 0;
}

/* ── Heatmap ──────────────────────────────── */
.hm-grid {
  display: grid; grid-template-rows: repeat(7, 1fr);
  grid-auto-flow: column; grid-auto-columns: 1fr; gap: 3px;
}
.hm-cell { aspect-ratio: 1; border-radius: 3px; min-width: 0; transition: all .15s; }
.hm-cell:hover { transform: scale(1.5); z-index: 1; }
.hm-0 { background: rgba(15,23,42,.6); }
.hm-1 { background: #064e3b; }
.hm-2 { background: #047857; }
.hm-3 { background: #10b981; box-shadow: 0 0 4px rgba(16,185,129,.3); }
.hm-4 { background: #34d399; box-shadow: 0 0 8px rgba(52,211,153,.4); }
.hm-legend {
  display: flex; align-items: center; gap: 4px; justify-content: flex-end;
  margin-top: 10px; font-size: .7em; color: var(--muted); font-family: var(--mono);
}
.hm-legend .hm-cell { width: 12px; height: 12px; display: inline-block; border-radius: 2px; }

/* ── Usage Analytics ─────────────────────── */
.ua-stats {
  display: grid; grid-template-columns: repeat(6, 1fr); gap: 10px; margin-bottom: 20px;
}
.ua-stat {
  text-align: center; padding: 14px 8px; background: var(--surface);
  border: 1px solid var(--border); border-radius: var(--r-sm); transition: all .2s;
}
.ua-stat:hover { border-color: var(--border-glow); transform: translateY(-2px); }
.ua-stat-val { font-size: 1.1em; font-weight: 700; color: var(--g); font-family: var(--mono); }
.ua-stat-key { font-size: .6em; color: var(--muted); margin-top: 2px; font-family: var(--mono); }
.ua-panels { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 16px; }
.ua-panel {
  background: var(--surface); border: 1px solid var(--border); border-radius: var(--r-sm);
  padding: 16px;
}
.ua-sub-title {
  font-size: .78em; font-weight: 600; color: var(--sub); margin-bottom: 12px;
  font-family: var(--mono); text-transform: uppercase; letter-spacing: .06em;
}
.ua-bar-item { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; }
.ua-bar-item:last-child { margin-bottom: 0; }
.ua-bar-label {
  min-width: 80px; font-size: .72em; color: var(--sub); font-family: var(--mono);
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}
.ua-bar-track {
  flex: 1; height: 8px; border-radius: 4px; background: rgba(255,255,255,.04);
  overflow: hidden;
}
.ua-bar-fill { height: 100%; border-radius: 4px; transition: width .5s; }
.ua-bar-pct { font-size: .65em; color: var(--muted); font-family: var(--mono); min-width: 65px; text-align: right; }

.ua-split-bar {
  display: flex; height: 14px; border-radius: 7px; overflow: hidden; margin-bottom: 8px;
  background: rgba(255,255,255,.04);
}
.ua-split-seg { height: 100%; transition: width .5s; }
.ua-split-legend {
  display: flex; gap: 16px; margin-bottom: 16px; font-size: .7em; color: var(--sub);
  font-family: var(--mono);
}
.ua-leg { display: flex; align-items: center; gap: 4px; }
.ua-dot { width: 8px; height: 8px; border-radius: 50%; display: inline-block; }

.ua-spark {
  display: flex; align-items: flex-end; gap: 2px; height: 60px; margin-bottom: 4px;
  padding: 0 2px;
}
.ua-spark-bar {
  flex: 1; border-radius: 3px 3px 0 0; min-width: 2px;
  background: linear-gradient(0deg, var(--g), var(--cyan)); opacity: .8;
  transition: all .2s;
}
.ua-spark-bar:hover { opacity: 1; transform: scaleY(1.05); }
.ua-spark-labels {
  display: flex; justify-content: space-between; font-size: .6em; color: var(--muted);
  font-family: var(--mono); margin-bottom: 16px;
}

/* ── Badges (multi-tier) ─────────────────── */
.bdg-cat { margin-bottom: 16px; }
.bdg-cat:last-child { margin-bottom: 0; }
.bdg-cat-title {
  font-size: .75em; font-weight: 600; color: var(--sub); text-transform: uppercase;
  letter-spacing: .08em; margin-bottom: 8px; padding-bottom: 4px;
  border-bottom: 1px solid var(--glass-border); font-family: var(--mono);
}
.bdg-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(105px, 1fr)); gap: 10px; }
.bdg {
  text-align: center; padding: 14px 8px; border-radius: var(--r-sm);
  border: 1px solid var(--border); cursor: default; transition: all .25s;
  position: relative; overflow: hidden;
}
.bdg:hover:not(.bdg-locked) { transform: translateY(-4px); }
.bdg-bronze {
  border-color: #92400e;
  background: linear-gradient(135deg, rgba(146,64,14,.12), rgba(146,64,14,.03));
}
.bdg-bronze:hover { box-shadow: 0 8px 24px rgba(146,64,14,.25); }
.bdg-silver {
  border-color: #6b7280;
  background: linear-gradient(135deg, rgba(156,163,175,.1), rgba(156,163,175,.03));
}
.bdg-silver:hover { box-shadow: 0 8px 24px rgba(156,163,175,.2); }
.bdg-gold {
  border-color: #d97706;
  background: linear-gradient(135deg, rgba(217,119,6,.12), rgba(251,191,36,.04));
}
.bdg-gold:hover { box-shadow: 0 8px 24px rgba(217,119,6,.25); }
.bdg-diamond {
  border-color: #06b6d4;
  background: linear-gradient(135deg, rgba(6,182,212,.1), rgba(6,182,212,.03));
}
.bdg-diamond:hover { box-shadow: 0 8px 24px rgba(6,182,212,.25); }
.bdg-legend {
  border-color: #a855f7;
  background: linear-gradient(135deg, rgba(168,85,247,.12), rgba(236,72,153,.06));
  box-shadow: 0 0 12px rgba(168,85,247,.15);
}
.bdg-legend:hover { box-shadow: 0 8px 28px rgba(168,85,247,.3); }
.bdg-locked { background: rgba(255,255,255,.015); opacity: .25; }
.bdg-icon { font-size: 1.8em; margin-bottom: 6px; }
.bdg-name { font-size: .64em; color: var(--sub); line-height: 1.3; margin-bottom: 4px; }
.bdg-stars { font-size: .6em; margin-bottom: 4px; }
.bdg-bar {
  height: 4px; border-radius: 2px; background: rgba(255,255,255,.06);
  overflow: hidden; margin: 0 4px 3px;
}
.bdg-fill {
  height: 100%; border-radius: 2px;
  background: linear-gradient(90deg, var(--g), var(--cyan)); transition: width .5s;
}
.bdg-tier { font-size: .55em; color: var(--muted); font-family: var(--mono); }

/* ── Personal Records ─────────────────────── */
.rec-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; }
.rec-card {
  text-align: center; padding: 20px 10px; background: var(--surface);
  border: 1px solid var(--border); border-radius: var(--r-sm); transition: all .25s;
}
.rec-card:hover { border-color: rgba(34,197,94,.25); transform: translateY(-3px); box-shadow: 0 4px 16px rgba(0,0,0,.15); }
.rec-icon { font-size: 1.8em; margin-bottom: 8px; }
.rec-val { font-size: 1.3em; font-weight: 700; color: var(--g); font-family: var(--mono); }
.rec-label { font-size: .7em; color: var(--muted); margin-top: 4px; }

/* ── Tasks ─────────────────────────────────── */
.tlist { display: flex; flex-direction: column; gap: 6px; }
.trow {
  display: flex; align-items: center; gap: 12px; padding: 12px 16px;
  background: var(--surface); border-radius: var(--r-sm); font-size: .84em;
  border: 1px solid var(--border); transition: all .2s;
}
.trow:hover { border-color: rgba(34,197,94,.2); transform: translateX(4px); }
.t-date { color: var(--muted); min-width: 82px; font-size: .8em; font-family: var(--mono); }
.t-desc { flex: 1; min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.t-xp { color: var(--g); font-weight: 700; white-space: nowrap; font-family: var(--mono); }
.t-cx {
  font-size: .65em; padding: 3px 10px; border-radius: 12px;
  text-transform: uppercase; font-weight: 600; font-family: var(--mono);
}
.cx-low { background: rgba(34,197,94,.12); color: #4ade80; }
.cx-medium { background: rgba(245,158,11,.12); color: #fbbf24; }
.cx-high { background: rgba(244,63,94,.12); color: #fb7185; }
.empty { color: var(--muted); text-align: center; padding: 24px; font-size: .9em; }

/* ── Leaderboard CTA ─────────────────────── */
.lb-cta { display: flex; gap: 24px; align-items: center; }
.lb-info { flex: 1; }
.lb-desc { color: var(--sub); font-size: .9em; margin-bottom: 14px; }
.lb-stats-row { display: flex; gap: 16px; }
.lb-stat {
  padding: 10px 16px; background: var(--surface);
  border: 1px solid var(--border); border-radius: var(--r-sm); text-align: center;
  flex: 1;
}
.lb-stat-val { display: block; font-size: 1em; font-weight: 700; color: var(--g); font-family: var(--mono); }
.lb-stat-key { display: block; font-size: .6em; color: var(--muted); margin-top: 2px; font-family: var(--mono); }
.lb-actions { flex-shrink: 0; }
.lb-btn {
  display: inline-block; padding: 14px 28px; border-radius: var(--r-sm);
  background: linear-gradient(135deg, var(--g), var(--g2));
  color: #fff; font-weight: 600; font-size: .92em; text-decoration: none;
  transition: all .25s; border: none; cursor: pointer;
  box-shadow: 0 4px 16px rgba(34,197,94,.25);
}
.lb-btn:hover {
  transform: translateY(-2px); box-shadow: 0 8px 24px rgba(34,197,94,.35);
  color: #fff;
}

/* Footer */
.foot {
  text-align: center; padding: 36px 0 16px; color: var(--muted);
  font-size: .72em; font-family: var(--mono);
}
.foot p + p { margin-top: 4px; }
.foot a { color: var(--g); }

/* ── Responsive ───────────────────────────── */
@media (max-width: 720px) {
  .hero { grid-template-columns: 1fr; text-align: center; gap: 16px; padding: 24px 20px; }
  .hero-left { justify-self: center; }
  .hero-stats { flex-direction: row; flex-wrap: wrap; justify-content: center; }
  .hs { min-width: 80px; }
  .q-row { grid-template-columns: 1fr; }
  .sk-group-cards { grid-template-columns: 1fr; }
  .rec-grid { grid-template-columns: repeat(2, 1fr); }
  .ua-stats { grid-template-columns: repeat(3, 1fr); }
  .ua-panels { grid-template-columns: 1fr; }
  .path-tasks { grid-template-columns: 1fr; }
  .lb-cta { flex-direction: column; text-align: center; }
  .lb-stats-row { flex-wrap: wrap; }
}
@media (max-width: 480px) {
  .shell { padding: 12px 14px 32px; }
  .nav { flex-wrap: wrap; gap: 8px; }
  .power-num { font-size: 2.4em; }
  .lg-bar { flex-wrap: wrap; }
  .lg-item { min-width: 50px; }
  .card { padding: 20px 16px; }
}

/* ── Animations ───────────────────────────── */
@keyframes fadeUp { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }
@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
@keyframes slideIn { from { opacity: 0; transform: translateX(-20px); } to { opacity: 1; transform: translateX(0); } }
.hero { animation: fadeUp .6s ease-out; }
.card { animation: fadeUp .5s ease-out backwards; }
.card:nth-child(1) { animation-delay: .08s; }
.card:nth-child(2) { animation-delay: .14s; }
.card:nth-child(3) { animation-delay: .2s; }
.card:nth-child(4) { animation-delay: .26s; }
.card:nth-child(5) { animation-delay: .32s; }
.card:nth-child(6) { animation-delay: .38s; }
.card:nth-child(7) { animation-delay: .44s; }
.card:nth-child(8) { animation-delay: .5s; }
.card:nth-child(9) { animation-delay: .56s; }
.card:nth-child(10) { animation-delay: .62s; }

/* ── Scrollbar ────────────────────────────── */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: var(--bg); }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: var(--muted); }

/* ── Selection ────────────────────────────── */
::selection { background: rgba(34,197,94,.3); color: var(--text); }
"""


def main():
    u = load_json(DATA_DIR / "user_stats.json")
    t = load_json(DATA_DIR / "tasks.json")
    c = load_json(DATA_DIR / "config.json")
    ci = load_json(DATA_DIR / "check_ins.json")

    quests_path = DATA_DIR / "daily_quests.json"
    q = load_json(quests_path) if quests_path.exists() else {"combo": {}, "challenge": {}, "streak": {}}

    analytics_path = DATA_DIR / "usage_analytics.json"
    a = load_json(analytics_path) if analytics_path.exists() else {}

    for lang in c["supported_languages"]:
        filename = "index.html" if lang == "en" else f"index_{lang}.html"
        html = generate_dashboard(u, t, c, ci, q, a, lang)
        with open(OUTPUT_DIR / filename, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"[generate] Written {filename}")

    with open(OUTPUT_DIR / "styles.css", "w", encoding="utf-8") as f:
        f.write(generate_css())
    print("[generate] Written styles.css")


if __name__ == "__main__":
    main()
