# Aha-ggregator

A living, breathing dashboard that collects AI "aha moments" — real testimonials of when people finally understood the value of AI tools. Built for Anthropic's Growth team to inform show-don't-tell content patterns.

## How It Works

```
┌─────────────────────────────────────────────────────────────┐
│                    Daily Pipeline (GitHub Actions)          │
├─────────────────────────────────────────────────────────────┤
│  1. scraper.py                                              │
│     └─ Fetch Reddit + HN posts matching "aha moment" terms  │
│                                                             │
│  2. classify.py                                             │
│     └─ Claude API analyzes each post:                       │
│        • What/How/Wow layer                                 │
│        • Growth lever (Activation/Retention/etc.)           │
│        • The Realization (one-liner insight)                │
│        • Provocation (strategic question)                   │
│                                                             │
│  3. generate_html.py                                        │
│     └─ Render cards into index.html                         │
│                                                             │
│  4. Git commit + push → GitHub Pages updates                │
└─────────────────────────────────────────────────────────────┘
```

## Local Development

### Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Set your Anthropic API key
export ANTHROPIC_API_KEY="your-key-here"
```

### Run the full pipeline

```bash
python collect.py
```

### Run individual steps

```bash
# Just scrape (no API key needed)
python scraper.py

# Just classify (requires API key)
python classify.py

# Just regenerate HTML
python generate_html.py
```

### View locally

```bash
# Open in browser
open index.html
```

## Deployment

### GitHub Pages Setup

1. Create a new GitHub repository
2. Push this code to the `main` branch
3. Go to Settings → Pages → Deploy from `main` branch
4. Add your `ANTHROPIC_API_KEY` as a repository secret:
   - Settings → Secrets and variables → Actions → New repository secret

### Manual Trigger

You can manually trigger the update workflow from the Actions tab in GitHub.

## Data Files

- `data/aha_moments.jsonl` — Final classified aha moments (used to generate HTML)
- `data/aha_moments_raw.jsonl` — Raw scraped posts before classification
- `data/aha_moments_classified.jsonl` — All classified posts (including rejected ones)

## Framework

Each aha moment is tagged with:

### Layer (What/How/Wow)
- **Wow**: Emotional breakthrough — mind was blown, completely changed their view
- **How**: Practical discovery — learned a new workflow or technique
- **What**: Conceptual understanding — mental model shift about what AI is

### Growth Lever
- **Activation**: Helps new users get started
- **Retention**: Keeps users coming back
- **Differentiation**: Shows what makes one AI different
- **B2B**: Relevant to business/team use cases

## Contributing

Add curated aha moments directly to `data/aha_moments.jsonl` with `"curated": true`.
