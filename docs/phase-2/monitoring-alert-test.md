
# Phase 2 — Monitoring Alert Test Results

## 1. Test Objective

Verify that the Innovatech hybrid monitoring platform can detect an unavailable on-premises monitoring target, trigger a Prometheus alert, forward it to Alertmanager, and recognize recovery.

The test validates monitoring and alert routing across the WireGuard VPN between AWS and the on-premises infrastructure.

## 2. Test Environment

| Component | Configuration |
|---|---|
| Monitoring platform | AWS EC2, Frankfurt (eu-central-1) |
| Monitoring server | 10.20.10.10 |
| Metrics collection | Prometheus v3.5.0 |
| Alert routing | Alertmanager v0.28.1 |
| Visualization | Grafana v12.1.1 |
| Test machine | cs2-onprem-security |
| Test machine IP | 10.30.0.20 |
| Metrics endpoint | TCP 9100 |
| Network connectivity | Site-to-site WireGuard VPN |

The monitoring platform also includes Grafana Alloy for log collection and Loki for log storage.

## 3. Alert Configuration

Three infrastructure alert rules were configured and validated using Prometheus promtool.

| Alert | Trigger | Duration | Severity |
|---|---|---|---|
| ServerDown | `up == 0` | 1 minute | Critical |
| HighCPUUsage | CPU usage greater than 85% | 5 minutes | Warning |
| HighMemoryUsage | RAM usage greater than 90% | 5 minutes | Warning |

All three alert rules were loaded successfully and reported `health: ok`.

The failure simulation specifically tested the ServerDown alert. CPU and memory threshold alerts were configuration-validated but not failure-tested during this exercise.

## 4. Test Procedure

1. Confirmed the Security VM was reachable by Prometheus.
2. Stopped the prometheus-node-exporter service on the Security VM.
3. Queried the Prometheus API to verify the target became unavailable.
4. Observed the ServerDown alert transition from pending to firing.
5. Queried the Alertmanager API to verify the alert was received.
6. Restarted prometheus-node-exporter on the Security VM.
7. Verified the target returned to healthy status.
8. Confirmed the alert cleared and all configured targets were healthy.

Stopping Node Exporter simulated monitoring endpoint failure without shutting down the Security VM or interrupting the VPN gateway.

## 5. Test Results

### T-MON-01 — Detect Unavailable Target

**Expected:** Prometheus reports `up = 0` for the Security VM.

**Observed:**

```json
{
  "job": "onprem-security",
  "instance": "10.30.0.20:9100",
  "value": "0"
}
```

**Result:** PASS

### T-MON-02 — Trigger Critical Alert

**Expected:** ServerDown initially enters pending and then firing after the configured one-minute duration.

**Observed:**

The alert first entered `pending`, with an activation timestamp of:

`2026-10-31T16:27:42Z`

It subsequently transitioned to:

```json
{
  "alertname": "ServerDown",
  "instance": "10.30.0.20:9100",
  "severity": "critical",
  "state": "firing"
}
```

**Result:** PASS

### T-MON-03 — Alertmanager Receives Incident

**Expected:** Alertmanager receives the critical ServerDown alert.

**Observed:**

```json
{
  "labels": {
    "alertname": "ServerDown",
    "environment": "on-premises",
    "host": "cs2-onprem-security",
    "instance": "10.30.0.20:9100",
    "job": "onprem-security",
    "severity": "critical"
  },
  "receivers": [
    {
      "name": "default-receiver"
    }
  ],
  "status": {
    "state": "active"
  },
  "startsAt": "2026-10-31T16:28:42.825Z"
}
```

**Result:** PASS

This confirms internal alert delivery and routing to the configured Alertmanager receiver. External notification delivery was not part of this test.

### T-MON-04 — Restore Monitoring

**Expected:** Node Exporter restarts successfully and Prometheus reports `up = 1`.

**Observed:**

Node Exporter returned to `active` status.

```json
{
  "job": "onprem-security",
  "instance": "10.30.0.20:9100",
  "value": "1"
}
```

**Result:** PASS

### T-MON-05 — Confirm Alert Resolution

**Expected:** The ServerDown alert clears after recovery.

**Observed:**

```json
{
  "status": "success",
  "data": {
    "alerts": []
  }
}
```

All five configured Prometheus targets subsequently reported `up = 1`:

- prometheus
- alloy
- onprem-linux
- onprem-security
- onprem-gateway

**Result:** PASS

## 6. Results Summary

| Test ID | Description | Result |
|---|---|---|
| T-MON-01 | Detect monitoring endpoint failure | PASS |
| T-MON-02 | Trigger ServerDown alert | PASS |
| T-MON-03 | Deliver alert to Alertmanager | PASS |
| T-MON-04 | Recover Node Exporter service | PASS |
| T-MON-05 | Clear alert and restore target health | PASS |

**Overall result: 5/5 tests passed.**

## 7. Evidence

Evidence was collected through:

- Prometheus HTTP API responses showing target availability and alert states.
- Alertmanager HTTP API response confirming receipt of the critical incident.
- Systemd service verification on the Security VM.
- Grafana Infrastructure Overview dashboard showing monitoring across the hybrid environment.

The alert API responses were captured during the test. No screenshot of the firing alert was captured.

## 8. Limitations and Follow-Up Work

The test verified detection, alert routing, and recovery recognition. The monitoring endpoint was restored manually.

External alert notifications and SOAR-driven automated remediation were not implemented or validated as part of this test.

The current centralized log collection configuration covers the AWS Monitoring server. Additional log collection from other infrastructure components remains a follow-up task.

## 9. Conclusion

The Innovatech hybrid monitoring platform successfully detected a simulated on-premises monitoring failure across the WireGuard VPN.

Prometheus transitioned the ServerDown alert from pending to firing, Alertmanager received the critical incident, and the monitoring platform recognized recovery after Node Exporter was restarted.

The test demonstrates functional cross-environment monitoring, alert detection, internal alert routing, and recovery verification.
