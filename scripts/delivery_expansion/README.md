# Delivery-prospect expansion (free tools only)

Scripts used on 2026-10-06 to expand the Lagos Delivery Prospects list. No paid services:
the repo's own Google Maps browser collector, plus a robots-aware crawl of public business websites.

Run order (paths assume `out/expand/` inside the repo; Playwright + Chromium required):

1. `collect.py` - resumable Maps search sweep (19 terms x 11 areas x 2-3 viewports) -> `raw.jsonl`
2. `candidates.py` - flatten, assign areas, match against the master by place ID / name+location
3. `enrich_pages.py` - Maps place pages: address, category, website, phone, ordering link
4. `crawl.py` - website crawl for emails, socials, delivery wording
5. `build_v5.py` then `finalize_v5.py` - classify, score with `src/lagosdata/score.py`, merge into the master workbook

Limit: Google's delivery / takeout / catering flags are not visible in the free signed-out view, so new rows are
scored without them (Score basis = "Partial") and show "Not checked" for those columns.
