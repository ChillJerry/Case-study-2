# Technical Design

## 1. Introduction

For this project, I built a hybrid infrastructure that connects an AWS environment with several Ubuntu virtual machines running locally in VirtualBox.

The main idea is to have a central monitoring platform in AWS that collects information from both environments. I also developed a Python SOAR application that can analyze security events and execute predefined response actions.

The infrastructure is managed using Terraform, Ansible, Docker Compose and GitHub Actions.

I wanted to keep the environment relatively simple and inexpensive while still implementing the main networking, monitoring, security and automation requirements.

## 2. Infrastructure Overview

The infrastructure is divided into two environments:

1. AWS cloud infrastructure.
2. On-premises infrastructure simulated through VirtualBox.

AWS hosts the monitoring platform, SOAR application and VPN gateway.

The on-premises environment contains three Ubuntu virtual machines used for networking, monitoring, security event generation and centralized updates.

Both environments communicate through an encrypted WireGuard VPN.

### 2.1 AWS Infrastructure

I deployed three EC2 instances in the AWS Frankfurt region (`eu-central-1`).

| Server | Instance Type | Private IP | Storage | Purpose |
|---|---|---|---|---|
| Monitoring | t3.medium | 10.20.10.10 | 40 GiB gp3 | Monitoring and logging |
| SOAR | t3.small | 10.20.20.10 | 20 GiB gp3 | Security event processing |
| Gateway | t3.micro | 10.20.30.10 | 12 GiB gp3 | VPN, routing and NAT |

All three instances use Ubuntu Server 24.04 LTS.

The monitoring and SOAR instances are deployed in private subnets without directly assigned public IPv4 addresses.

The gateway has a public IPv4 address because it needs to accept WireGuard connections from the on-premises environment.

The instances were provisioned using Terraform.

### 2.2 On-Premises Infrastructure

The on-premises environment runs in VirtualBox on my Windows computer.

It contains three Ubuntu virtual machines.

| VM | IP Address | Purpose |
|---|---|---|
| cs2-onprem-gateway | 10.30.0.1 | Local gateway, WireGuard, firewall and DNS |
| cs2-onprem-linux | 10.30.0.10 | Linux monitoring target and Ansible controller |
| cs2-onprem-security | 10.30.0.20 | Security monitoring target |

The VMs communicate through an internal VirtualBox network.

The gateway has an additional network adapter for outbound connectivity and uses the internal interface to communicate with the other two machines.

The Linux and Security VMs are separate from the AWS-hosted SOAR application, which satisfies the requirement to keep the monitored systems on a different platform.

### 2.3 Architecture Diagram

The network architecture diagram is stored under:

`docs/diagrams/network-architecture.png`

It shows the AWS VPC, on-premises network, VPN gateways and the connection between the two environments.

## 3. AWS Network Design

### 3.1 VPC and Subnets

I created a dedicated AWS VPC using:

`10.20.0.0/16`

The infrastructure is divided into three subnets.

| Subnet | CIDR | Resources |
|---|---|---|
| Monitoring | 10.20.10.0/24 | Monitoring EC2 |
| SOAR | 10.20.20.0/24 | SOAR EC2 |
| Gateway | 10.20.30.0/24 | VPN Gateway EC2 |

The separate subnets make it easier to control network access and understand which resources belong to each part of the infrastructure.

### 3.2 Routing

The gateway subnet has a route to the AWS Internet Gateway.

The private Monitoring and SOAR subnets use the gateway EC2 instance for outbound internet access.

The AWS gateway performs network address translation using Linux IP forwarding and nftables.

A route for the on-premises network `10.30.0.0/24` directs traffic through the gateway.

This allows AWS systems to communicate with the on-premises environment through WireGuard.

### 3.3 EC2 Gateway Instead of AWS NAT Gateway

I decided to use an EC2 instance for NAT instead of an AWS-managed NAT Gateway.

The main reason was cost.

A managed NAT Gateway would introduce additional hourly charges, while the EC2 gateway can also handle WireGuard connectivity.

The gateway uses:

- Linux IP forwarding.
- nftables.
- Source NAT masquerading for internet-bound traffic.
- Routing for the on-premises network.
- WireGuard VPN.

Source/destination checking is disabled on the gateway EC2 instance because it forwards traffic for other machines.

The disadvantage is that this gateway becomes a single point of failure.

If the gateway is stopped, the private AWS instances can lose outbound connectivity and the hybrid VPN becomes unavailable.

### 3.4 AWS Security Groups

I created separate security groups for the Monitoring, SOAR and Gateway instances.

The main access rules are:

| Source | Destination | Port | Purpose |
|---|---|---|---|
| On-premises network | Monitoring | TCP 3000 | Grafana |
| Authorized on-premises systems | Monitoring | TCP 3100 | Loki log ingestion |
| SOAR security group | Monitoring | TCP 3100 | SOAR log access |
| Monitoring security group | SOAR | TCP 8000 | SOAR API and metrics |
| Internet | AWS Gateway | UDP 51820 | WireGuard |

The SOAR API is not exposed directly to the on-premises environment.

Only the Monitoring security group is allowed to connect to SOAR on port 8000.

The gateway and monitoring rules are designed around the specific communication paths needed by the project instead of allowing unrestricted access.

Administrative access to the AWS instances is provided through Systems Manager Session Manager.

### 3.5 Network Testing

I verified the AWS infrastructure by checking:

- EC2 instance states and health checks.
- AWS security group rules.
- Private IP addressing.
- WireGuard connectivity.
- Private HTTP access to Grafana.

The on-premises gateway successfully accessed Grafana using its private AWS address.

**Evidence:**

- `docs/evidence/network/01-aws-ec2-instances.png`
- `docs/evidence/network/02-aws-security-groups.png`
- `docs/evidence/network/04-private-connectivity.png`

## 4. WireGuard VPN

### 4.1 VPN Design

WireGuard provides the encrypted connection between AWS and VirtualBox.

I use a dedicated tunnel network:

`10.40.0.0/30`

The tunnel addresses are:

| Gateway | Tunnel IP |
|---|---|
| AWS Gateway | 10.40.0.1 |
| On-premises Gateway | 10.40.0.2 |

The on-premises gateway connects to the AWS gateway using its public IPv4 address on UDP port 51820.

The VPN allows traffic between:

- AWS: `10.20.0.0/16`
- On-premises: `10.30.0.0/24`

### 4.2 Routing Through the VPN

The on-premises gateway routes AWS-bound traffic through its `wg0` interface.

The AWS gateway routes traffic intended for the on-premises network back through WireGuard.

Both gateways have IPv4 forwarding enabled.

The firewall rules allow the required communication while blocking unnecessary traffic.

### 4.3 VPN Security

WireGuard uses public and private keys to authenticate the two VPN peers.

Private keys are stored on the gateways rather than in the GitHub repository.

The VPN provides encrypted communication between the environments, but access is still controlled by security groups and firewalls.

Connecting to the VPN does not automatically mean that every internal service is accessible.

### 4.4 VPN Testing

I verified the tunnel using:

```bash
sudo wg show
```

The output showed an active peer, a recent handshake and transferred data.

I also tested application connectivity using:

```bash
curl -I http://10.20.10.10:3000/login
```

The request returned HTTP 200 from Grafana.

This confirmed that the VPN was working for an actual application connection rather than only showing an active tunnel.

**Evidence:**

- `docs/evidence/network/03-wireguard-vpn.png`
- `docs/evidence/network/04-private-connectivity.png`

## 5. On-Premises Firewall

### 5.1 Firewall Design

I use nftables on the on-premises gateway to control incoming and forwarded traffic.

The input chain uses a default-drop policy.

This means incoming traffic is rejected unless a rule explicitly allows it.

The configuration includes rules for:

- Loopback traffic.
- Established and related connections.
- ICMP diagnostics.
- WireGuard communication.
- SSH management.
- Monitoring traffic.
- Internal DNS requests.
- Allowed forwarding between AWS and on-premises networks.

### 5.2 Firewall Logging

I added a logging rule for traffic that does not match the allowed connections.

The logs use the prefix:

`INNOVATECH_FW_DROP`

The rule also includes rate limiting to avoid generating an excessive number of log messages.

The resulting events are written to the Linux kernel log and collected by Grafana Alloy.

This is important because the firewall acts as both a security control and a source of security events for SOAR.

### 5.3 Firewall Testing

I generated TCP connection attempts from `cs2-onprem-linux` toward unauthorized ports on the gateway.

The test used four destination ports:

- 45678
- 45679
- 45680
- 45681

The gateway blocked the attempts and generated 12 relevant firewall log events.

These events were later used for the SOAR port-scanning detection test.

**Evidence:**

- `docs/evidence/security/16-firewall-blocked-traffic.png`
- `docs/evidence/monitoring/09-loki-firewall-query.png`

## 6. Internal DNS

### 6.1 DNS Design

I configured dnsmasq on the on-premises gateway to provide internal DNS resolution.

The service listens on:

`10.30.0.1:53`

The internal domain is:

`innovatech.internal`

The configured records are:

| Hostname | Private IP |
|---|---|
| monitoring.innovatech.internal | 10.20.10.10 |
| soar.innovatech.internal | 10.20.20.10 |
| gateway.innovatech.internal | 10.30.0.1 |

I chose dnsmasq because the infrastructure only needs a few private DNS records.

It is simpler than introducing Route 53 resolver infrastructure or running a full BIND9 DNS server.

### 6.2 DNS Configuration

The main configuration is stored in:

`/etc/dnsmasq.d/innovatech-internal.conf`

The configuration uses:

```ini
port=53
listen-address=10.30.0.1
bind-interfaces
no-dhcp-interface=enp0s8

local=/innovatech.internal/

address=/monitoring.innovatech.internal/10.20.10.10
address=/soar.innovatech.internal/10.20.20.10
address=/gateway.innovatech.internal/10.30.0.1
```

The DNS service listens only on the gateway's private network address.

### 6.3 DNS Firewall Rules

Initially, DNS queries from the Linux client timed out because the gateway's default-drop firewall blocked port 53.

I fixed this by adding rules to `/etc/nftables.conf` that permit TCP and UDP DNS requests from `10.30.0.0/24`.

I checked the configuration using:

```bash
sudo nft -c -f /etc/nftables.conf
```

After validation, I reloaded nftables and confirmed that the rules were present.

The original firewall logging rule remained active.

### 6.4 DNS Testing

I tested DNS from both the gateway and the Linux VM.

Example:

```bash
dig @10.30.0.1 monitoring.innovatech.internal +short
```

The result was:

```text
10.20.10.10
```

The other two hostnames also resolved correctly.

The tests confirmed that DNS queries work from the tested on-premises systems after the persistent firewall configuration was reloaded.

At this stage, the DNS service has been verified using explicit queries. It is not configured as the default resolver for every machine.

**Evidence:**

- `docs/evidence/network/05-private-dns-gateway.png`
- `docs/evidence/network/05-private-dns-linux.png`

## 7. Monitoring Architecture

### 7.1 Monitoring Overview

I deployed the monitoring platform on the AWS Monitoring EC2 instance.

It uses Docker Compose to run five services:

| Service | Purpose |
|---|---|
| Prometheus | Collects and stores metrics |
| Grafana | Displays dashboards |
| Loki | Stores and queries logs |
| Grafana Alloy | Collects and forwards telemetry |
| Alertmanager | Handles Prometheus alerts |

The monitoring stack is stored on the server under:

`/opt/innovatech/monitoring`

Each component runs in its own Docker container.

The monitoring architecture diagram is stored in:

`docs/diagrams/monitoring-architecture.png`

### 7.2 Metrics Collection

Prometheus collects infrastructure and application metrics.

The monitored systems include AWS and on-premises servers, as well as the SOAR application.

The collected information includes:

- CPU usage.
- Memory usage.
- Disk usage.
- System availability.
- Process metrics.
- SOAR application metrics.

Prometheus uses scrape targets to collect the metrics through HTTP endpoints.

The monitoring dashboard showed six healthy scrape targets during testing.

### 7.3 Centralized Logging

Loki is used for log storage.

Grafana Alloy collects system and security logs and forwards them to Loki.

The configured log sources include:

| Log Job | Source |
|---|---|
| aws-monitoring | AWS monitoring system logs |
| aws-monitoring-auth | Linux authentication logs |
| onprem-firewall | On-premises gateway firewall logs |

The on-premises firewall logs are transferred over the WireGuard VPN.

This allows AWS and on-premises logs to be investigated from the same Grafana interface.

### 7.4 LogQL Queries

Grafana Explore supports querying Loki using LogQL.

For example, I used:

```logql
{job="onprem-firewall"} |= "INNOVATECH_FW_DROP"
```

This filters firewall logs and shows blocked traffic events.

I also used:

```logql
{job=~"aws-monitoring|onprem-firewall"}
```

This returns system logs from AWS and firewall logs from the on-premises environment.

Both queries returned results during testing.

### 7.5 Grafana Dashboards

I created three main dashboards.

#### Infrastructure Overview

This dashboard shows:

- CPU usage.
- Memory usage.
- Disk usage.
- Server availability.
- Monitoring target status.

#### Security Logs Overview

This dashboard shows:

- Firewall events.
- Authentication events.
- System warnings.
- Log activity over time.
- Raw security logs.

#### SOAR Security Operations

This dashboard shows:

- SOAR availability.
- Processed alerts.
- Duplicate alerts.
- Failed processing.
- Incident counts.
- Response action counts.
- Processing latency.
- Process memory usage.

The dashboards are maintained as JSON configuration files and can be updated through the monitoring CI/CD workflow.

### 7.6 Alerting

Prometheus evaluates infrastructure alert rules.

The three configured rules are:

| Alert | Purpose |
|---|---|
| ServerDown | Detects unavailable monitoring targets |
| HighCPUUsage | Detects high CPU utilization |
| HighMemoryUsage | Detects high memory utilization |

The rules are loaded from:

`/etc/prometheus/alerts.yml`

Alertmanager is deployed to handle Prometheus alerts.

During testing, all three alert rules were visible in their normal state.

For security event processing, the SOAR log analyzer queries Loki directly and evaluates the collected firewall events.

This is the security detection path demonstrated during the project. It is separate from a fully tested Grafana-alert-to-SOAR webhook workflow.

### 7.7 Monitoring Limitations

All monitoring services currently run on one EC2 instance.

If that instance fails, centralized monitoring becomes unavailable until the server is restored.

The monitoring system also depends on correct log forwarding, network connectivity and sufficient disk space.

I haven't implemented a redundant monitoring cluster because it would increase complexity and costs beyond the needs of this project.

**Evidence:**

- `docs/evidence/monitoring/06-infrastructure-overview-A.png`
- `docs/evidence/monitoring/06-infrastructure-overview-B.png`
- `docs/evidence/monitoring/07-security-logs-overview-A.png`
- `docs/evidence/monitoring/09-loki-firewall-query.png`
- `docs/evidence/monitoring/10-multiple-log-sources.png`
- `docs/evidence/monitoring/11-monitoring-alerting.png`

## 8. SOAR Architecture

### 8.1 SOAR Overview

I developed a custom SOAR application using Python and Flask.

The application runs on the AWS SOAR EC2 instance at:

`10.20.20.10`

Gunicorn hosts the Flask application on port 8000, while systemd manages the application service.

The SOAR system is responsible for:

- Receiving security alerts.
- Validating incoming requests.
- Evaluating security rules.
- Detecting duplicate alerts.
- Executing predefined response actions.
- Recording incidents and actions.
- Providing monitoring metrics.

### 8.2 Application Structure

The application source code is maintained in the GitHub repository under:

`app/soar`

The main modules are:

| Module | Purpose |
|---|---|
| main.py | Flask API and request processing |
| rules.py | Rule evaluation |
| actions.py | Response actions |
| dedup.py | Duplicate alert detection |
| log_analyzer.py | Loki firewall log analysis |
| log_response.py | Processes findings through SOAR |

Separating the application into modules makes it easier to test and maintain the individual parts.

### 8.3 API Endpoints

The main API endpoints are:

| Endpoint | Method | Purpose |
|---|---|---|
| /alerts | POST | Receive security alerts |
| /health | GET | Check application availability |
| /metrics | GET | Export Prometheus metrics |

The `/alerts` endpoint requires authentication.

Incoming events are checked before the rule engine processes them.

### 8.4 Event Processing

The basic event-processing flow is:

1. A security event is received.
2. The incoming information is validated.
3. The event is checked against existing fingerprints.
4. The rule engine evaluates the event.
5. Matching response actions are selected.
6. The selected actions are executed.
7. The results are recorded.
8. Prometheus metrics are updated.

Duplicate detection is important because monitoring systems can generate repeated alerts for the same underlying event.

Without deduplication, the same incident could generate multiple unnecessary response actions.

### 8.5 Rule Evaluation

The rule engine uses the event information to determine which responses should be executed.

Rules can consider:

- Event type.
- Severity.
- Source.
- Event status.
- Other event attributes.

The rule evaluation logic is maintained in Python.

This means I can add or modify rules without replacing the entire SOAR application.

### 8.6 Response Actions

The implemented response actions include:

| Action | Purpose |
|---|---|
| record_incident | Record the security incident |
| notify_operator | Prepare an operator notification |
| simulate_ip_containment | Simulate blocking a suspicious IP |
| simulate_service_containment | Simulate restricting a service |

The real firewall is not automatically modified by the current SOAR demonstration.

I chose simulated containment to prevent an incorrect detection from accidentally blocking legitimate traffic or breaking the VPN.

### 8.7 SOAR Storage

The application uses SQLite and JSONL files.

SQLite stores alert fingerprints used for deduplication.

JSONL files store incident information, execution records and prepared notifications.

This avoids the need for a separate PostgreSQL database service.

The approach is suitable for the current single-instance demonstration, although it is not designed for a large distributed SOAR deployment.

### 8.8 SOAR Monitoring

The application exposes Prometheus-compatible metrics through:

`GET /metrics`

Prometheus collects these metrics from the monitoring server.

Grafana displays them in the SOAR Security Operations dashboard.

This makes it possible to monitor the SOAR system in addition to monitoring the infrastructure it protects.

### 8.9 SOAR Architecture Diagram

The SOAR architecture diagram is stored at:

`docs/diagrams/soar-architecture.png`

The final diagram should represent the implemented Flask application, Loki log analysis, SQLite/JSONL storage and simulated containment actions.

## 9. Firewall Log Analysis and Security Detection

### 9.1 Detection Approach

I wanted the SOAR demonstration to use actual infrastructure logs rather than only manually created JSON alerts.

For this reason, I developed a Python log analyzer that retrieves blocked connection events from Loki.

The analyzer extracts information from firewall logs and looks for suspicious patterns.

The main demonstrated detection is possible port scanning.

### 9.2 Port-Scanning Detection

The analyzer checks for repeated blocked TCP connection attempts targeting different destination ports.

It uses the information available in the firewall log messages, including:

- Source IP.
- Destination IP.
- Protocol.
- Destination port.
- Event time.

Multiple attempts to different ports can indicate scanning behavior.

The analyzer groups the relevant connection information and generates a security finding when the defined detection conditions are met.

### 9.3 Controlled Test

I generated 12 blocked TCP attempts from:

`10.30.0.10`

The destination was:

`10.30.0.1`

The traffic targeted four ports:

- 45678
- 45679
- 45680
- 45681

The gateway blocked the traffic and recorded the events.

Grafana Alloy forwarded the logs to Loki.

The log analyzer then examined the collected events.

The test results were:

| Measurement | Result |
|---|---|
| Raw logs examined | 24 |
| Relevant TCP events | 12 |
| Different destination ports | 4 |
| Findings | 1 |
| Event type | PossiblePortScan |
| Severity | Warning |

The generated finding was processed by the SOAR application.

The response included incident recording and notification preparation.

### 9.4 Deduplication Test

I executed the same analysis again using the same time window.

The second execution produced a duplicate result.

The SOAR application recognized the fingerprint of the previously processed finding.

This prevented the same response actions from being repeated unnecessarily.

### 9.5 Local Execution Inspector

To make the security processing easier to demonstrate, I created a local SOAR Execution Inspector.

It runs on Windows using:

```powershell
py -3.11 tools/soar_viewer.py
```

The viewer is accessed through:

`http://127.0.0.1:5050`

The viewer displays imported analysis results and the Python functions responsible for different processing steps.

It shows:

- Firewall log information.
- Detected patterns.
- Event classification.
- Rule evaluation.
- Response actions.
- Deduplication results.
- Python source code.

The viewer is a local demonstration tool, not another AWS service.

Some displayed log examples are shortened for readability, so they should not be treated as complete original firewall log exports.

**Evidence:**

- `docs/evidence/soar/12-port-scan-detection.png`
- `docs/evidence/soar/13-soar-code-inspector.png`
- `docs/evidence/soar/14-soar-rule-evaluation.png`
- `docs/evidence/soar/15-soar-alert-deduplication.png`
- `docs/evidence/security/16-firewall-blocked-traffic.png`

## 10. Infrastructure Automation

### 10.1 Terraform

Terraform is responsible for provisioning the AWS infrastructure.

It manages resources such as:

- VPC.
- Subnets.
- Route tables.
- Security groups.
- EC2 instances.
- IAM roles.
- Instance profiles.
- Network gateways.

The configuration is stored in GitHub so infrastructure changes can be reviewed and tracked.

Terraform state is stored in Amazon S3.

Before making infrastructure changes, Terraform can generate a plan showing which resources will be created, modified or destroyed.

### 10.2 Terraform Validation

I created a GitHub Actions workflow that validates Terraform configuration.

The workflow performs formatting and configuration checks.

It runs using my local Windows self-hosted runner.

This helps detect syntax and configuration errors before infrastructure changes are applied.

### 10.3 Ansible

Ansible is used for centralized operating-system updates.

The control node is:

`cs2-onprem-linux`

The managed systems are:

- `cs2-onprem-linux`
- `cs2-onprem-security`

The update playbook:

1. Verifies the target operating system.
2. Refreshes APT package information.
3. Installs available upgrades.
4. Checks whether a reboot is required.
5. Reports the execution results.

It uses `serial: 1` so the machines are processed individually.

The playbook does not automatically reboot the systems.

### 10.4 Ansible Testing

I successfully executed the update playbook against both managed machines.

The results were:

| Machine | OK | Changed | Failed | Unreachable |
|---|---:|---:|---:|---:|
| cs2-onprem-linux | 6 | 1 | 0 | 0 |
| cs2-onprem-security | 6 | 0 | 0 | 0 |

Both systems completed the execution without errors.

**Evidence:**

- `docs/evidence/updates/33-ansible-multi-server-update.png`

## 11. Automatic System Updates

### 11.1 unattended-upgrades

I configured Ubuntu unattended-upgrades on five Linux machines.

These are:

- AWS Monitoring.
- AWS SOAR.
- On-premises Gateway.
- On-premises Linux.
- On-premises Security.

The service automatically checks for available package updates and installs updates based on its configuration.

This reduces the need to manually perform routine package maintenance.

### 11.2 Verification

I inspected the unattended-upgrades configuration and execution logs on the servers.

The evidence shows successful package installations on the AWS Monitoring, AWS SOAR, on-premises Linux and on-premises Security machines.

The on-premises Gateway also performed automatic update checks, although the captured logs did not show package installation during that check.

### 11.3 Difference Between Ansible and unattended-upgrades

These tools solve related but different problems.

Ansible provides centralized management by allowing an administrator to execute updates on multiple machines from one control node.

unattended-upgrades runs independently on each machine according to its configured update schedule.

The Ansible playbook currently covers two machines, while unattended-upgrades is enabled on all five.

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

## 12. CI/CD Design

### 12.1 GitHub Actions

I use GitHub Actions for automated testing and deployment.

The workflows run on a Windows self-hosted runner.

The repository contains three main pipelines:

| Pipeline | Purpose |
|---|---|
| Infrastructure Checks | Terraform validation |
| SOAR CI/CD | Python tests and SOAR deployment |
| Monitoring CI/CD | Grafana dashboard validation and deployment |

### 12.2 SOAR CI/CD

The SOAR pipeline validates the Python application before deployment.

After successful tests, the workflow prepares a deployment package.

The package is uploaded to Amazon S3.

AWS Systems Manager is then used to execute the deployment commands on the private SOAR EC2 instance.

This avoids needing public SSH access to deploy application changes.

The deployment updates the application files and restarts the SOAR service.

### 12.3 Monitoring CI/CD

The monitoring pipeline validates Grafana dashboard JSON files.

After successful validation, the workflow deploys the updated dashboards to the AWS Monitoring instance.

This allows dashboard changes to be maintained through Git instead of depending only on manual changes in Grafana.

### 12.4 Pipeline Failure Protection

I tested the monitoring pipeline by introducing an invalid dashboard JSON file on a separate branch.

The validation job failed.

Because the validation failed, the deployment job was skipped.

This demonstrated that the pipeline prevents invalid dashboard configuration from being deployed through the normal workflow.

### 12.5 CI/CD Limitations

The pipelines depend on the local self-hosted runner.

The runner must be online for the workflows to execute.

AWS authentication also needs to be available to the deployment workflow.

For a production environment, the runner and deployment authentication would need dedicated infrastructure and a more permanent credential-management approach.

**Evidence:**

- `docs/evidence/cicd/17-soar-cicd-success.png`
- `docs/evidence/cicd/18-monitoring-cicd-success.png`
- `docs/evidence/cicd/19-terraform-validation.png`
- `docs/evidence/cicd/20-pipeline-failure-protection.png`

## 13. Security Design

### 13.1 Private Networking

The monitoring and SOAR servers are placed in private AWS subnets.

Only the AWS gateway requires a public IP address for VPN connectivity.

The security groups restrict application access to specific network sources.

### 13.2 Administrative Access

AWS Systems Manager Session Manager is used to access the EC2 instances.

This avoids exposing SSH access directly to the public internet.

### 13.3 Firewall Policies

The on-premises gateway uses nftables with a default-drop input policy.

The rules permit the required VPN, SSH, monitoring and DNS traffic.

Other incoming traffic is blocked and can be logged.

### 13.4 SOAR Authentication

The SOAR API requires authentication for incoming alerts.

This prevents arbitrary unauthenticated requests from being processed through the normal alert endpoint.

### 13.5 Controlled Response Actions

The SOAR application includes validation and simulated containment functions.

These were designed to avoid accidentally blocking management addresses or interfering with critical network services.

The current demonstration does not perform live firewall containment.

### 13.6 Credentials

WireGuard private keys and AWS credentials are not intended to be stored in Git.

Deployment credentials and application secrets must be handled separately from public source code and documentation.

## 14. Resilience and Recovery

### 14.1 Design Approach

The environment is designed to support recovery from individual service failures.

It is not a fully redundant multi-region or multi-node high-availability platform.

The main recovery approach uses service management, Infrastructure as Code and documented operating procedures.

### 14.2 Monitoring Failure Test

I tested recovery by stopping the Grafana container.

The other monitoring containers remained running.

I then manually restarted Grafana and checked its health endpoint.

The endpoint returned HTTP 200, and the application database status was healthy.

This confirms that the affected service could be restored without restarting the entire monitoring stack.

### 14.3 Recovery Limitations

The test demonstrates manual recovery, not automatic failover.

I haven't measured an exact recovery time for the test.

I also haven't demonstrated a full backup restoration of the monitoring data or SOAR records.

These are important differences between a working development environment and a production-ready infrastructure.

### 14.4 Network Failure Risks

The AWS gateway and on-premises gateway are both important network components.

If either gateway becomes unavailable, communication between the two environments can stop.

The monitoring system can detect some unavailable services through Prometheus targets, but the VPN itself doesn't have automatic failover in the current design.

**Evidence:**

- `docs/evidence/resilience/21-monitoring-health-before-test.png`
- `docs/evidence/resilience/22-monitoring-component-failure.png`
- `docs/evidence/resilience/23-monitoring-component-recovery.png`

## 15. Infrastructure Costs

### 15.1 AWS Resources

The infrastructure uses three AWS EC2 instances.

| Resource | Instance Type |
|---|---|
| Monitoring | t3.medium |
| SOAR | t3.small |
| Gateway | t3.micro |

The instances use gp3 EBS volumes.

I avoided AWS-managed monitoring and NAT services because the project can demonstrate the required functionality using self-hosted tools.

### 15.2 Cost Reduction

To limit AWS spending, I:

- Use relatively small EC2 instances.
- Run monitoring services on one monitoring server.
- Use an EC2 gateway instead of a managed NAT Gateway.
- Use WireGuard instead of a managed Site-to-Site VPN.
- Use open-source monitoring and automation tools.
- Stop the EC2 instances when I'm not working on the infrastructure.

Stopping the instances reduces compute charges, but EBS storage and public IPv4 allocations can still generate costs.

### 15.3 Trade-Offs

These decisions reduce operating costs but also introduce limitations.

For example, the monitoring server and gateway are single points of failure.

A production environment would need additional redundancy, backup automation and stronger recovery procedures.

## 16. Testing Overview

I tested the infrastructure at different levels.

### 16.1 Network Tests

- AWS EC2 health checks.
- Security group inspection.
- WireGuard tunnel status.
- Private Grafana connectivity.
- Internal DNS resolution.
- Firewall blocking and logging.

### 16.2 Monitoring Tests

- Prometheus scrape targets.
- Grafana dashboards.
- Loki firewall log queries.
- Multiple log sources.
- Prometheus alert rules.

### 16.3 SOAR Tests

- Firewall log analysis.
- Port-scanning detection.
- Alert processing.
- Rule evaluation.
- Incident recording.
- Notification preparation.
- Duplicate detection.
- SOAR monitoring metrics.

### 16.4 Automation Tests

- Terraform validation.
- SOAR CI/CD deployment.
- Monitoring CI/CD deployment.
- Invalid dashboard rejection.
- Ansible multi-node updates.
- unattended-upgrades execution.

### 16.5 Recovery Tests

- Monitoring service health before failure.
- Grafana container stopped.
- Remaining monitoring services kept running.
- Grafana manually restarted.
- Grafana health endpoint checked after recovery.

## 17. Current Limitations

The infrastructure is working for the main project demonstrations, but there are still some limitations.

| Area | Limitation |
|---|---|
| Monitoring | Runs on one EC2 instance without a redundant server |
| VPN | No automatic gateway failover |
| DNS | Explicit DNS queries tested, but not default resolution everywhere |
| SOAR notifications | Notifications prepared locally rather than delivered externally |
| SOAR containment | Simulated rather than applied to the real firewall |
| SOAR storage | SQLite and JSONL instead of a distributed database |
| Backups | Complete backup and restoration tests not yet demonstrated |
| Recovery | Manual Grafana recovery demonstrated; automatic recovery not verified |
| Updates | Ansible centralizes updates for two machines, not the entire environment |
| CI/CD | Depends on the availability of the Windows self-hosted runner |
| Performance | No large-scale load or capacity benchmark |

## 18. Current Implementation

The project currently has a working hybrid infrastructure connecting AWS and VirtualBox through WireGuard.

The current design meets the main goals of the development environment, while the remaining recovery, backup and production-readiness limitations are documented separately.