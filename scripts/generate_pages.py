#!/usr/bin/env python3
"""
ClawRecord Dashboard Generator v4 — Data-Driven Architecture

Instead of generating HTML via Python string concatenation, this script
consolidates all data JSON files into a single `docs/data.js` module.
The actual rendering is done client-side by `docs/app.js`.
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from utils import DATA_DIR, OUTPUT_DIR, load_json

OUTPUT_DIR.mkdir(exist_ok=True)


def main():
    user_stats = load_json(DATA_DIR / "user_stats.json")
    tasks = load_json(DATA_DIR / "tasks.json")
    config = load_json(DATA_DIR / "config.json")
    check_ins = load_json(DATA_DIR / "check_ins.json")

    quests_path = DATA_DIR / "daily_quests.json"
    quests = load_json(quests_path) if quests_path.exists() else {
        "combo": {}, "challenge": {}, "streak": {}
    }

    analytics_path = DATA_DIR / "usage_analytics.json"
    analytics = load_json(analytics_path) if analytics_path.exists() else {}

    profile_path = DATA_DIR / "public_profile.json"
    profile = load_json(profile_path) if profile_path.exists() else {}

    bundle = {
        "user": user_stats,
        "tasks": tasks,
        "config": config,
        "checkIns": check_ins,
        "quests": quests,
        "analytics": analytics,
        "profile": profile,
        "generated": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
    }

    data_js = f"const D={json.dumps(bundle, ensure_ascii=False, separators=(',',':'))};"

    with open(OUTPUT_DIR / "data.js", "w", encoding="utf-8") as f:
        f.write(data_js)
    print(f"[generate] Written data.js ({len(data_js):,} bytes)")


if __name__ == "__main__":
    main()
