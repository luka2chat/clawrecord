#!/usr/bin/env python3
"""Unit tests for scripts/score.py"""

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))
from score import (
    calc_claw_power,
    calc_daily_xp,
    calc_league,
    calc_level,
    calc_personal_records,
    calc_skills,
    generate_daily_quests,
    get_streak_multiplier,
)


def load_config():
    config_path = Path(__file__).parent.parent.parent / "data" / "config.json"
    with open(config_path) as f:
        return json.load(f)


class TestCalcDailyXp(unittest.TestCase):
    def setUp(self):
        self.config = load_config()

    def test_zero_activity(self):
        day = {"messages": {"user": 0, "assistant": 0}}
        self.assertEqual(calc_daily_xp(day, self.config), 0)

    def test_messages_only(self):
        day = {"messages": {"user": 10, "assistant": 10}}
        xp = calc_daily_xp(day, self.config)
        expected = 10 * 3 + 10 * 2
        self.assertEqual(xp, expected)

    def test_with_tool_calls(self):
        day = {
            "messages": {"user": 5, "assistant": 5},
            "tool_calls": {"read": 3, "exec": 2},
        }
        xp = calc_daily_xp(day, self.config)
        expected = 5 * 3 + 5 * 2 + 3 * 2 + 2 * 8
        self.assertGreaterEqual(xp, expected)

    def test_multi_turn_bonus(self):
        day = {
            "messages": {"user": 1, "assistant": 1},
            "max_turns_in_session": 10,
        }
        xp = calc_daily_xp(day, self.config)
        base = 1 * 3 + 1 * 2
        threshold = self.config["xp_weights"]["multi_turn_threshold"]
        bonus = (10 - threshold) * self.config["xp_weights"]["multi_turn_bonus"]
        self.assertEqual(xp, base + bonus)

    def test_skill_diversity_bonus(self):
        day = {
            "messages": {"user": 1, "assistant": 1},
            "skills_used": ["coding", "research", "data"],
        }
        xp = calc_daily_xp(day, self.config)
        base = 1 * 3 + 1 * 2
        diversity = 3 * self.config["xp_weights"]["skill_diversity_bonus"]
        self.assertEqual(xp, base + diversity)


class TestStreakMultiplier(unittest.TestCase):
    def setUp(self):
        self.config = load_config()

    def test_no_streak(self):
        self.assertEqual(get_streak_multiplier(0, self.config), 1.0)

    def test_small_streak(self):
        self.assertEqual(get_streak_multiplier(3, self.config), 1.0)

    def test_7_day_streak(self):
        self.assertEqual(get_streak_multiplier(7, self.config), 1.1)

    def test_14_day_streak(self):
        self.assertEqual(get_streak_multiplier(14, self.config), 1.2)

    def test_30_day_streak(self):
        self.assertEqual(get_streak_multiplier(30, self.config), 1.5)

    def test_90_day_streak(self):
        self.assertEqual(get_streak_multiplier(90, self.config), 2.0)

    def test_100_day_streak(self):
        self.assertEqual(get_streak_multiplier(100, self.config), 2.0)


class TestCalcLevel(unittest.TestCase):
    def setUp(self):
        self.levels = load_config()["levels"]

    def test_zero_xp(self):
        cur, nxt = calc_level(0, self.levels)
        self.assertEqual(cur["level"], 1)
        self.assertIsNotNone(nxt)

    def test_level_3(self):
        cur, nxt = calc_level(500, self.levels)
        self.assertEqual(cur["level"], 3)

    def test_level_5(self):
        cur, nxt = calc_level(1500, self.levels)
        self.assertEqual(cur["level"], 5)

    def test_max_level(self):
        cur, nxt = calc_level(999999, self.levels)
        self.assertEqual(cur["level"], 100)
        self.assertIsNone(nxt)


class TestCalcLeague(unittest.TestCase):
    def setUp(self):
        self.config = load_config()

    def test_empty_daily(self):
        league, weekly_xp = calc_league({}, self.config)
        self.assertEqual(league["id"], "bronze")
        self.assertEqual(weekly_xp, 0)


class TestCalcClawPower(unittest.TestCase):
    def setUp(self):
        self.config = load_config()

    def test_zero_everything(self):
        power = calc_claw_power(0, 0, 0, {}, self.config)
        self.assertEqual(power, 0)

    def test_with_xp(self):
        power = calc_claw_power(1000, 0, 0, {}, self.config)
        self.assertGreater(power, 0)

    def test_with_streak(self):
        power = calc_claw_power(0, 10, 0, {}, self.config)
        self.assertGreater(power, 0)

    def test_with_badges(self):
        power = calc_claw_power(0, 0, 5, {}, self.config)
        self.assertGreater(power, 0)

    def test_with_skills(self):
        skills = {"coding": {"level": 5}, "research": {"level": 3}}
        power = calc_claw_power(0, 0, 0, skills, self.config)
        self.assertGreater(power, 0)


class TestCalcPersonalRecords(unittest.TestCase):
    def setUp(self):
        self.config = load_config()

    def test_empty_daily(self):
        records = calc_personal_records({}, self.config)
        self.assertEqual(records["best_daily_xp"], 0)
        self.assertEqual(records["best_daily_messages"], 0)

    def test_with_data(self):
        daily = {
            "2025-03-10": {
                "messages": {"user": 50, "assistant": 40},
                "tool_calls": {"read": 10},
                "max_turns_in_session": 20,
                "tokens": {"total": 5000},
            }
        }
        records = calc_personal_records(daily, self.config)
        self.assertGreater(records["best_daily_xp"], 0)
        self.assertEqual(records["best_daily_messages"], 90)
        self.assertEqual(records["best_session_turns"], 20)


class TestGenerateDailyQuests(unittest.TestCase):
    def setUp(self):
        self.config = load_config()

    def test_generates_quests(self):
        quests = generate_daily_quests({}, self.config, "2025-03-10")
        self.assertIn("combo", quests)
        self.assertIn("challenge", quests)
        self.assertIn("streak", quests)
        self.assertEqual(quests["date"], "2025-03-10")

    def test_deterministic_for_same_date(self):
        q1 = generate_daily_quests({}, self.config, "2025-03-10")
        q2 = generate_daily_quests({}, self.config, "2025-03-10")
        self.assertEqual(q1["challenge"]["id"], q2["challenge"]["id"])
        self.assertEqual(q1["combo"]["skills"], q2["combo"]["skills"])

    def test_different_for_different_dates(self):
        q1 = generate_daily_quests({}, self.config, "2025-03-10")
        q2 = generate_daily_quests({}, self.config, "2025-03-11")
        different = (
            q1["challenge"]["id"] != q2["challenge"]["id"]
            or q1["combo"]["skills"] != q2["combo"]["skills"]
        )
        self.assertTrue(different)

    def test_combo_with_activity(self):
        daily = {
            "2025-03-10": {
                "messages": {"user": 10, "assistant": 10},
                "tool_calls": {"read": 5, "exec": 3, "web_search": 2},
                "skills_used": ["coding", "research"],
            }
        }
        quests = generate_daily_quests(daily, self.config, "2025-03-10")
        self.assertGreaterEqual(quests["combo"]["activated"], 0)
        self.assertTrue(quests["streak"]["active"])


class TestCalcSkills(unittest.TestCase):
    def setUp(self):
        self.config = load_config()

    def test_empty_daily(self):
        skills = calc_skills({}, self.config)
        self.assertEqual(len(skills), len(self.config["skills"]))
        for sid, data in skills.items():
            self.assertEqual(data["level"], 0)
            self.assertEqual(data["xp"], 0)

    def test_with_tool_calls(self):
        daily = {
            "2025-03-10": {
                "messages": {"user": 5, "assistant": 5},
                "tool_calls": {"read": 10, "write": 10},
                "skills_used": ["coding"],
            }
        }
        skills = calc_skills(daily, self.config)
        self.assertGreater(skills["coding"]["xp"], 0)


if __name__ == "__main__":
    unittest.main()
