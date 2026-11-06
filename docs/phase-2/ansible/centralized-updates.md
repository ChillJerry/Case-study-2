# Centralized System Updates

## 1. Overview

I use Ansible to update multiple Linux machines from one control node and unattended-upgrades to install updates automatically on individual servers.

This reduces manual maintenance and helps keep the infrastructure updated.

## 2. Ansible Configuration

I configured `cs2-onprem-linux` as the Ansible control node.

The playbook manages two Ubuntu machines:

| Machine | IP Address | Connection |
|---|---|---|
| cs2-onprem-linux | 10.30.0.10 | Local |
| cs2-onprem-security | 10.30.0.20 | SSH |

The on-premises gateway is excluded from the playbook to avoid interrupting network connectivity during updates.

## 3. Update Playbook

The Ansible playbook performs the following tasks:

- Checks that the target machine is running Ubuntu.
- Refreshes the APT package cache.
- Installs available package upgrades.
- Checks whether a reboot is required.
- Reports the results for each machine.

I use `serial: 1` so the machines are updated one at a time. Reboots are reported but not performed automatically.

The playbook and inventory are stored in the GitHub repository.

## 4. Ansible Testing

I ran the playbook against both managed machines.

| Machine | OK | Changed | Failed | Unreachable |
|---|---:|---:|---:|---:|
| cs2-onprem-linux | 6 | 1 | 0 | 0 |
| cs2-onprem-security | 6 | 0 | 0 | 0 |

Both machines completed the execution without failed or unreachable tasks.

The playbook also supports repeated execution without reinstalling packages that are already up to date.

**Evidence:**

`docs/evidence/updates/33-ansible-multi-server-update.png`

## 5. Automatic Updates

I also configured Ubuntu unattended-upgrades on five Linux servers.

| Server | Automatic Updates |
|---|---|
| AWS Monitoring | Enabled |
| AWS SOAR | Enabled |
| On-premises Gateway | Enabled |
| On-premises Linux | Enabled |
| On-premises Security | Enabled |

I checked the unattended-upgrades configuration and execution logs on each server.

The evidence shows successful package installations on four servers. The on-premises gateway performed an update check, but no package installation was recorded in the captured output.

## 6. Update Verification

I use the following command to inspect automatic update activity:

```bash
sudo tail -30 /var/log/unattended-upgrades/unattended-upgrades.log
```

The Ansible execution results showed no failures, and the unattended-upgrades logs confirmed that automatic checks were running.

**Evidence:**

- `docs/evidence/updates/24-automated-system-updates.png`
- `docs/evidence/updates/25-soar-automatic-updates.png`
- `docs/evidence/updates/26-soar-update-execution.png`
- `docs/evidence/updates/27-onprem-gateway-updates.png`
- `docs/evidence/updates/28-onprem-gateway-update-execution.png`
- `docs/evidence/updates/29-onprem-linux-updates.png`
- `docs/evidence/updates/30-onprem-linux-update-execution.png`
- `docs/evidence/updates/31-onprem-security-updates.png`
- `docs/evidence/updates/32-onprem-security-update-execution.png`

## 7. Limitations

The Ansible playbook currently manages two on-premises systems and is started manually from the control node.

The remaining servers use unattended-upgrades independently, and the playbook does not automatically reboot machines.

## 8. Result

The centralized Ansible update test completed successfully on both managed machines.
