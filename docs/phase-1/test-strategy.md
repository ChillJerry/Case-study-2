# Test Strategy

## 1. Introduction

I tested the infrastructure to make sure the networking, monitoring, SOAR application and automation tools work correctly.

The tests include individual services, communication between AWS and VirtualBox, security restrictions and recovery from failures.

## 2. Testing Approach

| Test Type | What I Tested |
|---|---|
| Functional | Grafana, DNS, SOAR endpoints and system services |
| Integration | WireGuard, log forwarding and SOAR processing |
| Security | Firewall rules, private access and alert handling |
| Automation | Terraform, GitHub Actions, Ansible and system updates |
| Recovery | Stopping and restarting monitoring services |

## 3. Test Environment

### AWS

| Server | IP Address | Purpose |
|---|---|---|
| Monitoring | 10.20.10.10 | Grafana, Prometheus, Loki, Alloy and Alertmanager |
| SOAR | 10.20.20.10 | Python Flask SOAR |
| Gateway | 10.20.30.10 | WireGuard, routing and NAT |

### VirtualBox

| VM | IP Address | Purpose |
|---|---|---|
| cs2-onprem-gateway | 10.30.0.1 | VPN, firewall and DNS |
| cs2-onprem-linux | 10.30.0.10 | Monitoring and Ansible |
| cs2-onprem-security | 10.30.0.20 | Security monitoring |

## 4. Network and Security Tests

### T01 — Network Segmentation

I checked the AWS subnets and security groups to confirm that Monitoring, SOAR and Gateway are separated.

**Result:** Passed for the inspected configuration.

**Evidence:** `network/01-aws-ec2-instances.png`, `network/02-aws-security-groups.png`

### T02 — Database Isolation

The original PostgreSQL design was replaced with local SQLite and JSONL storage on the SOAR server.

**Result:** Original test no longer applicable; local storage permissions still need verification.

### T03 — WireGuard Connectivity

I checked the VPN handshake using `sudo wg show` and tested private HTTP access to Grafana.

**Result:** Passed.

**Evidence:** `network/03-wireguard-vpn.png`, `network/04-private-connectivity.png`

### T04 — Internal DNS

I tested the three internal DNS records from the gateway and Linux VM using `dig @10.30.0.1`.

**Result:** Passed for direct DNS queries.

**Evidence:** `network/05-private-dns-gateway.png`, `network/05-private-dns-linux.png`

### T05 — Firewall Restrictions

I generated 12 blocked TCP connection attempts across four ports and confirmed they appeared in the nftables logs.

**Result:** Passed.

**Evidence:** `security/16-firewall-blocked-traffic.png`

## 5. Monitoring Tests

### T06 — Infrastructure Metrics

I checked Grafana and confirmed that Prometheus displayed six healthy monitoring targets.

**Result:** Passed.

**Evidence:** `monitoring/06-infrastructure-overview-A.png`

### T07 — Authentication Logs

I verified that Linux system and authentication logs appeared in Grafana, although no failed logins were recorded during the selected period.

**Result:** Passed for log collection.

**Evidence:** `monitoring/07-security-logs-overview-A.png`

### T08 — Firewall Logs

I used Loki to query logs containing `INNOVATECH_FW_DROP` and confirmed that the blocked connections were collected.

**Result:** Passed.

**Evidence:** `monitoring/09-loki-firewall-query.png`

### T09 — Security Event Detection

The SOAR log analyzer retrieved firewall events from Loki and identified a possible port scan.

**Result:** Passed for the Python analyzer; Grafana webhook alerting was not separately tested.

**Evidence:** `soar/12-port-scan-detection.png`

### T10 — Grafana Dashboards

I checked the Infrastructure, Security Logs and SOAR dashboards to confirm that the available metrics and logs were displayed.

**Result:** Passed for the tested panels.

**Evidence:** `monitoring/06-infrastructure-overview-A.png`, `monitoring/07-security-logs-overview-A.png`, `monitoring/08-soar-dashboard-A.png`

## 6. SOAR Tests

### T11 — Security Event Processing

I processed a port-scanning finding generated from real firewall logs through the SOAR application.

**Result:** Passed.

**Evidence:** `soar/12-port-scan-detection.png`

### T12 — Invalid Event Handling

The SOAR application includes input validation and authentication, but I haven't collected separate runtime evidence showing an invalid request being rejected.

**Result:** Not separately verified.

### T13 — Operator Notification

SOAR executed `notify_operator` and prepared a notification record during the port-scanning test.

**Result:** Passed for notification preparation; external delivery was not tested.

**Evidence:** `soar/12-port-scan-detection.png`

### T14 — Simulated Containment

The SOAR application includes simulated containment actions, but I haven't collected evidence from a separate containment test.

**Result:** Not separately verified.

### T15 — Duplicate Detection

I processed the same finding again, and SOAR returned `duplicate` without repeating the original actions.

**Result:** Passed.

**Evidence:** `soar/15-soar-alert-deduplication.png`

### T16 — SOAR Monitoring

I checked the Grafana SOAR dashboard for processed alerts, action counts, failures and service availability.

**Result:** Passed.

**Evidence:** `monitoring/08-soar-dashboard-A.png`, `monitoring/08-soar-dashboard-B.png`

### T17 — Platform Separation

The monitored Linux machines run in VirtualBox, while the SOAR application runs on a separate AWS EC2 instance.

**Result:** Passed.

**Evidence:** `network/01-aws-ec2-instances.png`

## 7. Infrastructure and Automation Tests

### T18 — Terraform Validation

I ran Terraform formatting and validation checks through GitHub Actions.

**Result:** Passed.

**Evidence:** `cicd/19-terraform-validation.png`

### T19 — AWS Deployment

Terraform provisioned the AWS infrastructure, and all three EC2 instances passed their status checks.

**Result:** Passed.

**Evidence:** `network/01-aws-ec2-instances.png`

### T20 — CI/CD Pipelines

I verified successful SOAR and Monitoring deployments through GitHub Actions using my Windows self-hosted runner.

**Result:** Passed.

**Evidence:** `cicd/17-soar-cicd-success.png`, `cicd/18-monitoring-cicd-success.png`

### T21 — Ansible Multi-Node Updates

I ran one Ansible playbook against two Ubuntu machines, and both completed without failures or unreachable hosts.

**Result:** Passed.

**Evidence:** `updates/33-ansible-multi-server-update.png`

### T22 — Update Verification

I checked the Ansible results and unattended-upgrades logs, but didn't record before-and-after package versions for the Ansible run.

**Result:** Partially verified.

**Evidence:** `updates/33-ansible-multi-server-update.png`

## 8. Recovery Tests

### T23 — Grafana Failure and Recovery

I stopped Grafana while the other monitoring containers continued running, then restarted it and received HTTP 200 from its health endpoint.

**Result:** Passed for manual recovery.

**Evidence:** `resilience/21-monitoring-health-before-test.png`, `resilience/22-monitoring-component-failure.png`, `resilience/23-monitoring-component-recovery.png`

### T24 — SOAR Recovery

The SOAR application is managed through systemd, but I haven't documented a controlled failure and recovery test.

**Result:** Not tested.

### T25 — Incident Storage Persistence

I still need to verify that SQLite and JSONL records remain available after restarting SOAR.

**Result:** Not tested.

### T26 — EC2 Recovery

I haven't performed a documented test involving restarting an EC2 instance and checking the application afterward.

**Result:** Not tested.

### T27 — VPN Recovery

WireGuard connectivity works, but I haven't tested deliberately disconnecting and restoring the VPN.

**Result:** Not tested.

### T28 — Backup Restoration

I haven't completed a backup restoration test for monitoring or SOAR data.

**Result:** Not tested.

## 9. Additional Tests

### T29 — Multiple Log Sources

I queried Loki for `aws-monitoring` and `onprem-firewall` and received logs from both sources.

**Result:** Passed.

**Evidence:** `monitoring/10-multiple-log-sources.png`

### T30 — CI/CD Failure Protection

I introduced invalid Grafana dashboard JSON, which caused the validation job to fail and the deployment job to be skipped.

**Result:** Passed.

**Evidence:** `cicd/20-pipeline-failure-protection.png`

### T31 — Automatic OS Updates

I checked unattended-upgrades on five Linux servers and confirmed successful update checks, with package installations shown on four servers.

**Result:** Passed for the observed checks and installations.

**Evidence:** `updates/24-automated-system-updates.png` through `updates/32-onprem-security-update-execution.png`

### T32 — SOAR Code Inspection

I used the local SOAR Execution Inspector to view the detection results and Python functions responsible for processing them.

**Result:** Passed.

**Evidence:** `soar/13-soar-code-inspector.png`, `soar/14-soar-rule-evaluation.png`

## 10. Test Summary

| Category | Passed | Partial / Limited | Not Tested / Verified |
|---|---:|---:|---:|
| Network and Security | 4 | 0 | 1 |
| Monitoring | 4 | 1 | 0 |
| SOAR | 5 | 0 | 2 |
| Infrastructure and Automation | 4 | 1 | 0 |
| Recovery | 1 | 0 | 5 |
| Additional Tests | 4 | 0 | 0 |
| **Total** | **22** | **2** | **8** |

All screenshots are stored in `docs/evidence/` under the relevant folders.

## 11. Remaining Tests

The main things left to test are SOAR recovery, data persistence, backup restoration, VPN recovery and simulated containment.

The networking, monitoring, security event processing, CI/CD and multi-server update tests have already produced working results.