# Automation Setup Guide

## Overview

This project now uses two GitHub Actions workflows:

- `test_automation.yml` keeps an eye on pushes and pull requests.
- `production_automation.yml` updates market data every weekday evening.

No special staging branch is needed. Everything runs from `main` and feature branches.

## Workflow Structure

### Test Automation (CI)
- **Branches**: `main` and any branch under `feature/**`
- **Trigger**: Push, pull request, or manual dispatch
- **Purpose**: Run `analytics/test_enhanced_workflow.py` to be sure the automation code still loads and connects to the database

### Production Automation
- **Branch**: `main`
- **Trigger**: Monday–Friday at 21:00 UTC (22:00 Berlin during daylight saving, 21:00 otherwise)
- **Purpose**: Run the incremental market data update and commit any database/log changes

## Workflow Files

### `.github/workflows/test_automation.yml`
- **Name**: Test Automation
- **What it does**: Installs dependencies and runs `PYTHONPATH=. python analytics/test_enhanced_workflow.py`
- **When it runs**: Every push or pull request aimed at `main`, plus manual dispatch if you need it

### `.github/workflows/production_automation.yml`
- **Name**: Production Market Data Automation
- **What it does**: Performs the incremental update, prints diagnostics, and pushes changes back to `main`
- **When it runs**: Weekdays at `0 21 * * 1-5` (21:00 UTC)
- **Permissions**: Uses the built-in token with `contents: write` so the push step succeeds

## Typical Workflow

### 1. Create a feature branch
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

## Maintenance Checklist

- Review workflow runs a few times a week.
- Trim large log or database files if the repo grows too much.
- Update dependencies in `requirements.txt` when needed and make sure the test workflow passes.

If something breaks, start with the newest workflow logs, fix locally, push a branch, and let `test_automation.yml` confirm the fix. Merge once it is green.
