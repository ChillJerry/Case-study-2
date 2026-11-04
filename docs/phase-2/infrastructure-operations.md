
# Infrastructure Operations and Handover Manual

**Project:** Innovatech Solutions — Hybrid Cloud Infrastructure and Security Automation  
**Document type:** Client-facing operations and handover guide  
**Status:** Interim — initial AWS infrastructure commissioned; remaining services under implementation  
**Environment:** Development and validation  
**Region:** AWS Europe (Frankfurt), `eu-central-1`  
**Last reviewed:** 29 October 2026

## 1. Purpose and scope

This manual describes how an authorized operations team should manage, verify, and maintain the initial AWS environment delivered for the Innovatech Solutions hybrid-cloud project. It is written for a client or successor administrator, rather than for the original developer's workstation.

The initial infrastructure has been provisioned and checked. The hybrid VPN tunnel, internal DNS, centralized monitoring stack, log collection, SOAR application, automated security response workflows, and scheduled update automation have **not yet been commissioned**. Procedures for those components will be added only after implementation and acceptance testing.

This manual does **not** grant access to the environment. Administrative access, role assignments, and ownership transfer must be arranged separately by the AWS account owner.

## 2. Delivered environment

The initial AWS environment consists of a dedicated VPC (`10.20.0.0/16`) containing three segregated subnets and three Ubuntu Linux EC2 instances.

| Component | Private address | Function | Deployment state |
|---|---|---|---|
| Gateway | `10.20.30.10` | Internet egress for private subnets; future WireGuard endpoint | Deployed; NAT tested |
| Monitoring server | `10.20.10.10` | Host for planned metrics, logs, dashboards and alerting | EC2 deployed; application stack pending |
| SOAR server | `10.20.20.10` | Host for planned security orchestration service | EC2 deployed; application pending |

The gateway uses a public IPv4 address to support egress and the future VPN endpoint. The monitoring and SOAR instances have no public IPv4 addresses. The public address and all AWS-generated resource IDs should be retrieved from the current infrastructure inventory or Terraform outputs, rather than relied upon as permanent identifiers.

**Network design:** Private-subnet default routes forward internet-bound traffic through the gateway EC2 instance. Its `nftables` configuration enables IP forwarding and outbound NAT. A route toward the proposed on-premises network (`10.30.0.0/24`) is provisioned, but will not provide connectivity until the VPN is configured and tested.

**Operational limitation:** The gateway is a single point of failure. If stopped or unavailable, the private servers may lose outbound access to AWS management endpoints and internet services. This trade-off is intentional for the development environment and requires reassessment before production use.

## 3. Access, roles and prerequisites

Only personnel authorized by the organization should operate the AWS environment.

Before handover, the AWS account owner must:

1. Grant the operations team appropriate IAM Identity Center or IAM access to the correct AWS account, with least-privilege permissions for the required operations.
2. Confirm access to AWS EC2, Systems Manager Session Manager, relevant networking resources, CloudWatch/Billing, and the approved infrastructure repository.
3. Provide access to the Terraform state backend and its locking configuration, if the team is authorized to change infrastructure.
4. Assign ownership for infrastructure changes, incident response, backups, and billing alerts.
5. Define an approved secure process for transferring or rotating VPN keys and application secrets. Secret values must not be placed in documentation or source control.

**Access method:** Administrators normally reach Linux instances using **AWS Systems Manager Session Manager** through the AWS Console, rather than public SSH. Private instance access depends on outbound connectivity to Systems Manager service endpoints and correct IAM/SSM Agent configuration.

No client-specific login names, local CLI profile names, private keys, access tokens, or individual laptop file paths are required by this document.

## 4. Normal operating procedure

### 4.1 Pre-start checks

Before bringing the environment online:

- Confirm that the work is approved and that an authorized account has been selected.
- Check the AWS region and verify the environment using resource **Name** and **Project** tags.
- Review any unresolved incidents or pending Terraform changes.
- Confirm the maintenance window and expected cost impact.

### 4.2 Startup sequence

1. Start the EC2 instance tagged `Name=innovatech-cs2-gateway` in the AWS EC2 Console.
2. Wait until its EC2 instance and system status checks pass.
3. Verify that the gateway is **Online** in Systems Manager.
4. Through Session Manager, verify that `nftables` is active, IPv4 forwarding is enabled, and the required NAT rules are present.
5. Start the instances tagged `Name=innovatech-cs2-monitoring` and `Name=innovatech-cs2-soar`.
6. Wait for their EC2 health checks to pass and verify both are **Online** in Systems Manager.
7. Record the result and any unexpected behavior in the operations log.

The existence of a running EC2 instance does not, by itself, establish that its intended application services are ready. Application-specific health checks will be added when those services are deployed.

### 4.3 Shutdown sequence

For this development environment, the servers are intentionally stopped when no work is scheduled:

1. Ensure that work has been saved and any application services have been shut down safely, where applicable.
2. Stop **Monitoring** and **SOAR** through the AWS EC2 Console.
3. Confirm both instances have reached the `stopped` state.
4. Stop the **Gateway** last.
5. Confirm that all three instances show `stopped` and record the shutdown in the operations log.

**Cost warning:** Stopping EC2 instances stops normal instance compute billing, but attached EBS volumes, public IPv4 address allocations and any independently billed AWS services may continue to incur charges. Shutdown is a cost-control measure, not full infrastructure decommissioning.

## 5. Operational health and acceptance checks

The following checks were completed during the initial deployment and should be repeatable by authorized administrators:

| Check | Acceptance criterion | Initial result |
|---|---|---|
| EC2 provisioning | Three intended instances exist in the correct VPC and subnets | Passed |
| EC2 health | Instance and system status checks report `ok` | Passed |
| Managed access | Gateway, Monitoring and SOAR report `Online` in Systems Manager | Passed |
| Gateway firewall | `nftables` is active and contains forwarding/NAT rules | Passed |
| Gateway forwarding | `net.ipv4.ip_forward` is `1` | Passed |
| Gateway internet access | Outbound HTTPS request receives a valid HTTP response | Passed |
| Private server management reachability | Private instances register with Systems Manager through the intended egress path | Passed for SSM connectivity |
| Hybrid VPN reachability | On-premises and AWS hosts communicate across the VPN | Not yet tested |
| Monitoring and SOAR services | Service-level health and event-response checks | Not yet implemented |

Where EC2 health checks pass but a server is absent from Systems Manager, examine the IAM instance profile, SSM Agent, private-subnet routes, and gateway connectivity before attempting changes to instance access rules.

## 6. Configuration and change management

Infrastructure configuration is managed through **Terraform**, with source-controlled configuration in the project repository and state stored in an approved remote backend. Shell scripts and future Ansible playbooks provide machine-level configuration.

The recommended change procedure is:

1. Create a proposed change in version control and document its purpose, impact, and rollback approach.
2. Run automated formatting and validation checks through the CI workflow.
3. Generate and review a Terraform execution plan in the intended AWS account.
4. Obtain the required approval before applying changes that create, replace, or destroy resources.
5. Apply the approved change through the authorized deployment process.
6. Re-run infrastructure health checks and retain the results as evidence.
7. Update the asset inventory, operations manual, and issue log when behavior or access arrangements change.

**Do not use Terraform `apply` as a routine start/stop mechanism.** Stop and start existing instances through EC2 controls. After manual operational changes, inspect subsequent Terraform plans carefully to avoid unintended replacement or recreation.

The Windows self-hosted GitHub Actions runner used during development is an implementation tool, **not an assumed client asset**. A production handover would require a client-managed runner, an approved managed CI platform, or another explicitly agreed deployment mechanism. Similarly, the university SSO profile used during development is not a transferable client credential.

## 7. Security and secrets management

- Administrative connectivity should use Systems Manager and organization-controlled access policies.
- Monitoring and SOAR servers should remain private and should not receive public IP addresses unless the design is formally revised.
- Security groups must be reviewed against the approved connectivity matrix before new applications are exposed.
- WireGuard private keys must remain in protected locations and must not enter Git or Terraform output files.
- IAM permissions, infrastructure roles and incident-response privileges must be reviewed before client acceptance.
- Security logs and access records should be retained in accordance with the client's applicable policies, once centralized logging is implemented.

**Current limitation:** The intended hybrid VPN and automated security response controls have not yet been demonstrated. Their design must not be presented as an already operational security capability.

## 8. Failure handling and recovery

### 8.1 Gateway unavailable

**Symptoms:** Private servers lose outbound connectivity, package downloads fail, or Systems Manager shows private nodes as offline.

**Response:** Confirm gateway EC2 status, source/destination checking setting, route-table targets and security-group rules. When gateway access is available, inspect `nftables`, IP forwarding, and the outbound route. Restore the approved gateway configuration and then verify management connectivity from the private servers.

**Escalation:** If gateway recovery requires recreation or changes to routes/EIPs, obtain approval and review the Terraform plan before proceeding.

### 8.2 Instance healthy but not manageable

**Symptoms:** EC2 status checks pass but Systems Manager does not show the node as online.

**Response:** Check the instance profile, SSM Agent, DNS resolution, security-group egress and private-subnet gateway connectivity. Do not enable public SSH as an ad hoc workaround without security approval.

### 8.3 Provisioning or bootstrap failure

**Symptoms:** An instance exists but expected machine-level configuration is missing.

**Response:** Inspect cloud-init status and logs through an approved management path. Validate the relevant scripts in source control; repair the running instance using a documented change procedure, then correct the automation source so that future provisioning is repeatable.

**Known incident:** During the initial deployment, a leading newline before the Bash shebang caused a cloud-init `Exec format error` on the gateway. The script was corrected, the deployed gateway was repaired and its functionality verified. Details are recorded in `docs/phase-2/issue-log.md`.

**Recovery limitation:** Automated failover, backup restoration and disaster-recovery procedures have not yet been implemented or demonstrated. Their absence must be considered during client acceptance.

## 9. Costs, maintenance and ownership

The current environment is a time-limited development environment. Routine practice is to start resources only when work is scheduled and stop them afterward, while recognizing residual storage and public IPv4 charges.

The designated infrastructure owner should periodically review:

- EC2 running hours and EBS storage usage.
- Public IPv4 allocations and other hourly-billed network resources.
- AWS Budgets and Cost Explorer reports.
- Terraform drift and unresolved deployment changes.
- OS and package updates, security-group changes and access privileges.
- Remaining milestones and risks before any production use.

The client should assign an operational owner and named escalation contacts before formal handover. No particular individual or university account is assumed to be the owner.

## 10. Handover requirements and remaining work

This is an **interim** manual. Before full handover, the delivery team must provide or complete:

| Item | Current state |
|---|---|
| Infrastructure design and Terraform configuration | Prepared and initially deployed |
| Basic EC2, gateway and SSM evidence | Verified |
| Current asset inventory and access ownership | Requires client-specific handover |
| Simulated on-premises VMs | Pending |
| WireGuard site-to-site tunnel | Keys prepared on AWS side; tunnel pending |
| Internal DNS | Pending |
| Grafana, Prometheus, Loki and log ingestion | Pending |
| SOAR application and two automated responses | Pending |
| Automated OS/package update process | Pending |
| Operational alerts and service runbooks | Pending |
| Failure, recovery and integration acceptance tests | Pending |
| Final backup, rollback and incident escalation procedures | Pending |

A final version of this document should refer to the approved client IAM roles, alerting channels, recovery objectives and operating schedule **only after those decisions are agreed and implemented**.

## 11. Conclusion

The initial AWS infrastructure has been deployed and its basic health, remote management, gateway routing and outbound connectivity have been demonstrated. This manual provides a platform-independent operational baseline for authorized client administrators.

The environment is **not yet a complete operational hybrid-cloud monitoring and SOAR solution**. Formal acceptance should follow implementation and verification of the remaining services, access handover and recovery procedures.
