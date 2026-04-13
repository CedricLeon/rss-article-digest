"""rename_reports.py

One-time utility to rename legacy RSS report files to the new naming scheme
and inject Obsidian frontmatter into each one.

New naming scheme:  RSS-feed_YYYY-MM-DD_YYYY-WNN.md

Legacy patterns handled:
  - 2026_W4_2026-01-19.md
  - 2026-W3_2026-01-12.md
  - curated_latest.md  (date extracted from "Generated:" line inside the file)

Frontmatter injected into old files:
  - categories: ["[[RSS feeds]]"]
  - created:    <date from filename / file content>
  - Status:     Read
  - nb-articles-week: <total checkbox count in file (checked + unchecked)>
  - rating:     4
  - tags:       [literature]

Usage (Windows CMD / PowerShell / Git Bash):
  python rename_reports.py "C:\\path\\to\\your\\obsidian\\rss-feeds-folder"
  python rename_reports.py          # will prompt for the folder path
"""

import re
import sys
from datetime import date
from pathlib import Path


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _iso_week_str(d: date) -> str:
    iso = d.isocalendar()
    return f"{iso[0]}-W{iso[1]:02d}"


def _new_filename(d: date) -> str:
    return f"RSS-feed_{d.strftime('%Y-%m-%d')}_{_iso_week_str(d)}.md"


def _count_checkboxes(content: str) -> int:
    """Count all checkbox items regardless of checked state."""
    return len(re.findall(r"^- \[[ xX]\]", content, re.MULTILINE))


def _has_frontmatter(content: str) -> bool:
    return content.lstrip().startswith("---")


def _build_frontmatter(d: date, nb_articles: int) -> str:
    return (
        "---\n"
        "categories:\n"
        '  - "[[RSS feeds]]"\n'
        f"created: {d.strftime('%Y-%m-%d')}\n"
        "Status: Read\n"
        f"nb-articles-week: {nb_articles}\n"
        "rating: 4\n"
        "tags:\n"
        "  - literature\n"
        "---\n"
    )


def _parse_date_from_filename(name: str):
    """Extract YYYY-MM-DD from the tail of legacy filenames."""
    m = re.search(r"_(\d{4})-(\d{2})-(\d{2})\.md$", name)
    if m:
        try:
            return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        except ValueError:
            pass
    return None


def _parse_date_from_content(content: str):
    """Extract date from a 'Generated: YYYY-MM-DD ...' line inside the file."""
    m = re.search(r"Generated:\s*(\d{4})-(\d{2})-(\d{2})", content)
    if m:
        try:
            return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        except ValueError:
            pass
    return None


# ---------------------------------------------------------------------------
# Main processing
# ---------------------------------------------------------------------------

def process_folder(folder: str) -> None:
    folder_path = Path(folder)
    if not folder_path.is_dir():
        print(f"[ERROR] '{folder}' is not a valid directory.")
        sys.exit(1)

    md_files = sorted(folder_path.glob("*.md"))
    if not md_files:
        print("No .md files found in the folder.")
        return

    processed = 0
    skipped = 0

    for filepath in md_files:
        name = filepath.name

        # Already in the new format → nothing to do
        if re.match(r"^RSS-feed_\d{4}-\d{2}-\d{2}_\d{4}-W\d{2}\.md$", name):
            print(f"  [SKIP – already new format]  {name}")
            skipped += 1
            continue

        # Read file
        try:
            content = filepath.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            print(f"  [SKIP – read error: {exc}]  {name}")
            skipped += 1
            continue

        # Determine the report date
        d = _parse_date_from_filename(name) or _parse_date_from_content(content)
        if d is None:
            print(f"  [SKIP – cannot determine date]  {name}")
            skipped += 1
            continue

        # Count checkboxes for nb-articles-week
        nb_articles = _count_checkboxes(content)

        # Prepend frontmatter if not already present
        changed = False
        if not _has_frontmatter(content):
            content = _build_frontmatter(d, nb_articles) + content
            changed = True

        # Compute the new filename
        new_name = _new_filename(d)
        new_path = folder_path / new_name

        # Write out (to new path if renaming, else overwrite in place)
        try:
            new_path.write_text(content, encoding="utf-8")
        except OSError as exc:
            print(f"  [ERROR – write failed: {exc}]  {name}")
            skipped += 1
            continue

        # Remove old file when the name actually changed
        if new_name != name:
            filepath.unlink(missing_ok=True)
            action = "RENAMED + frontmatter" if changed else "RENAMED"
        else:
            action = "frontmatter added" if changed else "no changes needed"

        print(f"  [{action}]  {name}  →  {new_name}  ({nb_articles} articles)")
        processed += 1

    print(f"\nDone. {processed} file(s) updated, {skipped} skipped.")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    if len(sys.argv) > 1:
        target_folder = " ".join(sys.argv[1:])  # allow unquoted paths with spaces
    else:
        target_folder = input("Enter the path to your RSS feeds folder: ").strip().strip("\"'")

    process_folder(target_folder)
