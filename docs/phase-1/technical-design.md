
# Technical Design
## Innovatech Solutions — Hybrid Cloud Infrastructure

**Project:** Hybrid Cloud Infrastructure and Security Automation
**Client:** Innovatech Solutions
**Document Version:** 1.0
**Project Phase:** Phase 1 — Analysis and Design

---

## 1. Introduction

### 1.1 Purpose

This document describes the technical architecture of the hybrid cloud infrastructure implemented for Innovatech Solutions.

The design covers cloud hosting, network segmentation, hybrid connectivity, centralized monitoring, security automation, persistent storage and infrastructure management.

The architecture is designed to meet the functional and non-functional requirements defined in the Requirements Analysis.

### 1.2 Design Objectives

The infrastructure is designed to:

- Provide secure communication between AWS and on-premises systems.
- Separate monitoring, security automation and monitored workloads.
- Collect and visualize infrastructure metrics and security logs.
- Process security alerts through an automated SOAR application.
- Store incident records and response results persistently.
- Automate infrastructure provisioning and system configuration.
- Support centralized updates across multiple Linux machines.
- Allow recovery from isolated infrastructure and application failures.
- Support testing and deployment through version-controlled automation.

---

## 2. Infrastructure Architecture

### 2.1 Architecture Overview

The infrastructure consists of two environments:

1. AWS cloud infrastructure.
2. Simulated on-premises infrastructure.

AWS provides the hosting environment for the centralized monitoring and SOAR services.

The on-premises environment contains Linux systems responsible for generating operational metrics and security events.

The environments communicate through an encrypted WireGuard VPN.

Application services are deployed through Docker Compose, while Terraform and Ansible manage infrastructure provisioning and system configuration.

### 2.2 AWS Infrastructure

The AWS infrastructure will be deployed in the eu-central-1 (Frankfurt) region.

A dedicated VPC will contain separate network segments for monitoring and SOAR.

Two EC2 instances will provide the primary application hosting environment.

#### Monitoring Server

**Resource Name:** innovatech-monitoring

**Operating System:** Ubuntu Server LTS

**Application Platform:** Docker Compose

**Services:**

- Grafana
- Prometheus
- Grafana Loki
- Prometheus Alertmanager
- Grafana Alloy, where required

The monitoring server will collect and store telemetry received from cloud and on-premises systems.

Grafana will provide dashboards for infrastructure metrics, security events and SOAR activity.

Prometheus will store time-series metrics, while Loki will store collected logs.

Alertmanager will route Prometheus alerts to configured receivers.

#### SOAR Server

**Resource Name:** innovatech-soar

**Operating System:** Ubuntu Server LTS

**Application Platform:** Docker Compose

**Services:**

- Python/FastAPI SOAR application
- Event collector and rule engine
- Automated response modules
- PostgreSQL database

The SOAR server will receive security events from the monitoring environment and execute predefined automated responses.

PostgreSQL will store incident records, rule matches and execution results.

The SOAR application will expose health and metrics endpoints for Prometheus.

The database will not be accessible from the public internet.

### 2.3 On-Premises Infrastructure

The simulated on-premises environment will contain two Linux virtual machines.

#### Linux Server

**Resource Name:** innovatech-linux

Responsibilities:

- Generate Linux authentication events.
- Provide system logs.
- Expose infrastructure metrics.
- Run Grafana Alloy.
- Generate simulated suspicious activity.

#### Security Server

**Resource Name:** innovatech-security

Responsibilities:

- Generate firewall and network security logs.
- Simulate suspicious network connections.
- Provide events for security detection rules.
- Run Grafana Alloy.
- Support controlled automated firewall responses.

These systems will operate independently from the cloud-hosted SOAR platform.

### 2.4 Infrastructure Management

Terraform will define and provision AWS resources.

Ansible will configure the Linux servers, install required software and manage operating system updates.

GitHub Actions will execute automated testing and deployment workflows through a self-hosted runner.

The project will maintain separate configurations for infrastructure provisioning, system management and application deployment.

---

## 3. Network Architecture

### 3.1 AWS VPC

A dedicated VPC will be created for the infrastructure.

**VPC Name:** innovatech-cs2-vpc

**VPC CIDR:** 10.20.0.0/16

The VPC will contain two application subnets and a dedicated gateway subnet.

### 3.2 Subnet Design

| Subnet | CIDR | Purpose |
|---|---|---|
| Monitoring Subnet | 10.20.10.0/24 | Monitoring EC2 instance |
| SOAR Subnet | 10.20.20.0/24 | SOAR EC2 instance |
| Gateway Subnet | 10.20.30.0/24 | VPN and controlled network access |

The monitoring and SOAR application instances will use private IP addresses.

A VPN gateway will provide controlled connectivity to the on-premises environment.

Administrative access will use a documented restricted management path.

### 3.3 On-Premises Network

The simulated on-premises environment will use a separate private address range.

**Network CIDR:** 10.30.0.0/24

Initial addressing:

| Resource | IP Address |
|---|---|
| Local Gateway | 10.30.0.1 |
| Linux Server | 10.30.0.10 |
| Security Server | 10.30.0.20 |

These addresses will be assigned through the local virtual network configuration.

The local network will not overlap with the AWS VPC.

### 3.4 Hybrid Connectivity

WireGuard will establish encrypted communication between AWS and the on-premises network.

The gateway will route permitted traffic between:

- AWS VPC: 10.20.0.0/16
- On-premises network: 10.30.0.0/24

The VPN configuration will use authenticated peers and restricted AllowedIPs settings.

AWS route tables and host firewall rules will control the permitted network traffic.

The VPN will not provide unrestricted access to every cloud service.

### 3.5 Firewall and Security Groups

AWS Security Groups will restrict traffic between the different infrastructure components.

Planned communication:

| Source | Destination | Service | Port |
|---|---|---|---|
| On-premises systems | Loki | Log ingestion | TCP 3100 |
| On-premises systems | Monitoring server | Metrics collection / forwarding | To be defined |
| Monitoring server | SOAR API | Security event forwarding | TCP 8000 |
| Monitoring server | SOAR metrics | Prometheus scraping | TCP 8000 |
| SOAR application | PostgreSQL | Database access | TCP 5432 |
| Authorized administrator | Grafana | Web dashboard | TCP 3000 |
| VPN peers | WireGuard gateway | Encrypted tunnel | UDP 51820 |

These are application service ports, not public ingress permissions.

Prometheus, Loki, PostgreSQL and the SOAR API will remain on private network interfaces or internal container networks.

PostgreSQL access will be restricted to the SOAR application. If both services share a Docker network, database traffic will remain inside that network rather than crossing the AWS subnet.

The exact firewall implementation will be validated during deployment.

### 3.6 Private DNS

Internal service names will be used instead of hardcoded IP addresses.

The internal DNS namespace will be:

**innovatech.internal**

Planned records:

| Service | DNS Name |
|---|---|
| Monitoring | monitoring.innovatech.internal |
| SOAR | soar.innovatech.internal |
| Gateway | gateway.innovatech.internal |

AWS systems will resolve these records through Route 53 Private DNS.

On-premises clients will use a DNS forwarding service over the VPN.

The forwarding service must be able to resolve the internal namespace through an authorized AWS-side resolver.

The final DNS forwarding method will be selected during implementation after evaluating resource requirements and operating costs.

---

## 4. Network Security

### 4.1 Network Isolation

The infrastructure will maintain logical separation between the monitoring environment, SOAR environment and on-premises systems.

The following restrictions will apply:

- PostgreSQL will not have public network access.
- Monitoring backends will accept connections only from authorized sources.
- SOAR API access will be restricted to trusted monitoring and management components.
- On-premises systems will not receive unrestricted access to AWS resources.
- Only the VPN gateway will accept the WireGuard connection.
- Administrative connectivity will be restricted and authenticated.

### 4.2 Credentials and Secrets

The infrastructure will not store sensitive credentials in the Git repository.

Sensitive configuration includes:

- Database passwords.
- VPN private keys.
- API authentication credentials.
- AWS access credentials.
- CI/CD deployment credentials.

Terraform state and automation credentials will be protected from unauthorized access.

Application services will retrieve credentials through controlled environment configuration or an appropriate secret-management mechanism.

### 4.3 Security Validation

The network security configuration will be tested through:

- Authorized connection tests.
- Unauthorized connection attempts.
- Private DNS resolution tests.
- VPN connectivity tests.
- Database exposure verification.
- Security Group and firewall rule inspection.

The results will be recorded in the final testing documentation.

## 5. Monitoring Architecture

### 5.1 Overview

The monitoring infrastructure will provide centralized visibility into the AWS environment, on-premises Linux systems and SOAR application.

The monitoring stack consists of:

- Prometheus for collecting and storing metrics.
- Grafana for dashboards and visualization.
- Grafana Loki for centralized log storage.
- Grafana Alloy for collecting and forwarding telemetry.
- Prometheus Alertmanager for routing metric-based alerts.
- Grafana Alerting for detecting security events in Loki logs.

The services will run in Docker containers on the monitoring EC2 instance.

System telemetry will be transmitted through private network connections.

### 5.2 Metrics Collection

Prometheus will collect infrastructure and application metrics using HTTP endpoints.

Linux systems will expose system metrics through Grafana Alloy's Prometheus-compatible integrations.

The SOAR application will expose a dedicated `/metrics` endpoint.

The following information will be collected:

| Source | Metrics |
|---|---|
| Monitoring server | CPU, memory, disk usage, network activity |
| SOAR server | CPU, memory, disk usage, network activity |
| On-premises Linux server | CPU, memory, disk usage, network activity |
| Security server | CPU, memory, disk usage, network activity |
| SOAR application | Events processed, successful actions, failed actions, processing duration |
| Prometheus | Scrape status and collection performance |
| Loki | Log ingestion and processing metrics |
| PostgreSQL | Database availability and connection health |

Prometheus will collect metrics at a default interval of 15 seconds.

The collection interval can be adjusted for specific targets if required.

### 5.3 Log Collection

Grafana Alloy will collect logs from the monitored Linux systems.

The monitoring system will integrate at least two distinct log sources.

**Source 1 — Linux Authentication Logs**

Authentication events will be collected from the Linux system journal or authentication log files.

Events include:

- Failed SSH authentication.
- Successful SSH authentication.
- Authentication failures.
- Suspicious login activity.

**Source 2 — Firewall and Network Security Logs**

Firewall events will be collected from the security server.

Events include:

- Blocked connections.
- Repeated connection attempts.
- Suspicious source addresses.
- Port scanning activity.

Grafana Alloy will forward logs to Loki through the private network.

Loki will organize logs using labels identifying the source, host, service and environment.

### 5.4 Log Labels

The logging system will use consistent labels.

| Label | Purpose |
|---|---|
| host | Identifies the machine generating the log |
| job | Identifies the log collection job |
| service | Identifies the service generating the event |
| environment | Identifies the infrastructure environment |
| log_source | Distinguishes authentication, firewall and application logs |

Labels will use controlled values to avoid excessive cardinality.

Unique incident identifiers, timestamps and source IP addresses will remain in log content rather than being used as high-cardinality labels.

### 5.5 Grafana Dashboards

Three main dashboards will be created.

#### Infrastructure Overview

The dashboard will display:

- CPU utilization.
- Memory utilization.
- Disk usage.
- Network traffic.
- Machine availability.
- Monitoring target status.

#### Security Monitoring

The dashboard will display:

- Failed authentication attempts.
- Firewall events.
- Security alerts.
- Events grouped by monitored system.
- Event severity and detection trends.

#### SOAR Operations

The dashboard will display:

- Total security events processed.
- Successful automated responses.
- Failed automated responses.
- Processing duration.
- Application availability.
- Event processing rate.

Dashboards and data source configurations will be maintained as version-controlled files where supported.

### 5.6 Alerting

Two alerting paths will be used.

**Infrastructure and Application Metrics**

Prometheus will evaluate metric-based alerting rules.

Examples include:

- High CPU utilization.
- Low available disk space.
- Unavailable monitoring targets.
- SOAR application unavailability.
- Increased SOAR processing errors.

Triggered alerts will be routed through Alertmanager.

**Security Log Events**

Grafana-managed alert rules will query Loki using LogQL.

Examples include:

- Multiple failed SSH authentication attempts.
- Unusual firewall connection patterns.
- High frequency of blocked connections.

Grafana will evaluate matching log counts or rates against configured thresholds.

Security alerts will be delivered to the SOAR application through an authenticated HTTP webhook.

Only alerts matching the selected security rules will trigger automated security responses.

### 5.7 Alert Processing

The alert processing workflow will follow these steps:

1. A monitored system generates a metric or log event.
2. Prometheus or Loki receives the telemetry.
3. The appropriate alerting component evaluates a configured rule.
4. An alert is generated when the rule condition is satisfied.
5. The alert is forwarded to the SOAR API.
6. The SOAR application validates and processes the event.
7. The selected automated response is executed.
8. The outcome is stored and exported as monitoring metrics.

The SOAR application will normalize alerts from Grafana and Alertmanager into a common internal event structure.

Duplicate alerts will be handled using an event fingerprint and a defined deduplication period.

### 5.8 Monitoring Data Retention

The initial retention periods will be:

| Data | Retention |
|---|---|
| Prometheus metrics | 15 days |
| Loki logs | 14 days |
| PostgreSQL incidents | 90 days |
| Operational backups | 7 days |

Retention values are initial project targets and may be adjusted after storage utilization is measured.

Log retention will be enforced through Loki's supported retention configuration.

Prometheus retention will be configured through its storage settings.

PostgreSQL incident records will be maintained through a scheduled retention process.

---

## 6. SOAR Architecture

### 6.1 Overview

The Security Orchestration, Automation and Response system will process alerts generated by the monitoring environment and execute predefined actions.

The SOAR application will be developed using Python and FastAPI.

It will run in a Docker container on the SOAR EC2 instance.

The application will consist of the following components:

- Event receiver.
- Event validation and normalization.
- Rule engine.
- Response execution modules.
- Incident storage.
- Health and performance monitoring.

### 6.2 Event Receiver

The event receiver will accept security alerts through an HTTP API.

The primary endpoint will be:

`POST /api/v1/events`

The endpoint will receive alerts from Grafana and Alertmanager through the private network.

Incoming requests will require authentication.

The receiver will validate the incoming event structure and reject invalid requests.

The following information will be extracted where available:

- Event identifier.
- Event type.
- Severity.
- Source system.
- Source IP address.
- Event timestamp.
- Event description.
- Alert status.
- Associated metadata.

Source IP addresses and event metadata will be treated as untrusted input.

### 6.3 Internal Event Format

Incoming alerts will be converted into a common internal structure.

Example:

```json
{
  "event_id": "evt-0001",
  "event_type": "ssh_bruteforce",
  "severity": "high",
  "source": "innovatech-linux",
  "source_ip": "10.30.0.50",
  "timestamp": "2026-10-27T10:00:00Z",
  "description": "Repeated failed SSH authentication attempts"
}
```

The example represents a simulated security event.

Event identifiers will be used for incident tracking and duplicate detection.

### 6.4 Rule Engine

The rule engine will evaluate normalized security events against predefined rules.

Rules will be selected using:

- Event type.
- Severity.
- Source.
- Event attributes.
- Defined response conditions.

Initial rules will be stored as version-controlled YAML configuration.

Example rule definitions:

| Rule | Condition | Response |
|---|---|---|
| SSH-001 | Repeated failed SSH login alert | Create incident and send notification |
| FW-001 | Confirmed simulated malicious source | Create incident and request firewall block |
| SYS-001 | Suspicious process alert | Create incident and send notification |

The rule engine will support adding new detection and response rules without changing the event receiver.

Rules will be validated before they are loaded.

### 6.5 Automated Response Actions

The SOAR system will implement three initial response capabilities.

#### Action 1 — Incident Recording

When an event matches a rule, the SOAR application will create or update an incident in PostgreSQL.

The record will include:

- Event details.
- Matched rule.
- Incident status.
- Response actions.
- Execution results.
- Timestamps.

#### Action 2 — Security Notification

The SOAR application will send a notification containing relevant information about the detected incident.

The notification will include:

- Incident identifier.
- Event type.
- Severity.
- Source system.
- Detection time.
- Response status.

The notification destination will be configured through environment settings.

#### Action 3 — Simulated IP Blocking

The SOAR application will support blocking a simulated malicious IP address on the security server.

The response will use a restricted management API or controlled automation interface.

Before executing the block action, the system will:

1. Validate the source IP address.
2. Confirm that the event matches an authorized response rule.
3. Check that the IP belongs to an approved demonstration network.
4. Check that the IP is not on the protected address list.
5. Execute the firewall operation.
6. Record the result.

Administrative addresses, VPN endpoints and infrastructure management addresses will be excluded from automatic blocking.

Automatic firewall changes will be restricted to the simulated security environment.

### 6.6 Response Execution

Response actions will return a structured execution result.

Each result will contain:

- Action identifier.
- Incident identifier.
- Action type.
- Execution status.
- Start time.
- Completion time.
- Error details where applicable.

The SOAR system will distinguish successful, failed and skipped actions.

Failed actions will be recorded and included in monitoring metrics.

Actions will support idempotent behavior where practical to prevent repeated alerts from creating unintended duplicate effects.

### 6.7 SOAR API Endpoints

The application will expose the following endpoints:

| Endpoint | Method | Purpose |
|---|---|---|
| `/health` | GET | Application health check |
| `/metrics` | GET | Prometheus metrics |
| `/api/v1/events` | POST | Receive security events |
| `/api/v1/incidents` | GET | Retrieve incident records |
| `/api/v1/incidents/{id}` | GET | Retrieve an incident |
| `/api/v1/rules` | GET | List configured rules |

Administrative endpoints will require authentication.

The metrics endpoint will be restricted to authorized Prometheus collectors.

### 6.8 SOAR Monitoring

The application will expose custom Prometheus metrics.

Planned metrics include:

- `soar_events_processed_total`
- `soar_actions_total`
- `soar_action_failures_total`
- `soar_event_processing_duration_seconds`
- `soar_active_incidents`

Metric labels will identify event types, action types and execution status without including individual incident identifiers.

Prometheus will scrape the metrics endpoint.

Grafana will visualize the collected metrics in the SOAR Operations dashboard.

---

## 7. Database Architecture

### 7.1 PostgreSQL

PostgreSQL will provide persistent storage for security incidents and automated response execution records.

The database will run in a Docker container on the SOAR EC2 instance.

A dedicated persistent volume will store PostgreSQL data.

The database port will not be published to the public network.

Only authorized application containers and administrative maintenance processes will have access to the database.

### 7.2 Data Model

The database will contain the following primary tables.

**incidents**

Stores detected security incidents.

Fields:

- id
- event_id
- event_type
- severity
- source
- source_ip
- description
- status
- created_at
- updated_at

**rules**

Stores information about active and configured security rules.

Fields:

- id
- rule_name
- description
- severity
- enabled
- created_at

**action_executions**

Stores automated response execution records.

Fields:

- id
- incident_id
- rule_id
- action_type
- execution_status
- started_at
- completed_at
- error_message

The final database schema will define primary keys, foreign keys, indexes and field constraints.

### 7.3 Persistence

PostgreSQL will use a Docker volume backed by persistent EC2 storage.

Database data will remain available after container restarts and recreation.

Persistent storage will not be deleted during ordinary application deployments.

### 7.4 Database Backups

Database backups will be created using PostgreSQL backup utilities.

Backups will be stored separately from the live database volume.

The recovery process will be tested by restoring a backup into a clean database environment.

The initial backup retention target is seven days.

Backup execution and restoration results will be recorded.

---

## 8. Infrastructure Automation

### 8.1 Terraform

Terraform will provision and manage the AWS infrastructure.

Resources will include:

- VPC.
- Subnets.
- Route tables.
- Internet gateway where required.
- Security Groups.
- EC2 instances.
- Storage volumes.
- Private DNS records.
- Supporting IAM resources.

Terraform configuration will be divided into logical files or modules.

Infrastructure state will be stored remotely with access restrictions and locking.

Infrastructure changes will be reviewed through Terraform plans before deployment.

### 8.2 Ansible

Ansible will configure Linux systems after infrastructure provisioning.

Playbooks will manage:

- Operating system packages.
- Docker installation.
- Grafana Alloy installation.
- WireGuard configuration.
- Host firewall configuration.
- Application directories.
- Service deployment.
- Software updates.
- Service health verification.

Ansible inventories will distinguish AWS and on-premises hosts.

### 8.3 Docker Compose

Docker Compose will define application services.

The monitoring configuration will contain:

- Grafana.
- Prometheus.
- Loki.
- Alertmanager.

The SOAR configuration will contain:

- FastAPI application.
- PostgreSQL.

Services will use internal Docker networks and persistent volumes where required.

Container versions will be pinned to tested versions rather than using unrestricted latest tags.

### 8.4 GitHub Actions

GitHub Actions will manage application and infrastructure validation.

The CI/CD process will include:

1. Source code checkout.
2. Python dependency installation.
3. Python unit tests.
4. Terraform formatting and validation.
5. Terraform plan generation for infrastructure changes.
6. Container image build.
7. Deployment authorization.
8. SOAR application deployment.
9. Post-deployment health checks.

Deployment workflows will run on a configured self-hosted runner.

Credentials will be stored outside the Git repository and made available only to authorized workflows.

Production-impacting infrastructure changes will require an approval step or an explicitly authorized deployment workflow.

---

## 9. Automated Updates

### 9.1 Operating System Updates

Ansible will perform centralized operating system updates across multiple Linux systems.

The update process will:

1. Connect to the selected managed hosts.
2. Refresh package information.
3. Install approved updates.
4. Detect whether a reboot is required.
5. Reboot systems when necessary.
6. Verify that the systems become reachable.
7. Check application and service health.
8. Record the execution results.

Updates will be performed in controlled batches to reduce simultaneous service interruption.

### 9.2 Application Updates

Monitoring and SOAR application containers will use version-controlled images and configuration.

Application updates will follow this process:

1. Update the application or image version.
2. Execute automated tests.
3. Build or obtain the required container image.
4. Deploy the updated service.
5. Verify health checks and monitoring.
6. Restore the previous version if validation fails.

The deployment process will preserve persistent database and monitoring data volumes.

### 9.3 Update Verification

Evidence will include:

- Ansible execution results.
- Package versions before and after updates.
- Application container versions.
- Service availability checks.
- Failed update reports.
- Recovery results where applicable.

---

## 10. Resilience and Recovery

### 10.1 Design-for-Failure

The infrastructure will support recovery from isolated application and infrastructure failures.

The initial deployment will prioritize controlled recovery rather than fully redundant multi-node application clusters.

Critical application data will use persistent storage, and service recovery procedures will be documented.

### 10.2 Container Recovery

Application containers will use restart policies.

A container crash will trigger an automatic restart where possible.

Health checks will detect applications that remain unresponsive.

### 10.3 EC2 Recovery

EC2 instances will be provisioned through Terraform.

Application configuration will be managed through Ansible and Docker Compose.

If an instance must be replaced, the system configuration can be recreated from version-controlled infrastructure and configuration definitions.

Application data will be restored from the available persistent storage or backup.

### 10.4 Database Recovery

Database recovery will use a verified PostgreSQL backup.

The restoration procedure will:

1. Stop dependent application services.
2. Prepare the replacement database.
3. Restore the selected backup.
4. Verify database integrity.
5. Restart the SOAR application.
6. Verify incident access and event processing.

### 10.5 Hybrid Connectivity Failure

If the VPN becomes unavailable:

- The monitoring system will detect unavailable remote targets.
- Existing monitoring data will remain accessible.
- Cloud-hosted SOAR services will continue operating.
- Events requiring access to the on-premises environment may fail or be delayed.
- Failed response attempts will be recorded.

Recovery will involve restoring the VPN connection and verifying routing, DNS and telemetry collection.

### 10.6 Recovery Objectives

The following recovery targets will be used for initial testing.

| Component | Recovery Objective |
|---|---|
| Application container | Within 2 minutes |
| SOAR application restart | Within 2 minutes |
| Monitoring server restoration | Within 30 minutes |
| SOAR server restoration | Within 30 minutes |
| PostgreSQL backup restoration | Within 30 minutes |
| VPN reconnection | Within 10 minutes |

These are engineering targets, not guaranteed service levels.

They will be validated and adjusted using measured results during resilience testing.

### 10.7 Failure Testing

Failure tests will include:

- Monitoring container termination.
- SOAR application termination.
- PostgreSQL container restart.
- EC2 restart.
- VPN connection interruption.
- Database backup restoration.
- Loss and restoration of telemetry collection.

Test results will include the observed impact, recovery process, recovery time and any data loss.

---

## 11. Infrastructure Capacity

### 11.1 Compute Resources

The deployment will begin with two application EC2 instances and a separate VPN gateway where required by the finalized network topology.

| Resource | Initial Resource Target | Workload |
|---|---|---|
| Monitoring EC2 | 2 vCPU, 4–8 GiB RAM | Grafana, Prometheus, Loki and Alertmanager |
| SOAR EC2 | 2 vCPU, 4 GiB RAM | FastAPI and PostgreSQL |
| VPN gateway | 2 vCPU, 1–2 GiB RAM | WireGuard and network forwarding |

These values are planning estimates rather than measured minimum requirements.

The exact instance types will be selected after reviewing available AWS options and expected costs.

### 11.2 Storage

The monitoring server will require persistent storage for:

- Prometheus time-series data.
- Loki log data.
- Grafana configuration and internal application data.

The SOAR server will require persistent storage for:

- PostgreSQL database files.
- SOAR application configuration.
- Incident processing records.

Storage utilization will be monitored through Prometheus.

Retention policies will limit unnecessary data growth.

### 11.3 Capacity Validation

The infrastructure will be tested using simulated security events and monitoring workloads.

Tests will measure:

- CPU utilization.
- Memory utilization.
- Disk usage.
- Metrics ingestion.
- Log processing.
- SOAR processing duration.
- Automated response performance.

Instance sizing and retention settings will be adjusted if the baseline configuration cannot reliably support the expected workload.

---

## 12. Deployment and Handoff

### 12.1 Deployment Process

The infrastructure deployment will follow this order:

1. Provision AWS resources through Terraform.
2. Configure Linux instances using Ansible.
3. Deploy the on-premises virtual machines.
4. Establish WireGuard VPN connectivity.
5. Configure routing, firewall rules and DNS.
6. Deploy the monitoring stack.
7. Configure telemetry collection.
8. Deploy PostgreSQL and the SOAR application.
9. Configure alert forwarding.
10. Execute end-to-end integration tests.

### 12.2 Portable Demonstration

A separate Docker Compose deployment will be provided for application-level evaluation.

The demonstration will contain the monitoring services, SOAR application, PostgreSQL and simulated event sources.

The demonstration environment will allow security event processing to be tested without access to the original on-premises machines.

It will not be considered sufficient evidence of real hybrid VPN connectivity, cloud segmentation or AWS networking.

### 12.3 Operational Documentation

The final operations manual will include:

- Required software and dependencies.
- Infrastructure deployment commands.
- Configuration instructions.
- Monitoring access instructions.
- Security event simulation.
- SOAR operation and troubleshooting.
- Automated updates.
- Backup and recovery.
- Portable demonstration setup.
- Infrastructure teardown.

---

## 13. Technical Design Summary

The infrastructure combines AWS-hosted monitoring and security automation with independently operated on-premises systems.

The selected architecture provides:

- Private network segmentation.
- Encrypted hybrid connectivity.
- Centralized metrics and log collection.
- Event-driven security alerting.
- Automated SOAR responses.
- Persistent incident storage.
- Infrastructure provisioning through Terraform.
- Centralized configuration and updates through Ansible.
- Automated testing and deployment through GitHub Actions.
- Documented service and infrastructure recovery procedures.

The infrastructure will be validated through functional, integration, security and resilience testing.

The final deployed configuration and any changes from this design will be recorded in the as-built architecture documentation.
