# Technology Choices

## 1. Introduction

For this project, I needed technologies that could connect AWS with an on-premises environment, provide centralized monitoring, detect security events and automate infrastructure management.

Since this is a university project, I also wanted to avoid unnecessary infrastructure costs and complicated tools that wouldn't provide much benefit for the size of the environment.

The main things I considered when choosing technologies were:

- How well they fit the project requirements.
- How easily they work together.
- Security and network access.
- Infrastructure and licensing costs.
- How difficult they are to configure and maintain.
- Automation and Infrastructure as Code support.
- How easily the environment can be extended later.

Some of my original technology choices changed during implementation. For example, I initially considered FastAPI, PostgreSQL and Route 53 for SOAR and DNS, but ended up using Flask, SQLite/JSONL and dnsmasq because they were simpler for the actual implementation.

## 2. Cloud Infrastructure

### 2.1 Technologies Compared

I compared three infrastructure platforms:

| Technology | Advantages | Disadvantages |
|---|---|---|
| AWS | EC2, VPC, security groups, IAM and Terraform support | Running costs and cloud-specific configuration |
| Microsoft Azure | Virtual machines, networking and hybrid infrastructure services | Different tools and configuration requirements |
| Proxmox | Full control over virtual machines and local infrastructure | Requires physical hosting and maintenance |

### 2.2 Why I Chose AWS

I chose AWS because it provides the networking and compute services needed for the hybrid infrastructure.

The main AWS services used are:

- EC2 for virtual machines.
- VPC for private networking.
- Security groups for access control.
- IAM for managing permissions.
- Systems Manager for remote administration.
- S3 for Terraform state and deployment artifacts.

AWS also works well with Terraform, which allows me to define the infrastructure through configuration files instead of creating resources manually.

### 2.3 Implementation

The AWS environment uses three EC2 instances:

| Server | Instance Type | Purpose |
|---|---|---|
| Monitoring | t3.medium | Grafana, Prometheus, Loki, Alloy and Alertmanager |
| SOAR | t3.small | Python security automation application |
| Gateway | t3.micro | WireGuard VPN, routing and NAT |

All three instances run Ubuntu Server.

The monitoring and SOAR servers use private IP addresses, while the gateway provides access to the internet and the on-premises environment.

### 2.4 Limitations

Using EC2 means I am responsible for operating-system updates, service configuration, monitoring and recovery.

AWS resources also cost money while running. To reduce costs, I use relatively small instances and stop the environment when I'm not working on it.

The gateway is also a single point of failure because both private AWS connectivity and the hybrid VPN depend on it.

## 3. On-Premises Virtualization

### 3.1 Technologies Compared

For the on-premises environment, I considered VirtualBox, VMware Workstation and Proxmox.

| Technology | Advantages | Disadvantages |
|---|---|---|
| VirtualBox | Free, straightforward VM management and internal networking | Limited enterprise virtualization features |
| VMware Workstation | Good VM management and networking capabilities | Additional product-specific tooling and setup |
| Proxmox | Suitable for larger environments and server virtualization | Requires a dedicated host or more complicated setup |

### 3.2 Why I Chose VirtualBox

I chose VirtualBox because I could run the on-premises environment directly on my Windows computer without needing additional hardware.

It also supports internal networks and multiple virtual network adapters, which are useful for simulating a real on-premises infrastructure.

### 3.3 Implementation

The on-premises environment contains three Ubuntu VMs:

| VM | Private IP | Purpose |
|---|---|---|
| cs2-onprem-gateway | 10.30.0.1 | Network gateway, WireGuard and DNS |
| cs2-onprem-linux | 10.30.0.10 | Linux monitoring target and Ansible control node |
| cs2-onprem-security | 10.30.0.20 | Monitored security VM and Ansible target |

This setup allows me to generate events locally and forward monitoring data to AWS through the VPN.

One limitation is that the entire on-premises environment depends on my Windows computer being powered on.

## 4. Hybrid VPN

### 4.1 Technologies Compared

I compared WireGuard, OpenVPN and AWS Site-to-Site VPN.

| Technology | Advantages | Disadvantages |
|---|---|---|
| WireGuard | Lightweight, modern encryption and relatively simple configuration | Routing and firewall rules must be managed manually |
| OpenVPN | Flexible and widely supported | More configuration and additional operational complexity |
| AWS Site-to-Site VPN | Managed AWS integration | Additional service costs and configuration requirements |

### 4.2 Why I Chose WireGuard

I chose WireGuard because it provides an encrypted connection without needing a paid managed VPN service.

The configuration is relatively simple compared to some alternatives, and it works on both AWS EC2 and Ubuntu VMs.

WireGuard handles the encrypted tunnel, while routing and firewall configuration control which machines can communicate.

### 4.3 Implementation

The hybrid environment uses these networks:

| Network | Address Range |
|---|---|
| AWS VPC | 10.20.0.0/16 |
| On-premises | 10.30.0.0/24 |
| WireGuard tunnel | 10.40.0.0/30 |

The tunnel connects the AWS gateway at `10.40.0.1` with the on-premises gateway at `10.40.0.2`.

The AWS gateway accepts WireGuard connections on UDP port 51820.

I verified the VPN using `wg show`, which displayed an active peer, recent handshake and transferred data.

I also tested an actual private connection from the on-premises gateway to Grafana in AWS.

**Evidence:**

- `docs/evidence/network/03-wireguard-vpn.png`
- `docs/evidence/network/04-private-connectivity.png`

### 4.4 Limitations

WireGuard doesn't automatically configure network routes, firewall rules or DNS.

I had to configure these separately.

If either gateway becomes unavailable, communication between AWS and the on-premises environment is interrupted.

## 5. Internal DNS

### 5.1 Technologies Compared

I considered Route 53 Private Hosted Zones, BIND9 and dnsmasq.

| Technology | Advantages | Disadvantages |
|---|---|---|
| Route 53 Private DNS | Integrates with AWS VPC and Terraform | Hybrid DNS resolution requires additional configuration |
| BIND9 | Full control over DNS zones and records | More complicated than necessary for a few internal records |
| dnsmasq | Lightweight, simple configuration and low resource usage | Not intended for complex enterprise DNS environments |

### 5.2 Why I Chose dnsmasq

My original design considered Route 53, but I eventually chose dnsmasq.

The project only needs a small number of internal DNS records, so adding AWS-managed DNS resources and hybrid resolver infrastructure would introduce unnecessary complexity.

The on-premises gateway was already running Ubuntu and handling internal network traffic, making it a convenient location for the DNS service.

### 5.3 Implementation

dnsmasq runs on `cs2-onprem-gateway` and listens on `10.30.0.1`.

I configured these records:

| DNS Name | IP Address |
|---|---|
| monitoring.innovatech.internal | 10.20.10.10 |
| soar.innovatech.internal | 10.20.20.10 |
| gateway.innovatech.internal | 10.30.0.1 |

I also added nftables rules allowing TCP and UDP port 53 from the on-premises subnet.

The DNS records were tested from the gateway and another Linux VM.

**Evidence:**

- `docs/evidence/network/05-private-dns-gateway.png`
- `docs/evidence/network/05-private-dns-linux.png`

### 5.4 Limitations

The current setup has been tested through direct DNS queries.

I haven't configured every machine to use dnsmasq as its default DNS resolver, and AWS-side resolution hasn't been tested.

## 6. Monitoring and Observability

### 6.1 Technologies Compared

I compared three monitoring platforms.

| Technology | Advantages | Disadvantages |
|---|---|---|
| Grafana, Prometheus and Loki | Flexible metrics, logging, dashboards and integrations | Several separate services need to be maintained |
| Zabbix | Complete infrastructure monitoring with built-in alerting | Less flexible for my custom log-analysis and SOAR workflow |
| OpenSearch | Advanced searching and analysis of logs | Higher resource requirements and additional setup complexity |

### 6.2 Why I Chose the Grafana Stack

I chose Grafana, Prometheus and Loki because they provide the monitoring features I need while keeping the individual components separate.

Each tool has a specific responsibility:

- Prometheus collects and stores metrics.
- Loki stores and queries logs.
- Grafana displays dashboards and allows log investigation.
- Alloy collects and forwards telemetry.
- Alertmanager handles Prometheus alerts.

This separation also makes troubleshooting easier because I can check which specific part of the monitoring system is causing a problem.

### 6.3 Implementation

The monitoring services run through Docker Compose on the AWS Monitoring EC2 instance.

I created three main Grafana dashboards:

1. Infrastructure Overview.
2. Security Log Monitoring.
3. SOAR Monitoring.

These dashboards display server availability, CPU and memory usage, disk utilization, firewall activity, system logs and SOAR processing metrics.

I also configured three Prometheus alert rules:

- `ServerDown`
- `HighCPUUsage`
- `HighMemoryUsage`

The rules are defined in configuration files rather than being manually created in the Grafana interface.

### 6.4 Testing

I verified that Prometheus was collecting metrics from AWS and on-premises systems.

I also checked Loki using Grafana Explore and confirmed that logs from both environments appeared in the same query.

The monitoring stack was tested during a controlled failure simulation. I stopped Grafana while keeping the other containers running and then restarted it successfully.

**Evidence:**

- `docs/evidence/monitoring/06-infrastructure-overview-A.png`
- `docs/evidence/monitoring/06-infrastructure-overview-B.png`
- `docs/evidence/monitoring/09-loki-firewall-query.png`
- `docs/evidence/monitoring/10-multiple-log-sources.png`
- `docs/evidence/monitoring/11-monitoring-alerting.png`
- `docs/evidence/resilience/23-monitoring-component-recovery.png`

### 6.5 Limitations

The monitoring services currently run on one EC2 instance.

This means that losing the monitoring server would temporarily make the dashboards and centralized monitoring services unavailable.

The setup also requires managing storage, retention settings and container updates.

## 7. Log Collection

### 7.1 Technologies Compared

I compared Grafana Alloy, Fluent Bit and OpenTelemetry Collector.

| Technology | Advantages | Disadvantages |
|---|---|---|
| Grafana Alloy | Supports metrics and logs and integrates with Grafana tools | Requires learning Alloy configuration |
| Fluent Bit | Lightweight and efficient log forwarding | More focused on logs than overall telemetry collection |
| OpenTelemetry Collector | Flexible and supports standard telemetry formats | May need extra components or configurations for some log sources |

### 7.2 Why I Chose Grafana Alloy

I chose Alloy because it works directly with Loki and Prometheus.

It can collect system and security logs and forward them to the monitoring server without requiring a separate collection tool for each log type.

### 7.3 Implementation

The configured log sources include:

| Job | Log Source |
|---|---|
| aws-monitoring | AWS monitoring system logs |
| aws-monitoring-auth | AWS authentication logs |
| onprem-firewall | On-premises gateway firewall logs |

Alloy reads the relevant logs and forwards them to Loki.

The on-premises firewall logs travel through the WireGuard VPN before reaching the AWS Monitoring server.

During testing, Loki successfully received firewall events generated by nftables.

### 7.4 Limitations

If the VPN becomes unavailable, log forwarding from the on-premises environment can be interrupted.

The collection process also depends on log file permissions and correct Alloy configuration.

## 8. Security Automation (SOAR)

### 8.1 Technologies Compared

I researched custom Python development, Shuffle SOAR, and TheHive with Cortex.

| Technology | Advantages | Disadvantages |
|---|---|---|
| Custom Python SOAR | Full control over rules, event processing and automated actions | Requires implementing and testing the logic myself |
| Shuffle | Visual workflows and existing integrations | Additional services and configuration |
| TheHive and Cortex | Incident investigation and analysis features | More complicated than necessary for this project's requirements |

### 8.2 Why I Chose Python

I chose to build the SOAR application myself because the assignment requires implementing event handling, security rules and automated responses.

Using Python makes it possible to demonstrate exactly how the system works rather than only configuring an existing SOAR platform.

It also allows me to test individual components separately.

### 8.3 Why I Used Flask Instead of FastAPI

My original design proposed FastAPI, but the final implementation uses Flask.

Both frameworks can handle HTTP requests and work with Python applications.

I chose Flask because the SOAR API is relatively small and only needs a few endpoints.

Flask provides enough functionality for request validation, authentication, routing and JSON responses without introducing additional components that I don't need.

The deployed application uses Gunicorn as the application server and systemd to manage the service.

### 8.4 SOAR Components

The main SOAR modules are:

| Module | Responsibility |
|---|---|
| `main.py` | Flask API and request handling |
| `rules.py` | Security rule evaluation |
| `actions.py` | Response action execution |
| `dedup.py` | Duplicate alert detection |
| `metrics.py` | Prometheus metrics |
| `log_analyzer.py` | Firewall log filtering and security pattern detection |
| `log_response.py` | Converts detected findings into SOAR alerts |

The application exposes:

- `POST /alerts`
- `GET /health`
- `GET /metrics`

Incoming alerts require an authentication token.

The application checks the alert information, evaluates security rules, prevents duplicate processing and executes the selected actions.

### 8.5 Response Actions

The implemented actions include:

- Recording an incident.
- Preparing an operator notification.
- Simulating IP containment.
- Simulating service containment.

I decided to keep containment simulated to avoid accidentally disrupting my infrastructure during testing.

The actions include validation and restrictions to prevent inappropriate targets from being selected.

### 8.6 Firewall Log Analysis

I developed a Python analyzer that queries Loki for blocked firewall connections.

The analyzer filters irrelevant events, extracts TCP connection information and checks for repeated connections targeting different ports.

For the controlled test, I generated 12 blocked TCP attempts across four ports.

The analyzer identified one possible port-scanning event.

That finding was processed by SOAR, which recorded the incident and prepared an operator notification.

The same alert was later submitted again and recognized as a duplicate.

### 8.7 Local SOAR Execution Viewer

I also created a small local Flask application that displays SOAR analysis and execution results.

The viewer runs on my Windows computer rather than AWS.

It allows me to inspect the detected security finding, the recorded response summary and the actual Python functions involved.

The viewer reads source code directly from the local project files, so I can demonstrate how the functions work without copying the code into a separate presentation.

### 8.8 Limitations

The SOAR application focuses on a limited set of security events.

It doesn't provide all the investigation and response capabilities of a commercial SOAR platform.

Notifications are currently recorded and prepared rather than delivered through an external messaging service.

Containment actions are simulated and do not automatically block IP addresses on the gateway.

The local viewer displays imported execution results and does not provide live remote monitoring.

## 9. Incident Storage

### 9.1 Technologies Compared

Initially, I considered PostgreSQL, MySQL and SQLite.

| Technology | Advantages | Disadvantages |
|---|---|---|
| PostgreSQL | Strong relational features, transactions and scalability | Requires a separate database service and maintenance |
| MySQL | Reliable and widely supported | Requires database administration and deployment |
| SQLite | Lightweight, file-based and simple to integrate with Python | Less suitable for many concurrent writers or distributed application instances |

### 9.2 Why I Used SQLite and JSONL

The original design selected PostgreSQL, but I later decided that a separate database server wasn't necessary for the current SOAR implementation.

Instead, I use:

- SQLite for processed-alert fingerprints and deduplication.
- JSONL files for incident records, event history and notification records.

This is simpler to manage and doesn't require running a separate database container.

SQLite also provides uniqueness constraints that are useful for duplicate detection.

JSONL makes the recorded actions easy to inspect during development and debugging.

### 9.3 Implementation

The SOAR application stores processed fingerprints in a SQLite database.

When an alert arrives, the application checks whether the fingerprint has already been processed.

If the alert is a duplicate, it avoids repeating the associated response actions.

Incident and action records are written to JSONL files in the configured SOAR data directory.

### 9.4 Limitations

This storage approach is suitable for the current single-instance SOAR application.

It would be less suitable for a larger deployment with multiple SOAR instances writing to shared storage.

A complete backup and restoration test is also still needed.

## 10. Containerization and Service Management

### 10.1 Technologies Compared

I compared Docker Compose, Kubernetes and running applications directly through systemd.

| Technology | Advantages | Disadvantages |
|---|---|---|
| Docker Compose | Good for managing multiple related containers | Does not provide multi-host high availability |
| Kubernetes | Advanced scheduling, scaling and recovery | More complicated and resource-intensive |
| systemd | Simple management of services on Linux | Does not provide container isolation or orchestration |

### 10.2 Why I Used Docker Compose

Docker Compose is used for the monitoring environment because it consists of several services that need to run together.

The monitoring stack includes:

- Grafana.
- Prometheus.
- Loki.
- Alloy.
- Alertmanager.

Compose allows these services to be started, stopped and inspected together.

It also makes it possible to restart one component without restarting the rest of the stack.

### 10.3 Why I Used systemd for SOAR

The SOAR application is a relatively small Python service.

Instead of creating a separate Docker image for it, I decided to run it using Gunicorn and systemd.

This makes it easy to manage the application using standard Linux commands.

For example:

```bash
sudo systemctl status innovatech-soar
sudo systemctl restart innovatech-soar
sudo journalctl -u innovatech-soar --no-pager
```

The deployment process updates the application files and restarts the service.

### 10.4 Limitations

Docker Compose doesn't automatically provide high availability across multiple servers.

Similarly, systemd manages processes on one machine but doesn't provide multi-server failover.

For this project, documented recovery procedures are more suitable than adding a full orchestration platform.

## 11. Infrastructure as Code

### 11.1 Technologies Compared

I compared Terraform, CloudFormation and Pulumi.

| Technology | Advantages | Disadvantages |
|---|---|---|
| Terraform | Declarative configuration, version control and multi-cloud support | Requires state management |
| CloudFormation | Native AWS integration | Mainly designed for AWS resources |
| Pulumi | Infrastructure written using programming languages | Additional language dependencies and complexity |

### 11.2 Why I Chose Terraform

I chose Terraform because it allows AWS resources to be defined in configuration files.

Instead of manually creating the VPC, EC2 instances and security groups, I can manage them as code.

Terraform also provides a planning stage where I can review infrastructure changes before applying them.

### 11.3 Implementation

Terraform manages the main AWS infrastructure, including networking, EC2, security groups and IAM resources.

The Terraform state is stored in Amazon S3 with access restrictions and state locking.

The GitHub Actions Infrastructure Checks workflow runs formatting and validation checks.

Actual infrastructure changes are reviewed and applied separately rather than automatically applying every commit.

### 11.4 Limitations

Terraform state must be protected because it can contain sensitive resource information.

Another limitation is configuration drift. Manual changes made directly through AWS may not be reflected in Terraform.

For example, security group changes made during testing should also be added to Terraform to prevent future plans from reverting them.

## 12. Configuration Management and OS Updates

### 12.1 Technologies Compared

I compared Ansible, Puppet and Salt.

| Technology | Advantages | Disadvantages |
|---|---|---|
| Ansible | Agentless management, YAML playbooks and straightforward multi-node updates | Requires access to managed machines |
| Puppet | Continuous configuration enforcement | Requires additional infrastructure and configuration |
| Salt | Remote execution and large-scale management features | More complex than needed for a small environment |

### 12.2 Why I Chose Ansible

I chose Ansible because it allows me to manage multiple Linux machines from one control node.

Playbooks are written in YAML and can be stored in Git.

The managed machines don't need a dedicated Ansible agent.

### 12.3 Implementation

The Ansible control node is `cs2-onprem-linux`.

The update playbook manages:

- `cs2-onprem-linux`
- `cs2-onprem-security`

It refreshes APT package information, installs available updates and checks whether a reboot is required.

The playbook uses `serial: 1` to avoid updating both machines simultaneously.

I successfully executed the update workflow against both systems.

### 12.4 Unattended Upgrades

Alongside Ansible, I use Ubuntu unattended-upgrades.

This is enabled on the two AWS application servers and all three on-premises VMs.

I verified both the configuration and update execution logs.

Unattended-upgrades handles automatic updates independently, while Ansible provides centralized and repeatable updates when I choose to run the playbook.

### 12.5 Limitations

The centralized Ansible playbook currently covers two on-premises systems.

The gateway and AWS servers are not part of that inventory.

Reboots are reported but not automatically performed by the Ansible playbook.

The playbook is manually started from the control node rather than scheduled.

**Evidence:**

- `docs/evidence/updates/33-ansible-multi-server-update.png`
- `docs/evidence/updates/24-automated-system-updates.png`
- `docs/evidence/updates/26-soar-update-execution.png`
- `docs/evidence/updates/30-onprem-linux-update-execution.png`

## 13. CI/CD and Version Control

### 13.1 Technologies Compared

I compared GitHub Actions, GitLab CI/CD and Jenkins.

| Technology | Advantages | Disadvantages |
|---|---|---|
| GitHub Actions | Integrated with GitHub, YAML workflows and self-hosted runners | Runner and credential management are required |
| GitLab CI/CD | Built-in repository and automation features | Would require moving to another platform |
| Jenkins | Flexible and highly customizable | Requires maintaining a separate CI/CD server |

### 13.2 Why I Chose GitHub Actions

I already use GitHub for source control, so GitHub Actions was a convenient choice.

It also supports self-hosted runners, which allows me to execute workflows from my Windows computer.

### 13.3 Implementation

I created three main workflows:

| Workflow | Purpose |
|---|---|
| Infrastructure Checks | Terraform formatting and validation |
| SOAR CI/CD | Python tests and application deployment |
| Monitoring CI/CD | Grafana dashboard validation and deployment |

The SOAR workflow runs Python tests before deployment.

The deployment package is uploaded to S3 and deployed to the AWS SOAR instance using Systems Manager.

The Monitoring workflow validates dashboard JSON files before deploying them to AWS.

### 13.4 Pipeline Failure Testing

I also tested whether the monitoring pipeline would prevent an invalid configuration from being deployed.

I deliberately introduced invalid JSON into a Grafana dashboard file on a test branch.

The validation job failed, and the deployment job was skipped.

This confirmed that the pipeline blocks this type of invalid change.

### 13.5 Limitations

The deployment workflows depend on the local Windows runner being available.

The runner also uses AWS SSO credentials, which can expire and require a new login.

For a production environment, the runner and deployment credentials would need a more permanent management solution.

**Evidence:**

- `docs/evidence/cicd/17-soar-cicd-success.png`
- `docs/evidence/cicd/18-monitoring-cicd-success.png`
- `docs/evidence/cicd/19-terraform-validation.png`
- `docs/evidence/cicd/20-pipeline-failure-protection.png`

## 14. Operating System

### 14.1 Technologies Compared

I considered Ubuntu Server, Debian and Red Hat Enterprise Linux.

| Technology | Advantages | Disadvantages |
|---|---|---|
| Ubuntu Server LTS | Good documentation and compatibility with project tools | Requires regular updates and maintenance |
| Debian | Stable and lightweight | Some packages may be older |
| Red Hat Enterprise Linux | Enterprise support and management features | Subscription and licensing considerations |

### 14.2 Why I Chose Ubuntu

I chose Ubuntu Server because it supports all the main technologies used in the project.

This includes Docker, Python, WireGuard, nftables, Grafana Alloy and Ansible.

Using Ubuntu across AWS and VirtualBox also makes package management and troubleshooting more consistent.

### 14.3 Maintenance

I use unattended-upgrades for automatic security and package maintenance.

I also use Ansible to manage updates on two of the on-premises machines.

The update execution logs were checked to confirm that the services were actually running and installing updates when needed.

## 15. Testing Tools

Different tools are used depending on what is being tested.

| Tool | Purpose |
|---|---|
| Python unittest and pytest | SOAR application tests |
| PowerShell | Local commands and AWS CLI operations |
| Bash | Linux configuration and service checks |
| curl | API and HTTP connectivity testing |
| dig | DNS resolution testing |
| WireGuard tools | VPN connection verification |
| nftables | Firewall configuration and inspection |
| Grafana Explore | Loki log queries |
| Docker Compose | Monitoring service management |
| GitHub Actions | Automated testing and deployment |

I use automated tests for application logic and direct system tests for networking, DNS, monitoring and recovery.

This is necessary because Python unit tests cannot verify whether the real WireGuard connection, AWS security groups or Linux firewall rules work correctly.

## 16. Final Technology Selection

| Area | Selected Technology |
|---|---|
| Cloud platform | AWS |
| Local virtualization | VirtualBox |
| Operating system | Ubuntu Server |
| Networking | AWS VPC and Security Groups |
| VPN | WireGuard |
| Firewall | nftables |
| Internal DNS | dnsmasq |
| Metrics | Prometheus |
| Dashboards | Grafana |
| Logging | Grafana Loki |
| Telemetry collection | Grafana Alloy |
| Alerting | Prometheus Alertmanager |
| SOAR | Python and Flask |
| SOAR application server | Gunicorn |
| SOAR service management | systemd |
| Incident records | JSONL |
| Alert deduplication | SQLite |
| Monitoring deployment | Docker Compose |
| Infrastructure as Code | Terraform |
| Configuration management | Ansible |
| Automatic OS updates | unattended-upgrades |
| CI/CD | GitHub Actions |
| Source control | GitHub |
| Local SOAR viewer | Flask |
| Application testing | unittest and pytest |

## 17. References

The official documentation for the main technologies:

- AWS EC2: https://docs.aws.amazon.com/ec2/
- AWS VPC: https://docs.aws.amazon.com/vpc/
- Terraform: https://developer.hashicorp.com/terraform/docs
- WireGuard: https://www.wireguard.com/
- Grafana: https://grafana.com/docs/grafana/latest/
- Prometheus: https://prometheus.io/docs/
- Grafana Loki: https://grafana.com/docs/loki/latest/
- Grafana Alloy: https://grafana.com/docs/alloy/latest/
- Alertmanager: https://prometheus.io/docs/alerting/latest/alertmanager/
- Flask: https://flask.palletsprojects.com/
- Gunicorn: https://gunicorn.org/
- SQLite: https://www.sqlite.org/docs.html
- Docker Compose: https://docs.docker.com/compose/
- Ansible: https://docs.ansible.com/
- GitHub Actions: https://docs.github.com/en/actions
- Ubuntu: https://ubuntu.com/server/docs
- dnsmasq: https://thekelleys.org.uk/dnsmasq/doc.html