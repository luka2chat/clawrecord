# 🤖 ClawRecord

[English](./README.md) | [简体中文](./README_CN.md)

> OpenClaw 游戏化记录系统 - 追踪您的 AI 驯兽师之旅。

ClawRecord 是一个受多邻国（Duolingo）启发的记录系统，专门用于追踪和游戏化您使用 **OpenClaw**（开源 AI 个人助理）的过程。

## 🌟 核心功能

- **🔥 每日打卡 Streak**：保持连续使用，积累连胜。
- **📈 XP 经验值**：完成不同难度的任务获得 XP。
- **🛡️ 等级系统**：从“新手驯兽师”进化到“AI 领主”。
- **🏆 成就徽章**：解锁里程碑成就。
- **🎯 技能树**：在邮件管理、编程辅助等领域提升技能。
- **❤️ 生命值/挑战**：设定每周目标，保持动力。
- **📊 贡献热力图**：直观展示您的 AI 使用频率。
- **🌍 多语言支持**：支持英文和中文（i18n）。

## 🛠️ 技术方案

- **数据存储**：`/data` 目录下的 JSON 文件。
- **页面生成**：Python 脚本 `scripts/generate_pages.py`。
- **自动化**：GitHub Actions 每天定时构建。
- **部署**：GitHub Pages 免费托管。

## 🚀 如何记录新任务

1. 编辑 `data/tasks.json` 添加新任务。
2. 编辑 `data/check_ins.json` 更新打卡状态。
3. 编辑 `data/user_stats.json` 更新 XP 和等级。
4. 提交并推送代码，GitHub Actions 会自动更新页面。

---
Powered by OpenClaw & GitHub Actions
