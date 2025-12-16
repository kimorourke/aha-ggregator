#!/usr/bin/env python3
"""
Main collection script - runs the full pipeline.
Usage: python collect.py
"""

from scraper import scrape_all
from classify import classify_all, load_all_moments
from generate_html import generate_html, load_moments


def main():
    print("=" * 60)
    print("AHA-GGREGATOR COLLECTION PIPELINE")
    print("=" * 60)

    # Step 1: Scrape new posts
    print("\n[1/3] SCRAPING NEW POSTS")
    print("-" * 40)
    new_posts = scrape_all()
    print(f"Found {len(new_posts)} new posts to classify")

    # Step 2: Classify with Claude
    print("\n[2/3] CLASSIFYING WITH CLAUDE")
    print("-" * 40)
    if new_posts:
        new_moments = classify_all()
        print(f"Added {len(new_moments)} new valid aha moments")
    else:
        print("No new posts to classify")

    # Step 3: Generate HTML
    print("\n[3/3] GENERATING HTML")
    print("-" * 40)
    moments = load_moments()
    generate_html(moments)

    # Summary
    print("\n" + "=" * 60)
    print("COLLECTION COMPLETE")
    print("=" * 60)
    all_moments = load_all_moments()
    print(f"Total aha moments in database: {len(all_moments)}")
    print("Page regenerated: index.html")


if __name__ == "__main__":
    main()
