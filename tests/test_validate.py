"""本文・根拠ラベル・短いファイル参照の形式を検査する。"""

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
        encoding="utf-8",
        capture_output=True,
        check=False,
    )


class ValidateTests(unittest.TestCase):
    def test_valid_condensed_evidence(self):
        payload = {
            "lines": ["機能Aを修正しました。", "機能Bは接続エラーのため未検証です。"],
            "evidence": [
                {"summary": "機能Aの修正箇所", "lines": [1],
                 "refs": ["src/main.py:12", "https://example.org/spec"]},
                {"summary": "機能Bの接続失敗記録", "lines": [2],
                 "refs": ["logs/check.txt:1"]},
            ],
        }
        result = run(payload)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            result.stdout,
            "機能Aを修正しました。\n機能Bは接続エラーのため未検証です。\n\n"
            "機能Aの修正箇所：" + chr(96) + "main.py:12" + chr(96)
            + "・[example.org/spec](https://example.org/spec)\n"
            "機能Bの接続失敗記録：" + chr(96) + "check.txt:1" + chr(96) + "\n",
        )

    def test_markdown_links_disambiguate_identical_filenames(self):
        path_a = "client/config/paxi/resourcepacks/ja_jp_localize/assets/simplycataclysm/lang/ja_jp.json"
        path_b = "client/config/paxi/resourcepacks/ja_jp_localize/assets/skylands/lang/ja_jp.json"
        payload = {
            "style": "markdown",
            "lines": ["翻訳ファイルを二つ追加しました。"],
            "evidence": [{
                "summary": "二つの翻訳ファイル", "lines": [1],
                "refs": [path_a + ":1", path_b + ":1"],
            }],
        }
        result = run(payload)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(
            "[simplycataclysm/lang/ja_jp.json](" + path_a + "#L1)",
            result.stdout,
        )
        self.assertIn("[skylands/lang/ja_jp.json](" + path_b + "#L1)", result.stdout)
        self.assertNotIn("：client/config/", result.stdout)

    def test_codex_uses_clickable_suffix_with_collision(self):
        result = run({
            "lines": ["翻訳を追加しました。"],
            "evidence": [{
                "summary": "翻訳追加ファイル", "lines": [1],
                "refs": ["a/mod-a/lang/ja_jp.json:3", "b/mod-b/lang/ja_jp.json:2"],
            }],
        })
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(chr(96) + "mod-a/lang/ja_jp.json:3" + chr(96), result.stdout)
        self.assertIn(chr(96) + "mod-b/lang/ja_jp.json:2" + chr(96), result.stdout)
        self.assertNotIn(chr(96) + "a/mod-a/", result.stdout)

    def test_three_lines_and_80_chars(self):
        result = run({"lines": ["あ" * 80, "二行目", "三行目"], "evidence": []})
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.count("\n"), 3)

    def test_creative_reply_needs_no_evidence(self):
        result = run({"lines": ["おはよう。"], "evidence": []})
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "おはよう。\n")

    def test_windows_file_path(self):
        result = run({
            "lines": ["修正箇所はAです。"],
            "evidence": [{"summary": "Aの修正箇所", "lines": [1],
                          "refs": [r"C:\work\app\main.py:2-3"]}],
        })
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(chr(96) + "main.py:2" + chr(96), result.stdout)

    def test_windows_markdown_file_path(self):
        result = run({
            "style": "markdown",
            "lines": ["修正箇所はAです。"],
            "evidence": [{"summary": "Aの修正箇所", "lines": [1],
                          "refs": [r"C:\work\app\main.py:2"]}],
        })
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("[main.py](/c:/work/app/main.py#L2)", result.stdout)

    def test_markdown_file_path_with_spaces(self):
        result = run({
            "style": "markdown",
            "lines": ["文書を確認しました。"],
            "evidence": [{"summary": "確認した文書", "lines": [1],
                          "refs": ["docs/My File.md:10"]}],
        })
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("[My File.md](docs/My%20File.md#L10)", result.stdout)

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

    def test_verbatim_summary_rejected(self):
        self.assertEqual(run({
            "lines": ["修正しました。"],
            "evidence": [{"summary": "修正しました", "lines": [1], "refs": ["README.md:1"]}],
        }).returncode, 1)

    def test_unmatched_line_number_rejected(self):
        self.assertEqual(run({
            "lines": ["Aです。"],
            "evidence": [{"summary": "機能A", "lines": [2], "refs": ["README.md:1"]}],
        }).returncode, 1)

    def test_invalid_summary_rejected(self):
        self.assertEqual(run({
            "lines": ["Aです。"],
            "evidence": [{"summary": "A" * 49, "lines": [1], "refs": ["README.md:1"]}],
        }).returncode, 1)

    def test_commentary_in_reference_rejected(self):
        self.assertEqual(run({
            "lines": ["Aです。"],
            "evidence": [{"summary": "Aの根拠", "lines": [1],
                          "refs": ["詳しくは別文書を参照"]}],
        }).returncode, 1)

    def test_missing_reference_rejected(self):
        self.assertEqual(run({
            "lines": ["Aです。"],
            "evidence": [{"summary": "Aの根拠", "lines": [1], "refs": []}],
        }).returncode, 1)

    def test_extra_input_key_rejected(self):
        self.assertEqual(run({
            "lines": ["Aです。"], "evidence": [], "notes": "追加説明",
        }).returncode, 1)

    def test_invalid_style_rejected(self):
        self.assertEqual(run({
            "lines": ["Aです。"], "evidence": [], "style": "other",
        }).returncode, 1)

    def test_invalid_json_rejected(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "-"],
            input="{invalid", capture_output=True, text=True, encoding="utf-8", check=False,
        )
        self.assertEqual(result.returncode, 2)
        self.assertFalse(result.stdout)


if __name__ == "__main__":
    unittest.main()
