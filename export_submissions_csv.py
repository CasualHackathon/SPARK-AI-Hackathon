#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import csv
import sys
from pathlib import Path


def read_text(path: Path) -> str:
    # Prefer UTF-8; fall back to gbk if needed.
    for enc in ("utf-8-sig", "utf-8", "gbk"):
        try:
            return path.read_text(encoding=enc)
        except UnicodeDecodeError:
            continue
    # Last resort: replace errors.
    return path.read_text(encoding="utf-8", errors="replace")


def parse_md(md_path: Path) -> dict:
    data = {}
    text = read_text(md_path)
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith("#"):
            continue
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()
        if key:
            data[key] = value
    return data


def main() -> None:
    if len(sys.argv) < 3:
        print("Usage: python export_submissions_csv.py <submissions_dir> <output_csv>")
        sys.exit(1)

    submissions_dir = Path(sys.argv[1]).resolve()
    output_csv = Path(sys.argv[2]).resolve()

    rows = []
    keys = set()

    for subdir in sorted([p for p in submissions_dir.iterdir() if p.is_dir()]):
        md_files = list(subdir.glob("*.md"))
        for md in md_files:
            row = {
                "submission_folder": subdir.name,
                "file": md.name,
            }
            row.update(parse_md(md))
            rows.append(row)
            keys.update(row.keys())

    # Stable header order: put id fields first, then common fields, then the rest sorted.
    preferred = [
        "submission_folder",
        "file",
        "GitHub User",
        "ProjectName",
        "Track",
        "ProjectDescription",
        "Github Repo Link",
        "Team Lead",
        "Team Wallet Address",
    ]
    headers = []
    for k in preferred:
        if k in keys and k not in headers:
            headers.append(k)
    for k in sorted(keys):
        if k not in headers:
            headers.append(k)

    output_csv.parent.mkdir(parents=True, exist_ok=True)
    with output_csv.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} rows to {output_csv}")


if __name__ == "__main__":
    main()
