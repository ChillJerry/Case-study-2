# Requirements Analysis

## 1. Introduction

For this project, I'm building a hybrid infrastructure that connects AWS with an on-premises environment running in VirtualBox.

The idea is to have a central place where I can monitor servers, collect logs, detect suspicious activity and automate certain security responses.

I also want the infrastructure to be manageable through code instead of configuring everything manually.

The main technologies I'm using are AWS, Terraform, WireGuard, Grafana, Prometheus, Loki, Python, Ansible and GitHub Actions.

## 2. Project Goals

The main goals of the project are:

- Connect AWS and VirtualBox through a secure VPN.
- Separate the infrastructure into different network segments.
- Keep internal services private.
- Configure internal DNS resolution.
- Collect system metrics and logs in one location.
- Detect suspicious activity using firewall and system logs.
- Build a SOAR application that processes security events.
- Automate incident recording and notification preparation.
- Monitor the SOAR application itself.
- Use Terraform to manage AWS infrastructure.
- Use GitHub Actions for automated testing and deployment.
- Use Ansible to update multiple Linux machines.
- Configure automatic operating-system updates.
- Test failures and recovery.
- Document the infrastructure so it can be understood and maintained.

The project is built as a university demonstration environment, so it doesn't need to provide the same level of redundancy or scale as a production infrastructure.

## 3. Technologies Used

| Component | Technology |
|---|---|
| Cloud infrastructure | AWS EC2 and VPC |
| Local virtualization | VirtualBox |
| Operating system | Ubuntu Linux |
| VPN | WireGuard |
| Internal DNS | dnsmasq |
| Metrics | Prometheus |
| Dashboards | Grafana |
| Logs | Grafana Loki |
| Telemetry collection | Grafana Alloy |
| Alerting | Prometheus Alertmanager |
| SOAR | Python, Flask and Gunicorn |
| Incident records | JSONL |
| Alert deduplication | SQLite |
| Infrastructure as Code | Terraform |
| Configuration management | Ansible |
| Automatic OS updates | unattended-upgrades |
| CI/CD | GitHub Actions |
| Monitoring containers | Docker Compose |

## 4. Functional Requirements

### FR-01 — Infrastructure Resilience

**Requirement: REQ-NCA-P2-01**

The infrastructure should be able to recover when an individual service fails without requiring the entire environment to be rebuilt.

For monitoring, I use separate Docker containers for Grafana, Prometheus, Loki, Alloy and Alertmanager.

This allows me to restart one service while keeping the others running.

I tested this by stopping Grafana through Docker Compose.

While Grafana was stopped, the other four monitoring containers continued running. I then started Grafana again and checked its health endpoint.

The endpoint returned `HTTP 200 OK`, and its database status was `ok`.

This demonstrates manual recovery of an individual service. Automatic failover, complete backup restoration and measured recovery times still need additional testing.

**Evidence:**

- `docs/evidence/resilience/21-monitoring-health-before-test.png`
- `docs/evidence/resilience/22-monitoring-component-failure.png`
- `docs/evidence/resilience/23-monitoring-component-recovery.png`

### FR-02 — Network Segmentation

**Requirement: REQ-NCA-P2-02**

Different infrastructure components should be separated so that they cannot communicate freely with every other system.

I configured one AWS VPC using `10.20.0.0/16`.

The network is divided into three main subnets:

| Subnet | Network | Purpose |
|---|---|---|
| Monitoring | `10.20.10.0/24` | Grafana, Prometheus, Loki and other monitoring services |
| SOAR | `10.20.20.0/24` | SOAR application |
| Gateway | `10.20.30.0/24` | VPN and network routing |

The on-premises environment uses the separate network `10.30.0.0/24`.

AWS security groups control which cloud services can communicate with each other.

On the on-premises gateway, I use nftables with a default-drop input policy. Only specifically allowed connections are accepted.

I tested the firewall by generating TCP connection attempts to unauthorized ports. The firewall blocked these connections and recorded them in `/var/log/kern.log`.

These events were also collected by Loki and later analyzed by the SOAR application.

**Evidence:**

- `docs/evidence/network/01-aws-ec2-instances.png`
- `docs/evidence/network/02-aws-security-groups.png`
- `docs/evidence/security/16-firewall-blocked-traffic.png`

### FR-03 — Private Resource Access

**Requirement: REQ-NCA-P2-03**

Internal infrastructure services should not be directly exposed to the internet.

The AWS monitoring and SOAR instances have private IP addresses:

| Server | Private IP |
|---|---|
| Monitoring | `10.20.10.10` |
| SOAR | `10.20.20.10` |
| AWS VPN Gateway | `10.20.30.10` |

The monitoring and SOAR instances don't have public IPv4 addresses.

The gateway provides the connection between AWS and the on-premises infrastructure through WireGuard.

Grafana is accessible through the VPN, while Loki accepts log traffic from approved sources.

The SOAR API listens on port 8000, but its AWS security group only allows incoming connections from the monitoring server's security group.

For administration, I use AWS Systems Manager Session Manager instead of exposing SSH publicly.

I tested private connectivity from the on-premises gateway to Grafana using:

```bash
curl --max-time 10 -I http://10.20.10.10:3000/login
```

The request returned `HTTP 200 OK`, showing that the service was accessible through the private network.

I also confirmed that direct access from the on-premises gateway to SOAR port 8000 was not permitted by the existing security group rules.

**Evidence:**

- `docs/evidence/network/01-aws-ec2-instances.png`
- `docs/evidence/network/02-aws-security-groups.png`
- `docs/evidence/network/04-private-connectivity.png`

### FR-04 — Internal DNS Resolution

**Requirement: REQ-NCA-P2-04**

Machines should be able to resolve internal service names instead of relying only on IP addresses.

I configured dnsmasq on the on-premises gateway at `10.30.0.1`.

The following DNS records are available:

| Hostname | IP Address |
|---|---|
| `monitoring.innovatech.internal` | `10.20.10.10` |
| `soar.innovatech.internal` | `10.20.20.10` |
| `gateway.innovatech.internal` | `10.30.0.1` |

dnsmasq listens on the gateway's private interface instead of replacing Ubuntu's existing systemd-resolved service.

I also updated the nftables firewall to allow DNS queries from the on-premises network on UDP and TCP port 53.

The rules were added to `/etc/nftables.conf`, checked for syntax errors and applied using a service reload.

I tested DNS from both the gateway and `cs2-onprem-linux` using:

```bash
dig @10.30.0.1 monitoring.innovatech.internal +short
dig @10.30.0.1 soar.innovatech.internal +short
dig @10.30.0.1 gateway.innovatech.internal +short
```

All three records returned the expected private addresses.

DNS resolution was also checked again after reloading the firewall.

The current setup supports explicit DNS queries from the tested on-premises systems. I haven't configured the internal DNS server as the default resolver on every VM, and AWS-side DNS queries haven't been tested.

**Evidence:**

- `docs/evidence/network/05-private-dns-gateway.png`
- `docs/evidence/network/05-private-dns-linux.png`

### FR-05 — Automated Multi-Node Updates

**Requirement: REQ-NCA-P1-05**

The infrastructure should support updating multiple Linux machines from a central location instead of manually updating each server.

I implemented centralized updates using Ansible.

The `cs2-onprem-linux` VM acts as the Ansible control node.

The managed systems are:

- `cs2-onprem-linux`, using a local connection.
- `cs2-onprem-security`, using SSH over the internal network.

The update playbook refreshes the package list, installs available upgrades and checks whether a reboot is required.

It uses `serial: 1` so the machines are updated one at a time. Automatic reboots are disabled to avoid interrupting services unexpectedly.

The Ansible execution completed with these results:

| Server | OK | Changed | Failed | Unreachable |
|---|---:|---:|---:|---:|
| cs2-onprem-linux | 6 | 1 | 0 | 0 |
| cs2-onprem-security | 6 | 0 | 0 | 0 |

Both servers completed the playbook without failures.

I also configured Ubuntu unattended-upgrades across all five Linux servers:

- AWS Monitoring
- AWS SOAR
- On-premises Gateway
- On-premises Linux
- On-premises Security

I checked their update configurations and execution logs.

The logs show automatic update checks on all five machines and successful package installations on four of them.

The on-premises gateway also completed an automatic check, but its available log evidence did not show an actual package installation.

Ansible handles centralized updates for the two selected machines, while unattended-upgrades handles automatic updates independently on each server.

**Evidence:**

- `docs/evidence/updates/24-automated-system-updates.png`
- `docs/evidence/updates/25-soar-automatic-updates.png`
- `docs/evidence/updates/26-soar-update-execution.png`
- `docs/evidence/updates/27-onprem-gateway-updates.png`
- `docs/evidence/updates/28-onprem-gateway-update-execution.png`
- `docs/evidence/updates/29-onprem-linux-updates.png`
- `docs/evidence/updates/30-onprem-linux-update-execution.png`
- `docs/evidence/updates/31-onprem-security-updates.png`
- `docs/evidence/updates/32-onprem-security-update-execution.png`
- `docs/evidence/updates/33-ansible-multi-server-update.png`

### FR-06 — Observability Platform Evaluation

**Requirement: REQ-NCA-P2-06**

Before choosing the monitoring platform, I needed to compare different observability solutions.

I researched three options:

| Platform | Advantages | Disadvantages |
|---|---|---|
| Grafana, Prometheus and Loki | Flexible metrics, logs, dashboards and integrations | Requires managing multiple services |
| Zabbix | Integrated infrastructure monitoring and alerting | Less flexible for the custom SOAR integration |
| OpenSearch | Advanced log searching and analysis | Higher resource requirements and more complex setup |

I chose Grafana, Prometheus and Loki because they fit the project requirements without introducing unnecessary complexity.

Prometheus collects metrics, Loki stores logs, and Grafana provides dashboards and log investigation.

Grafana Alloy collects telemetry, while Alertmanager handles Prometheus alerts.

This setup also allows me to monitor the SOAR application using custom Prometheus metrics.

More details about the comparison are available in `docs/phase-1/technology-choices.md`.

### FR-07 — Centralized Logging and Alerting

**Requirement: REQ-NCA-P2-07**

The monitoring platform must collect logs from at least two different sources.

I use Grafana Alloy to collect logs and forward them to Loki.

The main log sources are:

| Log source | Content |
|---|---|
| `aws-monitoring` | AWS monitoring server system logs |
| `aws-monitoring-auth` | Linux authentication logs |
| `onprem-firewall` | On-premises firewall logs |

I tested the log collection using Grafana Explore.

One of the queries I used was:

```logql
{job=~"aws-monitoring|onprem-firewall"}
```

The query returned logs from both AWS and the on-premises gateway.

I also queried firewall events using:

```logql
{job="onprem-firewall"} |= "INNOVATECH_FW_DROP"
```

This returned the firewall logs generated during the controlled connection tests.

The monitoring platform also contains three Prometheus alert rules:

- `ServerDown`
- `HighCPUUsage`
- `HighMemoryUsage`

All three rules were loaded successfully and appeared in the normal state during the test.

The SOAR log analyzer also uses Loki as a source of firewall events. This allows security-related information to be filtered and processed instead of manually reading every raw log entry.

The existing evidence confirms logging, querying and rule configuration. It doesn't demonstrate external notification delivery for every possible alert type.

**Evidence:**

- `docs/evidence/monitoring/07-security-logs-overview-A.png`
- `docs/evidence/monitoring/07-security-logs-overview-B.png`
- `docs/evidence/monitoring/07-security-logs-overview-C.png`
- `docs/evidence/monitoring/07-security-logs-overview-D.png`
- `docs/evidence/monitoring/09-loki-firewall-query.png`
- `docs/evidence/monitoring/10-multiple-log-sources.png`
- `docs/evidence/monitoring/11-monitoring-alerting.png`

### FR-08 — Event-Driven SOAR

**Requirement: REQ-NCA-P2-08**

The infrastructure must include a SOAR application that receives security events, evaluates them and executes automated response actions.

I developed the SOAR application using Python and Flask.

It runs on a separate AWS EC2 instance through Gunicorn and a systemd service.

The application has three main API endpoints:

| Endpoint | Purpose |
|---|---|
| `POST /alerts` | Receive security alerts |
| `GET /health` | Check application health |
| `GET /metrics` | Expose monitoring metrics |

The SOAR workflow includes:

1. Receiving an authenticated alert.
2. Validating the incoming information.
3. Evaluating the event against predefined security rules.
4. Checking whether the alert has already been processed.
5. Selecting the appropriate response actions.
6. Recording the actions and their results.
7. Updating Prometheus metrics.

The response actions include:

- `record_incident` — records the security incident.
- `notify_operator` — prepares and records a notification.
- `simulate_ip_containment` — simulates an IP containment response using validation and approved targets.
- `simulate_service_containment` — simulates a service containment response.

Containment is simulated and does not automatically modify the real firewall.

#### Port-scanning detection

I also developed a Python log analyzer that retrieves firewall events directly from Loki.

The analyzer filters the logs and looks for multiple blocked TCP connections targeting different ports.

For the controlled test, I generated traffic from `10.30.0.10` toward `10.30.0.1`.

The analyzer reported:

| Result | Value |
|---|---|
| Raw logs examined | 24 |
| Relevant TCP events | 12 |
| Targeted ports | 4 |
| Security findings | 1 |
| Classification | Possible Port Scanning |
| Severity | Warning |

The finding was sent to the SOAR application, which processed it and reported the `record_incident` and `notify_operator` actions.

I then submitted the same finding again using the same analysis window.

The second execution returned `duplicate`, demonstrating that the application recognized the previously processed alert.

#### Local SOAR viewer

I built a local SOAR Execution Inspector to make the processing easier to follow.

The viewer displays:

- The detected incident.
- Source and destination IP addresses.
- The number of blocked connections.
- Targeted ports.
- The detection reason.
- The SOAR processing steps.
- Response results.
- Original firewall evidence.
- The Python functions responsible for each part of the processing.

The viewer runs locally on Windows and is not deployed to AWS.

**Evidence:**

- `docs/evidence/soar/12-port-scan-detection.png`
- `docs/evidence/soar/13-soar-code-inspector.png`
- `docs/evidence/soar/14-soar-rule-evaluation.png`
- `docs/evidence/soar/15-soar-alert-deduplication.png`
- `docs/evidence/security/16-firewall-blocked-traffic.png`

### FR-09 — SOAR Monitoring

**Requirement: REQ-NCA-P2-09**

The SOAR application must also be monitored so that its health and processing activity can be checked.

The Flask application exposes a `/metrics` endpoint that Prometheus collects.

Grafana displays the information in the SOAR Security Operations dashboard.

The dashboard includes:

- SOAR service status.
- Availability measurements.
- Process memory usage.
- Processed alerts.
- Duplicate alerts.
- Processing failures.
- Security event types.
- Event severity.
- Response action counts.
- Processing latency.

During testing, the dashboard displayed two processed alerts, three recorded actions and no processing failures at the time of capture.

The dashboard also showed the SOAR application as online.

**Evidence:**

- `docs/evidence/monitoring/08-soar-dashboard-A.png`
- `docs/evidence/monitoring/08-soar-dashboard-B.png`
- `docs/evidence/monitoring/08-soar-dashboard-C.png`
- `docs/evidence/monitoring/08-soar-dashboard-D.png`

### FR-10 — Infrastructure as Code

**Requirement: REQ-NCA-P2-10**

Infrastructure should be managed using configuration files instead of relying only on manual changes.

I use Terraform to manage the AWS infrastructure.

The Terraform configuration includes:

- VPC.
- Subnets.
- Route tables.
- EC2 instances.
- Security groups.
- IAM roles and instance profiles.
- Networking resources.

Terraform state is stored remotely in Amazon S3.

The monitoring services are managed using Docker Compose.

The SOAR application uses a systemd service and deployment scripts.

I also use Ansible to manage package updates on two on-premises Linux systems.

The infrastructure and application configuration is stored in GitHub.

The current setup uses Terraform for infrastructure provisioning, while application deployment is handled by separate CI/CD workflows.

**Evidence:**

- `docs/evidence/network/01-aws-ec2-instances.png`
- `docs/evidence/cicd/19-terraform-validation.png`
- `docs/evidence/updates/33-ansible-multi-server-update.png`

### FR-11 — CI/CD Automation

**Requirement: REQ-NCA-P2-11**

The project must use automated testing and deployment workflows.

I configured GitHub Actions with a Windows self-hosted runner.

The repository contains three main workflows:

| Workflow | Purpose |
|---|---|
| Infrastructure Checks | Terraform formatting and validation |
| SOAR CI/CD | Python application testing and AWS deployment |
| Monitoring CI/CD | Grafana dashboard validation and AWS deployment |

The SOAR workflow tests the Python application before deploying it.

The deployment package is uploaded to Amazon S3 and deployed to the SOAR server using AWS Systems Manager.

The Monitoring workflow checks the Grafana dashboard JSON files before deploying them to the monitoring instance.

I also tested the failure protection of the monitoring pipeline.

For this test, I introduced an invalid JSON file on a separate test branch.

The validation step failed with a JSON decoding error, and the deployment job was skipped.

This confirmed that invalid dashboard configuration would not be deployed through the normal pipeline.

**Evidence:**

- `docs/evidence/cicd/17-soar-cicd-success.png`
- `docs/evidence/cicd/18-monitoring-cicd-success.png`
- `docs/evidence/cicd/19-terraform-validation.png`
- `docs/evidence/cicd/20-pipeline-failure-protection.png`

### FR-12 — DevOps Platform Integration

**Requirement: REQ-NCA-P2-12**

The project must use a DevOps platform for source code management, infrastructure configuration and automated workflows.

I use GitHub to maintain the project.

The repository contains:

- Python SOAR application.
- Terraform infrastructure.
- Monitoring configuration.
- Ansible playbooks.
- CI/CD workflows.
- Automated tests.
- Documentation.
- Screenshots and testing evidence.

Git history makes it possible to track changes, while GitHub Actions handles testing and selected deployment tasks.

## 5. Non-Functional Requirements

### NFR-01 — Security

The infrastructure should restrict unnecessary access and keep internal services protected.

The main security controls are AWS security groups, private subnets, WireGuard, nftables and Systems Manager.

SOAR requests require authentication, and repeated alerts are handled through deduplication.

Potentially disruptive containment actions are simulated instead of changing firewall rules automatically.

### NFR-02 — Availability and Recovery

The system should support recovery when individual services fail.

The monitoring stack uses separate containers, and the SOAR application runs as a managed systemd service.

I tested manual recovery by stopping and restarting Grafana.

Automatic failover and complete disaster recovery have not been demonstrated.

### NFR-03 — Maintainability

The infrastructure should be manageable without having to remember every manual configuration step.

Terraform, Ansible, Docker Compose and GitHub Actions are used to organize infrastructure and deployment processes.

The SOAR application is separated into modules for processing, rules, deduplication and response actions.

The local execution viewer also helps explain how the different Python functions work.

### NFR-04 — Scalability

The monitoring system should support adding more monitored machines and log sources.

Prometheus targets and Alloy collection configurations can be extended.

Additional SOAR rules and actions can also be developed without replacing the whole application.

Large-scale performance testing has not been completed.

### NFR-05 — Observability

The infrastructure should make operational problems and security events easier to investigate.

Grafana provides a central interface for infrastructure metrics, system logs, firewall events and SOAR activity.

Prometheus stores metrics, while Loki stores logs.

### NFR-06 — Data Integrity and Persistence

Important monitoring and security information should remain available after normal service restarts.

SOAR uses SQLite to track processed alert fingerprints.

Incident information, events and notifications are recorded in JSONL files.

Prometheus and Loki use their own storage for metrics and logs.

The storage mechanisms are implemented, but a complete backup restoration test is still needed.

### NFR-07 — Reproducibility

Infrastructure and application configuration should be stored in a form that can be reused.

Terraform manages AWS infrastructure, Docker Compose manages monitoring services, and GitHub Actions automates application deployment.

Ansible provides repeatable package updates for two selected machines.

The local SOAR viewer can run without requiring an additional AWS server.

### NFR-08 — Performance

The infrastructure should be able to handle the expected demonstration workload.

Grafana displays CPU, memory, disk usage, availability and SOAR processing information.

The SOAR dashboard also includes response latency and action outcomes.

The current testing confirms normal operation under the demonstrated workload, but it does not establish maximum system capacity.

### NFR-09 — Data Protection

Operational and security information should be protected from unnecessary exposure.

Internal services use restricted network access.

Credentials and private keys should not be committed to the repository.

Loki is configured with a seven-day log retention period.

The security tests use controlled lab traffic instead of real user attacks.

## 6. Testing

### 6.1 Network Testing

I tested WireGuard connectivity, private access, security group rules and internal DNS.

I also generated unauthorized TCP connections to check that the firewall blocks and logs them.

### 6.2 Monitoring Testing

I checked the Grafana dashboards and used Loki queries to confirm that logs from both AWS and on-premises systems were being collected.

I also inspected the Prometheus alert rules and their current states.

### 6.3 SOAR Testing

I generated controlled security events, analyzed firewall logs and processed the resulting security finding.

I also repeated the same alert to check whether the system would recognize it as a duplicate.

The SOAR monitoring dashboard and local viewer were used to inspect processing results.

### 6.4 CI/CD Testing

I verified the successful SOAR and Monitoring CI/CD workflows.

I also tested the monitoring pipeline with invalid JSON to confirm that deployment is blocked when validation fails.

### 6.5 Update Testing

I ran an Ansible update playbook against two Linux systems and checked the results.

I also checked the unattended-upgrades configuration and execution logs on all five Linux servers.

### 6.6 Recovery Testing

I stopped the Grafana container while keeping the remaining monitoring services running.

After starting Grafana again, I verified its health through the HTTP API.

## 7. Remaining Work

The main infrastructure and automation components are working, but some areas still need additional testing.

| Area | Remaining work |
|---|---|
| Backup recovery | Test restoration of stored data |
| Automatic recovery | Test automatic recovery separately from manual restarts |
| Recovery duration | Measure service downtime during a controlled test |
| Internal DNS | Test default resolver configuration and AWS-side resolution if needed |
| Notifications | Verify external delivery if a notification service is configured |
| Containment | Test the simulated containment action separately |
| Performance | Perform more detailed workload testing |
| Reproducibility | Verify a complete deployment from a clean environment |

## 8. Risks

| Risk | Impact | How I reduce the risk |
|---|---|---|
| VPN gateway failure | AWS and on-premises connectivity is lost | Monitoring and recovery procedures |
| Incorrect firewall rules | Legitimate traffic gets blocked | Syntax checks and connectivity tests |
| Monitoring failure | Loss of operational visibility | Separate services and recovery procedures |
| Incorrect SOAR detection | False positives | Detection thresholds and controlled testing |
| Duplicate alerts | Repeated response actions | SQLite deduplication |
| Exposed credentials | Unauthorized access | Private configuration and restricted permissions |
| Update failures | Service interruption | Sequential Ansible updates and manual reboot control |
| Broken deployment | Application or dashboard errors | Automated CI/CD validation |
| AWS costs | Unnecessary spending | Small instances and stopping unused resources |

## 9. Current Result

At this stage, the project has a working hybrid network connecting AWS and VirtualBox through WireGuard.

Centralized monitoring and log collection are operational, and the SOAR application can process security findings generated from firewall events.

Terraform, GitHub Actions and Ansible are used for infrastructure and system management, while unattended-upgrades provides automatic updates on the Linux servers.

The main remaining work is focused on additional recovery testing, verifying the remaining limitations and completing the final project documentation.