
# Phase 2 — Initial AWS Deployment Results

## 1. Overview

This document records the initial deployment and verification of the AWS infrastructure for the Innovatech Solutions hybrid-cloud and security automation project.

The objective of this implementation stage was to provision the cloud infrastructure using Infrastructure as Code (IaC), establish secure instance management, implement the initial network routing configuration, and verify that the deployed servers are operational.

The infrastructure was provisioned in the AWS Frankfurt region (`eu-central-1`) using Terraform.

**Implementation date:** 29 October 2026

**Implementation status:** Initial AWS deployment completed and verified. Hybrid VPN connectivity, monitoring services, and SOAR functionality remain under implementation.

## 2. Deployed Infrastructure

### 2.1 Virtual Private Cloud

A dedicated AWS Virtual Private Cloud was created to provide network isolation and segmented infrastructure.

| Component | Configuration |
|---|---|
| AWS region | eu-central-1 (Frankfurt) |
| VPC | innovatech-cs2-vpc |
| VPC ID | vpc-025555df114f75969 |
| VPC CIDR | 10.20.0.0/16 |
| Monitoring subnet | 10.20.10.0/24 |
| SOAR subnet | 10.20.20.0/24 |
| Gateway subnet | 10.20.30.0/24 |
| Provisioning method | Terraform |

The Monitoring and SOAR subnets are private. Their EC2 instances do not have directly assigned public IP addresses.

The gateway subnet has a route to the Internet Gateway and hosts the instance responsible for NAT and future VPN connectivity.

### 2.2 EC2 Instances

Three Ubuntu EC2 instances were provisioned.

| Server | Instance type | Private IP | Storage | Purpose |
|---|---|---|---|---|
| Monitoring | t3.medium | 10.20.10.10 | 40 GiB gp3 | Centralized monitoring and logging |
| SOAR | t3.small | 10.20.20.10 | 20 GiB gp3 | Security orchestration and automated responses |
| Gateway | t3.micro | 10.20.30.10 | 12 GiB gp3 | Network routing, NAT, and WireGuard VPN |

The gateway was allocated the public IPv4 address `3.66.71.166`.

The instances use encrypted EBS root volumes, require IMDSv2, and are configured with standard T3 CPU credits.

The Monitoring and SOAR servers have no public IPv4 addresses.

## 3. Network Configuration

### 3.1 Routing

The infrastructure uses separate route tables for the gateway and private application subnets.

The gateway subnet routes internet-bound traffic through the Internet Gateway.

The private application subnets route outbound traffic through the gateway EC2 instance.

A route for the planned on-premises network (`10.30.0.0/24`) also points toward the gateway. This route is intended for future WireGuard connectivity.

Source/destination checking was disabled on the gateway instance to permit traffic forwarding.

### 3.2 NAT Gateway Functionality

Instead of using a managed AWS NAT Gateway, the architecture uses a dedicated EC2 instance running Linux IP forwarding and nftables.

This approach was selected to provide routing control and reduce infrastructure costs during the development stage.

The following components were configured:

- IPv4 forwarding enabled through sysctl.
- nftables forwarding policy.
- Connection tracking for established and related connections.
- Source NAT masquerading for internet-bound traffic from private AWS subnets.
- Exclusions for internal VPC and simulated on-premises destinations.
- Initial forwarding rules for future WireGuard traffic.

The gateway configuration was verified using Linux system commands.

### 3.3 Gateway Connectivity Test

The gateway's internet connectivity was tested using:

`curl -I --max-time 10 https://aws.amazon.com`

The command returned HTTP status `200`, confirming successful outbound HTTPS connectivity from the gateway.

The Monitoring and SOAR instances also successfully registered with AWS Systems Manager after the gateway routing configuration was repaired.

This provides evidence that the private instances can communicate with the required AWS management endpoints.

## 4. Security and Instance Management

### 4.1 AWS Systems Manager

AWS Systems Manager Session Manager was selected for instance administration.

An IAM instance profile with the AWS-managed `AmazonSSMManagedInstanceCore` policy was attached to the EC2 instances.

This provides a management method that does not require public SSH access.

All three EC2 instances were confirmed as online in Systems Manager.

### 4.2 Network Security

Security groups were created to restrict inbound communication according to server responsibilities.

The initial design includes:

- WireGuard UDP port 51820 on the gateway.
- Grafana TCP port 3000 from the planned on-premises network.
- Loki TCP port 3100 from the planned on-premises network.
- SOAR API TCP port 8000 from the monitoring security group.

The presence of these rules in Terraform was verified. Application-level access restrictions and VPN traffic policies still require runtime testing.

## 5. Infrastructure Validation

### 5.1 Terraform Validation

Terraform configuration checks were completed successfully.

The GitHub Actions infrastructure validation workflow was executed using a local Windows self-hosted runner.

The workflow completed successfully, including Terraform formatting and validation checks.

### 5.2 Terraform Deployment

Before deployment, Terraform generated the following execution plan:

- 31 resources to create.
- 0 resources to change.
- 0 resources to destroy.

The planned AWS infrastructure was subsequently deployed.

Terraform outputs confirmed the VPC ID, subnet IDs, gateway public address, and private server addresses.

### 5.3 EC2 Instance Health

AWS EC2 status checks were performed for all three instances.

| Server | Instance state | System status | Instance status |
|---|---|---|---|
| Monitoring | Running | OK | OK |
| SOAR | Running | OK | OK |
| Gateway | Running | OK | OK |

All three instances passed their EC2 health checks.

### 5.4 Systems Manager Verification

All three servers were confirmed online in AWS Systems Manager.

| Server | SSM status |
|---|---|
| Monitoring | Online |
| SOAR | Online |
| Gateway | Online |

This verified that the instances were registered as managed nodes and communicating with Systems Manager at the time of testing.

## 6. WireGuard Preparation

WireGuard was installed on the AWS gateway.

The installation was verified using `wg --version`.

An AWS WireGuard private/public key pair was generated and stored on the gateway under `/etc/wireguard/`.

The private key is not stored in the Git repository.

The VPN interface, peer configuration, and connection to the simulated on-premises network have not yet been completed.

## 7. Issues Encountered

During the initial deployment, the gateway's cloud-init user-data script failed to execute.

The error was caused by a newline character appearing before the Bash shebang (`#!/bin/bash`).

This prevented the nftables configuration and IP forwarding setup from being initialized automatically.

The issue was diagnosed using cloud-init logs, corrected on the running instance, and fixed in the Terraform bootstrap source.

Detailed troubleshooting information is recorded in `issue-log.md`.

## 8. Cost Management

The infrastructure is intended to operate as a development and testing environment rather than a continuously running production system.

To reduce unnecessary AWS expenditure:

- EC2 instances are stopped when development work is finished.
- The gateway is started before the private application instances.
- The private application instances are stopped before the gateway.
- EBS storage and public IPv4 charges are considered separately from EC2 compute usage.
- Managed networking services with ongoing hourly charges are avoided where technically appropriate.

All three EC2 instances were stopped at the end of the initial implementation session.

## 9. Remaining Work

The following activities remain:

1. Create the simulated on-premises virtual machines.
2. Configure the local virtual network and gateway.
3. Establish the WireGuard VPN connection.
4. Implement internal DNS resolution.
5. Deploy Grafana, Prometheus, Loki, and supporting monitoring components.
6. Develop and deploy the FastAPI-based SOAR application.
7. Configure log collection from multiple sources.
8. Implement security alerting and automated response actions.
9. Integrate Ansible-based updates and deployment automation.
10. Execute integration, security, availability, and recovery tests.

## 10. Conclusion

The initial AWS infrastructure was deployed and verified successfully.

The implementation demonstrated Infrastructure as Code provisioning, network segmentation, secure remote management, fault diagnosis, and operational cost control.

The completed cloud infrastructure provides the foundation for the upcoming hybrid networking, observability, and SOAR implementation activities.

Further testing will be required before the overall system can be considered fully operational.
