
# Requirements Analysis
## Innovatech Solutions — Hybrid Cloud Infrastructure

**Project:** Hybrid Cloud Infrastructure and Security Automation  
**Client:** Innovatech Solutions  
**Document Version:** 1.0  
**Status:** Initial Requirements Baseline

---

## 1. Introduction

### 1.1 Purpose

This document defines the requirements for the design and implementation of a hybrid cloud infrastructure for Innovatech Solutions.

The infrastructure will provide centralized monitoring, automated security incident handling, controlled communication between cloud and on-premises systems, and automated infrastructure management.

The requirements are derived from the Business Context, Core Assignment and Requirements specifications provided by Innovatech Solutions.

### 1.2 Business Context

Innovatech Solutions requires an infrastructure capable of supporting increasingly complex business operations while maintaining security, availability and operational visibility.

The organization aims to improve infrastructure monitoring, automate responses to security incidents and establish reliable integration between cloud services and on-premises systems.

The solution must provide a central overview of operational and security events while allowing infrastructure components to be managed and updated consistently.

### 1.3 Project Objectives

The project has the following objectives:

- Establish a secure hybrid cloud infrastructure.
- Separate infrastructure components into controlled network segments.
- Provide private communication and internal DNS resolution.
- Implement centralized monitoring of metrics and logs.
- Integrate at least two independent log sources.
- Develop an event-driven Security Orchestration, Automation and Response (SOAR) system.
- Implement at least two automated security response actions.
- Monitor the operational status of the SOAR system.
- Automate infrastructure provisioning and configuration.
- Implement centralized updates across multiple machines.
- Establish testing, backup and recovery procedures.
- Provide operational documentation and reproducible deployments.

### 1.4 Scope

The project includes:

- AWS network and compute infrastructure.
- Simulated on-premises Linux systems.
- Secure hybrid connectivity.
- Centralized metrics and log management.
- Security event detection and processing.
- Automated security responses.
- SOAR incident storage.
- Infrastructure as Code.
- CI/CD pipelines.
- Automated system updates.
- Infrastructure resilience and recovery testing.
- System documentation and handoff procedures.

The project does not include the development of a production-scale enterprise SOC or the replacement of existing business applications.

---

## 2. Functional Requirements

Functional requirements describe the functions and services that the infrastructure must provide.

The original requirement identifiers are retained for traceability.

### FR-01 — Infrastructure Resilience

**Source:** REQ-NCA-P2-01

The infrastructure must maintain critical functionality or support rapid recovery when individual software or infrastructure components fail.

The solution must provide mechanisms for service recovery, persistent data storage and restoration of affected components.

**Acceptance Criteria:**

- Critical services can be recovered after a simulated failure.
- Persisted monitoring and incident data remain available after service restarts.
- A backup can be restored successfully.
- Recovery procedures are documented and tested.
- Recovery results include the observed downtime and any data loss.

### FR-02 — Network Segmentation

**Source:** REQ-NCA-P2-02

The infrastructure must use logically isolated network segments to control communication between resources.

The network design must restrict unnecessary communication while allowing authorized services to interact.

**Acceptance Criteria:**

- Monitoring, SOAR and monitored environments are logically separated.
- Required communication paths are documented.
- Firewall rules restrict access between network segments.
- Unauthorized communication attempts are blocked.
- Network segmentation is verified through connectivity testing.

### FR-03 — Private Resource Access

**Source:** REQ-NCA-P2-03

Internal infrastructure components must not be directly exposed to the public internet.

Databases and internal application interfaces must be accessible only through authorized private routes.

**Acceptance Criteria:**

- The PostgreSQL database has no public access.
- Internal SOAR interfaces are restricted to authorized networks.
- Internal monitoring services use controlled access paths.
- Unauthorized external connections are rejected.

### FR-04 — Internal DNS Resolution

**Source:** REQ-NCA-P2-04

Infrastructure components must be able to resolve internal service names to their private IP addresses.

The solution must support DNS resolution for authorized systems connected through the hybrid infrastructure.

**Acceptance Criteria:**

- Internal service names resolve to private addresses.
- DNS resolution works from authorized cloud systems.
- DNS resolution works across the hybrid network.
- Internal DNS configuration and forwarding rules are documented.

### FR-05 — Automated Multi-Node Updates

**Source:** REQ-NCA-P1-05

The infrastructure must support centralized and automated software updates for multiple machines.

Updates must be executed consistently without requiring separate manual actions on individual systems.

**Acceptance Criteria:**

- One automation execution can update at least two Linux systems.
- Updates are executed using version-controlled configuration.
- Installed package versions are verified after execution.
- Failed updates are detected and reported.
- The update procedure can be repeated.

### FR-06 — Observability Platform Evaluation

**Source:** REQ-NCA-P2-06

An observability platform must be researched and evaluated against the organization's monitoring requirements.

The evaluation must consider infrastructure metrics, centralized logging, alerting, integration, operational complexity and scalability.

**Acceptance Criteria:**

- At least two observability solutions are compared.
- Evaluation criteria are documented.
- The selected solution is justified against the project requirements.
- Technical limitations and operational considerations are identified.

### FR-07 — Centralized Logging and Alerting

**Source:** REQ-NCA-P2-07

The monitoring infrastructure must collect and process logs from at least two distinct sources.

The system must support querying these logs and generating alerts from relevant events.

**Acceptance Criteria:**

- Linux authentication or system logs are collected.
- Firewall or network security logs are collected.
- Both log sources are visible in the central monitoring platform.
- Relevant alert rules are configured.
- A generated security event produces an alert.

### FR-08 — Event-Driven SOAR

**Source:** REQ-NCA-P2-08

The infrastructure must include an event-driven SOAR system that processes security alerts and executes predefined automated actions.

The SOAR system must contain an event collector, event-processing logic and at least two distinct response actions.

Monitored workstations must not run on the same platform as the SOAR system.

**Acceptance Criteria:**

- The SOAR system receives an event from the monitoring environment.
- The event is classified according to defined rules.
- The rule engine selects the appropriate response.
- At least two distinct automated response actions execute successfully.
- The event and action results are recorded.
- Monitored systems operate separately from the SOAR platform.
- Failed actions are logged and reported.

### FR-09 — SOAR Monitoring

**Source:** REQ-NCA-P2-09

The operational status and performance of the SOAR system must be monitored through the centralized observability platform.

**Acceptance Criteria:**

- SOAR service health is visible.
- Processed event counts are displayed.
- Successful and failed automated actions are recorded.
- Event processing performance is measurable.
- SOAR monitoring information is displayed in Grafana.

### FR-10 — Infrastructure as Code

**Source:** REQ-NCA-P2-10

Infrastructure resources and application deployment configurations must be defined using version-controlled code.

The solution must support repeatable provisioning and configuration of cloud infrastructure and SOAR components.

**Acceptance Criteria:**

- AWS infrastructure is defined using Terraform.
- System configuration is managed through Ansible.
- Container services are defined using Docker Compose.
- Configuration files are maintained in Git.
- Infrastructure can be deployed using documented procedures.

### FR-11 — CI/CD Automation

**Source:** REQ-NCA-P2-11

Automated pipelines must support testing and deployment of the SOAR application and underlying infrastructure configuration.

The pipelines must be executable through a local runner.

**Acceptance Criteria:**

- Application tests execute automatically.
- Terraform configuration is validated through CI.
- SOAR deployment is automated.
- Pipelines execute using a self-hosted local runner.
- Failed tests prevent deployment.
- Pipeline execution results are available for verification.

### FR-12 — DevOps Platform Integration

**Source:** REQ-NCA-P2-12

The project must use a DevOps platform for source code management, infrastructure configuration and deployment automation.

**Acceptance Criteria:**

- Source code is maintained in a Git repository.
- Infrastructure configuration is version-controlled.
- CI/CD workflows are stored in the repository.
- Changes can be tracked through Git history.
- Deployment procedures are documented.

---

## 3. Non-Functional Requirements

Non-functional requirements define the security, reliability, maintainability and operational characteristics expected from the solution.

The requirements in this section translate the business objectives and technical constraints into measurable engineering criteria.

The numerical targets below are project acceptance targets and are not explicitly prescribed by the source requirements.

### NFR-01 — Security

The infrastructure must enforce controlled access to internal services and restrict unnecessary network communication.

**Acceptance Criteria:**

- Internal databases are not publicly accessible.
- Administrative access requires authentication.
- Secrets are excluded from version control.
- Communication between environments is encrypted.
- Firewall rules follow the principle of least privilege.

### NFR-02 — Availability and Recovery

The infrastructure must support recovery from isolated component failures.

**Acceptance Criteria:**

- Application containers restart automatically after unexpected termination.
- Persistent data survives container recreation.
- Documented procedures allow the main services to be restored after failure.
- Recovery time and any data loss are measured during testing.

Recovery time objectives will be established during technical design.

### NFR-03 — Maintainability

Infrastructure configuration and application services must be organized so that maintenance and updates can be performed consistently.

**Acceptance Criteria:**

- Infrastructure configuration is stored in version control.
- Application services use documented configuration files.
- Deployment and update procedures are repeatable.
- Changes can be reviewed through Git history.
- Operational instructions are available.

### NFR-04 — Scalability

The architecture must allow monitoring and security processing capacity to be expanded without redesigning the entire system.

**Acceptance Criteria:**

- Monitoring and SOAR components are deployed as separate services.
- Additional monitored systems can be added through configuration.
- New SOAR rules can be introduced without changing the overall architecture.
- Resource usage can be observed to identify capacity limitations.

### NFR-05 — Observability

The system must provide sufficient information to identify operational issues and investigate security events.

**Acceptance Criteria:**

- Infrastructure metrics are collected centrally.
- Logs from multiple sources are searchable.
- Critical service failures generate alerts.
- SOAR health and response metrics are visible.
- Operational dashboards are available to authorized users.

### NFR-06 — Data Integrity and Persistence

Security incidents, action execution records and monitoring data must be stored reliably.

**Acceptance Criteria:**

- SOAR incident records are stored in PostgreSQL.
- Database data persists across application restarts.
- Backup procedures are available.
- Restored data is verified for correctness.
- Failed database operations are reported.

### NFR-07 — Portability and Reproducibility

The infrastructure and applications must be deployable using documented configuration and automation.

**Acceptance Criteria:**

- Infrastructure provisioning is performed using Terraform.
- Linux configuration is performed using Ansible.
- Application services are deployed using Docker Compose.
- A portable demonstration environment can be started independently.
- Installation requirements and limitations are documented.

### NFR-08 — Performance

The monitoring and SOAR systems must process the expected demonstration workload without sustained resource exhaustion or unbounded processing delays.

**Acceptance Criteria:**

- CPU and memory usage are measurable.
- Security events are processed within a documented time interval.
- SOAR processing duration is recorded.
- Performance tests identify the maximum tested workload.
- Performance limitations are documented.

Performance thresholds will be defined after baseline measurements.

### NFR-09 — Data Protection

The infrastructure must handle operational and security data according to applicable organizational policies and legal requirements.

**Acceptance Criteria:**

- Data collection purposes are documented.
- Log retention periods are defined.
- Access to security records is restricted.
- Demonstration evidence does not contain credentials or unnecessary personal data.
- Procedures exist for removing stored demonstration data.

---

## 4. Technical Constraints

The following constraints apply to the implementation.

### TC-01 — Hybrid Infrastructure

The solution must include connected cloud and on-premises infrastructure.

Cloud and local systems must communicate through controlled network paths.

### TC-02 — Platform Separation

Monitored workstations and servers must not run on the same platform as the SOAR system.

### TC-03 — Automated Deployment

Cloud infrastructure and SOAR components must be provisioned and deployed through version-controlled automation.

### TC-04 — Local CI/CD Runner

The CI/CD pipelines must support execution through a locally hosted runner.

### TC-05 — Multiple Log Sources

The observability platform must integrate at least two different log sources and provide alerting.

### TC-06 — Centralized Updates

Multiple systems must receive updates through centralized configuration management without requiring manual updates on each machine.

### TC-07 — Infrastructure Cost

The deployment will use AWS EC2 and self-hosted monitoring services. Cloud costs must be evaluated before provisioning.

The design will avoid unnecessary managed services while retaining the functionality required by the project.

### TC-08 — Independent Evaluation

The project must provide sufficient documentation for another technical user to understand, test and reproduce the deployment.

A portable demonstration environment will be provided for application-level testing.

---

## 5. Requirement Traceability

| Requirement | Implementation | Verification |
|---|---|---|
| REQ-NCA-P2-01 | Service recovery, persistent storage and backups | Failure and restoration tests |
| REQ-NCA-P2-02 | VPC segmentation and firewall controls | Connectivity and isolation tests |
| REQ-NCA-P2-03 | Private routes and restricted service access | External access tests |
| REQ-NCA-P2-04 | Private DNS and DNS forwarding | Internal name resolution tests |
| REQ-NCA-P1-05 | Ansible update playbooks | Multi-node update execution |
| REQ-NCA-P2-06 | Observability technology evaluation | Technology comparison document |
| REQ-NCA-P2-07 | Grafana Alloy, Loki and alert rules | Two-source log ingestion and alert tests |
| REQ-NCA-P2-08 | Python SOAR application | Event processing and response tests |
| REQ-NCA-P2-09 | Prometheus SOAR metrics and Grafana | SOAR dashboard verification |
| REQ-NCA-P2-10 | Terraform, Ansible and Docker Compose | Deployment verification |
| REQ-NCA-P2-11 | GitHub Actions and local runner | CI/CD execution tests |
| REQ-NCA-P2-12 | GitHub repository and workflows | Repository and pipeline verification |

---

## 6. Requirement Verification Strategy

Each requirement will be verified through one or more of the following methods:

**Configuration Inspection**

Review infrastructure configuration, network rules, application settings and version-controlled files.

**Functional Testing**

Execute defined tests to verify expected behavior.

**Integration Testing**

Verify communication and data exchange between infrastructure components.

**Security Testing**

Verify network restrictions, private resource access, event detection and automated responses.

**Failure Testing**

Simulate service and infrastructure failures and verify recovery behavior.

**Operational Testing**

Verify monitoring, automated updates, deployment workflows and backup restoration.

Test results will be recorded during the implementation and validation phases.

---

## 7. Risks and Dependencies

| Risk | Impact | Mitigation |
|---|---|---|
| Cloud resource costs exceed the project budget | Financial | Review pricing and resource requirements before deployment |
| VPN connectivity fails | High | Document routing and use controlled connectivity tests |
| Monitoring services exceed available resources | Medium | Measure CPU, memory and storage utilization |
| Incorrect SOAR rules trigger unwanted actions | High | Restrict automated actions to controlled test scenarios |
| Database failure causes incident data loss | High | Use persistent storage and tested backups |
| CI/CD credentials are exposed | High | Use restricted credentials and secure secret management |
| Local environment cannot be reproduced | Medium | Provide setup automation and a portable demonstration |
| Automated updates interrupt critical services | Medium | Use controlled update execution and post-update health checks |

---

## 8. Conclusion

The requirements establish the need for a secure, observable and automated hybrid infrastructure.

The system must connect cloud and on-premises resources, collect operational and security information, detect relevant security events and execute automated responses.

The implementation must also provide automated infrastructure management, centralized updates, controlled access, and tested recovery procedures.

The requirements defined in this document will be used as the basis for the technical design, implementation and final system verification.
