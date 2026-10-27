
# Project Roadmap
## Innovatech Solutions — Hybrid Cloud Infrastructure

**Project:** Hybrid Cloud Infrastructure and Security Automation  
**Client:** Innovatech Solutions  
**Document Version:** 1.0  
**Implementation:** Three Phases

---

## 1. Project Overview

The project will deliver a hybrid cloud infrastructure combining centralized monitoring, security automation and automated infrastructure management.

The implementation will use AWS for cloud hosting and networking, with open-source technologies providing monitoring, logging, security event processing and system management.

The project is divided into three phases:

1. Analysis, Design and Planning
2. Infrastructure Deployment and Integration
3. Testing, Resilience and Handoff

Each phase includes technical implementation activities, documentation and verification.

---

## 2. Technology Stack

| Component | Technology |
|---|---|
| Cloud Hosting | AWS EC2 |
| Networking | AWS VPC, subnets, Security Groups |
| Hybrid Connectivity | WireGuard |
| Internal DNS | Route 53 Private DNS |
| Virtualization | Linux virtual machines |
| Containerization | Docker Compose |
| Monitoring | Prometheus |
| Dashboards | Grafana |
| Logging | Grafana Loki |
| Telemetry Collection | Grafana Alloy |
| Alerting | Prometheus Alertmanager |
| SOAR | Python / FastAPI |
| Incident Database | PostgreSQL |
| Infrastructure as Code | Terraform |
| Configuration Management | Ansible |
| CI/CD | GitHub Actions |
| Testing | Pytest and integration scripts |

---

## 3. Phase 1 — Analysis, Design and Planning

**Objective:** Define the infrastructure architecture, justify technology choices and prepare the development environment.

### 3.1 Requirements Analysis

Analyze the business requirements and define the functional and non-functional requirements.

Tasks:
- Analyze the business context and project specifications.
- Define functional and non-functional requirements.
- Identify security and infrastructure constraints.
- Establish acceptance criteria.
- Create a requirement traceability table.

**Document:** `docs/phase-1/requirements-analysis.md`

### 3.2 Technology Research

Evaluate the technologies used in the implementation.

Tasks:
- Compare observability platforms.
- Evaluate logging and alerting solutions.
- Analyze AWS hosting requirements.
- Evaluate containerized application deployment.
- Justify the SOAR application architecture.
- Evaluate infrastructure automation and configuration management tools.
- Document technology costs and limitations.

**Document:** `docs/phase-1/technology-choices.md`

### 3.3 Network Design

Design the AWS and on-premises network topology.

Tasks:
- Define AWS VPC and subnet addressing.
- Plan monitoring and SOAR network segmentation.
- Define routing between AWS and local infrastructure.
- Design WireGuard VPN connectivity.
- Plan internal DNS resolution.
- Define firewall and Security Group rules.
- Document required communication ports.

**Documents:**
- `docs/phase-1/technical-design.md`
- `docs/diagrams/network-architecture.png`

### 3.4 Monitoring Design

Design the monitoring and logging architecture.

Tasks:
- Define Prometheus monitoring targets.
- Plan Grafana Alloy deployment.
- Define Loki log sources and storage.
- Create alerting rules and notification flows.
- Design infrastructure monitoring dashboards.
- Design security event dashboards.
- Design SOAR performance dashboards.

**Documents:**
- `docs/phase-1/technical-design.md`
- `docs/diagrams/monitoring-architecture.png`

### 3.5 SOAR Design

Design the security automation system.

Tasks:
- Define security event ingestion.
- Design the event-processing workflow.
- Define rule evaluation logic.
- Design PostgreSQL incident storage.
- Define automated response actions.
- Plan SOAR application authentication.
- Define health and performance metrics.

**Documents:**
- `docs/phase-1/technical-design.md`
- `docs/diagrams/soar-architecture.png`

### 3.6 Deployment and Recovery Design

Define procedures for infrastructure deployment, updates and recovery.

Tasks:
- Design Terraform resource structure.
- Define Ansible configuration management.
- Plan automated multi-node updates.
- Define container deployment procedures.
- Plan PostgreSQL backups.
- Define recovery procedures.
- Establish system testing methods.

**Documents:**
- `docs/phase-1/technical-design.md`
- `docs/phase-1/test-strategy.md`

### 3.7 DevOps Setup

Prepare the repository and automation environment.

Tasks:
- Configure the Git repository.
- Create Terraform and Ansible project directories.
- Prepare Docker Compose configurations.
- Create the SOAR application structure.
- Configure GitHub Actions for validation and testing.
- Prepare the self-hosted runner.
- Establish credential management procedures.

**Deliverables:**
- Repository structure
- Initial Terraform configuration
- Ansible playbook structure
- Docker Compose configuration
- GitHub Actions workflows

### Phase 1 Completion Criteria

Phase 1 is complete when:

- Requirements are documented.
- Technology selections are justified.
- Network, monitoring and SOAR designs are documented.
- Architecture diagrams are available.
- Update and recovery strategies are defined.
- The repository and initial automation structure are prepared.

---

## 4. Phase 2 — Infrastructure Deployment and Integration

**Objective:** Deploy the hybrid infrastructure and implement monitoring, SOAR and automated system management.

### 4.1 AWS Infrastructure

Tasks:
- Provision the VPC and subnets.
- Configure network routing.
- Create Security Groups.
- Deploy the monitoring EC2 instance.
- Deploy the SOAR EC2 instance.
- Configure persistent storage.
- Configure private DNS.
- Verify network connectivity.

**Evidence:** Terraform execution results and network connectivity tests.

### 4.2 On-Premises Environment

Tasks:
- Deploy Linux virtual machines.
- Configure authentication and firewall logging.
- Install monitoring agents.
- Configure WireGuard connectivity.
- Verify private routing.
- Test internal DNS resolution.

**Evidence:** VM configurations, VPN connectivity and DNS tests.

### 4.3 Monitoring Implementation

Tasks:
- Deploy Prometheus.
- Deploy Grafana.
- Deploy Loki.
- Deploy Grafana Alloy.
- Deploy Alertmanager.
- Configure infrastructure metrics collection.
- Configure log ingestion from two sources.
- Create dashboards and alerting rules.

**Evidence:** Monitoring dashboards, logs, metrics and generated alerts.

### 4.4 SOAR Implementation

Tasks:
- Develop the FastAPI application.
- Implement event ingestion.
- Implement rule evaluation.
- Configure PostgreSQL.
- Implement incident recording.
- Implement notifications.
- Implement simulated IP blocking.
- Implement health and performance metrics.
- Create unit and integration tests.

**Evidence:** SOAR application, test results and recorded security incidents.

### 4.5 Monitoring and SOAR Integration

Tasks:
- Configure alert forwarding.
- Connect alerts to the SOAR event listener.
- Generate simulated security events.
- Verify automated responses.
- Verify incident storage.
- Display SOAR activity in Grafana.

**Evidence:** End-to-end event processing and response tests.

### 4.6 CI/CD Implementation

Tasks:
- Configure Python testing workflows.
- Configure Terraform validation.
- Implement automated SOAR deployment.
- Configure deployment versioning.
- Verify execution through the local runner.

**Evidence:** Successful GitHub Actions workflow executions.

### 4.7 Automated Updates

Tasks:
- Configure Ansible inventory.
- Develop OS update playbooks.
- Execute updates across multiple Linux systems.
- Verify installed package versions.
- Implement health checks after updates.

**Evidence:** Ansible execution logs and package version comparisons.

### 4.8 Portable Demonstration

Tasks:
- Create a Docker Compose demonstration configuration.
- Include monitoring and SOAR components.
- Implement simulated event generation.
- Create setup and testing instructions.
- Verify the demonstration environment.

**Document:** Initial demonstration instructions in the operations manual.

### Phase 2 Completion Criteria

Phase 2 is complete when:

- AWS infrastructure is operational.
- Hybrid connectivity is working.
- Monitoring collects metrics and logs.
- At least two log sources are integrated.
- Security alerts are processed by SOAR.
- At least two automated response actions work.
- SOAR operational metrics are visible.
- CI/CD pipelines deploy application changes.
- Multi-node updates are automated.

---

## 5. Phase 3 — Testing, Resilience and Handoff

**Objective:** Verify the infrastructure, test recovery procedures and prepare the final documentation.

### 5.1 Functional Testing

Test:
- Network segmentation.
- Private resource accessibility.
- DNS resolution.
- VPN connectivity.
- Metrics collection.
- Log ingestion.
- Alert generation.
- SOAR event processing.
- Automated response actions.
- Incident persistence.
- CI/CD execution.
- Multi-node updates.

**Document:** `docs/phase-3/test-plan-and-results.md`

### 5.2 Resilience Testing

Test:
- Monitoring service failure.
- SOAR application failure.
- Database restart and recovery.
- EC2 instance restart.
- VPN disconnection.
- Backup restoration.

Record:
- Failure symptoms.
- Recovery procedures.
- Recovery time.
- Data loss, if any.
- Final system status.

**Document:** `docs/phase-3/failure-and-recovery.md`

### 5.3 Final Architecture

Document the completed infrastructure, including:

- AWS resources.
- Network configuration.
- Local virtual machines.
- VPN connectivity.
- Monitoring services.
- SOAR components.
- Data storage.
- Security controls.

**Document:** `docs/phase-3/as-built-architecture.md`

### 5.4 SOAR Playbook Documentation

Document:
- Event formats.
- Rule matching.
- Response actions.
- Incident storage.
- Error handling.
- Adding new rules.
- Adding new response actions.

**Document:** `docs/phase-3/soar-playbook-guide.md`

### 5.5 Operations Manual

Document:
- Infrastructure deployment.
- Service configuration.
- Monitoring access.
- Log inspection.
- SOAR operation.
- Automated updates.
- Application deployment.
- Backup and restoration.
- Troubleshooting.
- Portable demonstration setup.
- Infrastructure teardown.

**Document:** `docs/phase-3/operations-manual.md`

### 5.6 Final Demonstration and Reflection

Prepare a demonstration covering the full infrastructure and security automation workflow.

Demonstrate:
- Cloud and on-premises connectivity.
- Centralized monitoring.
- Security event generation.
- Automated SOAR actions.
- Incident records.
- SOAR dashboards.
- Automated updates.
- Failure recovery.

Document technical challenges, project decisions, changes and lessons learned.

**Document:** `docs/phase-3/reflective-report.md`

### Phase 3 Completion Criteria

Phase 3 is complete when:

- Functional tests have been executed.
- Failure recovery has been demonstrated.
- Backups have been restored successfully.
- Infrastructure documentation matches the deployed system.
- Operational procedures are documented.
- All core requirements have implementation and test evidence.
- The final system can be demonstrated.

---

## 6. Flavor A — Advanced Technical Activities

The following activities are included in the technical workstream, pending confirmation of the assigned Flavor.

### Process Detection and Response

- Simulate suspicious CPU usage.
- Generate failed SSH login events.
- Generate suspicious connection records.
- Configure detection rules.
- Connect detected events to SOAR responses.

**Document:** `docs/flavor-a/process-detection.md`

### Traffic Pattern Analysis

- Capture network traffic using tcpdump or Wireshark.
- Establish baseline traffic patterns.
- Identify abnormal connection behavior.
- Develop Python detection scripts.
- Forward generated alerts to SOAR.

**Document:** `docs/flavor-a/traffic-analysis.md`

### Synthetic Performance Testing

- Generate controlled monitoring workloads.
- Simulate increased event volume.
- Measure metrics and log ingestion.
- Observe application resource usage.
- Measure SOAR response performance.

**Document:** `docs/flavor-a/performance-testing.md`

---

## 7. Documentation and Project Management

All source code, infrastructure configuration and technical documentation will be maintained in GitHub.

Project documentation will be updated during implementation to reflect completed activities and technical changes.

Instructor feedback will be recorded in `docs/feedback-log.md`.

Each functional requirement must be linked to implementation evidence and verification results.

Sensitive information must not be committed to the repository.

The final project will include installation, operation, testing and recovery instructions.

---

## 8. Project Completion

The project is complete when the hybrid infrastructure operates as designed, the monitoring and SOAR systems are integrated, automated management procedures are working and the functional requirements have been verified.

The final delivery will include the implemented infrastructure, source code, test evidence, architecture diagrams and operational documentation.
