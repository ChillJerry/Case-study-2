# Phase 2 — SOAR Integration Test

## Objective

Verify that Prometheus monitoring alerts can be forwarded automatically through Alertmanager to the SOAR service running on AWS.

## Architecture

- **Prometheus and Alertmanager:** AWS Monitoring EC2 (`10.20.10.10`)
- **SOAR application:** AWS SOAR EC2 (`10.20.20.10:8000`)
- **Communication:** Private AWS VPC
- **Authentication:** Webhook token supplied through an HTTP header
- **Persistence:** SQLite deduplication database and JSONL audit records

## Test 1 — Application Health

The SOAR service was verified using its `/health` endpoint.

**Result:** Passed.

The service returned `healthy`, and the systemd service remained active after disconnecting from Session Manager.

## Test 2 — Authenticated Alert Delivery

A simulated `ServerDown` alert was submitted from the Monitoring server directly to SOAR.

**Result:** Passed.

The SOAR application authenticated the request, classified the event, and recorded the incident and notification.

## Test 3 — Automatic Alertmanager Delivery

A controlled `ServerDown` alert for `soar-e2e-test:9100` was submitted through Alertmanager.

**Result:** Passed.

SOAR automatically recorded the event at `2026-11-01T14:28:12.806105+00:00`.

The incident was classified as critical and the notification record was created.

## Test 4 — Prometheus-Generated Alerts

Prometheus reported three firing alerts from unavailable on-premises monitoring targets:

| Target | SOAR host label |
|---|---|
| 10.30.0.10:9100 | cs2-onprem-linux |
| 10.30.0.1:9100 | cs2-onprem-gateway |
| 10.30.0.20:9100 | cs2-onprem-security |

All three alerts appeared in the SOAR event records.

These were expected infrastructure availability alerts because the on-premises virtual machines were powered off. They do not indicate a security attack.

## Test 5 — Webhook Delivery Metrics

Alertmanager reported:

- Webhook notification attempts: **4**
- Webhook notification failures: **0**

These values were observed during the integration verification.

## Test 6 — Alert Deduplication

An identical simulated alert was submitted twice.

The first delivery executed the configured actions. The second delivery was identified as a duplicate and returned an empty action list.

**Result:** Passed.

## Conclusion

The Prometheus → Alertmanager → SOAR integration was successfully verified.

The implementation demonstrates authenticated alert forwarding, rule-based event classification, persistent incident recording, and basic duplicate prevention across the hybrid infrastructure.

## Remaining Work

- Implement and test two distinct automated security-response playbooks.
- Add safeguards, recovery procedures, and stronger concurrency handling for remediation.
- Configure SOAR monitoring metrics and automated deployment.
- Record final security and recovery testing evidence.

The current notification action records a local notification but does not send external email or messages.