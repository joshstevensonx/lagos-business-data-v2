# Lagos Local Business Data Collector — Codex Implementation Guide

**Project:** Lagos Business Data Collector  
**Client:** Nexora / Community Magazine  
**Date:** 2026-10-06  
**Implementation target:** Codex  
**Primary language:** Python 3.12+  
**Status:** Ready for implementation

---

## 1. Objective

Implement one configurable CLI application that produces two business-data pipelines:

1. `magazine` — a broad census of businesses across configured Lagos catchment areas, classified into the supplied 29-group / 436-subcategory taxonomy.
2. `delivery` — a targeted prospecting dataset for restaurants, supermarkets, pharmacies, and related businesses, scored for delivery-sales potential.

Both pipelines must share the same collection, normalisation, geographic assignment, classification, deduplication, enrichment, reporting, and verification machinery.

The supplied `reference/` code is already approved business logic. **Port it before rewriting or redesigning it.**

The original handoff explicitly says the reference modules are already-debugged and should be reused rather than rewritten.

---

## 2. Non-Negotiable Constraints

### Cost

The implementation must run at **zero marginal cost**.

Do not add:

- Apify
- SerpAPI
- ScrapingBee
- Bright Data
- DataForSEO
- paid scraping-as-a-service
- paid proxy providers
- paid Google APIs by default
- any other mandatory paid service

Google Places API may exist as an **optional, disabled-by-default** enrichment source. If enabled, it must be explicitly configured by the user and protected by a local usage ceiling.

### Collection boundaries

Only collect publicly available business listing data.

Do not:

- bypass authentication
- scrape behind a login
- solve CAPTCHAs
- bypass access controls
- add proxy rotation to evade rate limits
- add user-agent farms
- submit forms
- perform POST operations against business websites
- collect named individuals' personal contact details when not published as business contacts

Honour `robots.txt` for directories and business websites.

### Failure behaviour

The system must be resumable. A long-running collection must survive interruption without forcing completed work to be repeated.

Raw records must be persisted immediately after discovery.

Never make a silent zero-record source failure look like a successful empty dataset.

---

## 3. Recommended Technical Stack

Use the following stack unless a supplied reference module makes a different dependency necessary.

### Core

- Python 3.12+
- Pydantic
- Typer
- SQLite
- `httpx`
- `selectolax`
- Playwright
- `openpyxl`
- pytest
- PyYAML

### Optional helpers

- BeautifulSoup as a compatibility/fallback parser where useful
- Trafilatura for extracting useful page text when selector-based extraction is insufficient

### Scraper architecture decision

Use a **hybrid collector**, not one universal scraper.

| Workload | Preferred tool |
|---|---|
| Google Maps result pages | Playwright |
| Google Maps place pages | Playwright |
| JS-heavy directories | Playwright |
| Static directories | httpx + selectolax |
| Business websites | httpx + selectolax |
| Dynamic business websites | Playwright |
| HTML text extraction | selectolax / Trafilatura |
| POI discovery / cross-check | OpenStreetMap Overpass |

### Important

Do **not** replace the existing Google Maps browser implementation with a different abstraction unless necessary. The supplied specification contains working render timing, scrolling, extraction, concurrency, backoff, and wide-viewport guidance.

---

## 4. High-Level Architecture

```text
CLI / Config
    |
    v
Run State (SQLite)
    |
    v
discover
    |
    +---- OSM / Overpass
    |
    +---- Google Maps / Playwright
    |
    +---- Nigerian directories / HTTP or Playwright
    |
    v
raw/*.jsonl
    |
    v
geo
    |
    v
classify
    |
    v
enrich
    |
    +---- business websites
    |
    +---- Google Maps place pages (delivery pipeline)
    |
    +---- optional Places API
    |
    v
score
    |
    v
dedupe
    |
    v
report
    |
    v
verify
    |
    +---- XLSX validation
    +---- schema validation
    +---- KPI reconciliation
    +---- recalc verification
```

Every stage must be independently rerunnable.

---

## 5. Repository Structure

Implement this structure:

```text
lagos-data/
├── pyproject.toml
├── README.md
├── CODEX_IMPLEMENTATION.md
├── config/
│   ├── magazine.yaml
│   ├── delivery.yaml
│   └── areas.yaml
├── src/
│   └── lagosdata/
│       ├── __init__.py
│       ├── cli.py
│       ├── config.py
│       ├── models.py
│       ├── state.py
│       ├── logging.py
│       ├── areas.py
│       ├── tree.py
│       ├── classify.py
│       ├── taxonomy.py
│       ├── normalise.py
│       ├── merge.py
│       ├── score.py
│       ├── sources/
│       │   ├── __init__.py
│       │   ├── base.py
│       │   ├── osm.py
│       │   ├── gmaps_browser.py
│       │   ├── places_api.py
│       │   ├── site_contacts/
│       │   │   ├── __init__.py
│       │   │   ├── crawler.py
│       │   │   ├── robots.py
│       │   │   ├── cache.py
│       │   │   └── extractors.py
│       │   └── directories/
│       │       ├── __init__.py
│       │       ├── base.py
│       │       ├── finelib.py
│       │       ├── ngex.py
│       │       ├── cybo.py
│       │       ├── businesslist.py
│       │       └── vconnect.py
│       ├── stages/
│       │   ├── discover.py
│       │   ├── geo.py
│       │   ├── enrich.py
│       │   ├── scoring.py
│       │   ├── dedupe.py
│       │   ├── report.py
│       │   └── verify.py
│       └── workbook/
│           ├── __init__.py
│           ├── style.py
│           ├── magazine.py
│           └── delivery.py
├── reference/
├── tests/
│   ├── test_config.py
│   ├── test_tree.py
│   ├── test_classify.py
│   ├── test_phone.py
│   ├── test_normalise.py
│   ├── test_merge.py
│   ├── test_score.py
│   ├── test_geo.py
│   ├── test_verify.py
│   ├── fixtures/
│   │   ├── finelib-YYYY-MM-DD.html
│   │   ├── ngex-YYYY-MM-DD.html
│   │   ├── cybo-YYYY-MM-DD.html
│   │   ├── businesslist-YYYY-MM-DD.html
│   │   └── vconnect-YYYY-MM-DD.html
│   └── integration/
└── out/
```

---

# 6. Implementation Order

Follow this order exactly.

## Phase 1 — Scaffold and approved logic

Before writing any scraper:

1. Create the Python package.
2. Create config models and validation.
3. Create `Business`.
4. Create SQLite run state.
5. Create structured JSONL logging.
6. Port:
   - `reference/tree.py`
   - `reference/classify.py`
   - `reference/taxonomy.py`
   - `reference/merge_and_classify.py`
   - `reference/score.py`
7. Split `merge_and_classify.py` into the requested modules without changing behaviour.
8. Port tests.
9. Ensure all tests are green.

Do not write a scraper until this phase passes.

## Phase 2 — OpenStreetMap

Implement `sources/osm.py`.

Required:

- Overpass endpoint
- fallback Overpass endpoint
- configurable transport
- `requests`/`httpx` first
- Playwright browser fallback
- timeout handling
- non-fatal failure handling
- source attribution
- tag-to-classification mapping

Run the entire pipeline on the small OSM dataset before moving on.

## Phase 3 — Workbook + verification

Port:

- `reference/build_magazine_workbook.py`
- `reference/build_delivery_workbook.py`

Then implement `verify.py`.

This makes incorrect datasets visible before adding the more complex collectors.

## Phase 4 — Google Maps Playwright collector

Start with:

```text
one term
one geographic sweep
one browser context
```

Verify the rendering and extraction logic.

Then add:

1. feed render wait
2. feed scrolling
3. stable-result detection
4. field extraction
5. fresh browser contexts
6. concurrency
7. randomized delay
8. rate-limit backoff
9. wide-viewport sweeps
10. top-up searches
11. max-searches
12. max-runtime

Default concurrency = 3. Hard cap = 6.

Never attempt to solve a CAPTCHA.

## Phase 5 — Directories

Implement one directory at a time:

1. Finelib
2. Cybo
3. NGEX
4. BusinessList
5. VConnect
6. optional NigeriaGalleria / ConnectNigeria

Each site must have:

- dedicated parser
- selector block
- fixture
- parser test
- robots check
- rate limiting
- provenance tagging

## Phase 6 — Website enrichment

Implement the `site_contacts` subsystem.

For each business with a website:

1. fetch homepage
2. try `/contact`
3. try `/contact-us`
4. try `/about`
5. try `/order`
6. try `/delivery`

Do not fetch every path blindly when the site already exposes a useful contact page.

Extract:

- business email
- phone numbers
- WhatsApp
- Instagram
- Facebook
- X/Twitter
- LinkedIn
- TikTok
- delivery signals
- catering signals
- online-order signals

Use HTTP first. Use Playwright only for dynamic sites.

Implement:

- URL cache
- 2 MB response cap
- 10 second timeout
- concurrency 5
- per-host serialization
- robots.txt
- same-domain/depth restriction

## Phase 7 — Delivery place-page enrichment

Only the `delivery` pipeline needs this enrichment.

Use Google Maps place pages to collect:

- Delivery
- Takeout
- No-contact
- Catering
- Delivery hours
- Order online

Default:

```yaml
max_place_visits: 500
order_by: reviews_desc
```

Emit the nested `additional_info` shape expected by the scoring implementation.

## Phase 8 — Optional Places API

Implement last.

Default:

```yaml
enabled: false
```

Never put API keys in YAML.

Read from:

```text
GOOGLE_PLACES_API_KEY
```

or a gitignored `.env`.

Implement a local monthly usage file:

```text
~/.lagosdata/places_usage.json
```

Refuse calls above the configured local ceiling.

Default ceiling should be 80% of the configured monthly allowance.

Use the API only for high-value enrichment, not discovery.

---

# 7. Canonical Business Model

Use one canonical dataclass/model throughout all stages.

```python
@dataclass
class Business:
    name: str
    place_id: str = ''

    area: str = ''
    zone: str = ''
    street: str = ''
    addr: str = ''
    lat: float | str = ''
    lng: float | str = ''

    group: str = ''
    sub: str = ''
    legacy18: str = ''
    label: str = ''

    phone: str = ''
    phones_all: str = ''
    whatsapp: str = ''
    website: str = ''
    email: str = ''
    instagram: str = ''
    facebook: str = ''
    twitter: str = ''
    linkedin: str = ''
    tiktok: str = ''
    contact_channels: int = 0

    rating: float | str = ''
    reviews: int | str = ''
    additional_info: dict = field(default_factory=dict)
    delivery_text_signals: list = field(default_factory=list)

    priority: str = ''
    package: str = ''
    contactable: str = ''
    verification: str = ''
    sales_status: str = 'Not Contacted'
    notes: str = ''

    score: float | str = ''
    band: str = ''
    score_components: dict = field(default_factory=dict)
    score_basis: str = ''
    delivery_category: str = ''

    source: str = ''
    sources_all: list = field(default_factory=list)
    maps: str = ''
    added: str = ''
    conflicts: list = field(default_factory=list)
```

### Data rule

Use `''` for absent strings.

Do not write `None` into workbook string columns.

---

# 8. SQLite Run State

Create a resumable state database.

Minimum table:

```sql
CREATE TABLE searches (
    id INTEGER PRIMARY KEY,
    source TEXT NOT NULL,
    term TEXT NOT NULL,
    area TEXT NOT NULL,
    status TEXT NOT NULL,
    raw_count INTEGER DEFAULT 0,
    kept_count INTEGER DEFAULT 0,
    started_at TEXT,
    finished_at TEXT,
    error TEXT,
    UNIQUE(source, term, area)
);
```

Statuses:

```text
pending
running
done
failed
skipped
```

Rules:

- completed work is not repeated
- raw output is append-only
- Ctrl-C must flush current progress
- rerunning the same command is safe
- support force re-run of selected term/area combinations

---

# 9. Raw Data Contract

Every source must write raw records before derived transformations.

Structure:

```text
out/<run-id>/
├── raw/
│   ├── osm.jsonl
│   ├── gmaps.jsonl
│   ├── finelib.jsonl
│   ├── ngex.jsonl
│   ├── cybo.jsonl
│   ├── businesslist.jsonl
│   └── vconnect.jsonl
├── master.json
├── run.log
├── manifest.json
└── verify_sample.csv
```

Raw records must preserve the original source fields.

Never mutate raw data in place.

This allows classifier/scorer changes without re-collection.

---

# 10. Google Maps Collector

## URL

```text
https://www.google.com/maps/search/<urlencoded term>/@<lat>,<lng>,<zoom>z
```

## Render wait

Do not extract immediately after navigation.

Poll until at least three result anchors are present or the timeout expires.

Example logic:

```javascript
while (Date.now() - t0 < 22000 &&
       document.querySelectorAll('a.hfpxzc').length < 3) {
    await sleep(500);
}
```

Then scroll the feed until result count is stable across two consecutive checks.

## Extraction targets

From each result card:

- name
- category
- address
- phone
- rating
- reviews
- lat
- lng
- placeId
- Maps URL

Prefer Python-side locator/structured extraction when possible.

Use JS primarily for the scroll/render loop.

## Concurrency

Default:

```text
3 workers
```

Hard maximum:

```text
6 workers
```

Each worker:

- gets its own browser context
- uses a fresh context periodically
- waits 2–6 seconds between searches
- randomizes viewport
- uses a realistic browser UA

## Backoff

On:

- CAPTCHA
- consent wall
- empty feed where previous runs succeeded
- other clear rate limiting

use exponential backoff starting around 60 seconds.

After three consecutive failures:

- stop that worker
- persist the failure
- continue the rest of the run where safe

Never solve CAPTCHAs.

## Wide viewport strategy

Prefer a small number of wide-area searches and then perform coordinate assignment.

This is a key optimisation and should remain configurable.

---

# 11. OpenStreetMap / Overpass

Use Overpass as:

- a cheap source
- cross-verification
- an enrichment source for phone/website/opening-hours tags

Do not expect it to provide the main Lagos census.

Required endpoint:

```text
https://overpass-api.de/api/interpreter
```

Fallback:

```text
https://overpass.kumi.systems/api/interpreter
```

If Overpass fails, continue the run.

Credit OSM in the workbook README:

```text
© OpenStreetMap contributors
```

---

# 12. Directory Collectors

### Finelib

Highest-priority Nigerian directory.

### NGEX

Useful for directory listings and email information.

### Cybo

Useful for phone/coordinate cross-checks.

### BusinessList

Good static HTML source.

### VConnect

Treat as JS-heavy and use Playwright when required.

Each parser must define selectors in a small, isolated area of the module.

Example:

```python
SELECTORS = {
    "card": "...",
    "name": "...",
    "address": "...",
    "phone": "...",
}
```

If an expected page returns zero records, fail loudly if the fixture indicates it should return records.

---

# 13. Website Contact Enrichment

Extract only business-published contact information.

### Email

Prefer:

```text
mailto:
```

Then regex over rendered/text content.

Reject:

- `noreply@`
- `example.com`
- obvious image filename false positives

### Social links

Normalise to:

- canonical URL
- bare handle where appropriate

Supported:

- Instagram
- Facebook
- X/Twitter
- LinkedIn
- TikTok

### WhatsApp

Support:

```text
https://wa.me/<number>
https://api.whatsapp.com/send?phone=<number>
```

Promote WhatsApp to a first-class field because it is commercially useful for Nigerian SMBs.

### Delivery signals

Use the existing specification's signal words, including:

```text
delivery
deliveries
dispatch
bulk order
corporate order
catering
wholesale
we deliver
free delivery
```

---

# 14. Geographic Assignment

Do not trust informal Lagos area-name geocoding.

Use coordinates wherever available.

Required `nearest_area()` behaviour:

1. calculate distance to configured area centroids
2. assign within radius
3. otherwise use:
   - `Outside catchment`
4. if coordinates are missing:
   - string-match area name in address
   - otherwise `Unassigned`

Keep outside-catchment records in the dataset.

Exclude them only from headline catchment counts.

---

# 15. Classification

Port `tree.py`, `classify.py`, and `taxonomy.py` as supplied.

Important:

- rule order is semantic
- first match wins
- preserve the fallback category
- preserve legacy 18-category behaviour
- preserve existing barber/pre-check logic

Required test:

```text
Unclassified (needs review) < 5%
```

When this threshold fails:

- fail the test
- print the 20 most common unclassified labels

Do not hide classification gaps.

---

# 16. Normalisation and Dedupe

Port `clean_phone()` exactly from the reference implementation.

Target output:

```text
+234XXXXXXXXXX
```

or:

```text
''
```

Deduplication order:

```text
0. place_id
1. phone
2. normalized name + normalized address prefix
3. normalized name
```

On duplicate:

- fill empty fields from the duplicate
- preserve all sources
- set source to `Multiple sources (cross-verified)` when appropriate
- record conflicts

Trust order:

```text
Places API
    >
Google Maps
    >
OSM
    >
Directory
    >
Manual CSV
```

Add a `--dedupe-report` CSV for auditing merges.

---

# 17. Delivery Scoring

Do not retune the approved weights.

Keep:

```text
Google Delivery flag     25
Catering                 15
Review volume proxy      up to 25
Chain                    10
Category weight          10 / 6 / 4
Website                   8
Online ordering           7
No-contact                5
Takeout                   5
Delivery hours            5
Rating >= 4.0             5
```

Bands:

```text
Hot   >= 60
Warm  40–59
Cool  25–39
Cold  < 25
```

Keep:

```text
Score basis = Full
```

or:

```text
Score basis = Floor - not enriched
```

An unenriched score is a floor, not a definitive measurement.

---

# 18. Configuration

Validate configuration using Pydantic.

Unknown keys must be errors.

### Magazine

```yaml
pipeline: magazine
run_id_prefix: magazine

areas:
  - Anthony / Anthony Village
  - Maryland / Mende
  - Ilupeju
  - Gbagada
  - Obanikoro
  - Palmgrove
  - Ojota

core_areas:
  - Anthony / Anthony Village
  - Maryland / Mende

sources:
  places_api:
    enabled: false
    monthly_ceiling_pct: 80
  osm:
    enabled: true
    via_browser: false
  gmaps_browser:
    enabled: true
    concurrency: 3
    zoom: 14
  directories:
    enabled: true
    sites:
      - finelib
      - ngex
      - cybo
      - businesslist
  site_contacts:
    enabled: true
```

### Delivery

```yaml
pipeline: delivery

areas:
  - Lekki Phase 1
  - Lekki-Epe Corridor to Ajah
  - Victoria Island
  - Ikoyi
  - Yaba
  - Surulere

delivery_scoring:
  enabled: true
  bands:
    hot: 60
    warm: 40
    cool: 25
  keep_all: true

sources:
  gmaps_browser:
    enabled: true
    concurrency: 3
  osm:
    enabled: true
  directories:
    enabled: true
  site_contacts:
    enabled: true

enrich:
  place_pages:
    enabled: true
    max_place_visits: 500
    order_by: reviews_desc
```

---

# 19. CLI

Implement:

```bash
lagosdata run --config config/magazine.yaml

lagosdata run \
  --config config/magazine.yaml \
  --stages enrich,score,dedupe,report

lagosdata resume --run-id 2026-10-07-magazine

lagosdata discover \
  --config config/delivery.yaml \
  --area "Lekki Phase 1" \
  --term pharmacy

lagosdata report \
  --run-id 2026-10-07-magazine

lagosdata verify \
  --run-id 2026-10-07-magazine

lagosdata derive-centroids \
  --config config/magazine.yaml
```

Also support:

```text
--force-term
--force-area
--max-searches
--max-runtime
--dedupe-report
--import-csv
--osm-via-browser
```

---

# 20. Logging

Write JSONL to:

```text
out/<run-id>/run.log
```

Log:

- source
- search term
- area
- URL
- timestamp
- duration
- raw count
- kept count
- HTTP status
- browser events
- retry/backoff
- robots skips
- parser failures
- dropped non-business POIs
- dedupe decisions
- source conflicts
- API usage
- stage completion

Never log:

- API keys
- secrets
- tokens

---

# 21. Workbook Outputs

## Magazine workbook

Tabs:

1. `DASHBOARD`
2. `README`
3. `MASTER DATABASE`
4. `AREA SUMMARY`
5. `GROUP x AREA`
6. `CATEGORY TREE`
7. `RESEARCH MATRIX`
8. `SOURCE LOG`

Preserve the existing visual style and workbook conventions from the reference builders.

Dashboard KPIs must be live workbook formulas.

## Delivery workbook

Tabs:

1. `DASHBOARD`
2. `README`
3. `TARGET LIST`
4. `SCORING METHOD`

Sort target list by score descending.

---

# 22. Verification Requirements

`lagosdata verify` is mandatory.

It must:

1. Recalculate dashboard KPIs independently from `master.json`.
2. Compare them with workbook formulas.
3. Run spreadsheet recalculation/validation.
4. Detect spreadsheet formula errors.
5. Validate schema.
6. Validate phone formatting.
7. Validate category membership.
8. Validate area membership.
9. Validate `< 5%` unclassified.
10. Validate phone uniqueness.
11. Validate `place_id` uniqueness.
12. Match workbook row counts across summary tabs.
13. Generate a ten-record `verify_sample.csv`.
14. Report counts by source, area, group, contactability, enrichment, and score basis.
15. Exit non-zero on any failure.

Never ship a workbook that has not passed verification.

---

# 23. Tests

Minimum unit-test coverage:

### Config

- unknown key rejected
- invalid type rejected
- missing required configuration rejected

### Phone

Test all reference examples, including:

```text
0803 123 4567
+234 803 123 4567
234 1 234 5678
08031234567
01 2345678
+23412454213789 -> ''
0803-123-456 -> ''
0803 123 4567 / 0805 987 6543
WhatsApp: 0803 123 4567
```

### Classification

- representative real labels
- barber edge cases
- unclassified threshold

### Dedupe

- place_id
- phone
- name + address
- name fallback
- source conflict precedence
- field filling

### Geo

- inside radius
- outside radius
- missing coordinates
- catchment string fallback

### Directory parsers

Every directory must have a captured fixture and test.

### Google Maps

Test parsing of representative fixture-like HTML structures where possible. Keep live Maps tests separate from normal unit tests.

### Website enrichment

Test:

- mailto extraction
- email regex
- phone extraction
- WhatsApp extraction
- social extraction
- delivery signal extraction
- robots skip
- size limit
- caching

### Verification

Test intentionally broken workbook formulas and schema violations.

---

# 24. Development Rules for Codex

Codex should follow these rules throughout implementation:

1. Read `SPEC.md` and `README(2).md` before changing architecture.
2. Read the entire `reference/` directory before rewriting equivalent logic.
3. Port approved logic first.
4. Do not invent new taxonomy or scoring rules.
5. Do not silently change existing workbook column meanings.
6. Keep source adapters isolated.
7. Keep raw data immutable.
8. Make every expensive stage resumable.
9. Fail loudly on parser breakage.
10. Never make external access a hidden dependency.
11. Do not add paid services.
12. Do not add CAPTCHA solving or proxy evasion.
13. Prefer deterministic extraction over LLM-assisted extraction.
14. Keep tests next to the logic they protect.
15. Preserve provenance on every record.
16. Update documentation when a source selector or source behaviour changes.

---

# 25. Performance Strategy

Optimize by reducing expensive browser work.

### Preferred order

```text
OSM
   ↓
static directories
   ↓
Google Maps wide sweeps
   ↓
targeted Google Maps top-ups
   ↓
website HTTP enrichment
   ↓
browser enrichment only when necessary
   ↓
delivery place-page enrichment for high-value records
```

Do not browser-render every website unnecessarily.

Do not repeatedly recollect unchanged searches.

Use caching and resumability aggressively.

---

# 26. Implementation Milestones

## Milestone 1

```text
CLI
Config
Models
SQLite state
Logging
Reference modules
Tests
```

Acceptance:

```bash
pytest
```

passes.

## Milestone 2

OSM source + end-to-end pipeline.

Acceptance:

```text
discover → geo → classify → dedupe → report → verify
```

works on a small dataset.

## Milestone 3

Workbook builders + verification.

Acceptance:

- both workbook types open correctly
- formulas present
- verification catches intentional formula errors

## Milestone 4

Google Maps Playwright source.

Acceptance:

- single-term run works
- render timing works
- scroll extraction works
- controlled concurrency works
- backoff works
- resumability works

## Milestone 5

Directory sources.

Acceptance:

- every enabled directory has fixture coverage
- parser failure cannot silently produce zero records

## Milestone 6

Website enrichment.

Acceptance:

- contacts extracted
- caching works
- robots rules work
- dynamic fallback works

## Milestone 7

Delivery enrichment + optional Places API.

Acceptance:

- scoring receives real enrichment signals
- score basis correctly reflects enrichment status
- Places API stays disabled unless explicitly enabled

## Milestone 8

Full end-to-end run.

Start with a two-area subset before all magazine areas.

---

# 27. Definition of Done

The project is complete only when:

- both configs validate
- CLI commands work
- all reference logic tests pass
- OSM source works or fails gracefully
- Google Maps collector is resumable
- directories have fixtures
- website enrichment is cached
- delivery place-page enrichment works
- optional Places API is isolated and disabled by default
- raw JSONL exists
- master JSON exists
- run log exists
- manifest exists
- magazine workbook passes verify
- delivery workbook passes verify
- no paid service is required
- no CAPTCHA is solved
- robots.txt is honoured
- no secrets are written to logs/config/chat
- provenance is preserved
- dedupe conflicts are auditable

---

# 28. First Codex Task

Start by executing:

```text
1. Read CODEX_IMPLEMENTATION.md.
2. Read README(2).md.
3. Read SPEC(1).md.
4. Read every file under reference/.
5. Inventory what already exists.
6. Scaffold the repository.
7. Port the reference modules unchanged where possible.
8. Build the unit tests.
9. Run pytest.
10. Stop before implementing Google Maps or any large scraper if the approved logic is not green.
```

The first implementation checkpoint should be a **working, tested pipeline with no scraper dependency** using fixture/manual records.

Only after that should Codex implement OSM, then Google Maps, then directories, then enrichment.

---

# 29. Source-of-Truth Hierarchy

When instructions conflict, use this priority:

1. `reference/` working code for established business logic
2. `SPEC(1).md` for system behaviour and constraints
3. `README(2).md` for handoff intent
4. this document for scraper/tooling architecture
5. implementation convenience must never override the above

Do not silently "improve" approved business rules.

---

# 30. Final Engineering Principle

The collector is not primarily a scraping demo.

It is a **repeatable, auditable business-data pipeline**.

The most important properties are:

```text
correctness
+
provenance
+
resumability
+
deterministic transformation
+
honest coverage
+
safe failure
```

A slower run that can be resumed and audited is preferable to a faster run that loses data, silently misclassifies records, or requires paid infrastructure.
