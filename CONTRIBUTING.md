# Contributing

Thanks for your interest in contributing to regulatory-insight-engine. This repository is intended for internal/prototype use; contributions are welcome but please follow these minimal rules:

- Open issues for bugs or feature requests using the templates in `.github/ISSUE_TEMPLATE/`.
- Keep changes small and focused; follow the project's coding conventions.
- Run tests locally before proposing changes:

```bash
cd backend
source .venv/bin/activate
pytest -q
```

- For pull requests:
  - Base your branch on `main` and open a PR targeting `main`.
  - Provide a short description of the change and why it is needed.
  - Include tests for bug fixes where feasible.

Security: do not commit secrets or production data. If you discover a security issue, open a private issue or contact the repository owner directly.
