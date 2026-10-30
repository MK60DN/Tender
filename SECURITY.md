# Security Policy

## Supported version

Security fixes target the current `main` branch and the latest release.

## Reporting a vulnerability

Use GitHub Private Vulnerability Reporting / Security Advisories for this
repository. Do not open a public issue containing secrets, personal data,
database dumps, exploit details or production URLs.

## Repository hygiene

- `.env`, session secrets, runtime databases and tenant data are ignored.
- Demo authentication is not production authentication.
- Production deployments require OIDC, RBAC, secret rotation, encryption,
  retention controls and jurisdiction-specific compliance review.
- Raw learner, family, health and identity data must never be written on-chain.
