# Issue Log

## 1. AWS Gateway Bootstrap Failure

**Issue:** The AWS gateway was deployed successfully, but its cloud-init script failed to execute.

**Cause:** There was an empty line before `#!/bin/bash`, which caused an execution format error.

**Solution:** I removed the extra line, executed the corrected script on the gateway and updated the Terraform source.

**Result:** nftables, IP forwarding and NAT started working, and the private AWS instances became reachable through Systems Manager.

**Commit:** `3854d68`

## 2. Session Manager Plugin Missing

**Issue:** I couldn't start an AWS Systems Manager session through PowerShell.

**Cause:** The Session Manager plugin wasn't installed on my Windows computer.

**Solution:** I used the AWS Console's browser-based Session Manager instead.

**Result:** I could manage the EC2 instances without enabling public SSH access.

## 3. AWS CLI Authentication Problem

**Issue:** AWS CLI commands returned `Unable to locate credentials` even after I logged in through AWS SSO.

**Cause:** PowerShell wasn't using my configured AWS profile.

**Solution:** I selected the correct profile and region:

```powershell
$env:AWS_PROFILE = "university"
$env:AWS_DEFAULT_REGION = "eu-central-1"
```

**Result:** AWS CLI commands started working correctly.

## 4. Internal DNS Service Conflict

**Issue:** dnsmasq initially failed to start on the on-premises gateway.

**Cause:** Ubuntu's existing DNS resolver was already using port 53.

**Solution:** I configured dnsmasq to bind specifically to the gateway's internal IP address, `10.30.0.1`.

**Result:** dnsmasq started successfully and resolved the configured `innovatech.internal` records.

## 5. DNS Queries Blocked by Firewall

**Issue:** DNS worked directly on the gateway, but queries from `cs2-onprem-linux` timed out.

**Cause:** The nftables input chain had a default-drop policy without rules allowing DNS requests.

**Solution:** I added TCP and UDP port 53 exceptions for `10.30.0.0/24` to `/etc/nftables.conf`.

**Result:** The Linux VM successfully resolved all three internal DNS records.

**Evidence:**
- `docs/evidence/network/05-private-dns-gateway.png`
- `docs/evidence/network/05-private-dns-linux.png`

## 6. nftables Configuration Syntax Error

**Issue:** While making the DNS firewall rules persistent, nftables reported a syntax error.

**Cause:** The newly added rule configuration contained a formatting mistake.

**Solution:** I corrected the rules and validated the file before reloading nftables.

```bash
sudo nft -c -f /etc/nftables.conf
sudo systemctl reload nftables
```

**Result:** Both DNS rules loaded successfully, and the existing firewall logging rules remained active.

## 7. Monitoring Pipeline Validation Test

I deliberately introduced invalid JSON into a Grafana dashboard file to test the CI/CD pipeline.

The validation job failed and the deployment job was skipped, which confirmed that invalid dashboard configuration was blocked before deployment.

This was an intentional test rather than an unresolved issue.

**Evidence:** `docs/evidence/cicd/20-pipeline-failure-protection.png`

## 8. What I Learned

The main problems I encountered were related to network configuration, Linux services and deployment automation.
