import json
import os
from datetime import datetime

RANKED_CACHE = "cache/ranked_articles.json"
OUTPUT_DIR = "output"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "curated_latest.md")

os.makedirs(OUTPUT_DIR, exist_ok=True)

def generate_markdown():
    with open(RANKED_CACHE, "r") as f:
        ranked = json.load(f)

    lines = []
    lines.append("# Curated Research Articles\n")
    lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")

    for a in ranked[:100]:  # Already filtered previously
        title = a["title"].replace("\n", " ").strip()
        url = a["link"]
        score = f"{a['score']:.1f}"
        author = a.get("author", "")
        author_str = f" by {author}" if author else ""
        lines.append(f"- [ ] [{title}]({url}){author_str} — score: {score}")

    md = "\n".join(lines)

    with open(OUTPUT_FILE, "w") as f:
        f.write(md)

    print(f"Markdown written to {OUTPUT_FILE}")

if __name__ == "__main__":
    generate_markdown()
