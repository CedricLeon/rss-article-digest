import html
import json
import os
import re
from datetime import datetime

RANKED_CACHE = "cache/ranked_articles.json"
OUTPUT_DIR = "output"

os.makedirs(OUTPUT_DIR, exist_ok=True)


def strip_html(text: str) -> str:
    """Strip HTML tags, unescape HTML entities, and normalise whitespace."""
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def generate_markdown():
    with open(RANKED_CACHE, "r", encoding="utf-8") as f:
        ranked = json.load(f)

    now = datetime.now()
    today = now.date()
    date_str = today.strftime("%Y-%m-%d")
    iso = today.isocalendar()
    week_str = f"{iso[0]}-W{iso[1]:02d}"

    filename = f"RSS-feed_{date_str}_{week_str}.md"
    output_file = os.path.join(OUTPUT_DIR, filename)

    nb_articles = len(ranked)

    lines = []

    # --- Obsidian frontmatter ---
    lines.append(
        f"---\n"
        f"categories:\n"
        f'  - "[[RSS feeds]]"\n'
        f"created: {date_str}\n"
        f"Status: To read\n"
        f"nb-articles-week: {nb_articles}\n"
        f"rating: \n"
        f"tags:\n"
        f"  - literature\n"
        f"---"
    )

    lines.append("# Curated Research Articles\n")
    lines.append(f"Generated: {now.strftime('%Y-%m-%d %H:%M')}\n")

    for a in ranked[:50]:
        title = a["title"].replace("\n", " ").strip()
        url = a["link"]
        score = f"{a['score']:.1f}"
        author = a.get("author", "")
        author_str = f" by {author}" if author else ""
        lines.append(f"- [ ] [{title}]({url}){author_str} — score: {score}")

        content = strip_html(a.get("content", ""))
        if content:
            lines.append(f"> [!abstract]- Abstract\n> {content}")

    md = "\n".join(lines)

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(md)

    print(f"Markdown written to {output_file}")


if __name__ == "__main__":
    generate_markdown()
