# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

Contacalorie is a Flask web app that tracks meter readings for a shared condo heating system and computes the gas bill split among three apartments. The building has three floors (`floor_1`, `floor_2`, `floor_3`) plus a basement (`basement`, counted with `floor_3` for billing).

## Language convention

**Identifiers are English, everything a user reads is Italian.** Code, columns,
JSON keys, URL segments, comments and test names are English. The GUI, every
HTTP response body (including the 401/403 auth responses), and the PDF notice
are Italian. Terminal output — `utils.py` usage, the test runner's summary, the
Sheets import confirmation — counts as developer-facing and stays English.

`calorie.LABELS` is the bridge: Italian meter names keyed by English field
names. It is the only place the browser gets a meter's name from.

## Running the app

```bash
source .venv/bin/activate
python website.py   # starts Flask dev server at http://localhost:5000
```

Set `FLASK_DEBUG=1` to enable the Werkzeug debugger; it is off by default. Production runs under uwsgi in Docker behind a reverse proxy, so `__main__` never executes there.

```bash
python test_calorie.py   # checks on split_costs(); no framework, plain asserts
```

Authentication is HTTP Basic Auth. `users.txt` holds one `username:hash` per line (not version-controlled); generate a line with `python utils.py <username>`. Requests the reverse proxy marks as plain HTTP (`X-Forwarded-Proto: http`) are refused with 403 so credentials never cross an unencrypted channel.

## Google Sheets import (recovery path)

The Sheet `DBContacalorieMaiano` was the original source of truth and was retired in favour of the web UI. `populate_from_sheets()` remains as a way back to the historical data; it upserts by date, so re-running it is harmless.

```bash
python -c "from calorie import populate_from_sheets; populate_from_sheets()"
```

Requires `Contacalorie-cef2fe8fdd6c.json` (Google service account credentials, not version-controlled). Normal development uses the existing `contacalorie.db` SQLite file directly.

## Architecture

```
calorie.py       — SQLAlchemy model (Reading), FIELDS/LABELS, DB session, split_costs() cost algorithm
website.py       — Flask routes: / (shell), /report/... (PDF), /api/... (JSON)
report.py        — ReportLab PDF generation for per-apartment cost notices
utils.py         — requires_auth decorator; `python utils.py <user>` prints a users.txt line
test_calorie.py  — asserts on split_costs(); run it directly
templates/
  index.html     — Shell page; Bootstrap 4 + inline JS renders everything from the JSON API
  help.html      — "?" dialog: SVG plant diagram and the split explained step by step
```

The core logic lives in `calorie.py:split_costs()`. It takes two consecutive `Reading` rows (r1, r2) and splits costs proportionally:

1. **Direct gas**: each floor pays `euro_per_m3 × its own gas diff`. The floor gas meters are sub-meters of `gas_main`.
2. **Common gas** (`gas_common` = main − the three floor sub-meters) is what the central boiler burned, for heating *and* domestic hot water together. `cost_common` is its cost.
3. **Shares**: the central `calories_hot_water` meter is handed to the floors in proportion to net hot-water use (`supply − return`); each floor's share is its own heating calories plus that allocation. `cost_common` splits in proportion to the shares.

The three shares add up to `shares_total` by construction, which is why the split always closes exactly on the bill — that is the invariant `test_calorie.py` guards.

`split_costs()` also fills `CostSplit.steps` with every intermediate it computed, including each floor's `gas_cost`/`common_cost`/`total`. `/api/cost-splits` passes it through and `help.html` only formats it, so the explanation shown to residents cannot drift from the money. `steps` is `None` exactly when there was nothing to compute (an error, or no gas burned), and the dialog then shows em dashes.

`Reading.date` (a `Date`) is the primary key — one set of readings per day, with duplicates prevented by the database rather than by application checks. There is no separate id column.

`calorie.FIELDS` and `calorie.LABELS` are the single source of truth for the meter list: they are derived from the model's columns and drive JSON serialization, request validation, the table headers and the form. Adding a meter means adding a column and a label, nothing else.

## Domain abbreviations

The Italian column is what the GUI, the PDF and the residents say; the English
column is what the code says. Older commits and the Google Sheet use the
Italian names throughout.

| Italian | English identifier | Meaning |
|---------|--------------------|---------|
| Primo Piano (PP) | `floor_1` | 1st floor |
| Secondo Piano (SP) | `floor_2` | 2nd floor |
| Terzo Piano (TP) | `floor_3` | 3rd floor |
| Taverna Carlo (TC) | `basement` | basement, billed together with `floor_3` |
| Zona giorno / notte | `day_zone` / `night_zone` | living vs sleeping side of floor 1, metered separately |
| H2O calda andata | `hot_water_supply` | supply flow meter |
| H2O calda ricircolo | `hot_water_return` | recirculation flow meter |
| Costo bolletta | `bill_cost` | total gas bill for the period |
| Gas generale | `gas_main` | building-wide gas meter |
| Ripartizione | `CostSplit` | cost allocation result for a billing period |
| Rilevamento | `Reading` | one set of meter readings on a specific date |

## API endpoints

All routes require Basic Auth.

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | Page shell; the browser fills it from the JSON endpoints |
| GET | `/report/<floor_1\|floor_2\|floor_3>/<d1>/<d2>` | PDF notice; the amount is recomputed server-side |
| GET | `/api/cost-splits` | Computed periods, most recent first (`from`/`to`/`floor_*`/`total`/`bill_cost`/`steps`) |
| GET | `/api/readings` | All records as JSON |
| GET | `/api/readings/<date>` | Single record |
| POST | `/api/readings` | Create record (409 if that date exists) |
| PUT | `/api/readings/<date>` | Update record; any `date` in the body is ignored |
| DELETE | `/api/readings/<date>` | Delete record |

**All dates in URLs and JSON are ISO `YYYY-MM-DD`.** Italian `DD/MM/YYYY` is a display format only, applied in the browser and in the PDF. Because the date is the primary key, `PUT` cannot move a record to another date — delete and recreate instead; the UI makes the date field read-only when editing.

The schema was renamed to English wholesale rather than migrated: the table is now `readings` and the DB was rebuilt from the Google Sheet. Any copy still holding the old Italian `data` table must be rebuilt the same way — `create_all` would otherwise add an empty `readings` table beside it and the app would come up looking empty.

Errors come back as `{"error": "<Italian message>"}` with 400 (bad input), 404 (missing), or 409 (duplicate date).
