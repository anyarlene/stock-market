# Automation Setup Guide

## Overview

Two GitHub Actions workflows:

- `test_automation.yml` - CI testing on pushes and pull requests
- `production_automation.yml` - Automated daily updates on weekdays

Workflows run on `main` and `feature/**` branches.

## Workflow Structure

### Test Automation (CI)
- **Branches**: `main` and any branch under `feature/**`
- **Trigger**: Push, pull request, or manual dispatch
- **Purpose**: Run `analytics/test_enhanced_workflow.py` to be sure the automation code still loads and connects to the database

### Production Automation
- **Branch**: `main`
- **Trigger**: Monday–Friday at 21:15 UTC (22:15 Berlin during daylight saving, 21:15 otherwise)
- **Purpose**: Run the incremental market data update, export website data, and commit all changes

## Workflow Files

### `.github/workflows/test_automation.yml`
- **Name**: Test Automation
- **What it does**: Installs dependencies and runs `PYTHONPATH=. python analytics/test_enhanced_workflow.py`
- **When it runs**: Every push or pull request aimed at `main`, plus manual dispatch if you need it

### `.github/workflows/production_automation.yml`
- **Name**: Production Market Data Automation
- **What it does**: 
  1. Performs the incremental market data update
  2. Runs database diagnostics
  3. Exports website data (JSON files)
  4. Commits and pushes database, logs, and website data to `main`
- **When it runs**: Weekdays at `15 21 * * 1-5` (21:15 UTC)
- **Permissions**: Uses the built-in token with `contents: write` so the push step succeeds
- **Website Deployment**: Automatically triggers `deploy-website.yml` when data is pushed

## Typical Workflow

### 1. Create a feature branch
**Always work on feature branches, never directly on `main`:**
```bash
git checkout -b feature/my-update
```

### 2. Make your changes and push
```bash
git add .
git commit -m "Describe my update"
git push origin feature/my-update
```

The `Test Automation` workflow runs automatically. Check the Actions tab to confirm it passes.

### 3. Open a pull request
- Review feedback.
- When ready, merge into `main`.

### 4. Production automation takes over
- The weekday schedule runs from `main`.
- The job pulls, updates the database, commits results, and pushes back to `main`.

## Monitoring

- **GitHub Actions**: Repository → Actions → select either workflow and review the logs.
- **Logs in repo**: `analytics/logs/workflow_results.json` and any new files in `analytics/logs/`.
- **Database**: Updated file stays at `analytics/database/etf_database.db`.
- **Website Data**: Updated JSON files in `website/data/` are automatically deployed to GitHub Pages.

## Troubleshooting Tips

1. **Push fails in production job**  
   - Make sure repository settings allow workflows to have read/write permissions (Settings → Actions → General).

2. **Module not found**  
   - The workflow sets `PYTHONPATH=.` before running Python scripts. If you add new packages, update `requirements.txt`.

3. **Conflicts when pushing**  
   - The job runs `git pull origin main --rebase`. If conflicts appear, fix them locally on `main`, push, and the next run will succeed.

## Best Practices

1. Keep feature branches small and focused.
2. Let `test_automation.yml` be your first safety net before opening a pull request.
3. Watch the Actions tab for both workflows after merging.
4. Keep workflow files simple and only install what you need.

## Configuration Reminders

- **Repository settings**  
  - Allow all actions and reusable workflows.  
  - Set workflow permissions to “Read and write”.
- **Secrets**  
  - The built-in `GITHUB_TOKEN` is enough today. Add more secrets only if future steps need them.

## Airflow (Optional)

For local testing with Airflow, see `analytics/docs/airflow_setup.md`. The DAG runs the same scripts as production automation.
