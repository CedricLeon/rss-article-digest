# RSS Article Digest

A personal research assistant pipeline to explore recent scientific publications. It fetches updates from RSS feeds daily and delivers a curated, ranked (using LLMs) weekly digest to your email.

**Acknowledgements**: The idea for this project came from [this Reddit post](https://www.reddit.com/r/ObsidianMD/comments/1pmglpy/loving_obsidian_for_my_academic_literature/) by @jrcasey, describing how he used RSS feeds and LLMs to get a weekly email with articles ranked by interest. His original setup is at [jrcasey/RSS_Agent](https://github.com/jrcasey/RSS_Agent/tree/main).

## How it Works

The pipeline is split across two GitHub Actions:

1. **Daily Fetch** (`fetch-daily.yml`, 08:00 UTC every day): Fetches new articles from all configured RSS feeds, deduplicates them against the permanent seen-IDs log, and appends new entries to the weekly cache. Revised arXiv versions are treated as the same article during deduplication, so `v2`, `v3`, and later revisions do not reappear once the base paper has already been seen.

2. **Weekly Curation** (`weekly_rss.yml`, Monday 02:00 UTC):
   - Does one final feed fetch to catch any articles published since Sunday's daily run.
   - Uses OpenAI (GPT-4o-mini) to score every cached article against your research interests.
   - Generates a Markdown report (`output/RSS-feed_YYYY-MM-DD_YYYY-WNN.md`) of the top-ranked articles.
   - Emails the report to you as an attachment.
   - Resets the raw feed cache to `[]` for the next week.
   - Commits the updated cache state and the new report to the repo.

## File Reference

### Configuration (committed, user-edited)

| File | Purpose |
| --- | --- |
| `config/feeds.json` | List of RSS feed URLs to follow |
| `config/interests.txt` | Natural-language description of your research interests, used as the AI ranking prompt |

### Cache (committed, pipeline-managed)

| File | Purpose | Written by | Read by |
| --- | --- | --- | --- |
| `cache/raw_feeds.json` | Accumulates all new articles fetched during the week. Reset to `[]` each Monday after ranking. | `fetch_feeds.py` (append) · weekly workflow (reset) | `rank_articles.py` |
| `cache/seen_ids.txt` | Permanent log of every article ID ever fetched, used to skip duplicates on future fetches. Never cleared. | `fetch_feeds.py` | `fetch_feeds.py` |
| `cache/ranked_articles.json` | Top-scored articles from the current weekly run. Transient — exists only during the weekly workflow, **never committed (gitignored)**. | `rank_articles.py` | `generate_markdown.py` |

### Output (committed, pipeline-managed)

| File | Purpose |
| --- | --- |
| `output/RSS-feed_YYYY-MM-DD_YYYY-WNN.md` | Weekly curated digest. Generated every Monday, committed to the repo, and emailed as an attachment. |

## Setup & Configuration

### Prerequisites

- Python dependencies listed in `requirements.txt`
- An OpenAI API key

### Forking This Repository

If you're setting up your own fork (e.g., for different interests or email):

1. **Fork the repo** on GitHub
2. **Update workflow files** — The GitHub Actions workflows have hardcoded references that need updating:
   - `.github/workflows/fetch-daily.yml` — If you changed the repository URL structure
   - `.github/workflows/weekly_rss.yml` — Check if needed
   - As of the latest version, these now use `${GITHUB_REPOSITORY}` env var automatically ✅
3. **`GITHUB_TOKEN` permissions** — Already configured with `permissions: contents: write` ✅
4. Continue with the configuration steps below

### Configuration Files

**`config/feeds.json`** — add your RSS feed URLs:

```json
{
  "feeds": [
    {"name": "ArXiv ML", "url": "https://rss.arxiv.org/rss/cs.LG"},
    {"url": "https://some-other-feed.xml"}
  ]
}
```

**`config/interests.txt`** — describe your research interests in plain language (this is injected directly into the AI ranking prompt):

```text
Machine Learning, Large Language Models, Reinforcement Learning, Robotics.
```

### GitHub Secrets

Configure the following [repository secrets](https://docs.github.com/en/actions/security-guides/using-secrets-in-github-actions) to enable the automated pipeline:

| Secret | Purpose |
| --- | --- |
| `OPENAI_API_KEY` | Used by `rank_articles.py` to score articles with GPT-4o-mini |
| `GMAIL_EMAIL` | Gmail address used to send the digest |
| `GMAIL_APP_PASSWORD` | [App Password](https://support.google.com/accounts/answer/185833) for the Gmail account |
| `RECIPIENT_EMAIL` | Address where you want to receive the weekly digest |
