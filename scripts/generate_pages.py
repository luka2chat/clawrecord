#!/usr/bin/env python3
"""
ClawRecord Dashboard Generator

Aesthetic direction: Cyberpunk Command Center
DFII: 16 (Impact 4 + Fit 5 + Feasibility 4 + Performance 5 - Risk 2)

Fonts: Space Grotesk (display) + JetBrains Mono (data)
Palette: Deep navy + emerald primary + indigo accent
Texture: SVG noise overlay, gradient glow borders, layered translucency
"""

import json
import math
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from utils import DATA_DIR, OUTPUT_DIR, get_text, load_json

OUTPUT_DIR.mkdir(exist_ok=True)


# ── SVG Radar Chart ─────────────────────────────────────────────────

def build_radar_svg(skills_data, config_skills, lang):
    n = len(config_skills)
    if n < 3:
        return ""
    cx, cy, r = 140, 140, 105
    angle_step = 2 * math.pi / n

    grid_lines = []
    for ring in [0.25, 0.5, 0.75, 1.0]:
        points = []
        for i in range(n):
            a = -math.pi / 2 + i * angle_step
            px = cx + r * ring * math.cos(a)
            py = cy + r * ring * math.sin(a)
            points.append(f"{px:.1f},{py:.1f}")
        opacity = "0.08" if ring < 1.0 else "0.2"
        grid_lines.append(
            f'<polygon points="{" ".join(points)}" '
            f'fill="none" stroke="rgba(148,163,184,{opacity})" stroke-width="1"/>'
        )

    axis_lines = []
    labels = []
    data_points = []
    for i, skill in enumerate(config_skills):
        a = -math.pi / 2 + i * angle_step
        ex = cx + r * math.cos(a)
        ey = cy + r * math.sin(a)
        axis_lines.append(
            f'<line x1="{cx}" y1="{cy}" x2="{ex:.1f}" y2="{ey:.1f}" '
            f'stroke="rgba(148,163,184,0.08)" stroke-width="1"/>'
        )

        lx = cx + (r + 32) * math.cos(a)
        ly = cy + (r + 32) * math.sin(a)
        anchor = "middle"
        if lx < cx - 10:
            anchor = "end"
        elif lx > cx + 10:
            anchor = "start"
        label = get_text(skill["name"], lang)
        level = skills_data.get(skill["id"], 0)
        labels.append(
            f'<text x="{lx:.1f}" y="{ly:.1f}" text-anchor="{anchor}" '
            f'dominant-baseline="middle" fill="#94a3b8" '
            f'font-family="Space Grotesk,sans-serif" font-size="11" font-weight="500">'
            f'{skill["icon"]} {label} ({level})</text>'
        )

        ratio = min(level / skill["max_level"], 1.0) if skill["max_level"] > 0 else 0
        dx = cx + r * ratio * math.cos(a)
        dy = cy + r * ratio * math.sin(a)
        data_points.append(f"{dx:.1f},{dy:.1f}")

    polygon = (
        f'<polygon points="{" ".join(data_points)}" '
        f'fill="rgba(34,197,94,0.15)" stroke="url(#radarGrad)" stroke-width="2.5"/>'
    )
    dots = "".join(
        f'<circle cx="{p.split(",")[0]}" cy="{p.split(",")[1]}" r="3.5" '
        f'fill="#22c55e" filter="url(#glow)"/>'
        for p in data_points
    )

    return f'''<svg viewBox="0 0 280 280" class="radar-chart">
    <defs>
      <linearGradient id="radarGrad" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" stop-color="#22c55e"/>
        <stop offset="100%" stop-color="#06b6d4"/>
      </linearGradient>
      <filter id="glow"><feGaussianBlur stdDeviation="2" result="g"/>
        <feMerge><feMergeNode in="g"/><feMergeNode in="SourceGraphic"/></feMerge>
      </filter>
    </defs>
    {"".join(grid_lines)}
    {"".join(axis_lines)}
    {polygon}
    {dots}
    {"".join(labels)}
    </svg>'''


# ── Heatmap ─────────────────────────────────────────────────────────

def build_heatmap(check_ins, lang):
    today = datetime.utcnow().date()
    start = today - timedelta(days=90)
    weekday_offset = start.weekday()  # Mon=0

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
            f'style="grid-row:{row + 1};grid-column:{col + 1}" '
            f'title="{ds}: {xp} XP"></div>'
        )
    return "".join(cells)


# ── Dashboard HTML ──────────────────────────────────────────────────

def generate_dashboard(user_stats, tasks, config, check_ins, lang):
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

    radar_svg = build_radar_svg(user_stats.get("skills", {}), config["skills"], lang)
    heatmap_html = build_heatmap(check_ins, lang)

    # Achievements grouped by category
    unlocked_ids = {b["id"] for b in user_stats.get("badges", [])}
    unlocked_count = len(unlocked_ids)
    total_badges = len(config["badges"])

    badges_by_cat = {}
    for badge in config["badges"]:
        cat = badge.get("category", "other")
        badges_by_cat.setdefault(cat, []).append(badge)

    cat_labels = {
        "milestone": {"en": "Milestones", "zh": "\u91cc\u7a0b\u7891"},
        "streak": {"en": "Streaks", "zh": "\u8fde\u7eed\u7eaa\u5f55"},
        "skill": {"en": "Skills", "zh": "\u6280\u80fd"},
        "tool": {"en": "Tools", "zh": "\u5de5\u5177"},
        "efficiency": {"en": "Efficiency", "zh": "\u6548\u7387"},
        "time": {"en": "Time", "zh": "\u65f6\u95f4"},
        "special": {"en": "Special", "zh": "\u7279\u6b8a"},
        "other": {"en": "Other", "zh": "\u5176\u4ed6"},
    }

    badges_html_sections = []
    for cat, cat_badges in badges_by_cat.items():
        cat_name = get_text(cat_labels.get(cat, {"en": cat, "zh": cat}), lang)
        items = []
        for badge in cat_badges:
            is_unlocked = badge["id"] in unlocked_ids
            cls = "badge unlocked" if is_unlocked else "badge locked"
            name = get_text(badge["name"], lang)
            desc = get_text(badge["description"], lang)
            icon = badge["icon"] if is_unlocked else "&#x1f512;"
            items.append(
                f'<div class="{cls}" title="{desc}">'
                f'<span class="b-icon">{icon}</span>'
                f'<span class="b-name">{name}</span>'
                f'</div>'
            )
        badges_html_sections.append(
            f'<div class="badge-cat">'
            f'<h3 class="cat-title">{cat_name}</h3>'
            f'<div class="badge-row">{"".join(items)}</div>'
            f'</div>'
        )
    badges_html = "".join(badges_html_sections)

    # Recent tasks
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

    streak_freeze = ""
    sf = user_stats.get("streak_freezes", 0)
    if sf > 0:
        streak_freeze = f' <span class="freeze">&#x1f9ca; x{sf}</span>'

    xp_display = f"{user_stats['xp']:,}"
    next_xp_display = f"{next_level['xp_required']:,}" if next_level else xp_display

    # League tiers
    tiers_html = "".join(
        f'<div class="tier {"on" if lg["id"] == league.get("id") else ""}">'
        f'<span class="tier-icon">{lg["icon"]}</span>'
        f'<span class="tier-name">{get_text(lg["name"], lang)}</span>'
        f'<span class="tier-req">{lg["min_weekly_xp"]}+</span>'
        f'</div>'
        for lg in config["leagues"]
    )

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
    <div class="hero-avatar">
      <div class="av-ring">
        <div class="av-inner">{user_stats.get("avatar", level_info["icon"])}</div>
      </div>
      <div class="av-rank">{get_text(level_info["rank"], lang)}</div>
    </div>
    <div class="hero-body">
      <h1 class="hero-name">{user_stats["username"]}</h1>
      <div class="hero-sub">Lv.{user_stats["level"]} &middot; {get_text(level_info["rank"], lang)}</div>
      <div class="xp-track">
        <div class="xp-fill" style="width:{xp_progress:.1f}%"></div>
        <span class="xp-label">{xp_display} / {next_xp_display} XP</span>
      </div>
    </div>
    <div class="hero-stats">
      <div class="hs"><span class="hs-val">{user_stats["level"]}</span><span class="hs-key">{ui["level"]}</span></div>
      <div class="hs"><span class="hs-val">\U0001f525 {user_stats["streak"]}</span>{streak_freeze}<span class="hs-key">{ui["streak"]}</span></div>
      <div class="hs"><span class="hs-val">\u2764\ufe0f {user_stats["hp"]}<small>/{user_stats["max_hp"]}</small></span><span class="hs-key">{ui["hp"]}</span></div>
      <div class="hs"><span class="hs-val">\u26a1 {user_stats.get("weekly_xp", 0)}</span><span class="hs-key">{ui["weekly_xp"]}</span></div>
    </div>
  </header>

  <div class="grid2">
    <section class="card card-skills">
      <h2>{ui["skills_tree"]}</h2>
      <div class="radar-box">{radar_svg}</div>
    </section>
    <section class="card card-league">
      <h2>{ui["league"]}</h2>
      <div class="league-hero">
        <span class="l-icon">{league_conf["icon"]}</span>
        <span class="l-name">{league_name}</span>
        <span class="l-sub">{ui["weekly_xp"]}: <strong>{user_stats.get("weekly_xp", 0)}</strong></span>
      </div>
      <div class="tiers">{tiers_html}</div>
    </section>
  </div>

  <section class="card card-heat">
    <h2>{ui["heatmap"]}</h2>
    <div class="hm-grid">{heatmap_html}</div>
    <div class="hm-legend">
      <span>{ui["less"]}</span>
      <div class="hm-cell hm-0"></div><div class="hm-cell hm-1"></div><div class="hm-cell hm-2"></div><div class="hm-cell hm-3"></div><div class="hm-cell hm-4"></div>
      <span>{ui["more"]}</span>
    </div>
  </section>

  <section class="card card-badges">
    <h2>{ui["achievements"]} <span class="dim">{unlocked_count}/{total_badges}</span></h2>
    {badges_html}
  </section>

  <section class="card card-tasks">
    <h2>{ui["recent_tasks"]}</h2>
    {tasks_html}
  </section>

  <footer class="foot">
    <p>{ui["last_updated"]}: {datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")}</p>
    <p>Powered by <a href="https://github.com/openclaw/openclaw">OpenClaw</a> &amp; <a href="https://github.com/luka2chat/clawrecord">ClawRecord</a></p>
  </footer>
</div>

</body>
</html>'''


# ── CSS ─────────────────────────────────────────────────────────────

def generate_css():
    return """\
/* ClawRecord — Cyberpunk Command Center
   Fonts: Space Grotesk + JetBrains Mono
   Palette: Deep navy #050a18, emerald #22c55e, indigo #6366f1 */

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
  font-family: var(--font);
  background: var(--bg);
  color: var(--text);
  line-height: 1.6;
  min-height: 100vh;
  overflow-x: hidden;
}

a { color: var(--g); text-decoration: none; transition: color .2s; }
a:hover { color: var(--cyan); }

/* Noise overlay */
.noise {
  position: fixed; inset: 0; z-index: 9999; pointer-events: none;
  opacity: .035;
  background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='.85' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E");
  background-repeat: repeat;
  background-size: 200px 200px;
}

.shell {
  max-width: 940px;
  margin: 0 auto;
  padding: 20px 24px 40px;
}

/* ── Nav ────────────────────────────────────────── */
.nav {
  display: flex; justify-content: space-between; align-items: center;
  padding: 14px 0; margin-bottom: 28px;
  border-bottom: 1px solid var(--border);
}
.nav-l { display: flex; align-items: center; gap: 8px; }
.brand {
  font-weight: 700; font-size: 1.15em; letter-spacing: -.02em;
  background: linear-gradient(135deg, var(--g), var(--cyan));
  -webkit-background-clip: text; -webkit-text-fill-color: transparent;
  background-clip: text;
}
.sep { color: var(--muted); }
.nav-user { color: var(--sub); font-size: .9em; }
.nav-r { display: flex; align-items: center; gap: 10px; }
.pill {
  background: var(--card); padding: 5px 14px; border-radius: 20px;
  font-size: .82em; border: 1px solid var(--border);
  font-family: var(--mono); font-weight: 500;
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

/* ── Hero ───────────────────────────────────────── */
.hero {
  display: grid;
  grid-template-columns: auto 1fr auto;
  gap: 28px;
  align-items: center;
  background: linear-gradient(135deg, var(--card) 0%, rgba(99,102,241,.06) 100%);
  padding: 32px;
  border-radius: var(--r);
  border: 1px solid var(--border);
  margin-bottom: 24px;
  position: relative;
  overflow: hidden;
}
.hero::before {
  content: '';
  position: absolute; inset: 0;
  background: radial-gradient(ellipse at 20% 50%, rgba(34,197,94,.08) 0%, transparent 60%);
  pointer-events: none;
}

.av-ring {
  width: 96px; height: 96px; border-radius: 50%;
  background: conic-gradient(from 0deg, var(--g), var(--cyan), var(--indigo), var(--g));
  padding: 3px;
  animation: spin 8s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }
.av-inner {
  width: 100%; height: 100%; border-radius: 50%;
  background: var(--card);
  display: flex; align-items: center; justify-content: center;
  font-size: 42px;
}
.av-rank {
  text-align: center; margin-top: 6px;
  font-size: .72em; font-weight: 600; letter-spacing: .06em;
  text-transform: uppercase; color: var(--g);
  font-family: var(--mono);
}

.hero-body { min-width: 0; }
.hero-name {
  font-size: 2em; font-weight: 700; letter-spacing: -.03em;
  line-height: 1.1; margin-bottom: 2px;
}
.hero-sub { color: var(--sub); font-size: .88em; margin-bottom: 14px; font-family: var(--mono); }

.xp-track {
  position: relative; height: 22px; border-radius: 11px;
  background: var(--surface); overflow: hidden;
  border: 1px solid var(--border);
}
.xp-fill {
  height: 100%; border-radius: 11px;
  background: linear-gradient(90deg, #15803d, var(--g), #4ade80);
  box-shadow: 0 0 16px var(--g-glow);
  transition: width .8s cubic-bezier(.4,0,.2,1);
}
.xp-label {
  position: absolute; inset: 0;
  display: flex; align-items: center; justify-content: center;
  font-size: .7em; font-weight: 600; color: #fff;
  font-family: var(--mono);
  text-shadow: 0 1px 3px rgba(0,0,0,.6);
}

.hero-stats {
  display: flex; flex-direction: column; gap: 8px;
}
.hs {
  text-align: center; padding: 8px 16px; min-width: 100px;
  background: rgba(255,255,255,.03); border-radius: var(--r-sm);
  border: 1px solid var(--border);
}
.hs-val {
  display: block; font-size: 1.15em; font-weight: 700;
  color: var(--g); font-family: var(--mono);
}
.hs-val small { font-size: .7em; color: var(--sub); font-weight: 400; }
.hs-key { display: block; font-size: .65em; color: var(--muted); margin-top: 1px; }
.freeze { font-size: .65em; vertical-align: middle; margin-left: 2px; }

/* ── Cards ──────────────────────────────────────── */
.card {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: var(--r);
  padding: 24px;
  margin-bottom: 20px;
  transition: border-color .3s;
}
.card:hover { border-color: var(--border-glow); }
.card h2 {
  font-size: 1em; font-weight: 600; margin-bottom: 18px;
  display: flex; align-items: center; gap: 8px;
  letter-spacing: -.01em;
}
.dim { color: var(--muted); font-weight: 400; font-size: .85em; margin-left: auto; }

.grid2 { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }

/* ── Radar ──────────────────────────────────────── */
.radar-box { display: flex; justify-content: center; padding: 4px 0; }
.radar-chart { width: 100%; max-width: 280px; height: auto; }

/* ── League ─────────────────────────────────────── */
.league-hero { text-align: center; padding: 10px 0 18px; }
.l-icon { font-size: 3em; display: block; filter: drop-shadow(0 0 10px rgba(255,255,255,.15)); }
.l-name { font-size: 1.15em; font-weight: 600; display: block; margin: 4px 0; }
.l-sub { font-size: .82em; color: var(--sub); font-family: var(--mono); }
.l-sub strong { color: var(--g); }

.tiers { display: flex; gap: 6px; }
.tier {
  flex: 1; text-align: center; padding: 10px 4px;
  border-radius: var(--r-sm);
  background: var(--surface); border: 1px solid var(--border);
  opacity: .45; transition: all .25s;
}
.tier.on {
  opacity: 1; border-color: var(--g);
  box-shadow: 0 0 12px var(--g-dim), inset 0 0 20px var(--g-dim);
}
.tier-icon { display: block; font-size: 1.3em; }
.tier-name { display: block; font-size: .6em; color: var(--sub); margin-top: 2px; }
.tier-req { display: block; font-size: .55em; color: var(--muted); font-family: var(--mono); }

/* ── Heatmap ────────────────────────────────────── */
.hm-grid {
  display: grid;
  grid-template-rows: repeat(7, 1fr);
  grid-auto-flow: column;
  grid-auto-columns: 1fr;
  gap: 3px;
}
.hm-cell { aspect-ratio: 1; border-radius: 3px; min-width: 0; transition: transform .1s; }
.hm-cell:hover { transform: scale(1.4); z-index: 1; }
.hm-0 { background: #0f172a; }
.hm-1 { background: #064e3b; }
.hm-2 { background: #047857; }
.hm-3 { background: #10b981; box-shadow: 0 0 4px rgba(16,185,129,.3); }
.hm-4 { background: #34d399; box-shadow: 0 0 6px rgba(52,211,153,.4); }

.hm-legend {
  display: flex; align-items: center; gap: 4px;
  justify-content: flex-end; margin-top: 10px;
  font-size: .7em; color: var(--muted); font-family: var(--mono);
}
.hm-legend .hm-cell { width: 12px; height: 12px; display: inline-block; border-radius: 2px; }

/* ── Badges ─────────────────────────────────────── */
.badge-cat { margin-bottom: 16px; }
.badge-cat:last-child { margin-bottom: 0; }
.cat-title {
  font-size: .75em; font-weight: 600; color: var(--sub);
  text-transform: uppercase; letter-spacing: .08em;
  margin-bottom: 8px; padding-bottom: 4px;
  border-bottom: 1px solid rgba(148,163,184,.08);
  font-family: var(--mono);
}
.badge-row {
  display: grid; grid-template-columns: repeat(auto-fill, minmax(88px, 1fr)); gap: 8px;
}
.badge {
  text-align: center; padding: 12px 6px; border-radius: var(--r-sm);
  border: 1px solid var(--border); cursor: default; transition: all .2s;
}
.badge.unlocked {
  background: linear-gradient(135deg, rgba(34,197,94,.06), rgba(6,182,212,.04));
  border-color: rgba(34,197,94,.25);
}
.badge.unlocked:hover {
  transform: translateY(-3px);
  box-shadow: 0 8px 20px rgba(34,197,94,.15);
  border-color: var(--g);
}
.badge.locked { background: rgba(255,255,255,.02); opacity: .35; }
.b-icon { display: block; font-size: 1.7em; margin-bottom: 4px; }
.b-name {
  display: block; font-size: .6em; color: var(--muted);
  line-height: 1.3; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}
.badge.unlocked .b-name { color: var(--sub); }

/* ── Tasks ──────────────────────────────────────── */
.tlist { display: flex; flex-direction: column; gap: 6px; }
.trow {
  display: flex; align-items: center; gap: 12px;
  padding: 10px 14px; background: var(--surface);
  border-radius: var(--r-sm); font-size: .84em;
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

/* ── Footer ─────────────────────────────────────── */
.foot {
  text-align: center; padding: 32px 0 16px;
  color: var(--muted); font-size: .72em;
  font-family: var(--mono);
}
.foot p + p { margin-top: 4px; }
.foot a { color: var(--g); }

/* ── Responsive ─────────────────────────────────── */
@media (max-width: 720px) {
  .hero {
    grid-template-columns: 1fr;
    text-align: center;
    gap: 16px;
    padding: 24px 20px;
  }
  .hero-avatar { justify-self: center; }
  .hero-stats { flex-direction: row; flex-wrap: wrap; justify-content: center; }
  .hs { min-width: 80px; }
  .grid2 { grid-template-columns: 1fr; }
}

@media (max-width: 480px) {
  .shell { padding: 12px 14px 32px; }
  .nav { flex-wrap: wrap; gap: 8px; }
  .hero-name { font-size: 1.5em; }
  .tiers { flex-wrap: wrap; }
  .tier { min-width: 60px; }
}

/* ── Animations ─────────────────────────────────── */
@keyframes fadeUp {
  from { opacity: 0; transform: translateY(16px); }
  to { opacity: 1; transform: translateY(0); }
}
.hero { animation: fadeUp .6s ease-out; }
.card { animation: fadeUp .6s ease-out backwards; }
.card:nth-child(1) { animation-delay: .1s; }
.card:nth-child(2) { animation-delay: .15s; }
.card:nth-child(3) { animation-delay: .2s; }
.card:nth-child(4) { animation-delay: .25s; }
.card:nth-child(5) { animation-delay: .3s; }
"""


def main():
    u = load_json(DATA_DIR / "user_stats.json")
    t = load_json(DATA_DIR / "tasks.json")
    c = load_json(DATA_DIR / "config.json")
    ci = load_json(DATA_DIR / "check_ins.json")

    for lang in c["supported_languages"]:
        filename = "index.html" if lang == "en" else f"index_{lang}.html"
        html = generate_dashboard(u, t, c, ci, lang)
        with open(OUTPUT_DIR / filename, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"[generate] Written {filename}")

    with open(OUTPUT_DIR / "styles.css", "w", encoding="utf-8") as f:
        f.write(generate_css())
    print("[generate] Written styles.css")


if __name__ == "__main__":
    main()
