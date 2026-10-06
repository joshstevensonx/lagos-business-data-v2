# Lagos Local Business Data Collector

This repository contains a Python CLI and two strict YAML profiles for a resumable Lagos business-data workflow. The approved taxonomy, classification rules, legacy category mapping, delivery scorer, and raw workbook reference builders are kept under `reference/`; the core transformations are ported into `src/lagosdata/`.

## Setup

Use Python 3.12 or newer, then install the package and browser requirements:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
playwright install chromium
```

Validate the profiles and run unit tests with:

```bash
lagosdata validate --config config/magazine.yaml
lagosdata validate --config config/delivery.yaml
pytest
```

Google Maps is an automated reader of public listing pages. Keep runs small, respect rate limits, and stop if a CAPTCHA or consent wall appears. There is no CAPTCHA solving, authentication bypass, proxy rotation, or paid collector. Google Places API support is disabled by default and reads its key only from `GOOGLE_PLACES_API_KEY`.

## First bounded two-area run

The pilot config searches six terms at a single wide viewport centered over Anthony and Maryland. It is a deliberately small first run:

```bash
lagosdata run --config config/magazine-pilot.yaml --max-searches 12 --max-runtime 90
```

The run directory is created below `out/`. To continue an interrupted run, use its printed run ID:

```bash
lagosdata resume --run-id <run-id>
```

Other useful commands:

```bash
lagosdata run --config config/magazine.yaml --stages enrich,score,dedupe,report
lagosdata report --run-id <run-id> --config config/magazine.yaml
lagosdata verify --run-id <run-id> --config config/magazine.yaml
lagosdata derive-centroids --config config/magazine.yaml
```

## Current implementation notes

Run state and raw JSONL are append-only; derived records and both workbook layouts are generated from the same canonical business schema. OpenStreetMap uses Overpass with a fallback endpoint and optional browser transport. The Google Maps result collector and bounded delivery place-page enrichment use isolated Playwright contexts.

Directory parser adapters and HTTP-first website enrichment components are present. The directory adapters still need current, robots-permitted source URLs and recorded live fixtures before they can be treated as production-ready collectors. Delivery-place signal extraction is heuristic and should be reviewed against live public pages. The optional Places API adapter is isolated and does not participate in normal runs.

Coverage is limited to public listings and configured areas. OSM is credited as `© OpenStreetMap contributors`. Use records for B2B outreach, respect opt-outs, and verify contact details before relying on them.
