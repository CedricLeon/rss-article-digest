import feedparser
import json
import os

# Explore an RSS feed to find where abstracts are located
feed_url = "https://connect.biorxiv.org/biorxiv_xml.php?subject=systems_biology"
parsed = feedparser.parse(feed_url)

# list the keys of the first entry
first_entry = parsed.entries[0]
first_entry.keys()

# print the first entry entirely for inspection
print(json.dumps(first_entry, indent=2))

# ---- Look for abstract/description fields ----
FEED_LIST_FILE = "newFeeds.txt"
def load_feed_list():
    """Load feeds.txt (one URL per line, ignore empty lines and comments)."""
    if not os.path.exists(FEED_LIST_FILE):
        raise FileNotFoundError("feeds.txt not found in project root.")
    feeds = []
    with open(FEED_LIST_FILE, "r") as f:
        for line in f:
            stripped = line.strip()
            if stripped and not stripped.startswith("#"):
                feeds.append(stripped)
    return feeds
    
feeds = load_feed_list()
print("Loaded feeds:")
print(feeds)
