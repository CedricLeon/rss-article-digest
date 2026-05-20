import feedparser
import json
import os
import hashlib
import re

# Configuration
FEED_LIST_FILE = os.path.join("config", "feeds.json")
CACHE_DIR = "cache"
RAW_FEED_CACHE = os.path.join(CACHE_DIR, "raw_feeds.json")
SEEN_IDS_FILE = os.path.join(CACHE_DIR, "seen_ids.txt")

# Ensure cache directory exists
os.makedirs(CACHE_DIR, exist_ok=True)

def load_raw_feed_cache():
    if not os.path.exists(RAW_FEED_CACHE):
        return []
    with open(RAW_FEED_CACHE, "r") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            return []
    return data if isinstance(data, list) else []

# Utility functions
def hash_id(s: str) -> str:
    """Stable ID generator for any article."""
    return hashlib.sha256(s.encode("utf-8")).hexdigest()[:16]


ARXIV_VERSION_RE = re.compile(r"((?:arXiv:)?\d{4}\.\d{4,5})v\d+", re.IGNORECASE)


def normalize_entry_id(entry_id: str) -> str:
    """Collapse versioned arXiv identifiers to their base paper ID before hashing."""
    return ARXIV_VERSION_RE.sub(r"\1", entry_id.strip())

# Load seen IDs from file
def load_seen_ids():
    if not os.path.exists(SEEN_IDS_FILE):
        return set()
    with open(SEEN_IDS_FILE, "r") as f:
        return {line.strip() for line in f if line.strip()}

# Save seen IDs to file
def save_seen_ids(ids):
    with open(SEEN_IDS_FILE, "w") as f:
        for id_ in sorted(ids):
            f.write(id_ + "\n")

# Load feed list from config/feeds.json
def load_feed_list():
    """Load config/feeds.json and return a list of URLs."""
    if not os.path.exists(FEED_LIST_FILE):
        raise FileNotFoundError(f"{FEED_LIST_FILE} not found.")
    
    with open(FEED_LIST_FILE, "r") as f:
        data = json.load(f)
        
    feeds = []
    # Handle the structure {"feeds": [{"name": "...", "url": "..."}]}
    if isinstance(data, dict) and "feeds" in data:
        for item in data["feeds"]:
            if "url" in item:
                feeds.append(item["url"])
    # Handle simple list if changed later
    elif isinstance(data, list):
        for item in data:
             if isinstance(item, dict) and "url" in item:
                feeds.append(item["url"])
             elif isinstance(item, str):
                feeds.append(item)
                
    return feeds

def extract_authors(entry) -> str:
    """
    Robustly extract authors from a feedparser entry, handling the main formats:
      - Atom feeds (arXiv, ACM, Nature, SemiEng): `authors` is a list of dicts
            e.g. [{'name': 'John Doe'}, {'name': 'Jane Smith'}]
      - IEEE Xplore RSS: `authors` is a semicolon-separated string
            e.g. 'Kim, Y.;Lee, H.;Choi, S.;'
      - Generic RSS: plain `author` string
      - ScienceDirect and others: no author field at all → returns ''
    """
    authors_field = entry.get("authors")

    # List of dicts (Atom-style: arXiv, ACM, Nature, SemiEng, ...)
    if isinstance(authors_field, list) and authors_field:
        names = [p.get("name", "").strip() for p in authors_field if p.get("name", "").strip()]
        if names:
            return ", ".join(names)

    # Semicolon-separated string (IEEE Xplore)
    if isinstance(authors_field, str) and authors_field.strip():
        names = [n.strip() for n in authors_field.split(";") if n.strip()]
        if names:
            return ", ".join(names)

    # Plain author string fallback (generic RSS)
    author = entry.get("author", "").strip()
    if author:
        return author

    return ""


def fetch_all_feeds():
    feeds = load_feed_list()
    seen_ids = load_seen_ids()
    existing_entries = load_raw_feed_cache()
    new_entries = []
    # Fetch and process each feed
    for feed_url in feeds:
        print(f"Fetching: {feed_url}")
        parsed = feedparser.parse(feed_url)
        # Process each entry in the feed
        for entry in parsed.entries:
            entry_id = entry.get("id") or entry.get("link") or entry.get("title")
            if not entry_id:
                continue
            # Generate a stable hash ID for the entry
            hashed_id = hash_id(normalize_entry_id(entry_id))
            # Skip if already seen
            if hashed_id in seen_ids:
                continue
            # Extract relevant fields
            title = entry.get("title", "")
            link = entry.get("link", "")
            content = ""
            # Abstract/description
            if "content" in entry and len(entry.content) > 0:
                content = entry.content[0].value
            elif "summary" in entry:
                content = entry.summary
            
            # Author
            author = extract_authors(entry)

            # Store the new entry
            new_entries.append({
                "id": hashed_id,
                "title": title,
                "link": link,
                "content": content,
                "author": author
            })
            # Mark this ID as seen
            seen_ids.add(hashed_id)

    # Save new articles to cache (append to existing cache)
    all_entries = existing_entries + new_entries
    with open(RAW_FEED_CACHE, "w") as f:
        json.dump(all_entries, f, indent=2)

    save_seen_ids(seen_ids)

    print(f"Fetched {len(new_entries)} new unseen articles.")
    return new_entries

if __name__ == "__main__":
    fetch_all_feeds()