# ClawRecord

[English](./README.md) | [简体中文](./README_CN.md)

> Gamified OpenClaw Tracking System — Duolingo for your AI assistant.

ClawRecord automatically tracks your [OpenClaw](https://github.com/openclaw/openclaw) usage and turns it into a gamified experience: XP, levels, achievements, skill trees, streak tracking, leagues, and a global leaderboard.

**Your AI grows. You get the credit. No cheating allowed.**

## Features

- **Auto Data Collection** — Hook + session parser extracts metrics from OpenClaw runtime
- **XP System** — Earn XP from messages, tool calls, multi-turn conversations, skill diversity
- **Level & Evolution** — Progress from Novice Tamer (🥚) to AI Overlord (👑)
- **47 Achievements** — Milestones, streaks, skills, tools, efficiency, time-based, and special
- **6 Skill Trees** — Coding, Content, Research, Communication, Automation, Data Analysis
- **Streak & HP** — Daily streak with freeze protection and health decay
- **League System** — Bronze → Silver → Gold → Diamond → Obsidian based on weekly XP
- **Activity Heatmap** — 90-day visual activity map
- **Global Leaderboard** — Decentralized via GitHub, zero infrastructure cost
- **Multi-language** — English and Chinese (i18n)

## Architecture

```
OpenClaw Runtime → Hook (real-time) → collect.py → score.py → generate_pages.py → GitHub Pages
                   Session JSONL ────↗                ↓
                                              public_profile.json → Global Registry → Leaderboard
```

## Quick Start

### 1. Install the Hook

Copy the hook to your OpenClaw hooks directory:

```bash
cp -r hooks/clawrecord-hook ~/.openclaw/hooks/
openclaw hooks enable clawrecord-hook
openclaw gateway restart
```

### 2. Collect & Score

```bash
python3 scripts/collect.py    # Parse OpenClaw data → data/raw/metrics.json
python3 scripts/score.py      # Calculate XP, levels, achievements → data/*.json
python3 scripts/generate_pages.py  # Generate dashboard → docs/
```

### 3. Deploy

Push to GitHub. The GitHub Action runs the pipeline daily and deploys to Pages.

### 4. Join the Global Leaderboard

Submit a PR to [clawrecord-leaderboard](https://github.com/luka2chat/clawrecord-leaderboard) to add your repo.

## Project Structure

```
clawrecord/
├── hooks/clawrecord-hook/   # OpenClaw hook for real-time event capture
├── scripts/
│   ├── collect.py           # Data collection from OpenClaw runtime
│   ├── score.py             # XP / achievement / level calculation engine
│   ├── generate_pages.py    # Static dashboard generator
│   └── utils.py             # Shared utilities
├── data/
│   ├── config.json          # Game rules, levels, 47 achievements, leagues
│   ├── raw/                 # Auto-collected metrics (do not edit)
│   ├── user_stats.json      # Computed user state
│   ├── tasks.json           # Auto-detected daily tasks
│   ├── check_ins.json       # Daily check-in records
│   └── public_profile.json  # Public data for global leaderboard
├── registry/                # Global leaderboard aggregator (separate repo)
├── docs/                    # Generated static dashboard
└── .github/workflows/       # CI/CD pipeline
```

## Anti-Cheat

- All XP is computed from verified OpenClaw runtime logs
- `data/raw/` is machine-generated — manual edits are ignored by the pipeline
- `public_profile.json` includes a SHA-256 signature for integrity verification
- The global registry checks XP growth rate anomalies

---

Powered by OpenClaw & GitHub Actions
