# 🤖 ClawRecord

[English](./README.md) | [简体中文](./README_CN.md)

> Gamified OpenClaw Tracking System - Track your journey as an AI Tamer.

ClawRecord is a tracking system inspired by Duolingo, designed to track and gamify your experience with **OpenClaw** (an open-source AI personal assistant).

## 🌟 Key Features

- **🔥 Daily Streak**: Maintain your usage streak and accumulate wins.
- **📈 XP System**: Earn XP by completing tasks of varying difficulty.
- **🛡️ Leveling System**: Evolve from a "Novice Tamer" to an "AI Overlord".
- **🏆 Achievements**: Unlock milestone badges.
- **🎯 Skills Tree**: Level up your skills in Email Management, Coding, and more.
- **❤️ HP & Challenges**: Set weekly goals and stay motivated.
- **📊 Activity Heatmap**: Visualize your AI usage frequency.
- **🌍 Multi-language Support**: Supports English and Chinese (i18n).

## 🛠️ Technical Stack

- **Data Storage**: JSON files in the `/data` directory.
- **Page Generation**: Python script `scripts/generate_pages.py`.
- **Automation**: GitHub Actions for daily automated builds.
- **Deployment**: Free hosting via GitHub Pages.

## 🚀 How to Record New Tasks

1. Edit `data/tasks.json` to add new tasks.
2. Edit `data/check_ins.json` to update check-in status.
3. Edit `data/user_stats.json` to update XP and levels.
4. Push your changes, and GitHub Actions will automatically update the dashboard.

---
Powered by OpenClaw & GitHub Actions
