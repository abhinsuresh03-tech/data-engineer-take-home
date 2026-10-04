import time
import logging
import requests

from db import get_variants_to_enrich, save_enrichment


import os

API_URL = os.getenv(
    "ENRICHMENT_API_URL",
    "http://127.0.0.1:8000"
)

API_KEY = os.getenv(
    "ENRICHMENT_API_KEY",
    "test_key"
)
MAX_RETRIES = 3
REQUEST_TIMEOUT = 10

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)


def enrich_variant(variant_code):
    url = f"{API_URL}/enrich/{variant_code}"

    headers = {
        "X-Api-Key": API_KEY
    }

    for attempt in range(1, MAX_RETRIES + 1):

        try:
            start_time = time.perf_counter()
            response = requests.get(
                url,
                headers=headers,
                timeout=REQUEST_TIMEOUT
            )
            latency_ms = int(
    (time.perf_counter() - start_time) * 1000
)

            # Rate limited
            if response.status_code == 429:
                retry_after = int(
                    response.headers.get("Retry-After", "1")
                )

                logging.warning(
                    "Rate limited for %s. Waiting %s seconds.",
                    variant_code,
                    retry_after
                )

                time.sleep(retry_after)
                continue

            # Temporary server error
            if response.status_code >= 500:
                wait_time = 2 ** (attempt - 1)

                logging.warning(
                    "Server error for %s. Retry %s/%s.",
                    variant_code,
                    attempt,
                    MAX_RETRIES
                )

                time.sleep(wait_time)
                continue

            # Other HTTP errors
            response.raise_for_status()

            # Parse JSON
            try:
                data = response.json()
            except ValueError:
                logging.error(
                    "Malformed JSON returned for %s",
                    variant_code
                )
                save_enrichment(
        variant_code=variant_code,
        description=None,
        status="failed",
        latency_ms=latency_ms
    )
                return None
            save_enrichment(
    variant_code=variant_code,
    description=data.get("description"),
    status="success",
    latency_ms=latency_ms
)

            return data

        except requests.RequestException as exc:

            logging.warning(
                "Request failed for %s: %s",
                variant_code,
                exc
            )

            if attempt < MAX_RETRIES:
                time.sleep(2 ** (attempt - 1))

    logging.error(
        "Enrichment failed after %s attempts: %s",
        MAX_RETRIES,
        variant_code
    )
    save_enrichment(
    variant_code=variant_code,
    description=None,
    status="failed",
    latency_ms=None
)

    return None

if __name__ == "__main__":
    
    BATCH_SIZE = 100
    MAX_BATCHES = 20

    for batch_number in range(1, MAX_BATCHES + 1):

        variants = get_variants_to_enrich(BATCH_SIZE)

        if not variants:
            print("No variants left to enrich.")
            break

        print(
            f"\nBatch {batch_number}: "
            f"Found {len(variants)} variants to enrich"
        )

        for variant_code in variants:

            print(f"Enriching {variant_code}...")

            result = enrich_variant(variant_code)

            if result:
                print(f"SUCCESS: {variant_code}")
            else:
                print(f"FAILED: {variant_code}")

            # Keep below 5 requests/second
            time.sleep(0.21)

    print("\nEnrichment run finished.")