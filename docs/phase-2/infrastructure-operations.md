# Infrastructure Operations

## 1. Overview

This document contains the main commands and procedures I use to manage the AWS and on-premises infrastructure.

The environment includes three AWS EC2 instances, three VirtualBox VMs, WireGuard, centralized monitoring and a Python SOAR application.

## 2. Infrastructure

### AWS Servers

| Server | Private IP | Purpose |
|---|---|---|
| Monitoring | 10.20.10.10 | Grafana, Prometheus, Loki and Alertmanager |
| SOAR | 10.20.20.10 | Python security automation |
| Gateway | 10.20.30.10 | WireGuard, NAT and routing |

### On-Premises VMs

| VM | IP Address | Purpose |
|---|---|---|
| cs2-onprem-gateway | 10.30.0.1 | VPN, firewall and DNS |
| cs2-onprem-linux | 10.30.0.10 | Monitoring and Ansible |
| cs2-onprem-security | 10.30.0.20 | Security monitoring |

## 3. Starting the Infrastructure

I normally start the networking components before the application servers so the private systems have connectivity.

**Startup order:**

1. Start the AWS Gateway EC2 instance.
2. Start the AWS Monitoring and SOAR instances.
3. Start the on-premises gateway in VirtualBox.
4. Start the Linux and Security VMs.
5. Check WireGuard and monitoring connectivity.

The AWS instances should pass their EC2 status checks before I continue with application testing.

## 4. Stopping the Infrastructure

I stop the environment when I'm finished working to reduce AWS costs.

**Shutdown order:**

1. Stop the SOAR and Monitoring EC2 instances.
2. Stop the AWS Gateway last.
3. Shut down the VirtualBox VMs when they are no longer needed.

Stopping EC2 reduces compute charges, but EBS storage and public IPv4 allocations can still generate costs.

## 5. AWS Administration

I use AWS Systems Manager Session Manager to access the EC2 instances without opening public SSH ports.

For local AWS CLI operations, I use the `university` profile and Frankfurt region.

```powershell
aws sso login --profile university
```

I can check the deployed instances using:

```powershell
aws ec2 describe-instances --profile university --region eu-central-1 --query "Reservations[].Instances[].[Tags[?Key=='Name']|[0].Value,State.Name,PrivateIpAddress]" --output table
```

Infrastructure changes are managed through Terraform, and I review the plan before applying changes.

## 6. WireGuard VPN

WireGuard connects the AWS network `10.20.0.0/16` with the on-premises network `10.30.0.0/24`.

On the on-premises gateway, I check the tunnel using:

```bash
sudo wg show
```

A recent handshake and transferred data indicate that the VPN peer is communicating.

I also check private application connectivity using:

```bash
curl -I http://10.20.10.10:3000/login
```

This should return an HTTP response from Grafana when the monitoring server and VPN are working.

## 7. Firewall Management

The on-premises gateway uses nftables to restrict incoming traffic and log blocked connections.

The persistent configuration is stored in `/etc/nftables.conf`.

To inspect the active rules:

```bash
sudo nft list ruleset
```

Before applying configuration changes, I validate them using:

```bash
sudo nft -c -f /etc/nftables.conf
```

If validation succeeds, I can reload the firewall:

```bash
sudo systemctl reload nftables
```

To inspect blocked traffic:

```bash
sudo grep "INNOVATECH_FW_DROP" /var/log/kern.log | tail -20
```

I avoid changing firewall rules without checking VPN, DNS and monitoring access afterward.

## 8. Internal DNS

dnsmasq runs on the on-premises gateway and provides DNS records for the internal services.

I check its status using:

```bash
sudo systemctl status dnsmasq
```

To test DNS resolution:

```bash
dig @10.30.0.1 monitoring.innovatech.internal +short
dig @10.30.0.1 soar.innovatech.internal +short
dig @10.30.0.1 gateway.innovatech.internal +short
```

The expected addresses are `10.20.10.10`, `10.20.20.10` and `10.30.0.1`.

The DNS configuration is stored in `/etc/dnsmasq.d/innovatech-internal.conf`.

## 9. Monitoring Services

The monitoring stack runs through Docker Compose on the AWS Monitoring instance.

The main directory is:

`/opt/innovatech/monitoring`

To check the containers:

```bash
cd /opt/innovatech/monitoring
sudo docker compose ps
```

To restart an individual component:

```bash
sudo docker compose restart grafana
```

The stack contains Grafana, Prometheus, Loki, Alloy and Alertmanager.

Grafana is accessible from the approved private network path on port 3000. I can also access it through my configured local forwarding at `http://127.0.0.1:3000`.

### Checking Grafana

```bash
curl http://127.0.0.1:3000/api/health
```

This command runs on the Monitoring instance and checks whether Grafana responds correctly.

### Checking Logs

I use Grafana Explore to inspect Loki logs.

For example:

```logql
{job="onprem-firewall"} |= "INNOVATECH_FW_DROP"
```

This shows firewall events collected from the on-premises gateway.

## 10. SOAR Operations

The SOAR application runs on the AWS SOAR instance using Flask, Gunicorn and systemd.

The main endpoints are:

| Endpoint | Purpose |
|---|---|
| /health | Service health |
| /metrics | Prometheus metrics |
| /alerts | Receive authenticated alerts |

The service runs on port 8000 and accepts connections from the authorized AWS monitoring environment.

I can inspect the service using:

```bash
sudo systemctl status innovatech-soar
```

To restart it:

```bash
sudo systemctl restart innovatech-soar
```

To inspect application logs:

```bash
sudo journalctl -u innovatech-soar -n 50 --no-pager
```

I use the SOAR CI/CD workflow for normal application deployments instead of manually copying files to the server.

### Local SOAR Viewer

The SOAR Execution Inspector runs locally on Windows.

From the project repository:

```powershell
py -3.11 tools/soar_viewer.py
```

The viewer is available at:

`http://127.0.0.1:5050`

It displays imported execution results and the Python code responsible for processing security events.

## 11. CI/CD

I manage application and monitoring updates through GitHub Actions.

| Workflow | Purpose |
|---|---|
| Infrastructure Checks | Terraform formatting and validation |
| SOAR CI/CD | Test and deploy the SOAR application |
| Monitoring CI/CD | Validate and deploy Grafana dashboards |

The workflows use my Windows self-hosted runner.

For a deployment, I check that the tests pass and that the AWS services are healthy afterward.

## 12. System Updates

### Ansible

I use Ansible from `cs2-onprem-linux` to update two Ubuntu systems:

- `cs2-onprem-linux`
- `cs2-onprem-security`

The update playbook processes one machine at a time and reports whether a reboot is required.

I run the playbook from the control node using the inventory and playbook stored in the repository.

### Automatic Updates

Ubuntu unattended-upgrades is enabled on five Linux servers.

To inspect update activity:

```bash
sudo tail -30 /var/log/unattended-upgrades/unattended-upgrades.log
```

Automatic updates run independently on each machine, while Ansible is used for centralized updates of the two selected systems.

## 13. Recovery and Troubleshooting

### Grafana Not Working

I first check the container status with `docker compose ps`.

If Grafana is stopped, I can restart it and verify `/api/health`.

### VPN Not Working

I check `sudo wg show`, gateway status, routing and firewall rules.

I also verify that the AWS Gateway instance is running and UDP port 51820 is permitted.

### DNS Not Working

I check dnsmasq, test direct queries using `dig`, and verify that nftables allows TCP and UDP port 53 from the on-premises network.

This was an issue during implementation and was fixed by adding persistent DNS firewall rules.

### SOAR Not Working

I check the systemd service and application logs, followed by the `/health` endpoint from an authorized AWS host.

I also check whether Prometheus can still scrape the SOAR metrics endpoint.

### Missing Logs

I check Alloy, Loki and the WireGuard connection.

For firewall events, I also verify that the gateway is still generating logs with the `INNOVATECH_FW_DROP` prefix.

## 14. Backups and Limitations

Terraform configuration, deployment scripts and application code are stored in GitHub.

Terraform state is stored remotely in Amazon S3, while monitoring and SOAR data are stored on their respective servers.

A complete backup restoration test for monitoring and SOAR data has not yet been performed, so the current setup should not be treated as a fully tested disaster-recovery solution.

The AWS Gateway and Monitoring servers are also single points of failure.

## 15. Evidence

The project screenshots are stored in `docs/evidence/`.

The folders cover networking, monitoring, SOAR, security, CI/CD, resilience and system updates.
