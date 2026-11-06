# Project Roadmap

## 1. Project Overview

The goal of this project is to build a hybrid infrastructure connecting AWS and VirtualBox, with centralized monitoring, security automation and infrastructure management.

I divided the project into three phases to make the implementation easier to organize and test.

## 2. Technology Stack

| Component | Technology |
|---|---|
| Cloud | AWS EC2 and VPC |
| On-premises | VirtualBox and Ubuntu |
| VPN | WireGuard |
| Internal DNS | dnsmasq |
| Monitoring | Grafana and Prometheus |
| Logging | Grafana Loki and Alloy |
| Alerting | Alertmanager |
| SOAR | Python, Flask and Gunicorn |
| SOAR storage | SQLite and JSONL |
| Infrastructure as Code | Terraform |
| Configuration management | Ansible |
| Automatic updates | unattended-upgrades |
| CI/CD | GitHub Actions |

## 3. Phase 1 — Analysis and Planning

**Status: Completed**

During this phase, I researched the requirements, selected the technologies and designed the initial infrastructure.

### Completed Work

- **Requirements:** Identified the functional and non-functional requirements.
- **Technology research:** Compared AWS, monitoring platforms, VPN solutions and automation tools.
- **Network design:** Planned the AWS VPC, subnets, firewall rules and WireGuard connection.
- **Monitoring design:** Planned centralized metrics, logging, dashboards and alerts.
- **SOAR design:** Defined event processing, security rules and automated response actions.
- **Infrastructure as Code:** Prepared Terraform configurations and remote state storage.
- **CI/CD:** Configured GitHub Actions with a Windows self-hosted runner.
- **Testing:** Created the initial test strategy and acceptance criteria.

### Documents

- `requirements-analysis.md`
- `technology-choices.md`
- `technical-design.md`
- `test-strategy.md`
- `phase-1-results.md`

The original design included FastAPI, PostgreSQL and Route 53, but these choices were changed during implementation.

## 4. Phase 2 — Infrastructure Implementation

**Status: Main implementation completed**

This phase focused on deploying the infrastructure and connecting all the main components.

### AWS Infrastructure

- Deployed three EC2 instances using Terraform.
- Configured the VPC, subnets, route tables and security groups.
- Configured the AWS gateway for routing, NAT and WireGuard.
- Used Systems Manager for administration without public SSH access.

### On-Premises Infrastructure

- Created three Ubuntu VMs in VirtualBox.
- Configured internal networking and the on-premises gateway.
- Connected the on-premises network to AWS using WireGuard.
- Configured nftables firewall rules and private DNS using dnsmasq.

### Monitoring

- Deployed Grafana, Prometheus, Loki, Alloy and Alertmanager using Docker Compose.
- Configured metrics collection and centralized logging.
- Created Infrastructure, Security Logs and SOAR dashboards.
- Configured Prometheus infrastructure alert rules.

### SOAR

- Developed the Python Flask SOAR application.
- Implemented alert processing, rule evaluation and deduplication.
- Added incident recording, notification preparation and simulated containment.
- Connected the firewall log analyzer to Loki.
- Implemented Prometheus metrics for SOAR monitoring.

### Automation

- Created GitHub Actions workflows for Terraform checks, SOAR deployment and monitoring dashboards.
- Configured Ansible to update two on-premises Linux machines.
- Enabled unattended-upgrades on five Linux servers.
- Tested that invalid dashboard JSON prevents deployment.

### Evidence

Implementation screenshots are stored in `docs/evidence/`, organized by networking, monitoring, SOAR, security, CI/CD and updates.

## 5. Phase 3 — Testing and Documentation

**Status: In progress**

This phase focuses on verifying the infrastructure, testing failures and preparing the final documentation.

### Completed Testing

- Verified WireGuard connectivity and private access to Grafana.
- Tested internal DNS from two on-premises machines.
- Confirmed firewall blocking and logging.
- Verified infrastructure metrics and multiple Loki log sources.
- Detected a possible port scan using collected firewall logs.
- Tested SOAR incident processing and duplicate detection.
- Verified SOAR monitoring in Grafana.
- Tested successful CI/CD deployments and failure protection.
- Ran Ansible updates on two Linux machines.
- Verified automatic update checks and execution logs.
- Stopped and manually recovered Grafana while the other monitoring services stayed running.

### Remaining Testing

- Test SOAR restart and data persistence.
- Verify backup and restoration procedures.
- Test simulated containment separately.
- Test VPN failure and recovery.
- Measure service recovery time.
- Complete any remaining security and performance checks.

### Final Documentation

The remaining documentation work includes:

- Updating existing Markdown documents.
- Updating the architecture diagrams to match the deployed infrastructure.
- Preparing the final test results.
- Documenting SOAR processing and response actions.
- Updating the infrastructure operations manual.
- Recording technical issues and solutions.
- Preparing a final project reflection.

## 6. Portfolio Preparation

After completing the Markdown documentation, I plan to create separate Word documents for my portfolio.

These will focus on the infrastructure architecture, technologies used, automation workflows, security implementation and testing results.

The portfolio documents will be shorter and more visual than the technical project documentation.

## 7. Current Progress

The main hybrid infrastructure is operational, including WireGuard, monitoring, SOAR, DNS, CI/CD and centralized updates.

The remaining work is mainly focused on additional recovery testing, documentation and preparing the final project presentation.