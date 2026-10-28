
# Monitoring Deployment

The monitoring environment will be deployed using Docker Compose on the monitoring EC2 instance.

Services:
- Grafana
- Prometheus
- Grafana Loki
- Prometheus Alertmanager

The deployment will include persistent storage, service configuration, internal container networking and health checks.

Grafana Alloy will collect logs and metrics from the monitored Linux systems.

The Docker Compose configuration and service-specific configuration files will be implemented during Phase 2.
