#!/usr/bin/env python3
"""本文3行と要約付き根拠を検査し、短いファイル参照で表示する。"""

import json
import re
import sys
from pathlib import Path
from urllib.parse import quote, urlsplit

MAX_LINES = 3
MAX_CHARS = 80
MAX_SUMMARY = 48
FILE_REF = re.compile(
    r'^(?:(?:[A-Za-z]:)?[\\/])?'
    r'(?:[^\\/:*?"<>|\r\n`]+[\\/])*'
    r'[^\\/:*?"<>|\r\n`]+\.[A-Za-z0-9]{1,12}'
    r'(?::[1-9]\d*(?:-[1-9]\d*)?|#L[1-9]\d*(?:-L[1-9]\d*)?)?$'
)
LOCATION = re.compile(
    r'(?::(?P<line>[1-9]\d*)(?:-(?P<end>[1-9]\d*))?'
    r'|#L(?P<hashline>[1-9]\d*)(?:-L(?P<hashend>[1-9]\d*))?)$'
)


def render(data):
    """入力を一度検証し、検査済みの本文と資料一覧だけを返す。"""
    if type(data) is not dict or not {"lines", "evidence"} <= set(data) or set(data) - {"lines", "evidence", "style"}:
        raise ValueError("FORMAT: require lines, evidence and optional style")
    lines, evidence = data["lines"], data["evidence"]
    style = data.get("style", "codex")
    if style not in ("codex", "markdown"):
        raise ValueError("STYLE: expected codex or markdown")
    if type(lines) is not list or not 1 <= len(lines) <= MAX_LINES:
        raise ValueError("LINES: require 1-3 lines")
    for index, line in enumerate(lines, 1):
        if type(line) is not str or not line.strip() or line != line.strip():
            raise ValueError(f"LINE_{index}: empty or extra whitespace")
        if any(char in line for char in "\r\n\t\u2028\u2029"):
            raise ValueError(f"LINE_{index}: embedded line break or tab")
        if len(line) > MAX_CHARS:
            raise ValueError(f"LINE_{index}: exceeds {MAX_CHARS} characters")
        if line.startswith(("#", ">")):
            raise ValueError(f"LINE_{index}: heading or quotation")
    if type(evidence) is not list:
        raise ValueError("EVIDENCE: require a list")

    records = []
    paths = set()
    for index, item in enumerate(evidence, 1):
        if type(item) is not dict or set(item) != {"summary", "lines", "refs"}:
            raise ValueError(f"EVIDENCE_{index}: require summary, lines and refs")
        summary, targets, refs = item["summary"], item["lines"], item["refs"]
        if (type(summary) is not str or not summary.strip() or summary != summary.strip()
                or len(summary) > MAX_SUMMARY or any(mark in summary for mark in "：・\r\n")
                or summary.endswith("。") or any(summary == line.rstrip("。") for line in lines)):
            raise ValueError(f"EVIDENCE_{index}: provide a brief, nonverbatim noun label")
        if (type(targets) is not list or not targets or
                any(type(n) is not int or n < 1 or n > len(lines) for n in targets) or
                len(set(targets)) != len(targets)):
            raise ValueError(f"EVIDENCE_{index}: invalid body line numbers")
        if type(refs) is not list or not refs or any(type(ref) is not str for ref in refs):
            raise ValueError(f"EVIDENCE_{index}: require reference strings")
        if len(set(refs)) != len(refs):
            raise ValueError(f"EVIDENCE_{index}: duplicate references")
        validated = []
        for ref in refs:
            if not ref or ref != ref.strip() or any(char in ref for char in "\r\n\t\u2028\u2029"):
                raise ValueError(f"EVIDENCE_{index}: invalid reference")
            if ref.startswith(("https://", "http://")):
                parsed = urlsplit(ref)
                if not parsed.hostname or any(mark in ref for mark in (chr(96), "<", ">")) or any(char.isspace() for char in ref):
                    raise ValueError(f"EVIDENCE_{index}: invalid URL")
                validated.append(("url", ref, None, None))
            else:
                if not FILE_REF.fullmatch(ref) and ref != "LICENSE":
                    raise ValueError(f"EVIDENCE_{index}: expected file path or URL")
                found = LOCATION.search(ref)
                path = ref[:found.start()] if found else ref
                line = found.group("line") or found.group("hashline") if found else None
                end = found.group("end") or found.group("hashend") if found else None
                path = path.replace("\\", "/")
                paths.add(path)
                validated.append(("file", path, line, end))
        records.append((summary, validated))

    short_names = {}
    for path in paths:
        parts = path.split("/")
        for count in range(1, len(parts) + 1):
            suffix = "/".join(parts[-count:])
            if sum(other == suffix or other.endswith("/" + suffix) for other in paths) == 1:
                break
        short_names[path] = suffix

    rows = []
    for summary, refs in records:
        visible = []
        for kind, target, line, end in refs:
            if kind == "url":
                parsed = urlsplit(target)
                tail = parsed.path.rstrip("/").rsplit("/", 1)[-1]
                label = parsed.netloc + ("/" + tail if tail else "")
                visible.append(f"[{label}]({quote(target, safe=':/?&=#%+@,;-._~')})")
                continue
            short = short_names[target]
            if style == "codex":
                visible.append(chr(96) + short + (":" + line if line else "") + chr(96))
            else:
                url = target
                if re.match(r"^[A-Za-z]:/", url):
                    url = "/" + url[0].lower() + url[1:]
                anchor = "#L" + line + ("-L" + end if end else "") if line else ""
                visible.append(f"[{short}]({quote(url, safe='/:._-~')}{anchor})")
        rows.append(summary + "：" + "・".join(visible))

    return "\n".join(lines) + ("\n\n" + "\n".join(rows) if rows else "")


def main():
    sys.stdin.reconfigure(encoding="utf-8")
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    if len(sys.argv) > 2:
        print("INPUT: expected one JSON path or stdin", file=sys.stderr)
        return 2
    try:
        source = sys.argv[1] if len(sys.argv) == 2 else "-"
        raw = sys.stdin.read() if source == "-" else Path(source).read_text(encoding="utf-8-sig")
        data = json.loads(raw)
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        print(f"INPUT: {error}", file=sys.stderr)
        return 2
    try:
        result = render(data)
    except ValueError as error:
        print(f"REJECT: {error}", file=sys.stderr)
        return 1
    print(result)
    return 0


if __name__ == "__main__":
    sys.exit(main())