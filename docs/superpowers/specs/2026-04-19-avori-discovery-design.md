# Avori Discovery Design

## Scope

Implement PRD Tasks 1-4 only for a thin script-first Python package that:
- pulls TikTok Shop product candidates through TikHub
- scores and ranks them
- writes a dated JSON results file
- writes and prints a daily brief

Task 5 MCP server work is explicitly out of scope.

## File Structure

- `config.py`: environment loading, seed keywords, scoring weights, region, output paths
- `tikhub_client.py`: TikHub SDK bootstrap and shared client access
- `endpoints/__init__.py`: package marker
- `endpoints/search.py`: `search_products()` and `get_keyword_suggestions()`
- `endpoints/trending.py`: `get_hot_products()`
- `endpoints/detail.py`: `enrich_product()` and `get_seller_catalog()`
- `scorer.py`: `score_product()`, `flag_early_window()`, `rank_products()`
- `output.py`: result serialization and daily brief formatting
- `avori_discovery.py`: main runner
- `requirements.txt`: `tikhub`, `python-dotenv`
- `.env.example`: required env vars

## Runtime Design

1. Load config from environment.
2. Build a keyword list from configured seed keywords and keyword suggestions.
3. Fetch search candidates and hot-product candidates.
4. De-duplicate by product id.
5. Enrich each product with detail and seller catalog data.
6. Score, early-window flag, and rank products.
7. Write `output/avori_results_YYYY-MM-DD.json`.
8. Write `output/avori_daily_brief.txt`.
9. Print the daily brief to stdout.

## Data Handling

- Keep product records as dictionaries to avoid extra abstraction.
- Normalize only the fields needed for scoring and output.
- Preserve raw nested data under `raw_*` keys when useful for later inspection.

## Scoring

The scorer uses configurable weights from `config.py` and combines:
- sales momentum
- low review saturation
- rating quality
- creator/video signal when present
- seller catalog breadth penalty or bonus when present

`flag_early_window(product)` returns true when:
- `sold_count > 1000`
- `review_count < 30`

## Missing Credentials Behavior

The local environment currently has no visible `TIKHUB_API_KEY`.
To keep Task 4 runnable, the runner will:
- use live TikHub calls when `TIKHUB_API_KEY` is present
- otherwise fall back to bundled sample product data while keeping the same pipeline and outputs

This preserves a clean local run without adding a second architecture.
