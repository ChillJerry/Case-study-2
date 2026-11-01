
"""HTTP API for receiving monitoring alerts."""

import hashlib
import json
import os
from hmac import compare_digest

from flask import Flask, jsonify, request

from app.soar import actions
from app.soar.dedup import AlertStore
from app.soar.rules import evaluate_event


app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 1024 * 1024


def alert_key(alert):
    """Identify an alert occurrence across webhook deliveries."""
    labels = alert["labels"]

    identity = {
        "fingerprint": alert.get("fingerprint") or "",
        "labels": labels,
        "startsAt": alert.get("startsAt") or "",
    }

    encoded = json.dumps(
        identity, sort_keys=True
    ).encode("utf-8")

    return hashlib.sha256(encoded).hexdigest()


@app.get("/health")
def health():
    return jsonify({
        "status": "healthy",
        "service": "innovatech-soar",
    })


@app.post("/alerts")
def receive_alerts():
    expected_token = os.environ.get("SOAR_WEBHOOK_TOKEN")

    if not expected_token:
        return jsonify({
            "error": "Webhook authentication not configured"
        }), 503

    provided_token = request.headers.get("X-SOAR-Token", "")

    if not compare_digest(provided_token, expected_token):
        return jsonify({"error": "Unauthorized"}), 401

    payload = request.get_json(silent=True)

    if not isinstance(payload, dict):
        return jsonify({"error": "Expected JSON object"}), 400

    alerts = payload.get("alerts")

    if not isinstance(alerts, list) or not 0 < len(alerts) <= 100:
        return jsonify({
            "error": "Expected 1 to 100 alerts"
        }), 400

    validated = []

    for alert in alerts:
        if not isinstance(alert, dict):
            return jsonify({
                "error": "Each alert must be an object"
            }), 400

        try:
            decision = evaluate_event(alert)
        except ValueError as error:
            return jsonify({"error": str(error)}), 400

        validated.append((alert, decision))

    store = AlertStore(
        str(actions.DATA_DIR / "processed_alerts.db")
    )

    processed = []

    for alert, decision in validated:
        status = alert.get("status", "firing")
        key = alert_key(alert)

        if store.is_processed(key, status):
            processed.append({
                "event_type": decision.event_type,
                "host": decision.host,
                "status": "duplicate",
                "actions": [],
            })
            continue

        try:
            executed = actions.execute_actions(
                decision, status
            )
            store.mark_processed(key, status)
        except Exception:
            app.logger.exception(
                "Failed to process SOAR alert"
            )
            return jsonify({
                "error": "Alert processing failed"
            }), 500

        processed.append({
            "event_type": decision.event_type,
            "host": decision.host,
            "status": "processed",
            "severity": decision.severity,
            "actions": executed,
        })

    return jsonify({
        "status": "completed",
        "count": len(processed),
        "results": processed,
    }), 200


if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=8080,
        debug=False,
    )
