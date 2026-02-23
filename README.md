# RSS Article Digest

A personal research assistant pipeline to explore recent scientific publications. It fetches updates from RSS feeds daily and delivers a curated, ranked (using LLMs) weekly digest to your email.

**Acknowledgements**:
The idea for this project came from browsing Reddit, specifically [this post](https://www.reddit.com/r/ObsidianMD/comments/1pmglpy/loving_obsidian_for_my_academic_literature/) from @jrcasey. It described how he used RSS feeds and LLMs to get a weekly email with the latest articles published ranked depending on his interests. You can find his setup at [jrcasey/RSS_Agent](https://github.com/jrcasey/RSS_Agent/tree/main).

## How it Works

1. **Daily Fetch**: A GitHub Action runs every day to fetch new articles from your configured RSS feeds (`config/feeds.json`). New articles are de-duplicated and appended to the weekly cache.
2. **Weekly Curation**: On Monday mornings, another GitHub Action triggers to:
   - Load the week's cached articles.
   - Use OpenAI (GPT-4o-mini) to score each article based on your research interests (`config/interests.txt`).
   - Generate a Markdown report (`output/curated_latest.md`) of the top-ranked articles.
   - Email the report to you.
   - Commit the results and reset the cache for the next week.

## File Reference

### Configuration (committed, user-edited)

| File | Purpose | Written by |
|---|---|---|
| `config/feeds.json` | List of RSS feed URLs to follow | You |
| `config/interests.txt` | Natural-language description of your research interests, used as the AI ranking prompt | You |

### Cache (committed, pipeline-managed)

| File | Purpose | Written by | Read by |
|---|---|---|---|
| `cache/raw_feeds.json` | Accumulates all new articles fetched during the week (array of `{id, title, link, content, author}`). Reset to `[]` each Monday after ranking. | `fetch_feeds.py` (append) · weekly workflow (reset to `[]`) | `rank_articles.py` |
| `cache/seen_ids.txt` | Permanent log of every article ID ever fetched, used to skip duplicates on future fetches. Never cleared. | `fetch_feeds.py` | `fetch_feeds.py` |

### Cache (gitignored, transient)

| File | Purpose | Written by | Read by |
|---|---|---|---|
| `cache/ranked_articles.json` | Top-scored articles for the current week (array of `{id, title, link, content, author, score}`). Exists only during the weekly workflow run; never committed. | `rank_articles.py` | `generate_markdown.py` |

### Output (committed, pipeline-managed)

| File | Purpose | Written by |
|---|---|---|
| `output/curated_latest.md` | The current week's curated digest (overwritten each Monday). Emailed and committed. | `generate_markdown.py` |
| `output/YYYY-Www_YYYY-MM-DD.md` | Archived copies of past weekly digests. | Weekly workflow (copy of `curated_latest.md`) |
| `archive/raw_feeds_last_week.json` | Copy of last week's `raw_feeds.json`, kept for reference. Overwritten each Monday. | Weekly workflow |

## Setup & Configuration

### Prerequisites
- Specific Python dependencies (see `requirements.txt`)
- An OpenAI API Key

### Configuration Files

1. **`config/feeds.json`**:
   Add your RSS feed URLs here. Supported format:
   ```json
   {
     "feeds": [
       {"name": "ArXiv", "url": "http://export.arxiv.org/rss/cs.AI"},
       {"url": "https://some-other-feed.xml"}
     ]
   }
   ```

2. **`config/interests.txt`**:
   Describe your specific research interests in natural language. This text is used as the prompt for the AI ranker.
   ```text
   Machine Learning, Large Language Models, Reinforcement Learning, Robotics.
   ```

### GitHub Secrets

To enable the automated pipeline, you must configure the following [Secrets](https://docs.github.com/en/actions/security-guides/using-secrets-in-github-actions) in your repository settings:

- `OPENAI_API_KEY`: Your OpenAI API key (used for ranking articles with GPT-4o-mini).
- `GMAIL_EMAIL`: The Gmail address used to send the digest.
- `GMAIL_APP_PASSWORD`: The [App Password](https://support.google.com/accounts/answer/185833) for the Gmail account.
- `RECIPIENT_EMAIL`: The email address where you want to receive the digest.
