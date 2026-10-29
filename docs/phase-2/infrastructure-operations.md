
# Phase 2 — AWS Infrastructure Operations Manual

## 1. Purpose

This document describes the operational procedures for managing the AWS infrastructure used by the Innovatech Solutions hybrid-cloud and security automation project.

It covers AWS authentication, EC2 instance management, infrastructure verification, secure remote access, Terraform operations, and cost-control procedures.

The infrastructure is a development environment and is not intended to remain online continuously.

## 2. Infrastructure Inventory

**AWS region:** `eu-central-1`

**AWS CLI profile:** `university`

**Terraform working directory:** `terraform/`

| Server | Instance ID | Private IP | Type |
|---|---|---|---|
| Monitoring | i-0bff5bf5723ea330b | 10.20.10.10 | t3.medium |
| SOAR | i-06706f222e5ff9178 | 10.20.20.10 | t3.small |
| Gateway | i-012bef6214dd854e1 | 10.20.30.10 | t3.micro |

**Gateway public IPv4 address:** `3.66.71.166`

**VPC ID:** `vpc-025555df114f75969`

These identifiers reflect the initial deployment and must be reviewed if Terraform replaces or recreates infrastructure resources.

## 3. AWS Authentication

### 3.1 Authenticate Through University SSO

Open PowerShell and execute:

```powershell
aws sso login --profile university
```

Select the AWS CLI profile for the current terminal:

```powershell
$env:AWS_PROFILE = "university"
$env:AWS_DEFAULT_REGION = "eu-central-1"
```

Verify the active identity:

```powershell
aws sts get-caller-identity
```

Confirm that the output identifies the intended university AWS account before making infrastructure changes.

### 3.2 Session Persistence

The AWS profile environment variable only applies to the current PowerShell session.

When opening a new terminal, select the profile again.

If SSO credentials have expired, repeat the login command.

## 4. Starting the Infrastructure

The gateway must be started before the Monitoring and SOAR servers because it provides outbound routing for the private subnets.

### 4.1 Start the Gateway

```powershell
aws ec2 start-instances `
  --region eu-central-1 `
  --instance-ids i-012bef6214dd854e1
```

Wait until the gateway is running:

```powershell
aws ec2 wait instance-running `
  --region eu-central-1 `
  --instance-ids i-012bef6214dd854e1
```

### 4.2 Verify Gateway Management Connectivity

```powershell
aws ssm describe-instance-information `
  --region eu-central-1 `
  --query "InstanceInformationList[].{Instance:InstanceId,Status:PingStatus}" `
  --output table
```

Confirm that the gateway is Online before starting the private instances.

Where necessary, connect through the AWS Console and verify the routing services:

```bash
sudo systemctl is-active nftables
sysctl net.ipv4.ip_forward
sudo nft list ruleset
```

Expected results:

- nftables is active.
- IPv4 forwarding is enabled.
- Required forwarding and NAT rules exist.

### 4.3 Start Monitoring and SOAR

```powershell
aws ec2 start-instances `
  --region eu-central-1 `
  --instance-ids i-0bff5bf5723ea330b i-06706f222e5ff9178
```

Wait for the instances:

```powershell
aws ec2 wait instance-running `
  --region eu-central-1 `
  --instance-ids i-0bff5bf5723ea330b i-06706f222e5ff9178
```

## 5. Verifying Infrastructure Health

### 5.1 EC2 Health Checks

```powershell
aws ec2 describe-instance-status `
  --region eu-central-1 `
  --instance-ids i-0bff5bf5723ea330b i-06706f222e5ff9178 i-012bef6214dd854e1 `
  --query "InstanceStatuses[].{ID:InstanceId,State:InstanceState.Name,System:SystemStatus.Status,Instance:InstanceStatus.Status}" `
  --output table
```

Expected results:

- Instance state: `running`
- System status: `ok`
- Instance status: `ok`

### 5.2 Systems Manager Connectivity

```powershell
aws ssm describe-instance-information `
  --region eu-central-1 `
  --query "InstanceInformationList[].{Instance:InstanceId,Status:PingStatus}" `
  --output table
```

All three instances should report `Online`.

### 5.3 Gateway Internet Connectivity

From the gateway's Linux terminal:

```bash
curl -I --max-time 10 https://aws.amazon.com
```

A successful HTTP response verifies HTTPS connectivity from the gateway.

This check does not independently prove that every private instance has unrestricted internet connectivity.

## 6. Connecting Through AWS Systems Manager

### 6.1 Browser-Based Access

1. Open the AWS EC2 Console.
2. Select the Frankfurt region.
3. Open EC2 Instances.
4. Select the target instance.
5. Choose Connect.
6. Select the Session Manager tab.
7. Choose Connect.

This method does not require public SSH access.

### 6.2 PowerShell-Based Access

The following command requires the AWS Session Manager plugin to be installed locally.

```powershell
aws ssm start-session `
  --target i-012bef6214dd854e1 `
  --region eu-central-1
```

If the plugin is unavailable, use the browser-based method instead.

## 7. Stopping the Infrastructure

To reduce costs, all three EC2 instances should be stopped when development work has finished.

The application servers must be stopped before the gateway.

### 7.1 Stop Monitoring and SOAR

```powershell
aws ec2 stop-instances `
  --region eu-central-1 `
  --instance-ids i-0bff5bf5723ea330b i-06706f222e5ff9178
```

Wait until both instances are stopped:

```powershell
aws ec2 wait instance-stopped `
  --region eu-central-1 `
  --instance-ids i-0bff5bf5723ea330b i-06706f222e5ff9178
```

### 7.2 Stop the Gateway

```powershell
aws ec2 stop-instances `
  --region eu-central-1 `
  --instance-ids i-012bef6214dd854e1
```

Wait for the gateway:

```powershell
aws ec2 wait instance-stopped `
  --region eu-central-1 `
  --instance-ids i-012bef6214dd854e1
```

### 7.3 Verify All Instances Are Stopped

```powershell
aws ec2 describe-instances `
  --region eu-central-1 `
  --instance-ids i-0bff5bf5723ea330b i-06706f222e5ff9178 i-012bef6214dd854e1 `
  --query "Reservations[].Instances[].{Name:Tags[?Key=='Name']|[0].Value,State:State.Name}" `
  --output table
```

All three instances must report `stopped`.

## 8. Terraform Operations

Terraform is used to manage the AWS infrastructure.

### 8.1 Validate Configuration

From the Terraform directory:

```powershell
& "D:\Programs\terraform\terraform.exe" fmt -check -recursive
& "D:\Programs\terraform\terraform.exe" validate
```

### 8.2 Preview Infrastructure Changes

```powershell
& "D:\Programs\terraform\terraform.exe" plan
```

The plan must be inspected before applying any changes.

Pay particular attention to resources marked for replacement or destruction.

### 8.3 Apply Changes

Only apply an approved and reviewed plan.

For example:

```powershell
& "D:\Programs\terraform\terraform.exe" plan "-out=reviewed.tfplan"
& "D:\Programs\terraform\terraform.exe" apply "reviewed.tfplan"
```

Saved Terraform plans may contain sensitive configuration and must not be committed to GitHub.

### 8.4 Important Operational Warning

Do not use `terraform apply` as a substitute for starting stopped EC2 instances.

Use the AWS CLI start/stop commands for ordinary development sessions.

Manual EC2 stop/start operations can create differences between the live infrastructure state and Terraform's expectations. Always inspect subsequent Terraform plans before applying changes.

Do not execute `terraform destroy` unless complete infrastructure removal is explicitly intended.

## 9. Cost Management

The following practices are used to minimize expenditure:

- Stop all EC2 instances after development sessions.
- Confirm that stop operations have completed.
- Avoid unnecessary continuously running services.
- Monitor AWS billing and usage.
- Avoid creating unmanaged public IPv4 addresses.
- Review EBS volumes, snapshots, and networking charges regularly.

Stopped EC2 instances do not incur normal compute charges, but EBS storage and public IPv4 resources can still generate charges.

AWS budgets are useful for notifications but do not automatically impose a strict spending limit.

## 10. Troubleshooting

### 10.1 Instance Does Not Appear in Systems Manager

Check:

1. EC2 instance state and health checks.
2. IAM instance profile attachment.
3. SSM Agent status.
4. Gateway availability and NAT configuration.
5. Private subnet routing.
6. Network security policies.
7. Connectivity to AWS Systems Manager endpoints.

### 10.2 Gateway Startup Script Failure

Inspect:

```bash
sudo cloud-init status --long
sudo tail -n 100 /var/log/cloud-init-output.log
sudo grep -n "scripts_user" /var/log/cloud-init.log
```

Verify that bootstrap scripts begin with a valid Bash shebang and use Unix line endings.

### 10.3 NAT Routing Problems

Check:

```bash
sysctl net.ipv4.ip_forward
sudo systemctl status nftables --no-pager
sudo nft list ruleset
ip -4 route
```

If the gateway is unavailable, Monitoring and SOAR may lose outbound connectivity.

### 10.4 AWS Authentication Problems

If the AWS CLI reports missing credentials:

```powershell
aws sso login --profile university
$env:AWS_PROFILE = "university"
$env:AWS_DEFAULT_REGION = "eu-central-1"
aws sts get-caller-identity
```

## 11. Shutdown Checklist

Before ending a development session:

- Verify that important work has been committed to GitHub.
- Ensure configuration changes and logs needed for evidence have been saved.
- Stop Monitoring and SOAR.
- Wait until both instances are stopped.
- Stop the gateway.
- Verify all three instances report `stopped`.
- Check for newly created AWS resources that may continue generating charges.

## 12. Conclusion

This operations manual provides a repeatable approach for managing the initial AWS infrastructure.

It supports secure administration, controlled infrastructure changes, operational troubleshooting, and reduced development costs.

The manual will be extended as the hybrid VPN, monitoring platform, SOAR application, and automation processes are deployed.
