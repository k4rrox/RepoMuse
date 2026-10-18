# Security

RepoMuse runs a local server and shows demos built from third-party code, so isolation matters.

## In scope

- Escaping the demo sandbox (same-origin access, network access, reading files outside preview assets).
- Reaching the server from another host or origin, or writing feedback cross-site.
- Path traversal or symlink tricks that expose files outside `web/` and `demos/`.
- Data that passes the validator but makes the page run script or open non-HTTPS links.

## Not in scope

- What an agent does when a user tells it to ignore the skills.
- Vulnerabilities inside an upstream project that a demo shows; report those upstream.

## Reporting

Please use GitHub's private vulnerability reporting ("Security" tab, "Report a vulnerability") rather than a
public issue. Include steps to reproduce. We aim to reply within a week.
