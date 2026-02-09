# RSS Article Digest

A personal research assistant pipeline to explore recent scientific publications. It fetches updates from RSS feeds daily and delivers a curated, ranked (using LLMs) weekly digest to your email.

**Acknowledgements**:
The idea for this project came from browsing Reddit, specifically [this post](https://www.reddit.com/r/ObsidianMD/comments/1pmglpy/loving_obsidian_for_my_academic_literature/) from @jrcasey. It described how he used RSS feeds and LLMs to get a weekly email with the latest articles published ranked depending on his interests. You can find his setup at [jrcasey/RSS_Agent](https://github.com/jrcasey/RSS_Agent/tree/main).

## How it Works

1. **Daily Fetch**: A GitHub Action runs every day to fetch new articles from your configured RSS feeds (`config/feeds.json`). These are de-duplicated and stored in a cache.
2. **Weekly Curation**: On Monday mornings, another GitHub Action triggers to:
   - Load the week's cached articles.
   - Use OpenAI (Embeddings + GPT-4o-mini) to score each article based on your research interests (`config/interests.txt`).
   - Generate a Markdown report (`output/curated_latest.md`) of the top-ranked articles.
   - Email the report to you.
   - Commit the results and clear the cache for the next week.

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

- `OPENAI_API_KEY`: Your OpenAI API key (used for ranking and embeddings).
- `GMAIL_EMAIL`: The Gmail address used to send the digest.
- `GMAIL_APP_PASSWORD`: The [App Password](https://support.google.com/accounts/answer/185833) for the Gmail account.
- `RECIPIENT_EMAIL`: The email address where you want to receive the digest.
