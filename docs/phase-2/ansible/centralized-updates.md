# Centralized OS Update Automation — Ansible

## Objective

Implement centralized, repeatable Ubuntu package updates across multiple systems without manually logging into each server to install updates.

## Architecture

The `cs2-onprem-linux` VirtualBox VM operates as the Ansible control node.

The managed systems are:

- `cs2-onprem-linux` — local connection
- `cs2-onprem-security` — SSH connection over the internal network (`10.30.0.20`)

The on-premises gateway is excluded from automatic package updates to avoid disrupting network connectivity.

## Implementation

Ansible uses an inventory and version-controlled YAML playbook maintained in the Case Study 2 GitHub repository.

The update playbook:

1. Verifies that each target runs Ubuntu.
2. Refreshes the APT package cache.
3. Installs available package upgrades.
4. Checks whether a reboot is required.
5. Reports the result for each machine.

The playbook uses `serial: 1` to process machines individually and does not perform automatic reboots.

SSH public-key authentication is used for remote access, with sudo privilege escalation for package management.

## Validation

The implementation was tested against both managed Ubuntu systems.

Both hosts completed the update workflow without failed tasks or connectivity errors. Subsequent connectivity checks passed, and simulated APT upgrades reported no remaining packages to upgrade.

A repeat execution is used to assess idempotency.

## Limitations

The implementation currently covers two on-premises Ubuntu machines. The AWS instances and VPN gateway are not included in automated package updates.

Reboots are reported but remain administrator-controlled. The playbook is executed manually from the centralized controller rather than through a scheduled automation.

## Conclusion

The implementation demonstrates centralized Linux package management using Ansible, reducing the need for manual per-server updates and providing a repeatable, version-controlled automation process.