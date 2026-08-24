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

### Temporary upstream exception

`PYSEC-2026-3625` / `CVE-2026-57585` affects `msgpack 1.1.2`. The current upstream chain `fastf1 3.8.3 -> signalrcore 1.0.2` hard-pins that version even though the fixed `msgpack 1.2.1` is available.

Formula currently uses FastF1 historical-session loading only; it does not use FastF1's SignalR live-timing client or opt into SignalR MessagePack protocol handling, which is the affected code path. CI therefore carries one explicit, documented `pip-audit` exception for this advisory while Issue #4 tracks the upstream fix.

This exception must be removed as soon as `signalrcore` permits a fixed msgpack version, and it must be reassessed before any FastF1 live-timing/MessagePack functionality is added.
