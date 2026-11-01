# SOAR â€” Final Implementation and Validation

**Project:** Innovatech Solutions â€” Case Study 2
**Phase:** 2.6 â€” SOAR Security Automation
**Validation date:** 1 November 2026
**Overall result:** Successful controlled demonstration

## 1. Implementation Overview

A Python-based SOAR application was deployed on a dedicated AWS EC2 instance in the Frankfurt region.

The implementation integrates with Prometheus and Alertmanager to receive infrastructure alerts, evaluate response rules, record incidents, and prepare operator notifications.

Two security-response playbooks were developed:

- **IP containment:** Validates suspicious addresses, protects infrastructure networks, checks authorized targets, and records simulated containment.
- **Service containment:** Validates approved services and simulates containment of suspicious services.

Both alert-driven containment playbooks operate in dry-run mode.

An additional restricted, administrator-controlled helper was implemented to demonstrate real temporary containment of a disposable Linux service.

## 2. Automated Testing

The Python SOAR implementation passed **95 automated unit tests**, covering:

- Alert processing and authentication
- Duplicate event handling
- SOAR rule evaluation
- IP and service containment validation
- Authorization restrictions
- Recovery scheduling and deadline validation
- Exclusive operation locking
- Simulated systemd failures
- Recovery-before-containment execution ordering

**Result:** 95 tests passed.

## 3. AWS Live Containment Test

**Target:** `soar-demo.service`
**SOAR application:** `innovatech-soar.service`
**Execution method:** Administrator-triggered Python helper
**Planned containment duration:** 90 seconds

The helper scheduled and verified systemd recovery before stopping the disposable service.

### Observed timeline

| Event | UTC time |
|---|---|
| Service containment | 15:15:43 |
| Automatic restoration | 15:17:14 |
| Observed interruption | Approximately 91 seconds |

Systemd logs confirmed that the recovery service executed successfully and restarted `soar-demo.service`.

The main SOAR application remained active throughout the demonstration.

**Result: PASS**

## 4. Recovery and Cleanup

After successful restoration:

- Both `soar-demo.service` and `innovatech-soar.service` were verified active.
- The completed recovery timer was disabled and stopped.
- The pending containment record was archived as `completed.json`.
- The stale `pending.json` marker was removed.
- The original audit log was preserved.

The completed record includes a recovery verification timestamp of `2026-11-01T15:19:42.439006+00:00`.

**Final infrastructure state: Healthy.**

## 5. Security Controls

The live containment helper is restricted to the disposable demonstration service and is installed with root-only execution permissions.

The SOAR web application continues to operate without privileges to execute the helper.

The system records containment operations and requires recovery scheduling to be verified before stopping the service.

## 6. Limitations

Live containment was initiated by an administrator, not directly by an incoming Alertmanager webhook.

The IP containment playbook remains dry-run-only.

Recovery after an EC2 reboot has not been experimentally verified.

The current completion-record reconciliation process requires administrative action rather than operating fully unattended.

## 7. Conclusion

The SOAR implementation successfully demonstrated alert reception, rule evaluation, incident logging, two validated security-response playbooks, and real administrator-controlled service containment with automatic systemd recovery.

The implementation provides a working foundation for security automation while restricting potentially disruptive actions to an explicitly approved demonstration target.
