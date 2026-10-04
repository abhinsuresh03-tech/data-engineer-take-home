import os
import psycopg2

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", "5432")),
    "database": os.getenv("DB_NAME", "aventus_pipeline"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD"),
}


def get_connection():
    return psycopg2.connect(**DB_CONFIG)


def get_variants_to_enrich(limit=None):
    conn = get_connection()

    try:
        with conn.cursor() as cursor:

            query = """
                SELECT vs.variant_code
                FROM variant_summary vs
                WHERE NOT EXISTS (
                    SELECT 1
                    FROM variant_enrichment ve
                    WHERE ve.variant_code = vs.variant_code
                      AND ve.status = 'success'
                )
                ORDER BY vs.variant_code
            """

            if limit is not None:
                query += " LIMIT %s"
                cursor.execute(query, (limit,))
            else:
                cursor.execute(query)

            rows = cursor.fetchall()

            return [row[0] for row in rows]

    finally:
        conn.close()

def save_enrichment(
    variant_code,
    description,
    status,
    latency_ms
):
    conn = get_connection()

    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO variant_enrichment (
                    variant_code,
                    enrichment_description,
                    status,
                    latency_ms,
                    created_at
                )
                VALUES (%s, %s, %s, %s, NOW());
            """, (
                variant_code,
                description,
                status,
                latency_ms
            ))

        conn.commit()

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()

if __name__ == "__main__":
    variants = get_variants_to_enrich(5)

    print("Variants to enrich:")
    for variant in variants:
        print(variant)

        