# Mock enrichment API

```
pip install -r requirements.txt
python app.py
```

Serves on `http://127.0.0.1:8000`.

- `GET /enrich/<variant_code>` — requires header `X-Api-Key: <any string>`
- `GET /health` — plain health check, no key required


# 🚀 Aventus Data Engineering Take-Home Assessment

**End-to-End Catalog Data Engineering Pipeline**

A production-oriented data pipeline built to process catalog extracts, transform and validate variant-level data, enrich products through a resilient API integration, generate semantic embeddings, and orchestrate the complete workflow using Kestra.

---

## 📌 Project Overview

This project implements an end-to-end catalog data pipeline covering:

| Area                  | Implementation          |
| --------------------- | ----------------------- |
| Database              | PostgreSQL              |
| Data Transformation   | PostgreSQL / SQL        |
| API Integration       | Python + Flask Mock API |
| Retry & Rate Limiting | Python                  |
| Embeddings            | Sentence Transformers   |
| Vector Search         | FAISS                   |
| Orchestration         | Kestra                  |
| Analytics             |  GA4                    |
| Version Control       | Git / GitHub            |

### Pipeline at a Glance

```text
             📁 Catalog CSV Extracts
                       │
                       ▼
              ┌─────────────────┐
              │    PostgreSQL   │
              │     Staging     │
              └────────┬────────┘
                       │
                       ▼
              Latest-Wins Logic
                       │
                       ▼
              ┌─────────────────┐
              │ Variant Summary │
              └────────┬────────┘
                       │
            ┌──────────┴──────────┐
            │                     │
            ▼                     ▼
      Size / Stock          Price Outliers
        Rollups
            │                     │
            └──────────┬──────────┘
                       │
                       ▼
             🔗 Mock Enrichment API
                       │
                       ▼
             Enrichment History
                       │
                       ▼
             Sentence Embeddings
                       │
                       ▼
                 FAISS Index

                       ▲
                       │
                  ⚙️ Kestra
                 Orchestration
```

---

# 📂 Project Structure

```text
.
├── mock_api/
│   └── app.py
│
├── src/
│   ├── db.py
│   ├── enrichment.py
│   └── embeddings.py
│
├── sql/
│   ├── 01_create_tables.sql
│   ├── 02_load_staging.sql
│   ├── 03_variant_summary.sql
│   ├── 04_size_stock.sql
│   ├── 05_price_outlier.sql
│   ├── 06_enrichment_gap.sql
│   ├── 07_production_schema.sql
│   └── 08_ga4_sessions.sql
│
├── kestra/
│   └── aventus_catalog_pipeline.yml
│
├── tests/
│
├── requirements.txt
├── .gitignore
└── README.md
```

---

# 🛠️ Technology Stack

| Technology                | Purpose                                            |
| ------------------------- | -------------------------------------------------- |
| **Python 3.11+**          | API integration, enrichment and embeddings         |
| **PostgreSQL**            | Staging, transformation and persistence            |
| **SQL**                   | Deduplication, aggregation and data-quality checks |
| **Flask**                 | Mock enrichment API                                |
| **Sentence Transformers** | Semantic embeddings                                |
| **FAISS**                 | Local vector search                                |
| **Kestra**                | Workflow orchestration                             |
| **BigQuery**              | GA4 analytics                                      |
| **Git / GitHub**          | Source control                                     |

---

# 1️⃣ SQL Pipeline

The pipeline starts with two daily catalog extracts.

Each extract contains one row per variant, while item-level attributes such as name and brand may repeat across multiple variants.

The same `variant_code` can also appear in multiple catalog drops with updated or corrected values.

Therefore, the pipeline applies a **latest-wins strategy** based on `loaded_at`.

### SQL Flow

```text
Catalog Extracts
       │
       ▼
stg_catalog_extract
       │
       ▼
Latest record per variant
       │
       ▼
variant_summary
       │
       ├──► Size / Stock Rollups
       │
       ├──► Price Outlier Detection
       │
       └──► Enrichment Gap Detection
```

### Variant-Level Transformations

`variant_summary` contains one current record per `variant_code`.

Window functions are used to calculate:

* `variant_rank_in_item`
* `variants_for_item`

Additional transformations calculate:

* Available sizes by item
* In-stock sizes
* Out-of-stock sizes
* New-arrival indicators
* Category-level price outliers
* Enrichment gaps

### New Arrival Rule

A **30-day recency window** is used for the new-arrival definition.

A record is considered a new arrival when its `new_in_stock_date` falls within the selected 30-day window.

### Price Outlier Rule

A price is classified as an outlier when it is more than **two population standard deviations** from the mean price of its category.

`NULL` prices are excluded from the calculation and are not treated as zero.

---

# 2️⃣ API Enrichment

The project includes a Flask-based mock enrichment API that simulates an unreliable third-party service.

## Start the API

```bash
pip install -r requirements.txt
python mock_api/app.py
```

The API runs at:

```text
http://127.0.0.1:8000
```

### Endpoints

**Enrichment**

```text
GET /enrich/<variant_code>
```

Required header:

```text
X-Api-Key: <api-key>
```

**Health Check**

```text
GET /health
```

---

## 🔄 Resilient API Client

The enrichment client implements:

* API-key authentication
* Request rate limiting
* Retry handling
* Exponential backoff
* HTTP 429 handling
* HTTP 5xx handling
* Request timeout/error handling
* Malformed JSON handling
* Request latency measurement
* Structured logging
* PostgreSQL audit-history writes

### Enrichment Flow

```text
variant_summary
      │
      ▼
Check existing successful enrichment
      │
      ├── Already successful ──► Skip
      │
      ▼
Call enrichment API
      │
      ├── 200 ──► Store result
      │
      ├── 429 ──► Wait + Retry
      │
      ├── 5xx ──► Backoff + Retry
      │
      └── Invalid JSON ──► Record failure
```

---

# 3️⃣ 🧠 Semantic Embeddings

Successful enrichment descriptions are converted into semantic embeddings using:

```text
sentence-transformers/all-MiniLM-L6-v2
```

The resulting vectors contain **384 dimensions**.

### Embedding Flow

```text
Product Description
        │
        ▼
Sentence Transformer
        │
        ▼
384-Dimensional Vector
        │
        ▼
L2 Normalization
        │
        ▼
FAISS Inner-Product Index
```

FAISS is used as the local vector index.

Vectors are L2-normalized before being stored in an inner-product index, providing cosine-similarity-style retrieval.

Generated FAISS index and metadata files are excluded from source control because they can be regenerated from PostgreSQL data.

---

# 4️⃣ ⚙️ Kestra Orchestration

Kestra orchestrates the pipeline execution.

### Workflow

```text
Pipeline Start
      │
      ▼
PostgreSQL Connectivity / Validation
      │
      ▼
Python Enrichment
      │
      ▼
Post-Enrichment Validation
      │
      ▼
Pipeline Completion
```

The enrichment task has Kestra-level retry handling, while the Python enrichment implementation independently handles transient API failures.

This provides resilience at both the **application** and **orchestration** levels.

---

# 5️⃣ 🔁 Idempotency

Idempotency is implemented primarily in the enrichment stage.

Before calling the API, the pipeline checks whether the variant already has a successful enrichment record.

```text
Variant
   │
   ▼
Successful enrichment exists?
   │
 ┌─┴─────────┐
 │           │
YES          NO
 │           │
 ▼           ▼
Skip       Enrich
```

This means successful variants are not unnecessarily reprocessed during subsequent executions.

SQL transformations are based on deterministic current-state calculations from the staged catalog data.

---

# 6️⃣ 🛡️ Failure Handling

Transient enrichment failures are handled using retries and exponential backoff.

The client specifically handles:

* `HTTP 429` rate-limit responses
* `HTTP 5xx` responses
* Request timeouts and connection errors
* Malformed JSON responses

Each enrichment attempt is recorded with:

| Field     | Purpose                     |
| --------- | --------------------------- |
| Status    | Success / failure state     |
| Latency   | API performance measurement |
| Timestamp | Audit history               |

This ensures failed attempts remain visible instead of being overwritten.

---

# 7️⃣ 📊 Monitoring & Alerting

Operational signals are exposed through:

* Kestra execution status
* Kestra task status
* Structured Python logs
* Enrichment status history
* API request latency
* Remaining unenriched variants
* Post-run data-quality validation

### Alerting Strategy

In production, the following conditions should trigger alerts:

```text
❌ Failed Kestra execution
❌ Failed critical pipeline task
❌ Non-zero remaining unenriched variants
❌ Persistent API/enrichment failures
```

Possible notification integrations include:

```text
Slack
Email
PagerDuty
```

Routine execution information remains in logs, while actionable failures and data-quality issues are promoted to alerts.

---

# 8️⃣ 🗄️ Production Schema

The production model separates item, variant and enrichment responsibilities.

```text
              dim_item
                  │
                  │
                  ▼
              dim_variant
                  │
                  │
                  ▼
      variant_enrichment_history
```

### `dim_item`

Stores item-level attributes.

### `dim_variant`

Stores variant-level attributes and maintains the relationship with the parent item.

### `variant_enrichment_history`

Stores enrichment attempts as historical records rather than overwriting previous attempts.

### Integrity

Foreign keys maintain:

```text
Item → Variant → Enrichment History
```

Indexes are provided for common access patterns involving:

* Item
* Category
* Stock status
* Enrichment status
* Enrichment history

Production DDL:

```text
sql/07_production_schema.sql
```

---

# 9️⃣ 📈 BigQuery / GA4 Analytics

`sql/08_ga4_sessions.sql` demonstrates querying nested GA4 export data using BigQuery Standard SQL.

The query:

1. Filters `session_start` events.
2. Uses `UNNEST(event_params)` to access nested parameters.
3. Extracts `source` and `medium`.
4. Groups results by event date, source and medium.
5. Calculates daily session-start counts.

### Query Logic

```text
GA4 Events
    │
    ▼
Filter session_start
    │
    ▼
UNNEST(event_params)
    │
    ├──► source
    │
    └──► medium
    │
    ▼
GROUP BY
event_date
source
medium
    │
    ▼
Daily Session Counts
```

The query uses placeholder project and dataset identifiers because a live GA4 BigQuery dataset is not required for the assessment.

---

# 🔟 🔧 Environment Setup

## Prerequisites

* Python 3.11+
* PostgreSQL
* Kestra
* Git
* BigQuery access — optional

---

## Python Virtual Environment

### Create

```bash
python -m venv .venv
```

### Windows

```bash
.venv\Scripts\activate
```

### Linux / macOS

```bash
source .venv/bin/activate
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

---

# 🔐 Environment Variables

Configure the following environment variables:

```text
DB_HOST=localhost
DB_PORT=5432
DB_NAME=<database_name>
DB_USER=postgres
DB_PASSWORD=<password>

ENRICHMENT_API_URL=http://127.0.0.1:8000
ENRICHMENT_API_KEY=test_key
```

Credentials are supplied through environment variables and are not committed to source control.

---

# ▶️ Running the Pipeline

## 1. Start Mock API

```bash
python mock_api/app.py
```

Health check:

```text
http://127.0.0.1:8000/health
```

---

## 2. Load Catalog Data

Load the supplied catalog extracts into:

```text
stg_catalog_extract
```

using:

```text
sql/02_load_staging.sql
```

Run the script from the project root so relative CSV paths resolve correctly.

---

## 3. Build Variant Summary

Run:

```text
sql/03_variant_summary.sql
```

This applies the latest-wins logic and calculates variant-level aggregations.

---

## 4. Run Additional SQL Transformations

```text
sql/04_size_stock.sql
sql/05_price_outlier.sql
sql/06_enrichment_gap.sql
```

---

## 5. Run Enrichment

```bash
python src/enrichment.py
```

---

## 6. Build FAISS Index

```bash
python src/embeddings.py
```

---

## 7. Run Through Kestra

The complete workflow is defined in:

```text
kestra/aventus_catalog_pipeline.yml
```

---

# 🧪 Validation Results

A completed validation run produced:

| Metric                |    Result |
| --------------------- | --------: |
| Total variants        | **1,673** |
| Successfully enriched | **1,673** |
| Remaining unenriched  |     **0** |

A subsequent enrichment execution reported no variants remaining for enrichment, demonstrating the intended idempotent rerun behavior.

---

# 🧩 SQL Files

| File                       | Purpose                            |
| -------------------------- | ---------------------------------- |
| `01_create_tables.sql`     | Create initial database tables     |
| `02_load_staging.sql`      | Load catalog extracts              |
| `03_variant_summary.sql`   | Latest-wins + variant aggregations |
| `04_size_stock.sql`        | Size and stock rollups             |
| `05_price_outlier.sql`     | Category price outlier detection   |
| `06_enrichment_gap.sql`    | Identify enrichment gaps           |
| `07_production_schema.sql` | Production database redesign       |
| `08_ga4_sessions.sql`      | BigQuery GA4 analytics             |

---

# 📁 Source Code

| File                | Responsibility                           |
| ------------------- | ---------------------------------------- |
| `src/db.py`         | PostgreSQL connectivity                  |
| `src/enrichment.py` | API enrichment + retries + rate limiting |
| `src/embeddings.py` | Embedding generation + FAISS indexing    |
| `mock_api/app.py`   | Mock third-party enrichment API          |

---

# 🔒 Security

The project avoids committing sensitive information to source control.

The following are excluded through `.gitignore`:

```text
.env
credentials
logs
virtual environments
Python caches
generated FAISS artifacts
```

Production API keys and database credentials should be managed through environment variables or an orchestrator's secret-management system.

---

# 🎯 Key Design Decisions

| Decision                              | Rationale                                                     |
| ------------------------------------- | ------------------------------------------------------------- |
| **PostgreSQL**                        | Relational persistence and SQL-based transformation           |
| **Latest-wins**                       | Resolves corrected/repeated catalog observations              |
| **Enrichment history**                | Preserves auditability of API attempts                        |
| **Application rate limiting**         | Protects the enrichment API                                   |
| **Retries + backoff**                 | Handles transient third-party failures                        |
| **FAISS**                             | Suitable for the assessment's local vector-search requirement |
| **Kestra**                            | Provides orchestration, retries and execution history         |
| **Environment variables**             | Keeps credentials outside source control                      |
| **Deterministic SQL transformations** | Supports repeatable pipeline execution                        |

---

# 🚀 End-to-End Pipeline

```text
                    ┌──────────────────┐
                    │  Catalog Files   │
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │    PostgreSQL    │
                    │     Staging      │
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │  Latest-Wins     │
                    │  Deduplication   │
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │ Variant Summary  │
                    └────────┬─────────┘
                             │
                ┌────────────┼────────────┐
                │            │            │
                ▼            ▼            ▼
             Size /      Price       Enrichment
             Stock      Outliers        Gaps
                │            │            │
                └────────────┼────────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │ Enrichment API   │
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │ Enrichment       │
                    │ History          │
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │ Sentence         │
                    │ Transformers     │
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │      FAISS       │
                    │  Vector Index    │
                    └──────────────────┘

                 ⚙️ Kestra orchestrates
                  the complete workflow
```

---

## ✅ Assessment Coverage

| Assessment Area              | Status |
| ---------------------------- | ------ |
| PostgreSQL staging           | ✅      |
| Latest-wins deduplication    | ✅      |
| Window functions             | ✅      |
| Variant aggregations         | ✅      |
| Size / stock rollups         | ✅      |
| New-arrival detection        | ✅      |
| Price outlier detection      | ✅      |
| Enrichment gap detection     | ✅      |
| API integration              | ✅      |
| Rate limiting                | ✅      |
| Retry / backoff              | ✅      |
| Malformed response handling  | ✅      |
| Enrichment history           | ✅      |
| Semantic embeddings          | ✅      |
| FAISS vector search          | ✅      |
| Kestra orchestration         | ✅      |
| Idempotency                  | ✅      |
| Failure handling             | ✅      |
| Monitoring / alerting design | ✅      |
| Production schema            | ✅      |
| BigQuery / GA4 analysis      | ✅      |

---

## 📌 Conclusion

This project demonstrates an end-to-end data engineering workflow covering:

```text
Ingestion
   ↓
Staging
   ↓
Transformation
   ↓
Data Quality
   ↓
API Integration
   ↓
Retry & Rate Limiting
   ↓
Enrichment History
   ↓
Semantic Embeddings
   ↓
Vector Search
   ↓
Orchestration
   ↓
Validation
   ↓
Analytics
```

The implementation focuses on **resilience, idempotency, auditability, data quality, and production-oriented design** while remaining executable in a local development environment.
