"""出力形式と境界条件のテスト。Python標準ライブラリのみ。"""

import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills" / "x-folks" / "scripts" / "validate.py"


def run(payload):
    return subprocess.run(
        [sys.executable, str(SCRIPT), "-"],
        input=json.dumps(payload, ensure_ascii=False),
        text=True,
        capture_output=True,
        check=False,
    )


class ValidateTests(unittest.TestCase):
    def test_valid_grouped_evidence(self):
        payload = {
            "lines": ["機能Aは利用可能です。", "条件Bを満たす必要があります。"],
            "evidence": [
                {"claims": ["機能A", "条件B"], "refs": ["src/main.py:12-18", "https://example.org/spec"]}
            ],
        }
        result = run(payload)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            result.stdout,
            "機能Aは利用可能です。\n条件Bを満たす必要があります。\n\n"
            "機能A・条件B：src/main.py:12-18・https://example.org/spec\n",
        )

    def test_three_lines_and_80_chars(self):
        result = run({"lines": ["あ" * 80, "二行目", "三行目"], "evidence": []})
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.count("\n"), 3)

    def test_no_citations_for_creative_reply(self):
        result = run({"lines": ["おはよう。"], "evidence": []})
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "おはよう。\n")

    def test_windows_file_path(self):
        result = run({
            "lines": ["修正箇所はAです。"],
            "evidence": [{"claims": ["修正箇所"], "refs": [r"C:\work\app\main.py:2-3"]}],
        })
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_four_lines_rejected(self):
        self.assertEqual(run({"lines": ["一", "二", "三", "四"], "evidence": []}).returncode, 1)

    def test_long_single_line_rejected(self):
        self.assertEqual(run({"lines": ["あ" * 81], "evidence": []}).returncode, 1)

    def test_embedded_break_rejected(self):
        self.assertEqual(run({"lines": ["一行目\n二行目"], "evidence": []}).returncode, 1)

    def test_heading_rejected(self):
        self.assertEqual(run({"lines": ["# 結論"], "evidence": []}).returncode, 1)

    def test_empty_body_rejected(self):
        self.assertEqual(run({"lines": [], "evidence": []}).returncode, 1)

    def test_unmatched_claim_rejected(self):
        self.assertEqual(run({
            "lines": ["Aは正しい。"],
            "evidence": [{"claims": ["Bは正しい"], "refs": ["README.md:1"]}],
        }).returncode, 1)

    def test_commentary_in_reference_rejected(self):
        self.assertEqual(run({
            "lines": ["Aです。"],
            "evidence": [{"claims": ["A"], "refs": ["詳しくは別文書を参照"]}],
        }).returncode, 1)

    def test_missing_reference_rejected(self):
        self.assertEqual(run({
            "lines": ["Aです。"],
            "evidence": [{"claims": ["A"], "refs": []}],
        }).returncode, 1)

    def test_extra_input_key_rejected(self):
        self.assertEqual(run({"lines": ["Aです。"], "evidence": [], "notes": "追加説明"}).returncode, 1)

    def test_invalid_json_rejected(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "-"],
            input="{invalid", capture_output=True, text=True, check=False,
        )
        self.assertEqual(result.returncode, 2)
        self.assertFalse(result.stdout)


if __name__ == "__main__":
    unittest.main()