#!/usr/bin/env python3
"""
Generate the Aha-ggregator HTML page from classified aha moments.
"""

import json
from pathlib import Path
from datetime import datetime
from collections import Counter
from html import escape

def load_moments(data_dir: Path = Path("data")) -> list[dict]:
    """Load all classified aha moments."""
    moments_file = data_dir / "aha_moments.jsonl"
    moments = []

    if moments_file.exists():
        with open(moments_file, "r") as f:
            for line in f:
                try:
                    moments.append(json.loads(line))
                except json.JSONDecodeError:
                    continue

    # Sort by confidence (highest first), then by curated status
    moments.sort(key=lambda x: (x.get("curated", False), x.get("confidence", 0)), reverse=True)
    return moments


def analyze_patterns(moments: list[dict]) -> dict:
    """Analyze moments for dashboard insights."""
    # Count patterns in realizations
    realization_words = Counter()
    for m in moments:
        realization = m.get("realization", "").lower()
        for phrase in ["conversation", "dialogue", "partner", "thinking", "first-try", "accuracy", "trust", "time", "speed", "document", "pdf"]:
            if phrase in realization:
                realization_words[phrase] += 1

    # Count by layer
    layers = Counter(m.get("layer", "unknown") for m in moments)

    # Count by growth lever
    levers = Counter()
    for m in moments:
        for lever in m.get("growth_levers", []):
            levers[lever] += 1

    # Count by AI tool
    tools = Counter(m.get("ai_tool", "Unknown") for m in moments)

    return {
        "patterns": realization_words.most_common(5),
        "layers": layers,
        "levers": levers,
        "tools": tools,
        "total": len(moments),
    }


def generate_insights_html(analysis: dict) -> str:
    """Generate the insights dashboard section."""
    # Dynamic patterns based on actual data
    patterns = [
        (count, f'"{word.title()}" theme appears in realizations')
        for word, count in analysis["patterns"][:4]
    ]

    # Content gaps (these are more editorial - keeping them semi-static for now)
    gaps = [
        "No 'aha' stories about MCP or advanced features",
        "B2B end-user moments are missing entirely",
        "Claude Code 'wow' moments underrepresented",
        "Upgrade-triggering moments not captured",
    ]

    # Show-don't-tell opportunities
    opportunities = [
        "'Upload your longest PDF' as onboarding prompt",
        "Side-by-side comparison demos vs. competitors",
        "'Have a conversation' vs. 'give commands'",
        "Code that works on first try—showcase it",
    ]

    return f'''
        <div class="insights-dashboard">
            <div class="insight-card">
                <h3>Emerging patterns</h3>
                <ul class="insight-list">
                    {"".join(f'<li><span class="count">{count}×</span> {text}</li>' for count, text in patterns)}
                </ul>
            </div>

            <div class="insight-card">
                <h3>Content gaps revealed</h3>
                <ul class="insight-list">
                    {"".join(f"<li>{gap}</li>" for gap in gaps)}
                </ul>
            </div>

            <div class="insight-card">
                <h3>Show-don't-tell opportunities</h3>
                <ul class="insight-list">
                    {"".join(f"<li>{opp}</li>" for opp in opportunities)}
                </ul>
            </div>
        </div>
    '''


def generate_card_html(moment: dict, index: int) -> str:
    """Generate HTML for a single aha moment card."""
    layer = moment.get("layer", "wow")
    ai_tool = moment.get("ai_tool", "General")
    source = moment.get("source", "Unknown")
    use_case = escape(moment.get("use_case", ""))
    quote = escape(moment.get("quote", ""))
    url = escape(moment.get("url", "#"))
    realization = escape(moment.get("realization", ""))
    provocation = escape(moment.get("provocation", ""))
    growth_levers = moment.get("growth_levers", [])

    # Generate growth lever tags
    lever_tags = "".join(
        f'<span class="growth-tag {lever}">{lever.title()}</span>'
        for lever in growth_levers
    )

    # Data attributes for filtering
    growth_data = " ".join(growth_levers)

    return f'''
            <!-- Card {index + 1} -->
            <div class="card" data-layer="{layer}" data-growth="{growth_data}">
                <div class="card-main">
                    <div class="card-header">
                        <span class="layer-tag {layer}">{layer.title()}</span>
                        <span class="ai-tag">{escape(ai_tool)}</span>
                        <span class="source-tag">{escape(source)}</span>
                    </div>
                    <div class="use-case">{use_case}</div>
                    <p class="quote">{quote}</p>
                    <div class="meta-row">
                        <a href="{url}" target="_blank">Read full story →</a>
                    </div>
                </div>
                <div class="card-strategy">
                    <div class="strategy-section">
                        <div class="strategy-label">The realization</div>
                        <div class="strategy-content">{realization}</div>
                    </div>
                    <div class="strategy-section">
                        <div class="strategy-label">Provocation</div>
                        <div class="provocation">{provocation}</div>
                    </div>
                    <div class="strategy-section">
                        <div class="strategy-label">Growth levers</div>
                        <div class="growth-tags">
                            {lever_tags}
                        </div>
                    </div>
                </div>
            </div>
    '''


def generate_html(moments: list[dict], output_file: Path = Path("index.html")):
    """Generate the full HTML page."""
    analysis = analyze_patterns(moments)
    insights_html = generate_insights_html(analysis)
    cards_html = "".join(generate_card_html(m, i) for i, m in enumerate(moments))

    last_updated = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Aha-ggregator | Wow Moments for Growth</title>
    <style>
        :root {{
            --bg: #fafafa;
            --surface: #ffffff;
            --text: #18181b;
            --text-muted: #71717a;
            --border: #e4e4e7;
            --border-light: #f4f4f5;
            --accent: #2563eb;
            --accent-soft: #eff6ff;

            /* Semantic colors - subtle, purposeful */
            --wow: #7c3aed;
            --wow-soft: #f5f3ff;
            --how: #ca8a04;
            --how-soft: #fefce8;
            --what: #0891b2;
            --what-soft: #ecfeff;

            /* AI brand colors - muted for professionalism */
            --claude: #c2410c;
            --chatgpt: #059669;
            --gemini: #2563eb;
            --grok: #18181b;
            --perplexity: #7c3aed;
            --general: #71717a;

            /* Growth levers */
            --activation: #059669;
            --retention: #2563eb;
            --differentiation: #dc2626;
            --b2b: #ca8a04;
        }}

        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', sans-serif;
            background: var(--bg);
            color: var(--text);
            line-height: 1.6;
            font-size: 15px;
            -webkit-font-smoothing: antialiased;
        }}

        .container {{
            max-width: 1100px;
            margin: 0 auto;
            padding: 3rem 1.5rem;
        }}

        /* Header */
        header {{
            margin-bottom: 2.5rem;
        }}

        h1 {{
            font-size: 2rem;
            font-weight: 600;
            letter-spacing: -0.02em;
            margin-bottom: 0.5rem;
        }}

        .tagline {{
            color: var(--text-muted);
            font-size: 1.1rem;
        }}

        .last-updated {{
            font-size: 0.8rem;
            color: var(--text-muted);
            margin-top: 0.5rem;
        }}

        /* Purpose block */
        .purpose {{
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 1.5rem;
            margin-bottom: 2.5rem;
        }}

        .purpose-label {{
            font-size: 0.75rem;
            font-weight: 600;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: 0.75rem;
        }}

        .purpose p {{
            color: var(--text);
            font-size: 0.95rem;
            margin-bottom: 0.5rem;
        }}

        .purpose p:last-child {{
            margin-bottom: 0;
        }}

        .purpose strong {{
            font-weight: 600;
        }}

        .purpose .metrics {{
            margin-top: 1rem;
            padding-top: 1rem;
            border-top: 1px solid var(--border-light);
            font-size: 0.85rem;
            color: var(--text-muted);
        }}

        /* Insights dashboard */
        .insights-dashboard {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 1rem;
            margin-bottom: 2.5rem;
        }}

        @media (max-width: 900px) {{
            .insights-dashboard {{
                grid-template-columns: 1fr;
            }}
        }}

        .insight-card {{
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 1.25rem;
        }}

        .insight-card h3 {{
            font-size: 0.85rem;
            font-weight: 600;
            margin-bottom: 1rem;
            color: var(--text);
        }}

        .insight-list {{
            list-style: none;
        }}

        .insight-list li {{
            font-size: 0.875rem;
            color: var(--text-muted);
            padding: 0.5rem 0;
            border-bottom: 1px solid var(--border-light);
            display: flex;
            align-items: flex-start;
            gap: 0.75rem;
        }}

        .insight-list li:last-child {{
            border-bottom: none;
            padding-bottom: 0;
        }}

        .insight-list .count {{
            background: var(--border-light);
            color: var(--text-muted);
            font-size: 0.7rem;
            font-weight: 600;
            padding: 0.2rem 0.5rem;
            border-radius: 4px;
            flex-shrink: 0;
        }}

        /* Filters */
        .filter-section {{
            display: flex;
            flex-wrap: wrap;
            gap: 1.5rem;
            margin-bottom: 2rem;
            align-items: center;
        }}

        .filter-group {{
            display: flex;
            gap: 0.5rem;
            align-items: center;
            flex-wrap: wrap;
        }}

        .filter-label {{
            font-size: 0.8rem;
            color: var(--text-muted);
            font-weight: 500;
        }}

        .filter-btn {{
            padding: 0.4rem 0.85rem;
            border: 1px solid var(--border);
            background: var(--surface);
            border-radius: 6px;
            cursor: pointer;
            font-size: 0.8rem;
            font-weight: 500;
            color: var(--text-muted);
            transition: all 0.15s ease;
        }}

        .filter-btn:hover {{
            border-color: var(--text-muted);
            color: var(--text);
        }}

        .filter-btn.active {{
            background: var(--text);
            color: var(--surface);
            border-color: var(--text);
        }}

        /* Cards */
        .cards {{
            display: flex;
            flex-direction: column;
            gap: 1rem;
        }}

        .card {{
            background: var(--surface);
            border-radius: 12px;
            border: 1px solid var(--border);
            display: grid;
            grid-template-columns: 1fr 320px;
            overflow: hidden;
        }}

        @media (max-width: 900px) {{
            .card {{
                grid-template-columns: 1fr;
            }}
        }}

        .card-main {{
            padding: 1.5rem;
        }}

        .card-header {{
            display: flex;
            align-items: center;
            gap: 0.5rem;
            margin-bottom: 1rem;
            flex-wrap: wrap;
        }}

        .layer-tag {{
            padding: 0.25rem 0.6rem;
            border-radius: 4px;
            font-size: 0.7rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.03em;
        }}

        .layer-tag.wow {{ background: var(--wow-soft); color: var(--wow); }}
        .layer-tag.how {{ background: var(--how-soft); color: var(--how); }}
        .layer-tag.what {{ background: var(--what-soft); color: var(--what); }}

        .ai-tag {{
            padding: 0.2rem 0.5rem;
            border-radius: 4px;
            font-size: 0.7rem;
            font-weight: 500;
            background: var(--border-light);
            color: var(--text-muted);
        }}

        .source-tag {{
            font-size: 0.75rem;
            color: var(--text-muted);
            margin-left: auto;
        }}

        .use-case {{
            display: inline-block;
            font-size: 0.8rem;
            font-weight: 500;
            color: var(--text-muted);
            margin-bottom: 0.75rem;
        }}

        .quote {{
            font-size: 0.95rem;
            line-height: 1.65;
            color: var(--text-muted);
            margin-bottom: 1rem;
        }}

        .meta-row {{
            font-size: 0.85rem;
        }}

        .meta-row a {{
            color: var(--accent);
            text-decoration: none;
            font-weight: 500;
        }}

        .meta-row a:hover {{
            text-decoration: underline;
        }}

        /* Strategy sidebar */
        .card-strategy {{
            background: var(--bg);
            padding: 1.5rem;
            border-left: 1px solid var(--border);
            display: flex;
            flex-direction: column;
            gap: 1.25rem;
        }}

        @media (max-width: 900px) {{
            .card-strategy {{
                border-left: none;
                border-top: 1px solid var(--border);
            }}
        }}

        .strategy-section {{
            display: flex;
            flex-direction: column;
            gap: 0.35rem;
        }}

        .strategy-label {{
            font-size: 0.7rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: var(--text-muted);
        }}

        .strategy-content {{
            font-size: 0.9rem;
            font-weight: 500;
            color: var(--text);
            line-height: 1.5;
        }}

        .provocation {{
            background: var(--how-soft);
            border-radius: 8px;
            padding: 0.875rem 1rem;
            font-size: 0.875rem;
            font-style: italic;
            color: var(--text);
            line-height: 1.5;
        }}

        .growth-tags {{
            display: flex;
            gap: 0.35rem;
            flex-wrap: wrap;
        }}

        .growth-tag {{
            padding: 0.2rem 0.5rem;
            border-radius: 4px;
            font-size: 0.7rem;
            font-weight: 500;
        }}

        .growth-tag.activation {{ background: #d1fae5; color: #065f46; }}
        .growth-tag.retention {{ background: #dbeafe; color: #1e40af; }}
        .growth-tag.differentiation {{ background: #fee2e2; color: #991b1b; }}
        .growth-tag.b2b {{ background: #fef3c7; color: #92400e; }}

        /* Search section */
        .search-section {{
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 1.5rem;
            margin-top: 2.5rem;
        }}

        .search-section h2 {{
            font-size: 1rem;
            font-weight: 600;
            margin-bottom: 0.5rem;
        }}

        .search-section p {{
            color: var(--text-muted);
            font-size: 0.9rem;
            margin-bottom: 1rem;
        }}

        .search-links {{
            display: flex;
            flex-wrap: wrap;
            gap: 0.5rem;
        }}

        .search-link {{
            display: inline-flex;
            align-items: center;
            padding: 0.4rem 0.75rem;
            background: var(--bg);
            border: 1px solid var(--border);
            border-radius: 6px;
            text-decoration: none;
            color: var(--text-muted);
            font-size: 0.8rem;
            font-weight: 500;
            transition: all 0.15s ease;
        }}

        .search-link:hover {{
            border-color: var(--accent);
            color: var(--accent);
        }}

        /* Footer */
        footer {{
            text-align: center;
            margin-top: 3rem;
            padding-top: 2rem;
            border-top: 1px solid var(--border);
            color: var(--text-muted);
            font-size: 0.875rem;
        }}

        footer strong {{
            color: var(--text);
            font-weight: 500;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>Aha-ggregator</h1>
            <p class="tagline">Mining the "Wow" layer for Growth</p>
            <p class="last-updated">Last updated: {last_updated} · {analysis['total']} moments collected</p>
        </header>

        <div class="purpose">
            <div class="purpose-label">Why this exists</div>
            <p><strong>The biggest activation friction is people's mental model.</strong> Users don't know what kind of collaborator AI can be, what it can actually do, or why it's worth their time.</p>
            <p>This tool collects real "Wow" moments—when AI finally clicked for people—to inform show-don't-tell content patterns and surface what "getting it" actually looks like in the wild.</p>
            <div class="metrics">Supports: Week 2 retention (34% → 37%), Advanced feature adoption (14% → 20%), Differentiation</div>
        </div>

        {insights_html}

        <div class="filter-section">
            <div class="filter-group">
                <span class="filter-label">Layer</span>
                <button class="filter-btn active" data-filter="all">All</button>
                <button class="filter-btn" data-filter="wow">Wow</button>
                <button class="filter-btn" data-filter="how">How</button>
                <button class="filter-btn" data-filter="what">What</button>
            </div>
            <div class="filter-group">
                <span class="filter-label">Growth lever</span>
                <button class="filter-btn" data-growth="activation">Activation</button>
                <button class="filter-btn" data-growth="retention">Retention</button>
                <button class="filter-btn" data-growth="differentiation">Differentiation</button>
                <button class="filter-btn" data-growth="b2b">B2B</button>
            </div>
        </div>

        <div class="cards" id="cards-container">
            {cards_html}
        </div>

        <div class="search-section">
            <h2>Find more aha moments</h2>
            <p>Pre-built searches to discover more breakthrough stories:</p>
            <div class="search-links">
                <a href="https://www.reddit.com/search/?q=%22aha%20moment%22%20AI%20OR%20ChatGPT%20OR%20Claude&type=link&sort=relevance" target="_blank" class="search-link">Reddit: "aha moment"</a>
                <a href="https://www.reddit.com/search/?q=%22finally%20clicked%22%20AI%20OR%20LLM&type=link&sort=relevance" target="_blank" class="search-link">Reddit: "finally clicked"</a>
                <a href="https://www.reddit.com/search/?q=%22game%20changer%22%20Claude%20OR%20ChatGPT%20OR%20Gemini&type=link&sort=relevance" target="_blank" class="search-link">Reddit: "game changer"</a>
                <a href="https://hn.algolia.com/?q=aha%20moment%20AI%20LLM" target="_blank" class="search-link">Hacker News</a>
                <a href="https://www.google.com/search?q=site:substack.com+%22changed+how+I%22+AI" target="_blank" class="search-link">Substack</a>
                <a href="https://www.youtube.com/results?search_query=%22AI+changed+everything%22+workflow" target="_blank" class="search-link">YouTube</a>
                <a href="https://twitter.com/search?q=%22blown%20away%22%20(claude%20OR%20chatgpt%20OR%20gemini%20OR%20grok)&src=typed_query&f=live" target="_blank" class="search-link">X / Twitter</a>
            </div>
        </div>

        <footer>
            <p>A tool for understanding what "getting it" looks like—informing show-don't-tell content patterns.</p>
            <p style="margin-top: 0.5rem;">Part of the <strong>What / How / Wow</strong> framework for content design and activation.</p>
        </footer>
    </div>

    <script>
        const filterBtns = document.querySelectorAll('.filter-btn[data-filter]');
        const growthBtns = document.querySelectorAll('.filter-btn[data-growth]');
        const cards = document.querySelectorAll('.card');

        let activeLayerFilter = 'all';
        let activeGrowthFilters = new Set();

        function applyFilters() {{
            cards.forEach(card => {{
                const cardLayer = card.dataset.layer;
                const cardGrowth = card.dataset.growth || '';

                let layerMatch = activeLayerFilter === 'all' || cardLayer === activeLayerFilter;
                let growthMatch = activeGrowthFilters.size === 0 ||
                    [...activeGrowthFilters].some(g => cardGrowth.includes(g));

                card.style.display = (layerMatch && growthMatch) ? 'grid' : 'none';
            }});
        }}

        filterBtns.forEach(btn => {{
            btn.addEventListener('click', () => {{
                filterBtns.forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                activeLayerFilter = btn.dataset.filter;
                applyFilters();
            }});
        }});

        growthBtns.forEach(btn => {{
            btn.addEventListener('click', () => {{
                const growth = btn.dataset.growth;
                if (activeGrowthFilters.has(growth)) {{
                    activeGrowthFilters.delete(growth);
                    btn.classList.remove('active');
                }} else {{
                    activeGrowthFilters.add(growth);
                    btn.classList.add('active');
                }}
                applyFilters();
            }});
        }});
    </script>
</body>
</html>'''

    with open(output_file, "w") as f:
        f.write(html)

    print(f"Generated {output_file} with {len(moments)} aha moments")


if __name__ == "__main__":
    moments = load_moments()
    generate_html(moments)
