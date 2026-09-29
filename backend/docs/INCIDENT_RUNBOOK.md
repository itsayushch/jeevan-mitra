# Incident Runbook

- **Database Down**: Check container, restart DB. Validate volume mount.
- **AI Service Down**: Triggers fallback. Monitor logs and restart LLM gateway if needed.
- **High Latency**: Scale worker nodes via orchestrator.
