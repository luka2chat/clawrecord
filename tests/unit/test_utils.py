#!/usr/bin/env python3
"""Unit tests for scripts/utils.py"""

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))
from utils import (
    classify_skill_name,
    classify_tool,
    get_text,
    hour_from_iso,
    iso_date,
    load_json,
    read_jsonl,
    save_json,
    tool_xp,
)


class TestIsoDate(unittest.TestCase):
    def test_valid_iso(self):
        self.assertEqual(iso_date("2025-03-10T12:00:00Z"), "2025-03-10")

    def test_date_only(self):
        self.assertEqual(iso_date("2025-03-10"), "2025-03-10")

    def test_none(self):
        self.assertIsNone(iso_date(None))

    def test_empty(self):
        self.assertIsNone(iso_date(""))


class TestHourFromIso(unittest.TestCase):
    def test_valid_timestamp(self):
        self.assertEqual(hour_from_iso("2025-03-10T14:30:00+00:00"), 14)

    def test_utc_z(self):
        self.assertEqual(hour_from_iso("2025-03-10T03:00:00Z"), 3)

    def test_none(self):
        self.assertIsNone(hour_from_iso(None))

    def test_empty(self):
        self.assertIsNone(hour_from_iso(""))

    def test_midnight(self):
        self.assertEqual(hour_from_iso("2025-03-10T00:00:00Z"), 0)


class TestClassifyTool(unittest.TestCase):
    def test_read_tool(self):
        self.assertEqual(classify_tool("Read"), "coding")

    def test_write_tool(self):
        self.assertEqual(classify_tool("Write"), "coding")

    def test_exec_tool(self):
        self.assertEqual(classify_tool("exec"), "coding")

    def test_shell_tool(self):
        self.assertEqual(classify_tool("Shell"), "coding")

    def test_browser_tool(self):
        self.assertEqual(classify_tool("browser"), "research")

    def test_web_search(self):
        self.assertEqual(classify_tool("web_search"), "research")

    def test_fetch_tool(self):
        self.assertEqual(classify_tool("fetch"), "research")

    def test_unknown_tool(self):
        self.assertEqual(classify_tool("something_random"), "coding")


class TestClassifySkillName(unittest.TestCase):
    def test_coding(self):
        self.assertEqual(classify_skill_name("cursor-coding"), "coding")

    def test_content(self):
        self.assertEqual(classify_skill_name("content-writing"), "content")

    def test_research(self):
        self.assertEqual(classify_skill_name("web-research"), "research")

    def test_unknown(self):
        self.assertEqual(classify_skill_name("something-random"), "coding")


class TestToolXp(unittest.TestCase):
    def test_read(self):
        self.assertEqual(tool_xp("read"), 2)

    def test_write(self):
        self.assertEqual(tool_xp("write"), 5)

    def test_exec(self):
        self.assertEqual(tool_xp("exec"), 8)

    def test_browser(self):
        self.assertEqual(tool_xp("browser"), 10)

    def test_default(self):
        self.assertEqual(tool_xp("unknown_tool"), 3)


class TestGetText(unittest.TestCase):
    def test_dict_with_lang(self):
        obj = {"en": "Hello", "zh": "你好"}
        self.assertEqual(get_text(obj, "en"), "Hello")
        self.assertEqual(get_text(obj, "zh"), "你好")

    def test_dict_fallback(self):
        obj = {"en": "Hello"}
        self.assertEqual(get_text(obj, "zh"), "Hello")

    def test_string_passthrough(self):
        self.assertEqual(get_text("just a string", "en"), "just a string")


class TestJsonIO(unittest.TestCase):
    def test_save_and_load(self):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = f.name

        try:
            data = {"key": "value", "num": 42}
            save_json(path, data)
            loaded = load_json(path)
            self.assertEqual(loaded, data)
        finally:
            os.unlink(path)

    def test_save_creates_parent_dirs(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "nested" / "dir" / "file.json"
            save_json(path, {"test": True})
            self.assertTrue(path.exists())


class TestReadJsonl(unittest.TestCase):
    def test_valid_jsonl(self):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".jsonl", delete=False
        ) as f:
            f.write('{"a": 1}\n')
            f.write('{"b": 2}\n')
            path = f.name

        try:
            records = list(read_jsonl(path))
            self.assertEqual(len(records), 2)
            self.assertEqual(records[0], {"a": 1})
            self.assertEqual(records[1], {"b": 2})
        finally:
            os.unlink(path)

    def test_skips_malformed(self):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".jsonl", delete=False
        ) as f:
            f.write('{"good": 1}\n')
            f.write("not json\n")
            f.write('{"also_good": 2}\n')
            path = f.name

        try:
            records = list(read_jsonl(path))
            self.assertEqual(len(records), 2)
        finally:
            os.unlink(path)

    def test_nonexistent_file(self):
        records = list(read_jsonl("/nonexistent/file.jsonl"))
        self.assertEqual(len(records), 0)

    def test_empty_lines(self):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".jsonl", delete=False
        ) as f:
            f.write('{"a": 1}\n')
            f.write("\n")
            f.write('{"b": 2}\n')
            f.write("\n")
            path = f.name

        try:
            records = list(read_jsonl(path))
            self.assertEqual(len(records), 2)
        finally:
            os.unlink(path)


if __name__ == "__main__":
    unittest.main()
