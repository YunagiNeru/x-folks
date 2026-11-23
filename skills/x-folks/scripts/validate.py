#!/usr/bin/env python3
"""X folks: 3行の本文と出典の対応を検査し、提出文だけを出力する。"""

import json
import re
import sys
from pathlib import Path
from urllib.parse import urlsplit

MAX_LINES = 3
MAX_CHARS = 80
FILE_REF = re.compile(
    r'^(?:(?:[A-Za-z]:)?[\\/])?'
    r'(?:[^\\/:*?"<>|\r\n]+[\\/])*'
    r'[^\\/:*?"<>|\r\n]+\.[A-Za-z0-9]{1,12}'
    r'(?::[0-9]+(?:-[0-9]+)?|#L[0-9]+(?:-L[0-9]+)?)?$'
)


def render(data):
    """入力は境界で一度だけ検証し、合格した文章を組み立てる。"""
    if type(data) is not dict or set(data) != {"lines", "evidence"}:
        raise ValueError("FORMAT: top-level keys")
    lines, evidence = data["lines"], data["evidence"]
    if type(lines) is not list or not 1 <= len(lines) <= MAX_LINES:
        raise ValueError("LINES: require 1-3 lines")
    for number, line in enumerate(lines, 1):
        if type(line) is not str or not line.strip() or line != line.strip():
            raise ValueError(f"LINE_{number}: empty or extra whitespace")
        if any(char in line for char in "\r\n\t\u2028\u2029"):
            raise ValueError(f"LINE_{number}: embedded line break or tab")
        if len(line) > MAX_CHARS:
            raise ValueError(f"LINE_{number}: exceeds {MAX_CHARS} characters")
        if line.startswith(("#", ">")):
            raise ValueError(f"LINE_{number}: heading or quotation")
    if type(evidence) is not list:
        raise ValueError("EVIDENCE: require a list")

    rendered = []
    for number, item in enumerate(evidence, 1):
        if type(item) is not dict or set(item) != {"claims", "refs"}:
            raise ValueError(f"EVIDENCE_{number}: keys must be claims and refs")
        claims, refs = item["claims"], item["refs"]
        if type(claims) is not list or not claims or type(refs) is not list or not refs:
            raise ValueError(f"EVIDENCE_{number}: claims and refs must be nonempty lists")
        for claim in claims:
            if (type(claim) is not str or not claim.strip()
                    or claim != claim.strip() or "：" in claim or "・" in claim
                    or not any(claim in line for line in lines)):
                raise ValueError(f"EVIDENCE_{number}: claim not found in body")
        for ref in refs:
            if type(ref) is not str or not ref.strip() or ref != ref.strip() or "・" in ref or "：" in ref:
                raise ValueError(f"EVIDENCE_{number}: invalid reference")
            if ref.startswith(("http://", "https://")):
                parsed = urlsplit(ref)
                valid = bool(parsed.netloc) and not any(c.isspace() for c in ref)
            else:
                valid = bool(FILE_REF.fullmatch(ref)) or ref == "LICENSE"
            if not valid:
                raise ValueError(f"EVIDENCE_{number}: expected URL or file location")
        rendered.append("・".join(claims) + "：" + "・".join(refs))

    result = "\n".join(lines)
    if rendered:
        result += "\n\n" + "\n".join(rendered)
    return result


def main():
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