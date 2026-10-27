
# Technology Choices
## Innovatech Solutions — Hybrid Cloud Infrastructure

**Project:** Hybrid Cloud Infrastructure and Security Automation  
**Client:** Innovatech Solutions  
**Document Version:** 1.0  
**Project Phase:** Phase 1 — Analysis and Design

---

## 1. Introduction

### 1.1 Purpose

This document evaluates the technologies used to implement the hybrid cloud infrastructure 
for Innovatech Solutions.

The evaluation covers cloud hosting, networking, observability, security automation, data storage, containerization, infrastructure provisioning and configuration management.

The objective is to select technologies that satisfy the functional and non-functional requirements while maintaining reasonable infrastructure costs, security, reliability and maintainability.

### 1.2 Selection Criteria

The technologies were evaluated using the following criteria:

| Criterion | Description |
|---|---|
| Functionality | Ability to meet the identified technical requirements |
| Security | Support for access control, network isolation and secure communication |
| Integration | Compatibility with other infrastructure components |
| Automation | Support for Infrastructure as Code and automated deployment |
| Cost | Infrastructure, licensing and operational costs |
| Maintainability | Complexity of configuration, updates and troubleshooting |
| Scalability | Ability to support additional infrastructure components |
| Portability | Ability to deploy or migrate services between environments |

The evaluation is qualitative. No weighted scoring model has been applied because several requirements, including private resource access and local CI/CD execution, are mandatory rather than optional preferences.

---

## 2. Cloud Infrastructure

### 2.1 Evaluated Technologies

Three hosting platforms were considered.

| Technology | Advantages | Disadvantages |
|---|---|---|
| Amazon Web Services (AWS) | Mature networking services, EC2 hosting, IAM, Terraform support and extensive documentation | Resource costs, cloud-specific configuration and ongoing infrastructure management |
| Microsoft Azure | Strong hybrid cloud services, virtual networking, integration with Microsoft environments and Terraform support | Additional platform-specific configuration and potentially higher operational complexity |
| Local Proxmox Infrastructure | Full infrastructure control, no cloud compute charges and flexible virtualization | Requires dedicated hardware, external connectivity and maintenance of the physical host |

### 2.2 Selected Technology: Amazon Web Services

AWS was selected as the public cloud hosting platform.

The infrastructure will use EC2 virtual machines for monitoring and SOAR services. AWS VPC will provide network isolation, with route tables and Security Groups controlling communication.

The cloud environment will include two Linux EC2 instances:

- Monitoring server hosting Grafana, Prometheus, Loki and Alertmanager.
- SOAR server hosting the Python application and PostgreSQL.

AWS services will primarily provide compute, networking and storage. Monitoring and security automation will be implemented through independently managed applications.

### 2.3 Justification

AWS provides the networking controls required for the hybrid environment, including private addressing, subnet segmentation and firewall restrictions.

Using EC2 allows the selected open-source services to run without depending on a cloud-specific application platform.

Terraform support enables the environment to be provisioned and destroyed through version-controlled configuration.

Azure provides comparable technical capabilities and would also satisfy the requirements. However, AWS was selected because its infrastructure services provide a suitable foundation without requiring additional managed application services.

A fully local environment was not selected because it would depend on the availability and maintenance of physical hardware and would not demonstrate integration with a public cloud environment.

### 2.4 Limitations

EC2 instances require operating system administration, security updates, storage management and recovery procedures.

AWS resources also generate operating costs. The instance types, storage sizes and expected operating hours will be evaluated before deployment.

---

## 3. Observability Platform

### 3.1 Evaluated Technologies

The infrastructure requires centralized metrics, logging, dashboards and alerting across cloud and on-premises systems.

Three observability solutions were evaluated.

| Technology | Advantages | Disadvantages |
|---|---|---|
| Grafana + Prometheus + Loki | Modular architecture, PromQL and LogQL querying, custom metrics, flexible dashboards and strong integration with Python applications | Multiple services to deploy, configure and maintain |
| Zabbix | Integrated infrastructure monitoring, built-in alerting, network discovery and agent-based monitoring | Less flexible for custom application metrics and log-based security workflows without additional integration |
| OpenSearch + OpenSearch Dashboards | Powerful log search, indexing and analytics, suitable for detailed security event investigations | Higher resource requirements and additional complexity for comprehensive infrastructure metrics monitoring |

### 3.2 Selected Technologies: Grafana, Prometheus and Loki

The selected observability platform consists of three primary services.

**Grafana**

Grafana will provide centralized dashboards for infrastructure monitoring, security events and SOAR activity.

**Prometheus**

Prometheus will collect and store time-series metrics from monitored infrastructure and application services.

**Grafana Loki**

Loki will store and query system and security logs collected from monitored machines.

The services will be deployed in Docker containers on the AWS monitoring server.

### 3.3 Justification

The Grafana stack was selected because it supports the separation of metrics, logs and visualization into independent components.

Prometheus provides a suitable monitoring backend for infrastructure metrics and custom application instrumentation.

The SOAR application will expose a Prometheus-compatible metrics endpoint, allowing the monitoring system to collect information about event processing, response execution and application health.

Loki provides centralized logging and integrates directly with Grafana. Its label-based indexing approach reduces the need to maintain a full-text index of every log entry.

Grafana allows infrastructure metrics and security logs to be investigated through the same interface.

Zabbix would be a suitable alternative for conventional server and network monitoring. However, the selected stack provides greater flexibility for developing and instrumenting the custom SOAR application.

OpenSearch offers more advanced indexed log searching but would introduce additional resource consumption and operational complexity for the expected infrastructure size.

### 3.4 Limitations

The selected platform requires several independently managed services.

Prometheus and Loki storage must be configured with appropriate retention and persistence.

The monitoring server must have sufficient CPU, memory and storage capacity to support simultaneous metrics ingestion, log processing and dashboard queries.

---

## 4. Telemetry Collection

### 4.1 Evaluated Technologies

| Technology | Advantages | Disadvantages |
|---|---|---|
| Grafana Alloy | Collects logs and metrics, supports OpenTelemetry and integrates with Prometheus and Loki | Requires configuration of collection pipelines |
| OpenTelemetry Collector | Vendor-neutral telemetry processing, supports multiple exporters and protocols | May require additional components and configuration for certain system log sources |
| Fluent Bit | Lightweight, efficient log forwarding and filtering | Primarily focused on logs rather than complete metrics and log collection |

### 4.2 Selected Technology: Grafana Alloy

Grafana Alloy will collect telemetry from Linux systems and forward it to the monitoring infrastructure.

It will be configured to collect:

- Linux authentication logs.
- System logs.
- Firewall and network security logs.
- Host metrics and supported application metrics.

### 4.3 Justification

Grafana Alloy provides a single configurable collection agent for multiple telemetry types.

It is compatible with the selected Grafana, Prometheus and Loki infrastructure and supports OpenTelemetry-based integration.

Using a common agent across monitored systems simplifies configuration management and reduces the number of separate collection tools.

Fluent Bit would be a suitable solution for lightweight log forwarding but would require additional tooling to cover the complete metrics collection requirements.

The OpenTelemetry Collector provides comparable flexibility. Alloy was selected because it combines OpenTelemetry functionality with integrations designed for Prometheus and Loki.

---

## 5. Alerting

### 5.1 Evaluated Technologies

| Technology | Advantages | Disadvantages |
|---|---|---|
| Prometheus Alertmanager | Alert grouping, routing, silencing and webhook integration | Primarily designed around Prometheus alerts |
| Grafana Alerting | Unified alerting interface for multiple Grafana data sources | Requires management of Grafana alert rules and notification policies |
| Zabbix Alerting | Built-in alert configuration and notifications | Most suitable when using Zabbix as the primary monitoring platform |

### 5.2 Selected Technology: Prometheus Alertmanager

Prometheus will evaluate infrastructure and application metrics against defined alerting rules.

Alertmanager will receive alerts, apply notification routing and forward selected events to the SOAR application through HTTP webhooks.

Log-derived alerts will be handled through a defined integration path from Loki or Grafana to the SOAR system.

### 5.3 Justification

Alertmanager integrates directly with Prometheus and provides the notification routing required for event-driven automation.

Webhook support allows alerts to be delivered to the Python SOAR application without requiring a commercial integration platform.

The separation between monitoring and response processing also allows alert rules to be maintained independently from SOAR logic.

Grafana Alerting remains a suitable option for evaluating Loki log queries. The final technical design will specify the chosen log-alerting path to avoid duplicate alert processing.

---

## 6. Security Orchestration, Automation and Response

### 6.1 Evaluated Technologies

| Technology | Advantages | Disadvantages |
|---|---|---|
| Python + FastAPI | Full control over event processing, custom rules, API integration and automated testing | Requires development and maintenance of security logic |
| Shuffle SOAR | Existing workflow automation platform, visual playbooks and integrations | Additional platform components and operational overhead |
| TheHive + Cortex | Incident management and security analysis integrations | More complex deployment and broader incident response functionality than required |

### 6.2 Selected Technology: Python and FastAPI

A custom SOAR application will be developed using Python and FastAPI.

The application will provide:

- HTTP endpoint for receiving security alerts.
- Event validation and classification.
- Rule evaluation based on event characteristics.
- Automated response execution.
- PostgreSQL incident storage.
- Error handling and execution logging.
- Prometheus-compatible performance metrics.

### 6.3 Justification

The assignment requires an event listener, rule-processing logic and at least two distinct automated response actions.

A custom Python application provides direct control over these functions and makes the processing logic independently testable.

FastAPI provides an API framework suitable for receiving webhook events and exposing operational endpoints.

The first automated response actions will include:

1. Creating an incident record and sending a notification.
2. Blocking a simulated malicious source IP through a controlled firewall integration.

The implementation will restrict potentially disruptive security responses to authorized demonstration environments.

Shuffle provides visual workflow automation and could reduce custom development work. However, implementing the SOAR logic directly provides greater control over the event model, rule evaluation and monitoring instrumentation.

TheHive and Cortex provide broader incident investigation and analysis capabilities but introduce more functionality and infrastructure complexity than necessary.

### 6.4 Limitations

The custom SOAR application will require secure API authentication, input validation, error handling and testing.

It will not provide the complete functionality of an enterprise SOAR platform.

Its initial scope will focus on selected security events and predefined automated response actions.

---

## 7. Database and Data Storage

### 7.1 Evaluated Technologies

| Technology | Advantages | Disadvantages |
|---|---|---|
| PostgreSQL | Relational data model, transactions, indexing, JSON support and reliable persistence | Requires database administration, backups and storage management |
| MySQL | Mature relational database, widely supported and suitable for structured records | Some advanced data handling differs from PostgreSQL |
| SQLite | Lightweight, simple deployment and minimal administration | Less suitable for concurrent writes and expansion into multiple SOAR processing instances |

### 7.2 Selected Technology: PostgreSQL

PostgreSQL will store structured SOAR data, including:

- Security incidents.
- Event metadata.
- Rule matches.
- Automated response results.
- Processing status.
- Action execution timestamps.

PostgreSQL will run as a container with persistent storage on the SOAR server.

### 7.3 Justification

SOAR requires reliable storage of security events and response execution records.

PostgreSQL provides transactional consistency and supports relationships between incidents, rules and executed actions.

Its JSON capabilities also allow event-specific information to be stored without requiring a separate schema for every event type.

SQLite would reduce deployment complexity but would provide fewer options for expanding the application into multiple processing instances.

MySQL is a suitable alternative. PostgreSQL was selected for its combination of structured relational storage and flexible event metadata handling.

Prometheus and Loki will maintain their own metrics and log data. PostgreSQL will not replace either monitoring backend.

### 7.4 Limitations

The database requires persistent storage, backup automation and recovery testing.

A single PostgreSQL container does not provide database high availability. Recovery procedures will therefore be included in the infrastructure design.

---

## 8. Containerization

### 8.1 Evaluated Technologies

| Technology | Advantages | Disadvantages |
|---|---|---|
| Docker Compose | Simple multi-container deployment, readable configuration and portable development environments | Limited native orchestration and high-availability capabilities |
| Kubernetes | Advanced scheduling, service discovery, self-healing and scaling | Higher implementation and maintenance complexity |
| Podman | Daemonless container execution, rootless capabilities and compatibility with OCI images | Additional considerations for Compose compatibility and service management |

### 8.2 Selected Technology: Docker Compose

Docker Compose will deploy and manage the monitoring and SOAR application services.

Container configurations, networking, volumes and environment variables will be defined in version-controlled files.

### 8.3 Justification

The initial infrastructure contains a limited number of application services deployed across two Linux servers.

Docker Compose provides sufficient functionality for defining and operating these services without introducing an orchestration control plane.

It also supports the creation of a portable demonstration environment.

Kubernetes would offer stronger orchestration capabilities but would increase infrastructure resource requirements and operational complexity.

The project will address service recovery through container restart policies, persistent storage, monitoring and documented recovery procedures.

### 8.4 Limitations

Docker Compose does not automatically provide high availability across multiple hosts.

Host failure recovery and service restoration must be implemented through the surrounding infrastructure and operational procedures.

---

## 9. Hybrid Connectivity

### 9.1 Evaluated Technologies

| Technology | Advantages | Disadvantages |
|---|---|---|
| WireGuard | Lightweight, modern encryption, relatively simple configuration and no managed VPN service fee | Requires gateway configuration, routing and manual availability management |
| AWS Site-to-Site VPN | Managed VPN infrastructure and integration with AWS networking | Additional hourly charges and customer gateway requirements |
| OpenVPN | Flexible VPN configuration, widely supported and mature | More complex configuration and potentially higher operational overhead |

### 9.2 Selected Technology: WireGuard

WireGuard will provide encrypted connectivity between the on-premises environment and AWS.

The VPN will connect authorized private network ranges and allow monitoring traffic to travel between environments.

Routing and firewall rules will restrict communication to approved services.

### 9.3 Justification

WireGuard provides the encrypted communication required for the hybrid environment without requiring a paid AWS-managed VPN connection.

Its configuration can be automated through Ansible and included in the infrastructure documentation.

The project requires a controlled connection between a limited number of environments, making WireGuard suitable for the expected topology.

AWS Site-to-Site VPN would provide managed connectivity but would introduce recurring connection charges and additional network configuration.

OpenVPN offers comparable connectivity features but introduces more configuration options than required for this deployment.

### 9.4 Limitations

WireGuard does not automatically configure network routing or DNS.

The technical design must specify the VPN gateway, allowed network ranges, routes, firewall rules and DNS forwarding.

The VPN gateway may become a single point of failure. Connectivity loss and recovery will be included in the resilience tests.

---

## 10. Internal DNS

### 10.1 Evaluated Technologies

| Technology | Advantages | Disadvantages |
|---|---|---|
| Route 53 Private Hosted Zones | Integration with AWS VPC, private DNS records and infrastructure automation | Hybrid clients require a DNS forwarding or resolver path |
| BIND9 | Full control over DNS zones, forwarding and internal name resolution | Requires maintaining a separate DNS service |
| dnsmasq | Lightweight DNS forwarding and caching | Less suitable for complex DNS administration |

### 10.2 Selected Technology: Route 53 Private DNS

Route 53 Private Hosted Zones will provide internal DNS records for AWS-hosted services.

A DNS forwarding component will allow authorized on-premises systems to resolve the necessary private service names.

### 10.3 Justification

Route 53 integrates with AWS VPC networking and supports automated DNS configuration through Terraform.

Using private DNS records allows applications to communicate through service names instead of hardcoded IP addresses.

BIND9 and dnsmasq are possible solutions for forwarding DNS queries from the simulated on-premises environment.

The specific forwarding implementation will be determined in the technical network design.

### 10.4 Limitations

Private Hosted Zones do not automatically provide DNS resolution to external networks.

Hybrid name resolution requires additional configuration. AWS Route 53 Resolver endpoints are one option, while a self-managed forwarding service may reduce recurring costs.

---

## 11. Infrastructure as Code

### 11.1 Evaluated Technologies

| Technology | Advantages | Disadvantages |
|---|---|---|
| Terraform | Declarative configuration, multi-provider support, reusable modules and infrastructure state management | Requires state protection and provider management |
| AWS CloudFormation | Native integration with AWS and managed stack operations | Primarily focused on AWS resources |
| Pulumi | Infrastructure defined using programming languages, reusable application logic | Adds programming-language dependencies and a different infrastructure workflow |

### 11.2 Selected Technology: Terraform

Terraform will provision AWS infrastructure, including:

- VPC and subnets.
- Routing components.
- Security Groups.
- EC2 instances.
- Storage resources.
- Private DNS records.
- Required access policies and supporting resources.

### 11.3 Justification

Terraform provides a consistent approach to infrastructure provisioning through declarative configuration.

Its provider ecosystem supports multiple infrastructure platforms and reduces dependence on one cloud provider's infrastructure definition format.

Infrastructure changes can be reviewed through Terraform plans before deployment.

CloudFormation is a suitable AWS-native alternative but offers less flexibility for extending the same provisioning approach beyond AWS.

Pulumi provides powerful programming-language integration but introduces additional development and dependency management considerations.

### 11.4 Limitations

Terraform state can contain sensitive information and must be stored securely.

The project will define a controlled state storage and locking strategy.

---

## 12. Configuration Management and Automated Updates

### 12.1 Evaluated Technologies

| Technology | Advantages | Disadvantages |
|---|---|---|
| Ansible | Agentless SSH-based automation, YAML playbooks and repeatable multi-node configuration | Requires reliable management connectivity and careful privilege handling |
| Puppet | Continuous configuration enforcement and centralized infrastructure management | Requires additional agent and server management |
| Salt | Remote execution and configuration management across large environments | More complex architecture for a small deployment |

### 12.2 Selected Technology: Ansible

Ansible will configure Linux servers and automate software updates.

Playbooks will be developed for:

- Operating system configuration.
- Installation of required packages.
- Docker installation.
- Monitoring agent configuration.
- WireGuard configuration.
- Security settings.
- Software updates.
- Service health verification.

### 12.3 Justification

Ansible supports agentless remote management and can apply consistent configurations to multiple Linux systems.

Its YAML-based playbooks are suitable for version control and CI/CD integration.

Ansible also directly supports the requirement for centrally managed updates without separate manual actions on each system.

Puppet and Salt are capable alternatives, particularly for larger environments. However, Ansible offers a simpler management model for the number of hosts in this project.

### 12.4 Limitations

Ansible requires network access and appropriate permissions on managed systems.

Update workflows must handle failures, reboots and service availability checks.

---

## 13. CI/CD and Version Control

### 13.1 Evaluated Technologies

| Technology | Advantages | Disadvantages |
|---|---|---|
| GitHub Actions | Native GitHub integration, YAML workflows, self-hosted runners and reusable actions | Requires secure runner configuration and secret management |
| GitLab CI/CD | Integrated repository, pipeline and runner management | Requires adopting a separate platform or hosting environment |
| Jenkins | Highly customizable pipelines and extensive plugins | Requires maintaining a dedicated automation server and plugins |

### 13.2 Selected Technology: GitHub Actions

GitHub will host the source code and infrastructure configuration.

GitHub Actions will execute automated workflows for:

- Python unit testing.
- Terraform formatting and validation.
- Infrastructure change planning.
- SOAR container builds.
- SOAR application deployment.
- Ansible configuration and update execution.

A self-hosted runner will execute the required pipelines locally.

### 13.3 Justification

GitHub Actions integrates repository management with automation workflows.

It supports self-hosted runners, satisfying the requirement to execute pipelines from a local environment.

Infrastructure and application changes can be tested before deployment, reducing the risk of introducing invalid configurations.

GitLab CI/CD provides comparable capabilities, while Jenkins offers extensive customization. GitHub Actions was selected to avoid maintaining an additional CI/CD server.

### 13.4 Limitations

The local runner must be securely configured and have access only to the credentials required for its tasks.

Deployment workflows must protect sensitive information and restrict which repository events are permitted to trigger infrastructure changes.

---

## 14. Operating System

### 14.1 Evaluated Technologies

| Technology | Advantages | Disadvantages |
|---|---|---|
| Ubuntu Server LTS | Extensive documentation, broad package support and compatibility with selected tools | Requires regular security and package updates |
| Debian Stable | Stable package management, lightweight installation and conservative updates | Some software versions may be older |
| Red Hat Enterprise Linux | Enterprise support and long-term maintenance options | Subscription and licensing considerations |

### 14.2 Selected Technology: Ubuntu Server LTS

Ubuntu Server LTS will be used for the AWS instances and simulated on-premises Linux servers.

### 14.3 Justification

Ubuntu Server provides broad compatibility with Docker, Python, Ansible, WireGuard and the selected monitoring technologies.

Using a consistent operating system reduces differences in package management and configuration across the infrastructure.

The LTS release model supports predictable maintenance and security updates.

### 14.4 Limitations

Ubuntu Server requires ongoing package management, security hardening and service monitoring.

These activities will be automated using Ansible wherever practical.

---

## 15. Testing Technologies

### 15.1 Evaluated Technologies

| Technology | Advantages | Disadvantages |
|---|---|---|
| Pytest | Python test automation, reusable fixtures and CI/CD integration | Primarily focused on Python application testing |
| Robot Framework | Keyword-driven acceptance testing and readable test reports | Additional framework configuration |
| Bash / PowerShell Scripts | Direct system verification and command-line integration | Requires custom result handling and reporting |

### 15.2 Selected Technologies: Pytest and System Test Scripts

Pytest will validate SOAR application logic, event processing and automated response behavior.

Shell and Python scripts will test infrastructure integration, network connectivity, monitoring and system updates.

### 15.3 Justification

The system requires both application-level and infrastructure-level validation.

Pytest provides structured testing for the Python SOAR application, while system scripts can verify network and operational requirements that are outside the application's scope.

Both approaches can be integrated into GitHub Actions.

---

## 16. Final Technology Selection

The technologies selected for implementation are summarized below.

| Infrastructure Component | Selected Technology | Main Reason |
|---|---|---|
| Cloud Hosting | AWS EC2 | Flexible virtual machine hosting and network control |
| Network Isolation | AWS VPC and Security Groups | Private network segmentation |
| Hybrid VPN | WireGuard | Encrypted connectivity with limited additional service cost |
| Internal DNS | Route 53 Private DNS | Integration with AWS private networking |
| Operating System | Ubuntu Server LTS | Compatibility and maintainability |
| Containers | Docker Compose | Simple and portable multi-service deployment |
| Metrics | Prometheus | Time-series metrics and application instrumentation |
| Dashboards | Grafana | Centralized visualization |
| Logging | Loki | Integrated, label-based log aggregation |
| Telemetry Collection | Grafana Alloy | Unified metrics and log collection |
| Alert Routing | Alertmanager | Webhook integration and alert management |
| SOAR Application | Python / FastAPI | Customizable event-driven security automation |
| Structured Data | PostgreSQL | Reliable incident and response records |
| Infrastructure Provisioning | Terraform | Repeatable declarative provisioning |
| Configuration Management | Ansible | Multi-node configuration and updates |
| CI/CD | GitHub Actions | Automated testing and deployment |
| Testing | Pytest | Automated application validation |

---

## 17. Architectural Trade-offs

The selected architecture prioritizes maintainability, transparency, automation and the ability to reproduce deployments.

Several trade-offs have been accepted.

**Self-hosted monitoring instead of managed monitoring**

This increases maintenance responsibilities but provides control over metrics collection, logging, retention and system configuration.

**Docker Compose instead of Kubernetes**

This reduces infrastructure complexity and resource requirements but does not provide automatic multi-host orchestration or high availability.

**Custom SOAR instead of an existing SOAR platform**

This requires additional development and testing but provides control over rule processing, response logic and application instrumentation.

**WireGuard instead of managed VPN services**

This reduces managed service costs but requires manual gateway administration and recovery planning.

**PostgreSQL in a container instead of managed database hosting**

This reduces reliance on managed cloud services but requires implementing and testing database backups and restoration.

These trade-offs will be considered during resilience and operational testing.

---

## 18. Conclusion

The selected technology stack provides the components required to implement the hybrid cloud infrastructure for Innovatech Solutions.

AWS will provide the cloud hosting and networking foundation, while Grafana, Prometheus and Loki will deliver centralized observability.

Python and FastAPI will provide event-driven security automation, supported by PostgreSQL for incident storage.

Terraform, Ansible and GitHub Actions will provide repeatable infrastructure provisioning, configuration management and automated deployment.

The architecture supports the required separation between monitored systems and SOAR, centralized security event processing, multi-node updates and operational monitoring.

The detailed network topology, hardware sizing, backup strategy and service configuration will be specified in the Technical Design.

---

## 19. References

The following sources were used to evaluate the technologies.

### Project Documentation

- Innovatech Solutions — Business Context, CS2-MA-NCA.
- Innovatech Solutions — Core Assignment, CS2-MA-NCA.
- Innovatech Solutions — Requirements, CS2-MA-NCA.

### Technical Documentation

- AWS EC2: https://docs.aws.amazon.com/ec2/
- AWS VPC: https://docs.aws.amazon.com/vpc/
- AWS VPN Pricing: https://aws.amazon.com/vpn/pricing/
- Grafana: https://grafana.com/docs/grafana/latest/
- Prometheus: https://prometheus.io/docs/
- Grafana Loki: https://grafana.com/docs/loki/latest/
- Grafana Alloy: https://grafana.com/docs/alloy/latest/
- Alertmanager: https://prometheus.io/docs/alerting/latest/alertmanager/
- Zabbix: https://www.zabbix.com/documentation/current/en/manual
- OpenSearch: https://docs.opensearch.org/
- FastAPI: https://fastapi.tiangolo.com/
- PostgreSQL: https://www.postgresql.org/docs/
- Docker Compose: https://docs.docker.com/compose/
- WireGuard: https://www.wireguard.com/
- Terraform: https://developer.hashicorp.com/terraform/docs
- Ansible: https://docs.ansible.com/
- GitHub Actions: https://docs.github.com/en/actions
- Pytest: https://docs.pytest.org/
