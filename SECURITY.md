# Security Policy

## Supported Versions

| Version | Supported |
|---|---|
| 1.x | Yes |

## Reporting a Vulnerability

If you discover a security vulnerability in this project, please report it privately.

**Do not open a public GitHub issue** for security vulnerabilities.

**Contact:** houcem0508@gmail.com

Include in your report:
- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Any suggested remediation

You will receive a response within 5 business days.

## Security Notes

This is a demonstration project. For production deployments:

- **Database credentials**: Use secrets management (Vault, AWS Secrets Manager) — never `.env` files
- **Airflow**: Configure Fernet key rotation and enable RBAC
- **PostgreSQL**: Use SSL connections (`sslmode=require`), restrict pg_hba.conf
- **Docker**: Run containers as non-root user; pin image digests for reproducibility
- **Airflow connections**: Store credentials in Airflow Connections, not DAG code
