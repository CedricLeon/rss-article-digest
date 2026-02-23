import json
import os
from openai import OpenAI

RAW_FEED_CACHE = "cache/raw_feeds.json"
RANKED_CACHE = "cache/ranked_articles.json"
INTERESTS_FILE = os.path.join("config", "interests.txt")

client = OpenAI()



def load_interests():
    """Load interests from config/interests.txt."""
    if not os.path.exists(INTERESTS_FILE):
        return "General Technology and Science"
    with open(INTERESTS_FILE, "r") as f:
        return f.read().strip()

# DOMAIN-SPECIFIC PROMPT
def get_ranking_prompt():
    interests = load_interests()
    return f"""
You are a domain expert in the fields detailed below. Score the relevance of this article to the following interests:

{interests}

Give this article a score from 0 to 100. A score of 100 means “highly relevant" and implies overlap with multiple interests.
Be granular and precise in your assessment. Rely on specific keywords, topics, and concepts that align with the interests.

Return ONLY a JSON object: {{"score": float}}
"""

def get_relevance_score(title, content):
    text = f"Title: {title}\nAbstract: {content}"
    
    # Truncate for the chat model as well to save costs and avoid excessive context
    max_chars = 24000
    if len(text) > max_chars:
        text = text[:max_chars]

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": get_ranking_prompt()},
            {"role": "user", "content": text}
        ]
    )
    try:
        return float(json.loads(response.choices[0].message.content)["score"])
    except Exception:
        return 0.0

def rank_articles(threshold=50.0, keep_top_n=100):
    with open(RAW_FEED_CACHE, "r") as f:
        articles = json.load(f)

    ranked = []

    for a in articles:
        score = get_relevance_score(a["title"], a["content"])
        ranked.append({
            "id": a["id"],
            "title": a["title"],
            "link": a["link"],
            "content": a["content"],
            "author": a.get("author", ""),
            "score": score,
        })

    # Sort by score
    ranked_sorted = sorted(ranked, key=lambda x: x["score"], reverse=True)

    # Filter: keep only top N OR those above threshold
    filtered = [a for a in ranked_sorted if a["score"] >= threshold]
    if len(filtered) < keep_top_n:
        filtered = ranked_sorted[:keep_top_n]

    # Save filtered results
    with open(RANKED_CACHE, "w") as f:
        json.dump(filtered, f, indent=2)

    print(f"Ranked {len(ranked)} articles. Kept {len(filtered)}.")
    return filtered

if __name__ == "__main__":
    rank_articles()
