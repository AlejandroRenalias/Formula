# Security Policy

## Supported code

This project is under active development. Security fixes are applied to the current `main` branch.

## Reporting a vulnerability

Please do not publish API keys, tokens, credentials, or sensitive exploit details in a public issue.

If you find a security vulnerability, report it privately through GitHub's security reporting/advisory features for this repository when available. Include:

- the affected file or component;
- steps to reproduce;
- expected vs. observed behavior;
- impact and any suggested mitigation.

## Secrets

The repository must never contain real API keys, access tokens, passwords, `.env` files, or Streamlit secret files. Future live LLM integrations must read credentials from environment variables or another secret manager and must keep them out of source control, tests, logs, screenshots, and prompts.

## Dependency security

CI runs `pip-audit` against the resolved Python environment. Dependabot is configured to surface dependency updates. A green audit reduces known-dependency risk but is not a guarantee that the application has no vulnerabilities.
