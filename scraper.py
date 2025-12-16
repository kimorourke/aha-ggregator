#!/usr/bin/env python3
"""
Scraper for AI "aha moment" posts from Reddit and Hacker News.
Fetches posts that describe breakthrough moments with AI tools.
"""

import httpx
import json
import time
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

# Search terms that indicate an "aha moment"
AHA_KEYWORDS = [
    "aha moment",
    "finally clicked",
    "finally understood",
    "mind blown",
    "game changer",
    "changed everything",
    "holy shit",
    "blew my mind",
    "lightbulb moment",
    "eureka",
    "finally get it",
    "now I understand",
    "changed how I",
    "never going back",
    "completely changed",
    "revelation",
    "breakthrough",
    "wow moment",
]

# AI tools we care about
AI_TOOLS = [
    "claude",
    "chatgpt",
    "gpt-4",
    "gpt4",
    "gemini",
    "grok",
    "perplexity",
    "copilot",
    "cursor",
    "anthropic",
    "openai",
    "llm",
    "ai assistant",
    "ai tool",
]

# Subreddits to search
SUBREDDITS = [
    "ChatGPT",
    "ClaudeAI",
    "LocalLLaMA",
    "artificial",
    "MachineLearning",
    "singularity",
    "OpenAI",
    "Bard",
    "perplexity_ai",
    "PromptEngineering",
]

USER_AGENT = "AhaAggregator/1.0 (Growth Research Tool)"


def has_aha_signal(text: str) -> bool:
    """Check if text contains aha moment indicators."""
    text_lower = text.lower()
    return any(keyword in text_lower for keyword in AHA_KEYWORDS)


def has_ai_mention(text: str) -> bool:
    """Check if text mentions an AI tool."""
    text_lower = text.lower()
    return any(tool in text_lower for tool in AI_TOOLS)


def extract_ai_tool(text: str) -> str:
    """Extract the primary AI tool mentioned."""
    text_lower = text.lower()

    # Check specific tools first (more specific matches)
    tool_mapping = [
        (["claude", "anthropic"], "Claude"),
        (["chatgpt", "gpt-4", "gpt4", "openai"], "ChatGPT"),
        (["gemini", "bard"], "Gemini"),
        (["grok"], "Grok"),
        (["perplexity"], "Perplexity"),
        (["copilot"], "Copilot"),
        (["cursor"], "Cursor"),
    ]

    for keywords, tool_name in tool_mapping:
        if any(kw in text_lower for kw in keywords):
            return tool_name

    return "General"


def fetch_reddit_posts(subreddit: str, limit: int = 100) -> list[dict]:
    """Fetch recent posts from a subreddit."""
    posts = []
    url = f"https://www.reddit.com/r/{subreddit}/new.json?limit={limit}"

    try:
        with httpx.Client(timeout=30) as client:
            response = client.get(url, headers={"User-Agent": USER_AGENT})
            response.raise_for_status()
            data = response.json()

            for child in data.get("data", {}).get("children", []):
                post = child.get("data", {})
                title = post.get("title", "")
                selftext = post.get("selftext", "")
                full_text = f"{title} {selftext}"

                # Filter for aha moments about AI
                if has_aha_signal(full_text) and has_ai_mention(full_text):
                    posts.append({
                        "source": "Reddit",
                        "subreddit": subreddit,
                        "title": title,
                        "text": selftext[:2000] if selftext else "",
                        "url": f"https://reddit.com{post.get('permalink', '')}",
                        "score": post.get("score", 0),
                        "num_comments": post.get("num_comments", 0),
                        "created_utc": post.get("created_utc", 0),
                        "author": post.get("author", ""),
                        "ai_tool": extract_ai_tool(full_text),
                    })
    except Exception as e:
        print(f"Error fetching r/{subreddit}: {e}")

    return posts


def fetch_reddit_search(query: str, limit: int = 100) -> list[dict]:
    """Search Reddit for posts matching a query."""
    posts = []
    url = f"https://www.reddit.com/search.json?q={query}&sort=relevance&limit={limit}"

    try:
        with httpx.Client(timeout=30) as client:
            response = client.get(url, headers={"User-Agent": USER_AGENT})
            response.raise_for_status()
            data = response.json()

            for child in data.get("data", {}).get("children", []):
                post = child.get("data", {})
                title = post.get("title", "")
                selftext = post.get("selftext", "")
                full_text = f"{title} {selftext}"

                # Must mention an AI tool
                if has_ai_mention(full_text):
                    posts.append({
                        "source": "Reddit",
                        "subreddit": post.get("subreddit", ""),
                        "title": title,
                        "text": selftext[:2000] if selftext else "",
                        "url": f"https://reddit.com{post.get('permalink', '')}",
                        "score": post.get("score", 0),
                        "num_comments": post.get("num_comments", 0),
                        "created_utc": post.get("created_utc", 0),
                        "author": post.get("author", ""),
                        "ai_tool": extract_ai_tool(full_text),
                    })
    except Exception as e:
        print(f"Error searching Reddit for '{query}': {e}")

    return posts


def fetch_hn_top_stories(limit: int = 500) -> list[int]:
    """Fetch top story IDs from Hacker News."""
    url = "https://hacker-news.firebaseio.com/v0/topstories.json"
    try:
        with httpx.Client(timeout=30) as client:
            response = client.get(url)
            response.raise_for_status()
            return response.json()[:limit]
    except Exception as e:
        print(f"Error fetching HN top stories: {e}")
        return []


def fetch_hn_new_stories(limit: int = 500) -> list[int]:
    """Fetch new story IDs from Hacker News."""
    url = "https://hacker-news.firebaseio.com/v0/newstories.json"
    try:
        with httpx.Client(timeout=30) as client:
            response = client.get(url)
            response.raise_for_status()
            return response.json()[:limit]
    except Exception as e:
        print(f"Error fetching HN new stories: {e}")
        return []


def fetch_hn_item(item_id: int) -> Optional[dict]:
    """Fetch a single HN item."""
    url = f"https://hacker-news.firebaseio.com/v0/item/{item_id}.json"
    try:
        with httpx.Client(timeout=10) as client:
            response = client.get(url)
            response.raise_for_status()
            return response.json()
    except Exception as e:
        return None


def fetch_hn_posts() -> list[dict]:
    """Fetch and filter Hacker News posts for aha moments."""
    posts = []

    # Get both top and new stories
    story_ids = list(set(fetch_hn_top_stories(300) + fetch_hn_new_stories(300)))
    print(f"Checking {len(story_ids)} HN stories...")

    for i, story_id in enumerate(story_ids):
        if i % 50 == 0:
            print(f"  Processed {i}/{len(story_ids)} HN stories...")

        item = fetch_hn_item(story_id)
        if not item or item.get("type") != "story":
            continue

        title = item.get("title", "")
        text = item.get("text", "") or ""
        full_text = f"{title} {text}"

        # Filter for aha moments about AI
        if has_aha_signal(full_text) and has_ai_mention(full_text):
            posts.append({
                "source": "HackerNews",
                "title": title,
                "text": text[:2000] if text else "",
                "url": item.get("url") or f"https://news.ycombinator.com/item?id={story_id}",
                "hn_url": f"https://news.ycombinator.com/item?id={story_id}",
                "score": item.get("score", 0),
                "num_comments": item.get("descendants", 0),
                "created_utc": item.get("time", 0),
                "author": item.get("by", ""),
                "ai_tool": extract_ai_tool(full_text),
            })

        # Be nice to the API
        time.sleep(0.1)

    return posts


def fetch_hn_search_algolia(query: str, limit: int = 100) -> list[dict]:
    """Search HN via Algolia API for specific terms."""
    posts = []
    url = f"https://hn.algolia.com/api/v1/search?query={query}&tags=story&hitsPerPage={limit}"

    try:
        with httpx.Client(timeout=30) as client:
            response = client.get(url)
            response.raise_for_status()
            data = response.json()

            for hit in data.get("hits", []):
                title = hit.get("title", "")
                text = hit.get("story_text", "") or ""
                full_text = f"{title} {text}"

                if has_ai_mention(full_text):
                    posts.append({
                        "source": "HackerNews",
                        "title": title,
                        "text": text[:2000] if text else "",
                        "url": hit.get("url") or f"https://news.ycombinator.com/item?id={hit.get('objectID')}",
                        "hn_url": f"https://news.ycombinator.com/item?id={hit.get('objectID')}",
                        "score": hit.get("points", 0),
                        "num_comments": hit.get("num_comments", 0),
                        "created_utc": hit.get("created_at_i", 0),
                        "author": hit.get("author", ""),
                        "ai_tool": extract_ai_tool(full_text),
                    })
    except Exception as e:
        print(f"Error searching HN Algolia for '{query}': {e}")

    return posts


def deduplicate_posts(posts: list[dict]) -> list[dict]:
    """Remove duplicate posts based on URL."""
    seen_urls = set()
    unique_posts = []

    for post in posts:
        url = post.get("url", "")
        if url and url not in seen_urls:
            seen_urls.add(url)
            unique_posts.append(post)

    return unique_posts


def load_existing_urls(data_file: Path) -> set[str]:
    """Load URLs of already-processed posts."""
    urls = set()
    if data_file.exists():
        with open(data_file, "r") as f:
            for line in f:
                try:
                    item = json.loads(line)
                    urls.add(item.get("url", ""))
                except json.JSONDecodeError:
                    continue
    return urls


def scrape_all(data_dir: Path = Path("data")) -> list[dict]:
    """Run the full scraping pipeline."""
    data_dir.mkdir(exist_ok=True)
    data_file = data_dir / "aha_moments_raw.jsonl"

    # Load existing URLs to avoid duplicates
    existing_urls = load_existing_urls(data_file)
    print(f"Found {len(existing_urls)} existing posts")

    all_posts = []

    # Reddit: Search for aha moment terms
    print("\n--- Searching Reddit ---")
    for keyword in ["aha moment AI", "finally clicked AI", "mind blown ChatGPT", "mind blown Claude", "game changer AI"]:
        print(f"Searching Reddit for: {keyword}")
        posts = fetch_reddit_search(keyword, limit=50)
        all_posts.extend(posts)
        time.sleep(2)  # Rate limiting

    # Reddit: Check specific subreddits
    for subreddit in SUBREDDITS[:5]:  # Limit to avoid rate limits
        print(f"Checking r/{subreddit}...")
        posts = fetch_reddit_posts(subreddit, limit=50)
        all_posts.extend(posts)
        time.sleep(2)

    # Hacker News: Search via Algolia
    print("\n--- Searching Hacker News ---")
    for query in ["aha moment AI", "LLM changed", "Claude AI", "ChatGPT workflow"]:
        print(f"Searching HN for: {query}")
        posts = fetch_hn_search_algolia(query, limit=50)
        all_posts.extend(posts)
        time.sleep(1)

    # Deduplicate
    all_posts = deduplicate_posts(all_posts)
    print(f"\nFound {len(all_posts)} total unique posts")

    # Filter out already-processed posts
    new_posts = [p for p in all_posts if p.get("url") not in existing_urls]
    print(f"Found {len(new_posts)} new posts to process")

    # Save raw posts for classification
    if new_posts:
        with open(data_file, "a") as f:
            for post in new_posts:
                post["scraped_at"] = datetime.utcnow().isoformat()
                f.write(json.dumps(post) + "\n")
        print(f"Saved {len(new_posts)} new posts to {data_file}")

    return new_posts


if __name__ == "__main__":
    posts = scrape_all()
    print(f"\nScraping complete. Found {len(posts)} new aha moment candidates.")
