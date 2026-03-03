#!/usr/bin/env python3
import json, os
from datetime import datetime, timedelta
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
OUTPUT_DIR = Path(__file__).parent.parent / "docs"
OUTPUT_DIR.mkdir(exist_ok=True)

def load_json(f):
    with open(DATA_DIR / f, 'r', encoding='utf-8') as f: return json.load(f)

def get_text(obj, lang, default='en'):
    if isinstance(obj, dict): return obj.get(lang, obj.get(default, ""))
    return obj

def calculate_streak(check_ins):
    dates = sorted([datetime.strptime(d, '%Y-%m-%d') for d in check_ins.keys()])
    if not dates: return 0
    streak, last = 0, None
    for d in dates:
        if check_ins[d.strftime('%Y-%m-%d')]['checked']:
            if last is None or (d - last).days == 1: streak += 1
            else: streak = 1
            last = d
    return streak

def generate_dashboard(user_stats, tasks, config, check_ins, lang):
    ui = {k: get_text(v, lang) for k, v in config['ui_text'].items()}
    streak = calculate_streak(check_ins)
    level_info = next((l for l in reversed(config['levels']) if l['level'] <= user_stats['level']), config['levels'][0])
    
    lang_links = "".join([f'<a href="{"index.html" if l=="en" else f"index_{l}.html"}" class="lang-link {"active" if l==lang else ""}">{l.upper()}</a>' for l in config['supported_languages']])
    
    skills_html = "".join([f'<div class="skill-item"><div class="skill-header"><span>{s["icon"]} {get_text(s["name"], lang)}</span><span>Lv.{user_stats["skills"].get(s["id"], 0)}</span></div><div class="skill-bar"><div class="skill-progress" style="width: {(user_stats["skills"].get(s["id"], 0)/s["max_level"])*100}%"></div></div></div>' for s in config['skills']])
    
    badges_html = "".join([f'<div class="badge"><span>{b["icon"]}</span><div>{get_text(next((bc["name"] for bc in config["badges"] if bc["id"]==b["id"]), b["name"]), lang)}</div><small>{b["date"]}</small></div>' for b in user_stats['badges']])

    return f"""<!DOCTYPE html>
<html lang="{lang}">
<head>
    <meta charset="UTF-8"><title>{ui['title']}</title>
    <link rel="stylesheet" href="styles.css">
</head>
<body>
    <div class="container">
        <div class="lang-switcher">{lang_links}</div>
        <header class="header"><h1>{ui['title']}</h1><p>{ui['subtitle']}</p></header>
        <main class="main">
            <section class="card">
                <div class="user-header"><span style="font-size:3em">{level_info['icon']}</span><div><h2>{user_stats['username']}</h2><p style="color:#22c55e">{get_text(level_info['rank'], lang)}</p></div></div>
                <div class="stats-grid">
                    <div class="stat"><small>{ui['level']}</small><div>Lv.{user_stats['level']}</div></div>
                    <div class="stat"><small>{ui['streak']}</small><div>🔥 {streak}</div></div>
                    <div class="stat"><small>{ui['hp']}</small><div>{user_stats['hp']}/{user_stats['max_hp']}</div></div>
                </div>
            </section>
            <section class="card"><h3>{ui['skills_tree']}</h3><div class="skills-grid">{skills_html}</div></section>
            <section class="card"><h3>{ui['achievements']}</h3><div class="badges-grid">{badges_html}</div></section>
        </main>
        <footer class="footer"><p>{ui['last_updated']}: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p></footer>
    </div>
</body>
</html>"""

def main():
    u, t, c, ci = load_json('user_stats.json'), load_json('tasks.json'), load_json('config.json'), load_json('check_ins.json')
    for l in c['supported_languages']:
        with open(OUTPUT_DIR / ("index.html" if l=="en" else f"index_{l}.html"), 'w') as f:
            f.write(generate_dashboard(u, t, c, ci, l))
    with open(OUTPUT_DIR / 'styles.css', 'w') as f:
        f.write(":root{--primary-color:#22c55e;--dark-bg:#0f172a;--card-bg:#1e293b;--text-primary:#f1f5f9;--text-secondary:#cbd5e1}body{font-family:sans-serif;background:var(--dark-bg);color:var(--text-primary);margin:0}.container{max-width:800px;margin:0 auto;padding:20px}.lang-switcher{text-align:right;margin-bottom:10px}.lang-link{color:var(--text-secondary);text-decoration:none;margin-left:10px;padding:2px 5px;border:1px solid #334155;border-radius:3px}.lang-link.active{background:var(--primary-color);color:#fff}.header{text-align:center;margin-bottom:30px}.card{background:var(--card-bg);padding:20px;border-radius:10px;margin-bottom:20px}.user-header{display:flex;align-items:center;gap:20px;margin-bottom:20px}.stats-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;text-align:center}.stat div{font-size:1.5em;font-weight:bold;color:var(--primary-color)}.skills-grid{display:grid;grid-template-columns:1fr 1fr;gap:15px}.skill-header{display:flex;justify-content:space-between;margin-bottom:5px}.skill-bar{height:8px;background:#000;border-radius:4px;overflow:hidden}.skill-progress{height:100%;background:var(--primary-color)}.badges-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(100px,1fr));gap:10px;text-align:center}.badge{padding:10px;border:1px solid #334155;border-radius:5px}.footer{text-align:center;color:var(--text-secondary);font-size:0.8em}")

if __name__ == "__main__": main()
