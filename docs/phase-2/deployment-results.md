# Phase 2 — Deployment Results

## 1. Overview

During Phase 2, I deployed the AWS infrastructure, created the on-premises environment in VirtualBox and connected both environments using WireGuard.

I also configured centralized monitoring, security event processing, internal DNS and automated deployment workflows.

## 2. AWS Infrastructure

I used Terraform to deploy three Ubuntu EC2 instances in the Frankfurt region (`eu-central-1`).

| Server | Instance Type | Private IP | Storage |
|---|---|---|---|
| Monitoring | t3.medium | 10.20.10.10 | 40 GiB |
| SOAR | t3.small | 10.20.20.10 | 20 GiB |
| Gateway | t3.micro | 10.20.30.10 | 12 GiB |

The infrastructure uses the VPC `10.20.0.0/16`, with separate subnets for each server.

The Monitoring and SOAR servers have no public IP addresses, while the gateway provides internet access, NAT and VPN connectivity.

All three instances passed their EC2 status checks, and I used AWS Systems Manager for administration.

**Evidence:**
- `docs/evidence/network/01-aws-ec2-instances.png`
- `docs/evidence/network/02-aws-security-groups.png`

## 3. On-Premises Infrastructure

I created three Ubuntu VMs in VirtualBox.

| VM | IP Address | Purpose |
|---|---|---|
| cs2-onprem-gateway | 10.30.0.1 | VPN, firewall and DNS |
| cs2-onprem-linux | 10.30.0.10 | Monitoring and Ansible |
| cs2-onprem-security | 10.30.0.20 | Security monitoring |

The machines communicate through an internal VirtualBox network, with the gateway handling traffic between the local network and AWS.

## 4. WireGuard VPN

I configured WireGuard between the AWS gateway (`10.40.0.1`) and on-premises gateway (`10.40.0.2`).

The tunnel connects the AWS network `10.20.0.0/16` with the on-premises network `10.30.0.0/24`.

I verified the connection using `sudo wg show` and successfully accessed Grafana through its private AWS IP address.

**Evidence:**
- `docs/evidence/network/03-wireguard-vpn.png`
- `docs/evidence/network/04-private-connectivity.png`

## 5. Firewall and Internal DNS

I configured nftables on the on-premises gateway with a default-drop input policy and rules allowing the required network traffic.

Unauthorized TCP connections were blocked and logged using the prefix `INNOVATECH_FW_DROP`.

I also installed dnsmasq to resolve these internal hostnames:

| Hostname | Private IP |
|---|---|
| monitoring.innovatech.internal | 10.20.10.10 |
| soar.innovatech.internal | 10.20.20.10 |
| gateway.innovatech.internal | 10.30.0.1 |

The DNS firewall rules were saved in `/etc/nftables.conf`, and I successfully tested resolution from both the gateway and a Linux client.

**Evidence:**
- `docs/evidence/security/16-firewall-blocked-traffic.png`
- `docs/evidence/network/05-private-dns-gateway.png`
- `docs/evidence/network/05-private-dns-linux.png`

## 6. Monitoring Deployment

I deployed the monitoring stack on the AWS Monitoring server using Docker Compose.

The stack contains:

| Service | Purpose |
|---|---|
| Grafana | Dashboards |
| Prometheus | Infrastructure and application metrics |
| Loki | Centralized logs |
| Alloy | Telemetry collection |
| Alertmanager | Prometheus alert management |

I configured three dashboards for infrastructure monitoring, security logs and SOAR activity.

Prometheus showed six healthy targets, and Loki successfully collected logs from both AWS and the on-premises gateway.

I also configured the `ServerDown`, `HighCPUUsage` and `HighMemoryUsage` alert rules.

**Evidence:**
- `docs/evidence/monitoring/06-infrastructure-overview-A.png`
- `docs/evidence/monitoring/07-security-logs-overview-A.png`
- `docs/evidence/monitoring/09-loki-firewall-query.png`
- `docs/evidence/monitoring/10-multiple-log-sources.png`
- `docs/evidence/monitoring/11-monitoring-alerting.png`

## 7. SOAR Deployment

I developed the SOAR application using Python and Flask and deployed it on a separate AWS EC2 instance using Gunicorn and systemd.

The application handles security alerts, evaluates rules, detects duplicates and executes predefined response actions.

The main actions include incident recording, notification preparation and simulated containment.

### Security Detection Test

I generated 12 blocked TCP connections across four destination ports on the on-premises gateway.

The firewall logs were sent to Loki, where my Python log analyzer identified one possible port-scanning event.

SOAR processed the finding, recorded the incident and prepared an operator notification.

I also repeated the same analysis and confirmed that the application recognized the finding as a duplicate.

**Evidence:**
- `docs/evidence/soar/12-port-scan-detection.png`
- `docs/evidence/soar/14-soar-rule-evaluation.png`
- `docs/evidence/soar/15-soar-alert-deduplication.png`

## 8. CI/CD Deployment

I configured GitHub Actions using my Windows self-hosted runner.

The repository contains three main workflows:

| Workflow | Purpose |
|---|---|
| Infrastructure Checks | Terraform validation |
| SOAR CI/CD | Python testing and AWS deployment |
| Monitoring CI/CD | Grafana dashboard validation and deployment |

The SOAR workflow uses Amazon S3 and Systems Manager to deploy application changes without exposing SSH publicly.

I also tested the monitoring pipeline with invalid JSON, which caused validation to fail and deployment to be skipped.

**Evidence:**
- `docs/evidence/cicd/17-soar-cicd-success.png`
- `docs/evidence/cicd/18-monitoring-cicd-success.png`
- `docs/evidence/cicd/19-terraform-validation.png`
- `docs/evidence/cicd/20-pipeline-failure-protection.png`

## 9. System Updates

I configured Ubuntu unattended-upgrades on all five Linux servers and checked their update logs.

I also used Ansible to update `cs2-onprem-linux` and `cs2-onprem-security` from one control node.

Both machines completed the Ansible playbook without failed or unreachable tasks.

**Evidence:**
- `docs/evidence/updates/24-automated-system-updates.png`
- `docs/evidence/updates/26-soar-update-execution.png`
- `docs/evidence/updates/30-onprem-linux-update-execution.png`
- `docs/evidence/updates/33-ansible-multi-server-update.png`

## 10. Recovery Testing

I performed a controlled monitoring failure test by stopping the Grafana container while keeping Prometheus, Loki, Alloy and Alertmanager running.

After manually restarting Grafana, its health endpoint returned HTTP 200 and confirmed that the service was healthy.

**Evidence:**
- `docs/evidence/resilience/21-monitoring-health-before-test.png`
- `docs/evidence/resilience/22-monitoring-component-failure.png`
- `docs/evidence/resilience/23-monitoring-component-recovery.png`

## 11. Issues Encountered

During the initial AWS deployment, the gateway's cloud-init script failed because an empty line appeared before the Bash shebang.

I fixed the script, repaired the gateway configuration and updated the Terraform source to prevent the same issue during future deployments.

Another issue occurred when DNS queries from the Linux VM timed out because nftables was blocking port 53.

I added specific TCP and UDP DNS rules, validated the configuration and confirmed that the client could resolve the internal records.

## 12. Current Result

The AWS and VirtualBox environments are connected through WireGuard, and the main monitoring and SOAR services are operational.

Terraform, GitHub Actions, Ansible and unattended-upgrades provide infrastructure and system automation.
