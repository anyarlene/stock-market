# Airflow Setup Guide

## Overview

This guide shows how to run Apache Airflow locally with Docker. You can reuse the same DAG later on any server or managed Airflow service. GitHub Actions stays in place for nightly production runs, while Airflow is great for local orchestration, demos, or dry-runs.

## Prerequisites

- Docker Desktop (or Docker Engine) installed and running.
- `docker compose` command available.
- Git repository cloned locally.

## Project Structure

```
airflow/
├─ docker-compose.yaml
├─ Dockerfile
├─ env.example
├─ dags/
│  └─ market_data_update.py
├─ logs/
└─ plugins/
```

- `market_data_update.py` mirrors the GitHub Actions workflow. It initializes the SQLite database, loads symbols, runs the incremental update, and prints diagnostics.
- The entire repository mounts into the container at `/opt/airflow/project` so the DAG can call the existing scripts without duplication.

## First-Time Setup

1. **Copy the environment file.**
   ```bash
   cd airflow
   cp env.example .env
   ```
   Adjust `AIRFLOW_UID` if your host UID is different (see comments inside the file).

2. **Build images and initialize Airflow metadata.**
   ```bash
   docker compose build
   docker compose up airflow-init
   ```
   **Note**: The Dockerfile has been configured to work with Airflow 2.9.1 and SQLAlchemy 1.4.x (compatibility fix).
   Re-run `docker compose build` whenever you change files under `airflow/` (for example updating `requirements.txt`).

3. **Start the Airflow services.**
   ```bash
   docker compose up
   ```
   Keep this terminal running, or run `docker compose up -d` to start in the background.

4. **Access the UI.**
   - Open <http://localhost:8080>.
   - Log in with the default credentials.

## Daily DAG

- DAG ID: `market_data_incremental_update`
- Schedule: Weekdays at 21:15 UTC (same as the production GitHub Action).
- Tasks:
  1. `initialize_database`: runs `analytics/database/init_db.py` and `load_symbols.py`.
  2. `run_incremental_update`: runs `analytics/enhanced_workflow.py --step incremental`.
  3. `show_results`: runs `analytics/database_diagnostic.py`.
- The DAG sets `PYTHONPATH=/opt/airflow/project` so all analytics modules import correctly.

### Manual Trigger

In the Airflow UI, switch the toggle to “On”, then press “▶ Trigger DAG”. Watch the three task boxes turn green when everything succeeds.

## Stopping and Cleaning Up

- Stop services: `docker compose down`
- Remove database volume (if you want a clean slate): `docker compose down --volumes --remove-orphans`

## Production vs Local

- **GitHub Actions** is the production automation that runs in the cloud. It updates the database, exports website data, and commits everything to the repository. This is the source of truth for production updates.
- **Airflow (local)** is perfect for:
  - testing workflow changes before deploying to production
  - rehearsing the workflow locally without affecting production
  - debugging issues in a controlled environment
  - demonstrating orchestration skills to stakeholders

**Important**: 
- Airflow only runs when Docker containers are running locally
- Scheduled runs in Airflow UI show data interval dates, not execution times
- If containers aren't running at the scheduled time, runs won't execute (but may show as scheduled in the UI)
- Always work on feature branches, never directly on `main`

When you are ready to host Airflow remotely, reuse this same folder. Point `docker-compose.yaml` at a VM or adapt the DAG to Astro, MWAA, or Google Composer with minimal tweaks.

## Next Steps (Optional Enhancements)

- Add email or Slack alerts by configuring Airflow connections.
- Create a second DAG to rebuild the website assets once new data arrives.
- Parameterize the DAG (for example pass a manual date range to reprocess specific days).

Keeping the setup simple today makes it easy to scale tomorrow.

