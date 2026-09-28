# JeevanMitra 2.0 Operations Runbook

## Deployments
- **Environments**: Local, Staging, Production.
- **Process**: Code merged to main triggers CI pipeline -> Lints, type checks, unit/integration tests -> Docker build -> Staging deployment. Manual approval required for Production.
- **Rollback**: Previous Docker images should be tagged. In case of failure, deploy the immediate previous tag and revert database migrations if necessary.

## Monitoring
- **Health Checks**: `/health/live`, `/health/ready`
- **Metrics**: Error rates, latency, 5xx spikes, AI provider failure rates, queue backlog.
- **Alerting**: Trigger alerts for high AI failure rates, scheduled job failures, queue backups.

## Backups & Recovery
- **Database**: Daily encrypted automated backups.
- **Retention**: Defined data retention policy for backups, audio storage, and user data.
- **Restore**: Documented procedure for restoring the latest database snapshot to staging for verification.

## Incident Response
1. Identify the issue via Sentry/Logs.
2. If critical AI hallucination/bypass occurs, disable the AI subsystem and fall back to manual workflows.
3. If data integrity is compromised, initiate lockdown mode (read-only) while investigating.
