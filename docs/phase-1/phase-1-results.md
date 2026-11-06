# Phase 1 Results — Analysis, Design and Planning

**Project:** Innovatech Solutions — Hybrid Cloud Infrastructure and Security Automation  
**Phase:** Phase 1 — Analysis, Design and Planning  
**Status:** Completed  
**Document purpose:** Record the initial design, preparation and validation activities before infrastructure deployment.


## 1. Overview

Phase 1 focused on analyzing the Innovatech Solutions requirements, evaluating suitable technologies, designing the hybrid infrastructure and preparing the automation foundations for implementation.

The main objective was to establish a technically justified architecture that could be deployed, tested and maintained through version-controlled infrastructure and application configuration.

This phase focused on planning and validation rather than commissioning operational services.

## 2. Completed Activities

### 2.1 Requirements Analysis

The business context, core assignment and technical requirements were reviewed.

Functional and non-functional requirements were documented, including:

- Secure hybrid connectivity between AWS and on-premises systems.
- Network segmentation and restricted private access.
- Internal DNS resolution.
- Centralized infrastructure monitoring and security logging.
- Event-driven SOAR processing.
- Automated security responses.
- Infrastructure as Code and CI/CD automation.
- Centralized system updates.
- Resilience testing, recovery procedures and documentation.

Each major requirement was assigned acceptance criteria to support later verification.

### 2.2 Technology Evaluation

Technologies were evaluated against functionality, security, integration, cost, maintainability and implementation complexity.

The initial design selected:

| Area | Initial design decision |
|---|---|
| Cloud infrastructure | AWS EC2 and VPC |
| On-premises virtualization | VirtualBox with Ubuntu Linux |
| Hybrid connectivity | WireGuard |
| Monitoring | Prometheus and Grafana |
| Centralized logging | Grafana Loki and Alloy |
| Alert routing | Prometheus Alertmanager |
| SOAR application | Custom Python application |
| Infrastructure provisioning | Terraform |
| Configuration management | Ansible |
| CI/CD | GitHub Actions with a Windows self-hosted runner |
| Container management | Docker Compose |

The original design proposed FastAPI, PostgreSQL and Route 53 private DNS. These were design choices rather than deployed components during Phase 1.

Their later implementation changes are documented in the final as-built architecture.

### 2.3 Architecture Design

Three initial architecture diagrams were prepared:

1. Hybrid Network Architecture.
2. Observability Architecture.
3. SOAR Event Processing Architecture.

The proposed infrastructure separated AWS-hosted monitoring and SOAR services from independently operated on-premises systems.

The initial network plan included:

- AWS VPC: `10.20.0.0/16`
- Monitoring subnet: `10.20.10.0/24`
- SOAR subnet: `10.20.20.0/24`
- Gateway subnet: `10.20.30.0/24`
- On-premises network: `10.30.0.0/24`
- WireGuard tunnel network: `10.40.0.0/30`

The design included separate security groups, private application instances, restricted administrative access and controlled routing between environments.

### 2.4 Infrastructure as Code Preparation

Terraform configurations were prepared for the planned AWS infrastructure.

These included:

- Virtual Private Cloud and subnet definitions.
- Routing and network gateway configuration.
- EC2 resources.
- Security groups.
- IAM roles and instance profiles.
- Supporting network and management resources.

Remote Terraform state storage in Amazon S3 was configured as part of the infrastructure management approach.

The purpose was to support repeatable provisioning, reviewable infrastructure changes and controlled resource management.

### 2.5 Automation and Repository Preparation

A GitHub repository was established to maintain source code, configuration and project documentation.

The initial project structure separated:

- Terraform infrastructure definitions.
- System and deployment configurations.
- SOAR application source code.
- Automated tests.
- GitHub Actions workflows.
- Technical documentation.

A local Windows self-hosted GitHub Actions runner was configured to execute validation workflows.

### 2.6 Testing Strategy

An initial testing strategy was developed covering:

- Functional testing.
- Network connectivity and segmentation.
- Monitoring and log collection.
- SOAR rule processing and response actions.
- Infrastructure automation.
- Failure recovery and data persistence.

A requirement-to-test mapping was prepared to guide later verification.

## 3. Phase 1 Validation

### 3.1 Terraform Configuration Validation

Terraform configuration was checked using automated GitHub Actions.

The workflow included:

- Terraform formatting checks.
- Initialization without connecting to the remote state backend.
- Terraform configuration validation.

These checks verified the structure and syntax of the infrastructure definitions.

They did not establish that the AWS services were operational.

### 3.2 Infrastructure Planning

Terraform planning was used to inspect the intended infrastructure changes before deployment.

The plan was reviewed to identify the resources that would be provisioned and detect unexpected changes.

Actual resource provisioning was reserved for Phase 2.

### 3.3 Phase 1 Completion

At the end of Phase 1:

- Requirements and acceptance criteria were documented.
- Initial technology choices were justified.
- Network, monitoring and SOAR architectures were designed.
- Terraform configuration was prepared.
- The initial repository and CI validation workflow were operational.
- The testing approach was established.

No operational hybrid monitoring or SOAR service was claimed as complete at this stage.

## 4. Risks Identified

| Risk | Potential impact | Planned mitigation |
|---|---|---|
| Incorrect network routing | Loss of connectivity between environments | Controlled network tests and route verification |
| Unnecessary cloud expenditure | Higher development cost | Small EC2 instances and stopping unused resources |
| Unauthorized service access | Exposure of internal services | Security groups, private subnets and firewall restrictions |
| Monitoring resource limitations | Slow or unavailable dashboards | Measure CPU, memory and storage utilization |
| Incorrect security responses | Disruption of legitimate traffic | Validation, allowlists and simulated containment |
| Infrastructure configuration errors | Failed deployment or unexpected changes | Terraform validation and controlled plans |
| Configuration differences between systems | Inconsistent maintenance | Version-controlled configuration and repeatable procedures |

## 5. Work Planned for Phase 2

The next phase was defined to implement and verify:

1. AWS infrastructure provisioning.
2. On-premises VirtualBox environments.
3. WireGuard VPN connectivity.
4. Network segmentation and private service access.
5. Internal DNS resolution.
6. Centralized monitoring, logging and alerting.
7. SOAR event reception, rule evaluation and automated responses.
8. CI/CD deployment workflows.
9. System update automation.

Results from these activities belong in the Phase 2 implementation documentation rather than this historical Phase 1 report.

## 6. Work Planned for Phase 3

The final phase was planned to focus on:

- Functional and integration testing.
- Controlled security event simulations.
- CI/CD failure protection.
- Resilience and recovery verification.
- Final architecture documentation.
- Operational procedures and troubleshooting.
- Evidence collection.
- Reflection and technical handoff.

## 7. Conclusion

Phase 1 successfully established the requirements, initial technical design, technology evaluation, automation foundations and verification strategy for the Innovatech Solutions infrastructure.

The resulting preparation supported the transition from design into practical deployment.
