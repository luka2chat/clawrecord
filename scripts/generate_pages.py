#!/usr/bin/env python3
"""
ClawRecord 静态页面生成脚本
根据 JSON 数据生成 HTML 页面
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path

# 配置路径
DATA_DIR = Path(__file__).parent.parent / "data"
OUTPUT_DIR = Path(__file__).parent.parent / "docs"
TEMPLATES_DIR = Path(__file__).parent.parent / "templates"

OUTPUT_DIR.mkdir(exist_ok=True)

def load_json(filename):
    """加载 JSON 文件"""
    with open(DATA_DIR / filename, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_html(filename, content):
    """保存 HTML 文件"""
    with open(OUTPUT_DIR / filename, 'w', encoding='utf-8') as f:
        f.write(content)

def calculate_streak_data(check_ins):
    """计算连续打卡数据"""
    dates = sorted([datetime.strptime(d, '%Y-%m-%d') for d in check_ins.keys()])
    
    if not dates:
        return 0, []
    
    current_streak = 0
    max_streak = 0
    streak_dates = []
    
    today = datetime.now()
    last_date = None
    
    for date in dates:
        if check_ins[date.strftime('%Y-%m-%d')]['checked']:
            if last_date is None or (date - last_date).days == 1:
                current_streak += 1
                streak_dates.append(date.strftime('%Y-%m-%d'))
            else:
                max_streak = max(max_streak, current_streak)
                current_streak = 1
                streak_dates = [date.strftime('%Y-%m-%d')]
            last_date = date
    
    max_streak = max(max_streak, current_streak)
    
    return current_streak, streak_dates

def generate_heatmap_data(check_ins):
    """生成热力图数据（类似 GitHub 贡献）"""
    heatmap = {}
    
    for date_str, data in check_ins.items():
        if data['checked']:
            date = datetime.strptime(date_str, '%Y-%m-%d')
            week = date.isocalendar()[1]
            day = date.weekday()
            
            if week not in heatmap:
                heatmap[week] = {}
            
            heatmap[week][day] = data['xp_gained']
    
    return heatmap

def generate_dashboard(user_stats, tasks, config, check_ins):
    """生成主面板 HTML"""
    streak, streak_dates = calculate_streak_data(check_ins)
    heatmap = generate_heatmap_data(check_ins)
    
    # 计算本周 XP
    today = datetime.now()
    week_start = today - timedelta(days=today.weekday())
    weekly_xp = sum(
        data['xp_gained'] for date_str, data in check_ins.items()
        if data['checked'] and datetime.strptime(date_str, '%Y-%m-%d') >= week_start
    )
    
    # 获取当前等级信息
    current_level_info = None
    next_level_info = None
    for level_info in config['levels']:
        if level_info['level'] <= user_stats['level']:
            current_level_info = level_info
        elif next_level_info is None:
            next_level_info = level_info
    
    # 生成技能条形图
    skills_html = ""
    for skill in config['skills']:
        skill_id = skill['id']
        level = user_stats['skills'].get(skill_id, 0)
        progress = (level / skill['max_level']) * 100
        skills_html += f"""
        <div class="skill-item">
            <div class="skill-header">
                <span class="skill-icon">{skill['icon']}</span>
                <span class="skill-name">{skill['name']}</span>
                <span class="skill-level">Lv.{level}</span>
            </div>
            <div class="skill-bar">
                <div class="skill-progress" style="width: {progress}%"></div>
            </div>
        </div>
        """
    
    # 生成热力图 HTML
    heatmap_html = ""
    for week in sorted(heatmap.keys()):
        week_html = f'<div class="heatmap-week">'
        for day in range(7):
            xp = heatmap[week].get(day, 0)
            intensity = min(xp / 300, 1.0)  # 标准化到 0-1
            color = f"rgba(34, 197, 94, {intensity})"
            week_html += f'<div class="heatmap-cell" style="background-color: {color}" title="{xp} XP"></div>'
        week_html += '</div>'
        heatmap_html += week_html
    
    # 生成成就徽章
    badges_html = ""
    for badge in user_stats['badges']:
        badges_html += f"""
        <div class="badge">
            <div class="badge-icon">{badge['icon']}</div>
            <div class="badge-name">{badge['name']}</div>
            <div class="badge-date">{badge['date']}</div>
        </div>
        """
    
    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ClawRecord - OpenClaw 游戏化记录系统</title>
    <link rel="stylesheet" href="styles.css">
</head>
<body>
    <div class="container">
        <header class="header">
            <h1>🤖 ClawRecord</h1>
            <p>OpenClaw 游戏化记录系统</p>
        </header>
        
        <main class="main">
            <!-- 用户信息卡片 -->
            <section class="card user-card">
                <div class="user-header">
                    <div class="user-avatar">{current_level_info['icon'] if current_level_info else '🐣'}</div>
                    <div class="user-info">
                        <h2>{user_stats['username']}</h2>
                        <p class="rank">{user_stats['rank']}</p>
                    </div>
                </div>
                
                <div class="stats-grid">
                    <div class="stat">
                        <div class="stat-label">等级</div>
                        <div class="stat-value">Lv.{user_stats['level']}</div>
                    </div>
                    <div class="stat">
                        <div class="stat-label">连续打卡</div>
                        <div class="stat-value">🔥 {streak}</div>
                    </div>
                    <div class="stat">
                        <div class="stat-label">本周 XP</div>
                        <div class="stat-value">{weekly_xp}</div>
                    </div>
                    <div class="stat">
                        <div class="stat-label">生命值</div>
                        <div class="stat-value">{user_stats['hp']}/{user_stats['max_hp']}</div>
                    </div>
                </div>
                
                <!-- XP 进度条 -->
                <div class="xp-section">
                    <div class="xp-header">
                        <span>经验值</span>
                        <span>{user_stats['xp']} / {user_stats['xp_to_next_level']}</span>
                    </div>
                    <div class="xp-bar">
                        <div class="xp-progress" style="width: {(user_stats['xp'] / user_stats['xp_to_next_level']) * 100}%"></div>
                    </div>
                </div>
                
                <!-- HP 进度条 -->
                <div class="hp-section">
                    <div class="hp-header">
                        <span>生命值</span>
                        <span>{user_stats['hp']} / {user_stats['max_hp']}</span>
                    </div>
                    <div class="hp-bar">
                        <div class="hp-progress" style="width: {(user_stats['hp'] / user_stats['max_hp']) * 100}%"></div>
                    </div>
                </div>
            </section>
            
            <!-- 技能树 -->
            <section class="card skills-card">
                <h3>🎯 技能树</h3>
                <div class="skills-grid">
                    {skills_html}
                </div>
            </section>
            
            <!-- 成就徽章 -->
            <section class="card badges-card">
                <h3>🏆 成就徽章</h3>
                <div class="badges-grid">
                    {badges_html if badges_html else '<p class="empty-state">继续使用 OpenClaw，解锁更多成就！</p>'}
                </div>
            </section>
            
            <!-- 贡献热力图 -->
            <section class="card heatmap-card">
                <h3>📊 打卡热力图</h3>
                <div class="heatmap">
                    {heatmap_html if heatmap_html else '<p class="empty-state">开始打卡，记录您的 AI 之旅！</p>'}
                </div>
                <div class="heatmap-legend">
                    <span>少</span>
                    <div class="heatmap-cell" style="background-color: rgba(34, 197, 94, 0.1)"></div>
                    <div class="heatmap-cell" style="background-color: rgba(34, 197, 94, 0.3)"></div>
                    <div class="heatmap-cell" style="background-color: rgba(34, 197, 94, 0.6)"></div>
                    <div class="heatmap-cell" style="background-color: rgba(34, 197, 94, 1)"></div>
                    <span>多</span>
                </div>
            </section>
            
            <!-- 最近任务 -->
            <section class="card tasks-card">
                <h3>📝 最近任务</h3>
                <div class="tasks-list">
                    {generate_tasks_html(tasks)}
                </div>
            </section>
        </main>
        
        <footer class="footer">
            <p>Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p>Powered by ClawRecord | <a href="https://github.com/luka2chat/clawrecord">GitHub</a></p>
        </footer>
    </div>
</body>
</html>
"""
    
    return html

def generate_tasks_html(tasks):
    """生成任务列表 HTML"""
    if not tasks:
        return '<p class="empty-state">暂无任务记录</p>'
    
    tasks_sorted = sorted(tasks, key=lambda x: x['date'], reverse=True)[:10]
    
    html = ""
    for task in tasks_sorted:
        complexity_emoji = {'low': '🟢', 'medium': '🟡', 'high': '🔴', 'epic': '🟣'}.get(task['complexity'], '⚪')
        html += f"""
        <div class="task-item">
            <div class="task-header">
                <span class="task-complexity">{complexity_emoji}</span>
                <span class="task-date">{task['date']}</span>
            </div>
            <div class="task-description">{task['description']}</div>
            <div class="task-xp">+{task['xp_gained']} XP</div>
        </div>
        """
    
    return html

def generate_css():
    """生成 CSS 样式"""
    css = """
:root {
    --primary-color: #22c55e;
    --secondary-color: #3b82f6;
    --danger-color: #ef4444;
    --warning-color: #f59e0b;
    --dark-bg: #0f172a;
    --card-bg: #1e293b;
    --border-color: #334155;
    --text-primary: #f1f5f9;
    --text-secondary: #cbd5e1;
}

* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen', 'Ubuntu', 'Cantarell', sans-serif;
    background-color: var(--dark-bg);
    color: var(--text-primary);
    line-height: 1.6;
}

.container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 20px;
}

.header {
    text-align: center;
    margin-bottom: 40px;
    padding: 30px 0;
    border-bottom: 2px solid var(--border-color);
}

.header h1 {
    font-size: 2.5em;
    margin-bottom: 10px;
    background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

.header p {
    color: var(--text-secondary);
    font-size: 1.1em;
}

.main {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
    gap: 20px;
    margin-bottom: 40px;
}

.card {
    background-color: var(--card-bg);
    border: 1px solid var(--border-color);
    border-radius: 12px;
    padding: 20px;
    transition: all 0.3s ease;
}

.card:hover {
    border-color: var(--primary-color);
    box-shadow: 0 0 20px rgba(34, 197, 94, 0.1);
}

.user-card {
    grid-column: 1 / -1;
}

.user-header {
    display: flex;
    align-items: center;
    gap: 15px;
    margin-bottom: 20px;
}

.user-avatar {
    font-size: 3em;
    width: 80px;
    height: 80px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
    border-radius: 50%;
}

.user-info h2 {
    font-size: 1.5em;
    margin-bottom: 5px;
}

.rank {
    color: var(--primary-color);
    font-weight: bold;
}

.stats-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 15px;
    margin-bottom: 20px;
}

.stat {
    text-align: center;
    padding: 15px;
    background-color: rgba(34, 197, 94, 0.05);
    border-radius: 8px;
    border-left: 3px solid var(--primary-color);
}

.stat-label {
    color: var(--text-secondary);
    font-size: 0.9em;
    margin-bottom: 5px;
}

.stat-value {
    font-size: 1.5em;
    font-weight: bold;
    color: var(--primary-color);
}

.xp-section, .hp-section {
    margin-bottom: 15px;
}

.xp-header, .hp-header {
    display: flex;
    justify-content: space-between;
    margin-bottom: 8px;
    font-size: 0.9em;
    color: var(--text-secondary);
}

.xp-bar, .hp-bar {
    height: 24px;
    background-color: rgba(0, 0, 0, 0.3);
    border-radius: 12px;
    overflow: hidden;
}

.xp-progress {
    height: 100%;
    background: linear-gradient(90deg, var(--primary-color), var(--secondary-color));
    transition: width 0.3s ease;
}

.hp-progress {
    height: 100%;
    background: linear-gradient(90deg, var(--danger-color), var(--warning-color));
    transition: width 0.3s ease;
}

.skills-card, .badges-card, .heatmap-card, .tasks-card {
    grid-column: 1 / -1;
}

.skills-card h3, .badges-card h3, .heatmap-card h3, .tasks-card h3 {
    margin-bottom: 20px;
    font-size: 1.3em;
}

.skills-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 15px;
}

.skill-item {
    padding: 15px;
    background-color: rgba(34, 197, 94, 0.05);
    border-radius: 8px;
    border-left: 3px solid var(--primary-color);
}

.skill-header {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 10px;
}

.skill-icon {
    font-size: 1.5em;
}

.skill-name {
    flex: 1;
    font-weight: 500;
}

.skill-level {
    color: var(--primary-color);
    font-weight: bold;
}

.skill-bar {
    height: 8px;
    background-color: rgba(0, 0, 0, 0.3);
    border-radius: 4px;
    overflow: hidden;
}

.skill-progress {
    height: 100%;
    background-color: var(--primary-color);
    transition: width 0.3s ease;
}

.badges-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
    gap: 15px;
}

.badge {
    text-align: center;
    padding: 15px;
    background-color: rgba(59, 130, 246, 0.05);
    border-radius: 8px;
    border: 1px solid var(--secondary-color);
}

.badge-icon {
    font-size: 2em;
    display: block;
    margin-bottom: 8px;
}

.badge-name {
    font-size: 0.9em;
    font-weight: 500;
    margin-bottom: 5px;
}

.badge-date {
    font-size: 0.8em;
    color: var(--text-secondary);
}

.heatmap {
    display: flex;
    flex-wrap: wrap;
    gap: 5px;
    margin-bottom: 15px;
}

.heatmap-week {
    display: flex;
    flex-direction: column;
    gap: 3px;
}

.heatmap-cell {
    width: 20px;
    height: 20px;
    border-radius: 4px;
    border: 1px solid var(--border-color);
    cursor: pointer;
    transition: all 0.2s ease;
}

.heatmap-cell:hover {
    transform: scale(1.2);
    border-color: var(--primary-color);
}

.heatmap-legend {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 10px;
    font-size: 0.9em;
    color: var(--text-secondary);
}

.tasks-list {
    display: flex;
    flex-direction: column;
    gap: 12px;
}

.task-item {
    padding: 15px;
    background-color: rgba(34, 197, 94, 0.05);
    border-radius: 8px;
    border-left: 3px solid var(--primary-color);
}

.task-header {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 8px;
}

.task-complexity {
    font-size: 1.2em;
}

.task-date {
    color: var(--text-secondary);
    font-size: 0.9em;
    margin-left: auto;
}

.task-description {
    margin-bottom: 8px;
    color: var(--text-primary);
}

.task-xp {
    color: var(--primary-color);
    font-weight: bold;
    font-size: 0.9em;
}

.empty-state {
    text-align: center;
    color: var(--text-secondary);
    padding: 20px;
}

.footer {
    text-align: center;
    padding: 20px;
    border-top: 1px solid var(--border-color);
    color: var(--text-secondary);
    font-size: 0.9em;
}

.footer a {
    color: var(--primary-color);
    text-decoration: none;
}

.footer a:hover {
    text-decoration: underline;
}

@media (max-width: 768px) {
    .stats-grid {
        grid-template-columns: repeat(2, 1fr);
    }
    
    .header h1 {
        font-size: 2em;
    }
    
    .main {
        grid-template-columns: 1fr;
    }
}
"""
    return css

def main():
    """主函数"""
    print("📊 正在生成 ClawRecord 页面...")
    
    # 加载数据
    user_stats = load_json('user_stats.json')
    tasks = load_json('tasks.json')
    config = load_json('config.json')
    check_ins = load_json('check_ins.json')
    
    # 生成 HTML
    dashboard_html = generate_dashboard(user_stats, tasks, config, check_ins)
    save_html('index.html', dashboard_html)
    print("✅ 已生成 index.html")
    
    # 生成 CSS
    css = generate_css()
    with open(OUTPUT_DIR / 'styles.css', 'w', encoding='utf-8') as f:
        f.write(css)
    print("✅ 已生成 styles.css")
    
    print("🎉 页面生成完成！")

if __name__ == '__main__':
    main()
