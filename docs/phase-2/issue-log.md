
# Phase 2 — Issue and Resolution Log

## 1. Purpose

This document records technical issues encountered during the implementation of the Innovatech Solutions hybrid-cloud infrastructure.

Its purpose is to provide traceability of failures, troubleshooting activities, corrective actions, and preventive improvements.

Issues are documented to support infrastructure maintainability, repeatability, and continuous improvement.

---

## Issue P2-001 — Gateway Bootstrap Execution Failure

**Date:** 29 October 2026

**Component:** AWS Gateway EC2 Instance

**Severity:** High

**Status:** Resolved on the running instance; source correction committed.

### 1. Description

During initial infrastructure deployment, the gateway EC2 instance was created successfully, but its cloud-init initialization process reported an error.

The following command was used:

`sudo cloud-init status --long`

The resulting status was:

`status: error`

The logs reported that the `scripts_user` module failed while attempting to execute the gateway initialization script.

### 2. Impact

The gateway bootstrap script was responsible for installing and configuring nftables and enabling IPv4 forwarding.

Because the script did not execute, these settings were not initialized automatically.

The Monitoring and SOAR instances initially failed to appear as online nodes in AWS Systems Manager.

This indicated a potential failure in the outbound connectivity path used by the private instances.

### 3. Investigation

The following logs were inspected:

- `/var/log/cloud-init-output.log`
- `/var/log/cloud-init.log`

The detailed cloud-init log contained:

`Exec format error. Missing #! in script?`

The failing file was:

`/var/lib/cloud/instance/scripts/part-001`

The beginning of the file was inspected at the byte level using:

`sudo head -c 20 /var/lib/cloud/instance/scripts/part-001 | od -An -tx1`

The output started with:

`0a 23 21 2f 62 69 6e 2f 62 61 73 68`

The first byte (`0a`) represented a newline character.

As a result, the Bash shebang was not located at the beginning of the executable file.

### 4. Root Cause

The cloud-init executable script contained a leading newline before:

`#!/bin/bash`

Linux could not execute the file directly because the shebang did not appear at the beginning of the script.

The immediate root cause was therefore an incorrectly formatted cloud-init user-data script.

The project was developed on Windows, where file formatting and Terraform user-data construction both required additional attention.

### 5. Corrective Action

The deployed cloud-init script was repaired by removing the leading empty line.

The corrected script was then executed manually on the existing gateway instance.

The script installed and configured nftables and enabled Linux packet forwarding.

The local Terraform bootstrap source was also updated to ensure the script begins with a valid Bash shebang and uses LF line endings.

The correction was committed to GitHub.

**Commit:** `3854d68`

**Commit message:** `fix: ensure gateway bootstrap starts with valid shebang`

### 6. Verification

The following checks were completed successfully:

| Verification | Result |
|---|---|
| nftables service | Active |
| IPv4 forwarding | Enabled |
| Forwarding rules | Present |
| NAT masquerading rule | Present |
| Gateway HTTPS connectivity | HTTP 200 |
| Gateway SSM status | Online |
| Monitoring SSM status | Online |
| SOAR SSM status | Online |
| EC2 instance health | All checks OK |

The private instances registered with AWS Systems Manager following the gateway repair.

### 7. Preventive Improvements

To prevent recurrence:

- Ensure Bash scripts begin directly with `#!/bin/bash`.
- Save shell scripts using UTF-8 without BOM.
- Enforce LF line endings for `.sh` files using Git attributes.
- Add automated validation of bootstrap scripts to the CI/CD workflow.
- Review rendered Terraform user data before infrastructure deployment.
- Include cloud-init checks in initial infrastructure acceptance testing.

### 8. Lessons Learned

A Terraform configuration can pass syntax validation and still contain errors in executable user-data scripts.

Successful infrastructure provisioning does not guarantee successful operating-system initialization.

Cloud-init logs and byte-level inspection can help identify failures that are not immediately visible through the AWS Console.

This issue demonstrated the importance of validating infrastructure behavior after deployment rather than relying only on Terraform execution results.

---

## Issue P2-002 — Session Manager Plugin Missing on Windows

**Date:** 29 October 2026

**Component:** Local Windows Development Environment

**Severity:** Low

**Status:** Workaround implemented

### 1. Description

An attempt to open an interactive AWS Systems Manager session from PowerShell failed.

The AWS CLI returned:

`SessionManagerPlugin is not found`

### 2. Cause

The local Windows environment did not have the Session Manager plugin available to the AWS CLI.

### 3. Workaround

The AWS Management Console's browser-based Session Manager terminal was used.

This allowed secure access to the gateway without modifying security group rules or exposing SSH access.

### 4. Verification

The gateway was successfully accessed through the AWS Console and Linux administrative commands were executed.

### 5. Follow-up

Install the official AWS Session Manager plugin on Windows if interactive CLI-based sessions become necessary.

The AWS Console remains an acceptable access method for the development environment.

---

## Issue P2-003 — AWS CLI SSO Profile Not Selected

**Date:** 29 October 2026

**Component:** Local AWS CLI Authentication

**Severity:** Medium

**Status:** Resolved

### 1. Description

AWS SSO authentication succeeded, but AWS CLI commands still reported:

`NoCredentials: Unable to locate credentials`

### 2. Root Cause

The university SSO profile was configured and authenticated, but it was not selected as the active AWS CLI profile in the PowerShell session.

### 3. Corrective Action

The following environment variables were configured:

`$env:AWS_PROFILE = "university"`

`$env:AWS_DEFAULT_REGION = "eu-central-1"`

The AWS CLI was then able to use the authenticated profile for subsequent infrastructure operations.

### 4. Lesson Learned

Successful SSO authentication does not necessarily mean that the AWS CLI is using the authenticated profile.

Explicit profile selection reduces the likelihood of authentication errors and accidental operations against an unintended AWS account.

---

## 2. Future Issues

Additional issues discovered during VPN configuration, monitoring deployment, SOAR development, system integration, and testing will be recorded in this document.

Each issue should include its impact, investigation, root cause, corrective action, verification, and preventive improvements.
