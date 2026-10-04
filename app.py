"""
Mock enrichment API for the data engineer take-home.

Behavior (documented in the assessment):
  - GET /enrich/<variant_code>, requires header X-Api-Key
  - Returns a generated product description + tags for the given variant_code
  - ~15% of calls return HTTP 429 (rate limited, independent of the real limiter below)
  - ~5% of calls return HTTP 500
  - ~2% of calls return HTTP 200 with a malformed (truncated/invalid) JSON body
  - Enforces a REAL per-API-key rate limit of 5 requests/second (returns 429 with
    Retry-After when exceeded, on top of the random 429s above)

Run:
    pip install -r requirements.txt
    python app.py
    # serves on http://127.0.0.1:8000

No persistence, no auth beyond checking the header is present — this is a stub to be
called by the candidate's enrichment script, not a real service.
"""
import random
import time
import threading
from collections import defaultdict, deque
from flask import Flask, jsonify, request, Response

app = Flask(__name__)

RATE_LIMIT_PER_SEC = 5
RANDOM_429_RATE = 0.15
RANDOM_500_RATE = 0.05
MALFORMED_RATE = 0.02

_lock = threading.Lock()
_request_times = defaultdict(deque)  # api_key -> deque[timestamps]

ADJECTIVES = ["breathable", "lightweight", "tailored", "durable", "classic", "relaxed-fit",
              "hand-finished", "timeless", "versatile", "premium"]
DETAILS = ["with a soft brushed interior", "designed for everyday wear", "cut for a modern silhouette",
           "made to layer easily", "finished with subtle contrast stitching",
           "built from a quality-tested fabric blend", "styled for both work and weekend"]


def generate_description(variant_code: str) -> dict:
    adj = random.choice(ADJECTIVES)
    detail = random.choice(DETAILS)
    return {
        "variant_code": variant_code,
        "description": f"A {adj} piece, {detail}.",
        "tags": random.sample(ADJECTIVES, k=3),
    }


def check_rate_limit(api_key: str) -> bool:
    """Returns True if the request is allowed, False if it should be rate limited."""
    now = time.monotonic()
    with _lock:
        window = _request_times[api_key]
        while window and now - window[0] > 1.0:
            window.popleft()
        if len(window) >= RATE_LIMIT_PER_SEC:
            return False
        window.append(now)
        return True


@app.route("/enrich/<variant_code>", methods=["GET"])
def enrich(variant_code):
    api_key = request.headers.get("X-Api-Key")
    if not api_key:
        return jsonify({"error": "missing X-Api-Key header"}), 401

    if not check_rate_limit(api_key):
        resp = jsonify({"error": "rate limit exceeded"})
        resp.status_code = 429
        resp.headers["Retry-After"] = "1"
        return resp

    roll = random.random()
    if roll < RANDOM_500_RATE:
        return jsonify({"error": "internal error"}), 500
    if roll < RANDOM_500_RATE + RANDOM_429_RATE:
        resp = jsonify({"error": "rate limited"})
        resp.status_code = 429
        resp.headers["Retry-After"] = "1"
        return resp
    if roll < RANDOM_500_RATE + RANDOM_429_RATE + MALFORMED_RATE:
        # Deliberately broken JSON — truncated body, still a 200
        body = str(generate_description(variant_code))[:40]
        return Response(body, status=200, mimetype="application/json")

    return jsonify(generate_description(variant_code))


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8000)
