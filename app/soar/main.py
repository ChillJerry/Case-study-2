
"""HTTP API for receiving monitoring alerts."""

import os
from hmac import compare_digest

from flask import Flask, jsonify, request

from app.soar.actions import execute_actions
from app.soar.rules import evaluate_event


app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 1024 * 1024


@app.get("/health")
def health():
    return jsonify({"status": "healthy", "service": "innovatech-soar"})


@app.post("/alerts")
def receive_alerts():
    expected_token = os.environ.get("SOAR_WEBHOOK_TOKEN")

    if not expected_token:
        return jsonify({"error": "Webhook authentication not configured"}), 503

    provided_token = request.headers.get("X-SOAR-Token", "")

    if not compare_digest(provided_token, expected_token):
        return jsonify({"error": "Unauthorized"}), 401

    payload = request.get_json(silent=True)

    if not isinstance(payload, dict):
        return jsonify({"error": "Expected JSON object"}), 400

    alerts = payload.get("alerts")

    if not isinstance(alerts, list) or not alerts:
        return jsonify({"error": "Expected non-empty alerts list"}), 400

    if len(alerts) > 100:
        return jsonify({"error": "Too many alerts"}), 400

    results = []

    for alert in alerts:
        if not isinstance(alert, dict):
            return jsonify({"error": "Each alert must be an object"}), 400

        try:
            decision = evaluate_event(alert)
        except ValueError as error:
            return jsonify({"error": str(error)}), 400

        results.append((decision, alert.get("status", "firing")))

    processed = []

    for decision, status in results:
        actions = execute_actions(decision, status)

        processed.append({
            "event_type": decision.event_type,
            "host": decision.host,
            "severity": decision.severity,
            "actions": actions,
        })

    return jsonify({
        "status": "processed",
        "count": len(processed),
        "results": processed,
    }), 200


if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=8080,
        debug=False,
    )
