# EcoTrove CCA Pipeline

## Overview
This project ingests CCA coverage data, stores it in a normalized PostgreSQL database, and provides an API to resolve user addresses to eligible CCAs and their signup links.

---

## Setup

### Prerequisites
- Docker & Docker Compose
- (Optional) Python 3.11+ and pip (for local development)

### 1. Clone the repository and place `cca_coverage.csv` in the root directory.

### 2. Start the infrastructure
```bash
docker-compose up --build
```
This will start:
- PostgreSQL (port 5432)
- FastAPI backend (port 8000)
- Frontend (port 5173)

### 3. Ingest CCA data
```bash
docker-compose exec backend python load_cca.py
```

### 4. Test the API
You can use `httpie` or `curl`:
```bash
http POST localhost:8000/eligible_ccas address="95032"
http POST localhost:8000/eligible_ccas address="San Rafel, CA"
http POST localhost:8000/eligible_ccas address="400 Beach St, Santa Cruz, CA 95060"
```

### 5. Run Unit Tests
- All backend tests are in `backend/tests/`.
- Test discovery is automatic due to `pytest.ini` (no need to set PYTHONPATH).
```bash
cd backend
pytest
```

---

## Project Structure
- `schema.sql` — Normalized PostgreSQL schema
- `backend/` — Backend code, ingestion, and tests
  - `app.py` — FastAPI app
  - `load_cca.py` — Ingestion script
  - `requirements.txt` — Python dependencies
  - `Dockerfile` — Backend container
  - `pytest.ini` — Ensures test discovery works out of the box
  - `tests/` — All unit tests
- `cca_coverage.csv` — CCA coverage data (exported from Google Sheets)

---

## Known Limitations
- City matching is fuzzy but not typo-proof for all cases; some edge cases may not match as expected.
- No geocoding: only parses zip and city from address string.
- Data entry errors (malformed arrays, typos) are handled best-effort in ingestion, but front-end validation is recommended.
- The ingestion script attempts to robustly parse inconsistent CSV formats, but perfect normalization depends on source data quality.

---

## Geomapping Technique

The backend leverages the `uscities.csv` dataset to perform city/ZIP geomapping. This file contains mappings between city names, state abbreviations, and all ZIP codes associated with each city. At API startup, the backend loads this file and builds two in-memory mappings:

- **City+State → ZIP codes:** Allows the backend to look up all ZIP codes for a given city and state.
- **ZIP code → City/State:** Allows the backend to resolve a ZIP code to its corresponding city and state.

**How it's used:**
- If a user provides only a ZIP code, the backend looks up the city/state for that ZIP and uses it for CCA eligibility lookup.
- If a user provides only a city (and state), the backend looks up all ZIP codes for that city/state and uses them for matching.
- If both are provided, both are used for the most accurate lookup.
- Fuzzy matching is also applied to city names to tolerate typos.

This approach enables robust, typo-tolerant address resolution without requiring a full geocoding service, and supports both city-based and ZIP-based CCA eligibility queries.

## Data Entry Improvements
- Use dropdowns/autocomplete for counties, cities, and zips in the labeling interface.
- Validate array fields and enforce consistent formatting before submission.
- Consider using a reference dataset for valid city/county/zip names.
- Add front-end validation to prevent malformed or duplicate entries.

---

## Bonus Discussion
### 1. Scaling
- Add DB indexes on zip/city columns for fast lookup.
- Cache CCA coverage rules in memory for high-throughput API (e.g., Redis or in-process cache).
- Use async DB access and horizontal scaling for the API.
- Consider sharding or partitioning by geography for very large datasets.

### 2. Data Entry
- Redesign the labeling UI to use select fields, autocomplete, and validation against a canonical list of cities/counties/zips.
- Provide real-time feedback for malformed or duplicate entries.
- Use batch validation and preview before submission.

### 3. Extensibility
- Support overlapping CCAs by returning all matches, not just the first.
- Add a `state` field to all restriction tables for multi-state support.
- Use a geospatial database (e.g., PostGIS) for more complex coverage rules in the future.
- Modularize the ingestion and API logic to support new data sources or rules.

---

## References
- [Google Sheet: cca_coverage](https://docs.google.com/spreadsheets/d/10IwOR_V55J8wK0dIllh2a4_Y9CjF0lGyZfqgQb1mRSU/edit?gid=0#gid=0)