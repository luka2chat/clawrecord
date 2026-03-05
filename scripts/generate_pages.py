#!/usr/bin/env python3
"""
ClawRecord Dashboard Generator v2 — Hamster-style Command Center

Layout: Claw Power hero -> Daily quests -> Skill cards -> League -> Heatmap
        -> Multi-tier badges -> Personal records -> Recent activity
"""

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from utils import DATA_DIR, OUTPUT_DIR, get_text, load_json

OUTPUT_DIR.mkdir(exist_ok=True)


# ── Heatmap ────────────────────────────────────────────────────────

def build_heatmap(check_ins, lang):
    today = datetime.utcnow().date()
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

    def quest_card(title, inner, done, xp_reward):
        done_cls = " q-done" if done else " q-pulse"
        check = '<span class="q-check">\u2714</span>' if done else ""
        xp_tag = f'<span class="q-xp">+{xp_reward} XP</span>' if xp_reward else ""
        return (
            f'<div class="q-card{done_cls}">'
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

    now = datetime.utcnow()
    midnight = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    remaining = midnight - now
    hours_left = int(remaining.total_seconds() // 3600)
    mins_left = int((remaining.total_seconds() % 3600) // 60)
    timer = f'{ui.get("resets_in", "Resets in")} {hours_left}h {mins_left}m'

    return (
        f'<div class="q-row">'
        f'{quest_card(combo_name, combo_inner, combo_done, combo_xp)}'
        f'{quest_card(ch_name, ch_inner, ch_done, ch_xp)}'
        f'{quest_card(st_name, st_inner, st_done, 0)}'
        f'</div>'
        f'<div class="q-timer">\u23f0 {timer}</div>'
    )


# ── League Bar ─────────────────────────────────────────────────────

def build_league_bar(config, current_league_id, weekly_xp, lang):
    leagues = config["leagues"]
    items = []
    for lg in leagues:
        on = "on" if lg["id"] == current_league_id else ""
        name = get_text(lg["name"], lang)
        items.append(
            f'<div class="lg-item {on}">'
            f'<span class="lg-icon">{lg["icon"]}</span>'
            f'<span class="lg-name">{name}</span>'
            f'</div>'
        )
    return "".join(items)


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


# ── Dashboard HTML ─────────────────────────────────────────────────

def generate_dashboard(user_stats, tasks, config, check_ins, quests, lang):
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
    league_bar = build_league_bar(config, league.get("id", "bronze"), user_stats.get("weekly_xp", 0), lang)
    heatmap_html = build_heatmap(check_ins, lang)
    skill_cards_html = build_skill_cards(user_stats.get("skills", {}), config, lang)
    daily_quests_html = build_daily_quests(quests, config, lang)
    badges_html = build_badges(user_stats.get("badges", []), config, lang)
    records = user_stats.get("personal_records", {})
    records_html = build_records(records, config, lang)

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

    return f'''<!DOCTYPE html>
<html lang="{lang}">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{ui["title"]} \u2014 {user_stats["username"]}</title>
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
    <span class="nav-user">{user_stats["username"]}</span>
  </div>
  <div class="nav-r">
    <span class="pill">{league_conf["icon"]} {league_name}</span>
    {lang_links}
  </div>
</nav>

<header class="hero">
  <div class="hero-left">
    <div class="av-ring"><div class="av-inner">{user_stats.get("avatar", level_info["icon"])}</div></div>
    <div class="av-rank">{get_text(level_info["rank"], lang)}</div>
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
    <div class="hs"><span class="hs-val">\u26a1 {user_stats.get("weekly_xp", 0)}</span><span class="hs-key">{ui["weekly_xp"]}</span></div>
  </div>
</header>

<section class="card card-quests">
  <h2>\U0001f3af {ui.get("daily_quests", "Daily Quests")}</h2>
  {daily_quests_html}
</section>

<section class="card card-skills">
  <h2>\U0001f0cf {ui.get("skills_tree", "Skill Cards")}</h2>
  <div class="sk-wall">{skill_cards_html}</div>
</section>

<section class="card card-league">
  <h2>\U0001f3c6 {ui["league"]} <span class="dim">{ui["weekly_xp"]}: {user_stats.get("weekly_xp", 0)}</span></h2>
  <div class="lg-bar">{league_bar}</div>
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

<section class="card card-badges">
  <h2>\U0001f3c5 {ui["achievements"]} <span class="dim">{unlocked_count}/{total_badges}</span></h2>
  {badges_html}
</section>

<section class="card card-records">
  <h2>\U0001f947 {ui.get("personal_bests", "Personal Bests")}</h2>
  <div class="rec-grid">{records_html}</div>
</section>

<section class="card card-tasks">
  <h2>\U0001f4cb {ui["recent_tasks"]}</h2>
  {tasks_html}
</section>

<footer class="foot">
  <p>{ui["last_updated"]}: {datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")}</p>
  <p>Powered by <a href="https://github.com/openclaw/openclaw">OpenClaw</a> &amp; <a href="https://github.com/luka2chat/clawrecord">ClawRecord</a></p>
</footer>

</div>
</body>
</html>'''


# ── CSS ────────────────────────────────────────────────────────────

def generate_css():
    return """\
:root {
  --bg: #050a18;
  --surface: #0a1128;
  --card: #0f1a35;
  --card-hover: #142040;
  --border: #172554;
  --border-glow: rgba(34,197,94,.2);
  --g: #22c55e;
  --g-dim: rgba(34,197,94,.1);
  --g-glow: rgba(34,197,94,.35);
  --indigo: #6366f1;
  --cyan: #06b6d4;
  --text: #f1f5f9;
  --sub: #94a3b8;
  --muted: #475569;
  --danger: #f43f5e;
  --warn: #f59e0b;
  --r: 16px;
  --r-sm: 10px;
  --font: 'Space Grotesk', system-ui, sans-serif;
  --mono: 'JetBrains Mono', ui-monospace, monospace;
}
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
body {
  font-family: var(--font); background: var(--bg); color: var(--text);
  line-height: 1.6; min-height: 100vh; overflow-x: hidden;
}
a { color: var(--g); text-decoration: none; transition: color .2s; }
a:hover { color: var(--cyan); }

.noise {
  position: fixed; inset: 0; z-index: 9999; pointer-events: none; opacity: .035;
  background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='.85' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E");
  background-repeat: repeat; background-size: 200px 200px;
}
.shell { max-width: 960px; margin: 0 auto; padding: 20px 24px 40px; }

/* Nav */
.nav {
  display: flex; justify-content: space-between; align-items: center;
  padding: 14px 0; margin-bottom: 28px; border-bottom: 1px solid var(--border);
}
.nav-l { display: flex; align-items: center; gap: 8px; }
.brand {
  font-weight: 700; font-size: 1.15em; letter-spacing: -.02em;
  background: linear-gradient(135deg, var(--g), var(--cyan));
  -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;
}
.sep { color: var(--muted); }
.nav-user { color: var(--sub); font-size: .9em; }
.nav-r { display: flex; align-items: center; gap: 10px; }
.pill {
  background: var(--card); padding: 5px 14px; border-radius: 20px;
  font-size: .82em; border: 1px solid var(--border); font-family: var(--mono); font-weight: 500;
}
.lang-btn {
  color: var(--sub); padding: 4px 12px; border: 1px solid var(--border);
  border-radius: var(--r-sm); font-size: .78em; font-weight: 500;
  transition: all .2s; font-family: var(--mono);
}
.lang-btn.active {
  background: var(--g); color: #fff; border-color: var(--g);
  box-shadow: 0 0 12px var(--g-glow);
}
.lang-btn:hover:not(.active) { border-color: var(--g); color: var(--g); }

/* Hero — Claw Power front and center */
.hero {
  display: grid; grid-template-columns: auto 1fr auto;
  gap: 28px; align-items: center;
  background: linear-gradient(135deg, var(--card) 0%, rgba(99,102,241,.06) 100%);
  padding: 32px; border-radius: var(--r); border: 1px solid var(--border);
  margin-bottom: 24px; position: relative; overflow: hidden;
}
.hero::before {
  content: ''; position: absolute; inset: 0;
  background: radial-gradient(ellipse at 30% 50%, rgba(34,197,94,.1) 0%, transparent 60%);
  pointer-events: none;
}
.hero-left { text-align: center; position: relative; z-index: 1; }
.av-ring {
  width: 96px; height: 96px; border-radius: 50%;
  background: conic-gradient(from 0deg, var(--g), var(--cyan), var(--indigo), var(--g));
  padding: 3px; animation: spin 8s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }
.av-inner {
  width: 100%; height: 100%; border-radius: 50%;
  background: var(--card); display: flex; align-items: center; justify-content: center;
  font-size: 42px;
}
.av-rank {
  margin-top: 6px; font-size: .72em; font-weight: 600; letter-spacing: .06em;
  text-transform: uppercase; color: var(--g); font-family: var(--mono);
}

.hero-center { min-width: 0; position: relative; z-index: 1; }
.power-label {
  font-size: .75em; font-weight: 600; text-transform: uppercase;
  letter-spacing: .1em; color: var(--sub); font-family: var(--mono);
}
.power-num {
  font-size: 3.2em; font-weight: 700; line-height: 1.05;
  letter-spacing: -.03em; font-family: var(--mono);
  background: linear-gradient(135deg, var(--g), var(--cyan));
  -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;
}
.power-delta {
  font-size: .85em; color: var(--g); font-family: var(--mono); margin-bottom: 12px;
}
.hero-mult {
  display: inline-block; background: rgba(245,158,11,.15); color: var(--warn);
  padding: 1px 8px; border-radius: 10px; font-size: .85em; font-weight: 600;
  margin-left: 6px;
}
.xp-track {
  position: relative; height: 22px; border-radius: 11px;
  background: var(--surface); overflow: hidden; border: 1px solid var(--border);
}
.xp-fill {
  height: 100%; border-radius: 11px;
  background: linear-gradient(90deg, #15803d, var(--g), #4ade80);
  box-shadow: 0 0 16px var(--g-glow); transition: width .8s cubic-bezier(.4,0,.2,1);
}
.xp-label {
  position: absolute; inset: 0; display: flex; align-items: center; justify-content: center;
  font-size: .7em; font-weight: 600; color: #fff; font-family: var(--mono);
  text-shadow: 0 1px 3px rgba(0,0,0,.6);
}

.hero-stats { display: flex; flex-direction: column; gap: 8px; position: relative; z-index: 1; }
.hs {
  text-align: center; padding: 8px 16px; min-width: 100px;
  background: rgba(255,255,255,.03); border-radius: var(--r-sm); border: 1px solid var(--border);
}
.hs-val { display: block; font-size: 1.15em; font-weight: 700; color: var(--g); font-family: var(--mono); }
.hs-val small { font-size: .7em; color: var(--sub); font-weight: 400; }
.hs-key { display: block; font-size: .65em; color: var(--muted); margin-top: 1px; }
.freeze { font-size: .65em; vertical-align: middle; margin-left: 2px; }

/* Cards */
.card {
  background: var(--card); border: 1px solid var(--border); border-radius: var(--r);
  padding: 24px; margin-bottom: 20px; transition: border-color .3s;
}
.card:hover { border-color: var(--border-glow); }
.card h2 {
  font-size: 1em; font-weight: 600; margin-bottom: 18px;
  display: flex; align-items: center; gap: 8px; letter-spacing: -.01em;
}
.dim { color: var(--muted); font-weight: 400; font-size: .85em; margin-left: auto; }

/* ── Daily Quests ─────────────────────────── */
.q-row { display: grid; grid-template-columns: repeat(3, 1fr); gap: 14px; }
.q-card {
  background: var(--surface); border: 1px solid var(--border); border-radius: var(--r-sm);
  padding: 16px; transition: all .3s;
}
.q-card.q-done { border-color: var(--g); background: linear-gradient(135deg, rgba(34,197,94,.06), rgba(6,182,212,.03)); }
.q-card.q-pulse { animation: pulse 2s ease-in-out infinite; }
@keyframes pulse { 0%,100% { box-shadow: none; } 50% { box-shadow: 0 0 16px rgba(34,197,94,.12); } }
.q-hdr {
  font-weight: 600; font-size: .88em; margin-bottom: 10px;
  display: flex; align-items: center; gap: 6px; flex-wrap: wrap;
}
.q-check { color: var(--g); font-weight: 700; }
.q-xp {
  margin-left: auto; font-size: .78em; font-family: var(--mono);
  color: var(--g); font-weight: 600;
}
.q-desc { color: var(--sub); font-size: .8em; margin-bottom: 8px; }
.q-pills { display: flex; flex-wrap: wrap; gap: 4px; margin-bottom: 8px; }
.q-pill {
  font-size: .7em; padding: 2px 8px; border-radius: 12px;
  background: rgba(255,255,255,.04); border: 1px solid var(--border);
  color: var(--muted); font-family: var(--mono);
}
.q-pill.active { background: rgba(34,197,94,.12); border-color: var(--g); color: var(--g); }
.q-bar {
  height: 6px; border-radius: 3px; background: rgba(255,255,255,.06); overflow: hidden;
  margin-bottom: 4px;
}
.q-fill {
  height: 100%; border-radius: 3px;
  background: linear-gradient(90deg, var(--g), var(--cyan));
  transition: width .5s;
}
.q-stat { font-size: .7em; color: var(--muted); font-family: var(--mono); text-align: right; }
.q-timer {
  text-align: center; margin-top: 12px; font-size: .78em;
  color: var(--warn); font-family: var(--mono); font-weight: 500;
}

/* ── Skill Cards ──────────────────────────── */
.sk-wall { display: flex; flex-direction: column; gap: 18px; }
.sk-group-hdr {
  font-size: .78em; font-weight: 600; color: var(--sub); text-transform: uppercase;
  letter-spacing: .08em; margin-bottom: 10px; font-family: var(--mono);
  padding-bottom: 4px; border-bottom: 1px solid rgba(148,163,184,.08);
}
.sk-group-cards { display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; }
.sk-card {
  background: var(--surface); border: 1px solid var(--border); border-radius: var(--r-sm);
  padding: 14px; display: grid; grid-template-columns: auto 1fr; gap: 8px 12px;
  align-items: center; transition: all .25s;
}
.sk-card:hover { border-color: rgba(34,197,94,.25); transform: translateY(-2px); }
.sk-card.maxed { border-color: rgba(245,158,11,.3); }
.sk-icon { font-size: 1.8em; grid-row: span 2; }
.sk-info { display: flex; justify-content: space-between; align-items: baseline; }
.sk-name { font-weight: 600; font-size: .88em; }
.sk-lvl { font-family: var(--mono); font-weight: 700; color: var(--g); font-size: .85em; }
.sk-max { font-weight: 400; color: var(--muted); font-size: .8em; }
.sk-bar {
  grid-column: 2; height: 5px; border-radius: 3px; background: rgba(255,255,255,.06);
  overflow: hidden;
}
.sk-fill {
  height: 100%; border-radius: 3px;
  background: linear-gradient(90deg, var(--g), var(--cyan)); transition: width .5s;
}
.sk-pwr {
  grid-column: 2; font-size: .7em; color: var(--sub); font-family: var(--mono);
  text-align: right;
}

/* ── League Bar ───────────────────────────── */
.lg-bar { display: flex; gap: 4px; overflow-x: auto; }
.lg-item {
  flex: 1; min-width: 60px; text-align: center; padding: 12px 4px;
  border-radius: var(--r-sm); background: var(--surface);
  border: 1px solid var(--border); opacity: .4; transition: all .25s;
}
.lg-item.on {
  opacity: 1; border-color: var(--g);
  box-shadow: 0 0 14px var(--g-dim), inset 0 0 20px var(--g-dim);
  background: linear-gradient(135deg, rgba(34,197,94,.08), rgba(6,182,212,.04));
}
.lg-icon { display: block; font-size: 1.4em; }
.lg-name { display: block; font-size: .6em; color: var(--sub); margin-top: 3px; font-family: var(--mono); }

/* ── Heatmap ──────────────────────────────── */
.hm-grid {
  display: grid; grid-template-rows: repeat(7, 1fr);
  grid-auto-flow: column; grid-auto-columns: 1fr; gap: 3px;
}
.hm-cell { aspect-ratio: 1; border-radius: 3px; min-width: 0; transition: transform .1s; }
.hm-cell:hover { transform: scale(1.4); z-index: 1; }
.hm-0 { background: #0f172a; }
.hm-1 { background: #064e3b; }
.hm-2 { background: #047857; }
.hm-3 { background: #10b981; box-shadow: 0 0 4px rgba(16,185,129,.3); }
.hm-4 { background: #34d399; box-shadow: 0 0 6px rgba(52,211,153,.4); }
.hm-legend {
  display: flex; align-items: center; gap: 4px; justify-content: flex-end;
  margin-top: 10px; font-size: .7em; color: var(--muted); font-family: var(--mono);
}
.hm-legend .hm-cell { width: 12px; height: 12px; display: inline-block; border-radius: 2px; }

/* ── Badges (multi-tier) ─────────────────── */
.bdg-cat { margin-bottom: 16px; }
.bdg-cat:last-child { margin-bottom: 0; }
.bdg-cat-title {
  font-size: .75em; font-weight: 600; color: var(--sub); text-transform: uppercase;
  letter-spacing: .08em; margin-bottom: 8px; padding-bottom: 4px;
  border-bottom: 1px solid rgba(148,163,184,.08); font-family: var(--mono);
}
.bdg-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(100px, 1fr)); gap: 8px; }
.bdg {
  text-align: center; padding: 12px 8px; border-radius: var(--r-sm);
  border: 1px solid var(--border); cursor: default; transition: all .2s;
}
.bdg:hover:not(.bdg-locked) { transform: translateY(-3px); }
.bdg-bronze { border-color: #92400e; background: linear-gradient(135deg, rgba(146,64,14,.1), transparent); }
.bdg-bronze:hover { box-shadow: 0 6px 18px rgba(146,64,14,.2); }
.bdg-silver { border-color: #6b7280; background: linear-gradient(135deg, rgba(107,114,128,.1), transparent); }
.bdg-silver:hover { box-shadow: 0 6px 18px rgba(107,114,128,.2); }
.bdg-gold { border-color: #d97706; background: linear-gradient(135deg, rgba(217,119,6,.1), transparent); }
.bdg-gold:hover { box-shadow: 0 6px 18px rgba(217,119,6,.2); }
.bdg-diamond { border-color: #06b6d4; background: linear-gradient(135deg, rgba(6,182,212,.08), transparent); }
.bdg-diamond:hover { box-shadow: 0 6px 18px rgba(6,182,212,.2); }
.bdg-legend {
  border-color: #a855f7;
  background: linear-gradient(135deg, rgba(168,85,247,.1), rgba(236,72,153,.06));
  box-shadow: 0 0 10px rgba(168,85,247,.15);
}
.bdg-legend:hover { box-shadow: 0 6px 24px rgba(168,85,247,.3); }
.bdg-locked { background: rgba(255,255,255,.02); opacity: .3; }
.bdg-icon { font-size: 1.6em; margin-bottom: 4px; }
.bdg-name { font-size: .62em; color: var(--sub); line-height: 1.3; margin-bottom: 3px; }
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
  text-align: center; padding: 18px 10px; background: var(--surface);
  border: 1px solid var(--border); border-radius: var(--r-sm); transition: all .25s;
}
.rec-card:hover { border-color: rgba(34,197,94,.25); transform: translateY(-2px); }
.rec-icon { font-size: 1.6em; margin-bottom: 6px; }
.rec-val { font-size: 1.2em; font-weight: 700; color: var(--g); font-family: var(--mono); }
.rec-label { font-size: .7em; color: var(--muted); margin-top: 2px; }

/* ── Tasks ─────────────────────────────────── */
.tlist { display: flex; flex-direction: column; gap: 6px; }
.trow {
  display: flex; align-items: center; gap: 12px; padding: 10px 14px;
  background: var(--surface); border-radius: var(--r-sm); font-size: .84em;
  border: 1px solid var(--border); transition: border-color .2s;
}
.trow:hover { border-color: rgba(34,197,94,.2); }
.t-date { color: var(--muted); min-width: 82px; font-size: .8em; font-family: var(--mono); }
.t-desc { flex: 1; min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.t-xp { color: var(--g); font-weight: 700; white-space: nowrap; font-family: var(--mono); }
.t-cx {
  font-size: .65em; padding: 2px 10px; border-radius: 12px;
  text-transform: uppercase; font-weight: 600; font-family: var(--mono);
}
.cx-low { background: rgba(34,197,94,.12); color: #4ade80; }
.cx-medium { background: rgba(245,158,11,.12); color: #fbbf24; }
.cx-high { background: rgba(244,63,94,.12); color: #fb7185; }
.empty { color: var(--muted); text-align: center; padding: 24px; font-size: .9em; }

/* Footer */
.foot {
  text-align: center; padding: 32px 0 16px; color: var(--muted);
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
}
@media (max-width: 480px) {
  .shell { padding: 12px 14px 32px; }
  .nav { flex-wrap: wrap; gap: 8px; }
  .power-num { font-size: 2.2em; }
  .lg-bar { flex-wrap: wrap; }
  .lg-item { min-width: 50px; }
}

/* Animations */
@keyframes fadeUp { from { opacity: 0; transform: translateY(16px); } to { opacity: 1; transform: translateY(0); } }
.hero { animation: fadeUp .6s ease-out; }
.card { animation: fadeUp .6s ease-out backwards; }
.card:nth-child(1) { animation-delay: .1s; }
.card:nth-child(2) { animation-delay: .15s; }
.card:nth-child(3) { animation-delay: .2s; }
.card:nth-child(4) { animation-delay: .25s; }
.card:nth-child(5) { animation-delay: .3s; }
.card:nth-child(6) { animation-delay: .35s; }
.card:nth-child(7) { animation-delay: .4s; }
"""


def main():
    u = load_json(DATA_DIR / "user_stats.json")
    t = load_json(DATA_DIR / "tasks.json")
    c = load_json(DATA_DIR / "config.json")
    ci = load_json(DATA_DIR / "check_ins.json")

    quests_path = DATA_DIR / "daily_quests.json"
    q = load_json(quests_path) if quests_path.exists() else {"combo": {}, "challenge": {}, "streak": {}}

    for lang in c["supported_languages"]:
        filename = "index.html" if lang == "en" else f"index_{lang}.html"
        html = generate_dashboard(u, t, c, ci, q, lang)
        with open(OUTPUT_DIR / filename, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"[generate] Written {filename}")

    with open(OUTPUT_DIR / "styles.css", "w", encoding="utf-8") as f:
        f.write(generate_css())
    print("[generate] Written styles.css")


if __name__ == "__main__":
    main()
