# Mock enrichment API

```
pip install -r requirements.txt
python app.py
```

Serves on `http://127.0.0.1:8000`.

- `GET /enrich/<variant_code>` — requires header `X-Api-Key: <any string>`
- `GET /health` — plain health check, no key required

This is a stand-in for a real third-party enrichment provider. Don't assume it's well-behaved.


# Aventus Data Engineering Take-Home Assessment

## Overview

This project implements an end-to-end catalog data pipeline covering:

- PostgreSQL staging and transformation
- Latest-wins variant deduplication
- Variant ranking and item-level aggregations
- Price outlier detection
- Mock API enrichment with retry and rate limiting
- FAISS-based semantic embeddings
- Kestra orchestration
- Production schema design
- BigQuery / GA4 nested event analysis

## Project Structure

```text
.
├── mock_api/
├── src/
│   ├── db.py
│   ├── enrichment.py
│   └── embeddings.py
├── sql/
│   ├── 01_create_tables.sql
│   ├── 02_load_staging.sql
│   ├── 03_variant_summary.sql
│   ├── 04_size_stock.sql
│   ├── 05_price_outlier.sql
│   ├── 06_enrichment_gap.sql
│   ├── 07_production_schema.sql
│   └── 08_ga4_sessions.sql
├── kestra/
│   └── aventus_catalog_pipeline.yml
├── tests/
├── requirements.txt
├── .gitignore
└── README.md

CSV extracts
     |
     v
PostgreSQL staging
     |
     v
Latest-wins deduplication
     |
     v
Variant summary
     |
     +--> Item size / stock summary
     |
     +--> Price outlier detection
     |
     v
Mock enrichment API
     |
     v
PostgreSQL enrichment history
     |
     v
FAISS semantic index

Kestra orchestrates execution, retries, validation, and logging.

Implementation

1. SQL Pipeline

Two daily catalog extracts are loaded into stg_catalog_extract.

For duplicate variant_code values, the pipeline applies a latest-wins rule based on loaded_at.

variant_summary contains one current record per variant. Window functions are used to calculate:

variant_rank_in_item
variants_for_item

Additional SQL transformations provide:

item-level available sizes
stock-status rollups
new-arrival indicators
category-level price outlier detection
enrichment-gap classification

A 30-day recency window is used for the new-arrival definition.

A price is classified as an outlier when it is more than two population standard deviations from its category mean. NULL prices are excluded.

2. API Enrichment

The mock Flask API exposes:

GET /enrich/<variant_code>

The enrichment client implements:

API-key authentication
request rate limiting
retry handling
exponential backoff
HTTP 429 handling
HTTP 5xx handling
malformed JSON handling
request latency measurement
structured logging
PostgreSQL audit-history writes

Successful variants are excluded from subsequent runs, making enrichment idempotent.

3. Embeddings

Successful enrichment descriptions are embedded using:

sentence-transformers/all-MiniLM-L6-v2

The resulting vectors have 384 dimensions.

FAISS is used as the local vector index. Before indexing, vectors are L2-normalized and stored in an inner-product index for cosine-similarity-style retrieval.

Generated FAISS index and metadata files are excluded from source control because they can be regenerated from PostgreSQL.

4. Orchestration

Kestra is used for orchestration.

The flow performs:

pipeline start logging
PostgreSQL connectivity/data validation
Python enrichment execution
post-enrichment data-quality validation
pipeline completion logging

The enrichment task has retry handling and the Python enrichment implementation independently handles transient API failures.

The validation step checks:

total variants
successfully enriched variants
variants remaining without successful enrichment

A completed validation run produced:

Total variants: 1,673
Successfully enriched: 1,673
Remaining: 0

A subsequent enrichment execution reported no variants left to enrich, demonstrating idempotent rerun behavior.

5. Production Schema

The proposed production model separates:

dim_item — item-level attributes
dim_variant — variant-level attributes
variant_enrichment_history — enrichment attempt history

Foreign keys preserve item-to-variant and variant-to-enrichment relationships.

Indexes are included for common item, category, stock-status, enrichment-status, and enrichment-history access patterns.

6. BigQuery / GA4

sql/08_ga4_sessions.sql demonstrates querying GA4 export data in BigQuery.

It:

filters session_start events
extracts source and medium from repeated event_params using UNNEST
groups results by date, source, and medium
counts daily session-start events
Idempotency

The enrichment pipeline does not reprocess variants that already have a successful enrichment record.

This allows failed executions to be safely rerun without repeating successful API work.

SQL transformations are designed around deterministic current-state calculations from the staged catalog data.

Failure Handling

Transient enrichment failures are handled using retries and backoff.

The client specifically handles:

HTTP 429 rate-limit responses
HTTP 5xx responses
request timeouts/errors
malformed JSON responses

Each enrichment attempt is recorded with status, latency, and timestamp so failures remain auditable.

Kestra also retries the enrichment task if the task itself fails.

Monitoring and Alerting

The pipeline exposes operational signals through:

Kestra execution/task status
structured Python logs
enrichment status history
request latency
remaining-unenriched variant count
post-run data-quality validation

In production, failed Kestra executions and non-zero remaining-variant counts should trigger an alert through the organization's notification system such as Slack, email, or PagerDuty.

Security

Database credentials are supplied through environment variables rather than committed to source control.

The submitted Kestra configuration references an environment-provided PostgreSQL password.

Production API keys and other credentials should similarly be stored in the orchestrator's secret-management system.

Setup
Python

Create and activate a virtual environment, then install dependencies:

pip install -r requirements.txt
Environment Variables

Configure:

DB_HOST=localhost
DB_PORT=5432
DB_NAME=<database_name>
DB_USER=postgres
DB_PASSWORD=<password>
ENRICHMENT_API_URL=http://127.0.0.1:8000
ENRICHMENT_API_KEY=test_key

Do not commit real credentials.

Run the Mock API
python mock_api/app.py

Load Catalog Data
The supplied catalog extracts are loaded into PostgreSQL using the `sql/02_load_staging.sql` script.
Run the script from `psql` from the project root so the relative CSV paths can be resolved correctly.
Run Enrichment
python src/enrichment.py
Build the FAISS Index
python src/embeddings.py
Design Decisions
PostgreSQL provides relational persistence and SQL analytics.
Latest-wins logic resolves duplicate daily catalog observations.
Enrichment attempts are retained as history rather than overwritten.
Application-level rate limiting protects the mock API.
FAISS was selected for the assessment's local vector-search implementation.
Kestra provides orchestration, retries, execution history, and observability.
Heavy embedding dependencies are kept outside the lightweight Kestra runtime; in production, the embedding stage would use a prebuilt container image containing the model and required libraries.
Notes

The BigQuery query contains placeholder project and dataset identifiers because no live GA4 BigQuery dataset is required for the assessment.

Generated FAISS artifacts, virtual environments, caches, logs, and local credentials are excluded from source control.
