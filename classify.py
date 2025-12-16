#!/usr/bin/env python3
"""
Classify aha moment posts using Claude API.
Generates strategic analysis: layer, growth lever, realization, provocation.
"""

import anthropic
import json
import time
from pathlib import Path
from datetime import datetime

CLASSIFICATION_PROMPT = """You are analyzing user testimonials about AI tools to identify "aha moments" - breakthrough realizations that changed how someone thinks about or uses AI.

Analyze this post and extract strategic insights for a Growth team.

POST:
Source: {source}
Title: {title}
Content: {text}
AI Tool Mentioned: {ai_tool}

Respond with a JSON object containing:

1. "is_valid_aha_moment": boolean - Is this genuinely an aha moment (breakthrough realization) vs. just a complaint, question, or neutral comment?

2. "layer": one of "wow", "how", or "what"
   - "wow": Emotional breakthrough - they felt something shift, mind was blown, completely changed their view
   - "how": Practical discovery - they learned a new way to use AI, workflow improvement, technique
   - "what": Conceptual understanding - they now understand what AI is/isn't, mental model shift

3. "growth_levers": array of applicable levers from ["activation", "retention", "differentiation", "b2b"]
   - "activation": Helps new users get started or have their first success
   - "retention": Keeps users coming back, builds habits
   - "differentiation": Shows what makes one AI different from others
   - "b2b": Relevant to business/team use cases

4. "use_case": short category (e.g., "Code generation", "Document analysis", "Creative writing", "Research", "Learning", "Workflow automation")

5. "quote": The most compelling 1-2 sentence excerpt that captures the aha moment. Clean it up for readability but preserve the authentic voice. Use proper punctuation.

6. "realization": A single punchy sentence summarizing what they realized (written in third person, e.g., "First-try accuracy creates trust and saves time")

7. "provocation": A strategic question this raises for the Growth team (e.g., "What if onboarding taught 'conversation' not 'prompting'?")

8. "confidence": 0-100 how confident you are this is a genuine, useful aha moment

Only respond with the JSON object, no other text."""


def classify_post(client: anthropic.Anthropic, post: dict) -> dict | None:
    """Classify a single post using Claude."""
    try:
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            messages=[
                {
                    "role": "user",
                    "content": CLASSIFICATION_PROMPT.format(
                        source=post.get("source", ""),
                        title=post.get("title", ""),
                        text=post.get("text", "")[:1500],  # Truncate long posts
                        ai_tool=post.get("ai_tool", "General"),
                    ),
                }
            ],
        )

        # Parse the response
        response_text = message.content[0].text.strip()

        # Handle markdown code blocks
        if response_text.startswith("```"):
            response_text = response_text.split("```")[1]
            if response_text.startswith("json"):
                response_text = response_text[4:]
            response_text = response_text.strip()

        result = json.loads(response_text)
        return result

    except json.JSONDecodeError as e:
        print(f"JSON parse error: {e}")
        print(f"Response was: {response_text[:200]}")
        return None
    except Exception as e:
        print(f"Classification error: {e}")
        return None


def classify_all(
    data_dir: Path = Path("data"),
    min_confidence: int = 60,
    min_score: int = 5,
) -> list[dict]:
    """Classify all raw posts and save valid aha moments."""
    raw_file = data_dir / "aha_moments_raw.jsonl"
    classified_file = data_dir / "aha_moments_classified.jsonl"
    final_file = data_dir / "aha_moments.jsonl"

    if not raw_file.exists():
        print("No raw posts to classify. Run scraper.py first.")
        return []

    # Load already-classified URLs
    classified_urls = set()
    if classified_file.exists():
        with open(classified_file, "r") as f:
            for line in f:
                try:
                    item = json.loads(line)
                    classified_urls.add(item.get("url", ""))
                except json.JSONDecodeError:
                    continue

    # Load raw posts that need classification
    posts_to_classify = []
    with open(raw_file, "r") as f:
        for line in f:
            try:
                post = json.loads(line)
                if post.get("url") not in classified_urls:
                    posts_to_classify.append(post)
            except json.JSONDecodeError:
                continue

    if not posts_to_classify:
        print("No new posts to classify.")
        return []

    print(f"Classifying {len(posts_to_classify)} posts...")

    client = anthropic.Anthropic()  # Uses ANTHROPIC_API_KEY env var
    valid_moments = []

    for i, post in enumerate(posts_to_classify):
        print(f"  [{i+1}/{len(posts_to_classify)}] {post.get('title', '')[:50]}...")

        # Skip low-engagement posts
        if post.get("score", 0) < min_score:
            print(f"    Skipping (low score: {post.get('score', 0)})")
            continue

        result = classify_post(client, post)

        if result:
            # Merge classification with original post data
            classified = {
                **post,
                **result,
                "classified_at": datetime.utcnow().isoformat(),
            }

            # Save all classified posts (for debugging/review)
            with open(classified_file, "a") as f:
                f.write(json.dumps(classified) + "\n")

            # Only keep valid, high-confidence aha moments
            if result.get("is_valid_aha_moment") and result.get("confidence", 0) >= min_confidence:
                valid_moments.append(classified)
                print(f"    Valid aha moment (confidence: {result.get('confidence')})")
            else:
                print(f"    Not valid (is_valid: {result.get('is_valid_aha_moment')}, confidence: {result.get('confidence', 0)})")

        # Rate limiting
        time.sleep(0.5)

    # Append valid moments to final file
    if valid_moments:
        with open(final_file, "a") as f:
            for moment in valid_moments:
                f.write(json.dumps(moment) + "\n")
        print(f"\nAdded {len(valid_moments)} valid aha moments to {final_file}")

    return valid_moments


def load_all_moments(data_dir: Path = Path("data")) -> list[dict]:
    """Load all classified aha moments."""
    final_file = data_dir / "aha_moments.jsonl"
    moments = []

    if final_file.exists():
        with open(final_file, "r") as f:
            for line in f:
                try:
                    moments.append(json.loads(line))
                except json.JSONDecodeError:
                    continue

    return moments


if __name__ == "__main__":
    moments = classify_all()
    print(f"\nClassification complete. {len(moments)} new valid aha moments.")

    all_moments = load_all_moments()
    print(f"Total aha moments in database: {len(all_moments)}")
