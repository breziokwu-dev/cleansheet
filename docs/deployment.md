# Deployment preparation

This guide prepares CleanSheet for a container-based deployment. It does not select a hosting provider or make the application production-ready for confidential company data.

## Build and run locally

From the repository root:

```bash
docker build -t cleansheet:local .
docker run --rm -p 8501:8501 cleansheet:local
```

Open `http://localhost:8501` in your browser. The container exposes Streamlit on port `8501` and includes a health check at `/_stcore/health`.

To stop the container, press `Ctrl+C` in the terminal running it.

## Dependencies

- `requirements.txt` contains packages required to run the app.
- `requirements-dev.txt` includes runtime packages plus test tooling.

Set up a local development environment with:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements-dev.txt
python -m pytest -q
```

## Before selecting a hosting provider

Confirm the company's requirements with its owner or IT administrator:

1. Approved hosting provider and data-processing terms.
2. Required hosting region and any data-residency restrictions.
3. Approved identity provider (for example, Microsoft Entra ID or Google Workspace), if company sign-in is required.
4. Named administrator and employee accounts; no shared logins or public self-registration.
5. Expected concurrent usage, file sizes, and peak processing time.
6. Retention and deletion requirements for uploaded files, exports, logs, and backups.
7. Who is responsible for security updates, monitoring, backups, and incident response.

Do not upload real customer, employee, financial, or other confidential company records until the company has approved the hosting and data-handling design.

## Current limitations

This container is deployment packaging only. It does not add authentication, authorization, company-level data isolation, a database, durable audit logging, or a verified file-deletion lifecycle. Streamlit session cleanup is not a guarantee that all in-memory copies are immediately erased. Do not treat this milestone as approval for production use with sensitive data.

## Secrets

Do not commit `.env` files, Streamlit secrets, passwords, tokens, or private keys. Configure any future production secrets through the chosen hosting provider's secret manager. `.env.example` contains placeholders only.

## Next milestones

1. Confirm the company's identity provider and hosting constraints.
2. Design invite-only authentication and server-side role checks.
3. Define temporary file handling and deletion behavior, including restarts and failed jobs.
4. Run container, upload-limit, security, and concurrency tests.
5. Complete a company-approved pilot before production rollout.
