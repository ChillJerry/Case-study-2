
# SOAR Deployment

The SOAR environment will be deployed using Docker Compose on the SOAR EC2 instance.

Services:
- Python FastAPI application
- PostgreSQL database

The FastAPI application will provide event ingestion, detection rules, automated response actions, incident management and Prometheus metrics.

PostgreSQL will store incidents and automated action results in persistent storage.

The database will be accessible only through the internal application network.

The Docker Compose configuration, application image and database initialization will be implemented during Phase 2.
