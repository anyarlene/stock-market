# Automation Setup Guide

## Overview

This project uses GitHub Actions for automated daily market data updates with separate testing and production environments.

## Workflow Structure

### Testing Environment
- **Branch**: `automation-daily-update`
- **Workflow**: `test_daily_update.yml`
- **Trigger**: Push to branch
- **Purpose**: Test automation changes before production

### Production Environment
- **Branch**: `main`
- **Workflow**: `production_automation.yml`
- **Trigger**: Daily at 10 PM Berlin time (UTC+1)
- **Purpose**: Production daily automation

## Workflow Files

### `.github/workflows/test_daily_update.yml`
- **Name**: Test Daily Market Data Update
- **Trigger**: Push to `automation-daily-update` branch
- **Schedule**: None (manual/push triggered)
- **Purpose**: Testing automation changes

### `.github/workflows/production_automation.yml`
- **Name**: Production Market Data Automation
- **Trigger**: Daily at 10 PM Berlin time
- **Schedule**: `0 21 * * *` (9 PM UTC)
- **Purpose**: Production daily automation

## Setup Process

### 1. Testing Phase
```bash
# Work on automation-daily-update branch
git checkout automation-daily-update

# Make changes to workflows
# Push changes
git push origin automation-daily-update

# test_daily_update.yml runs automatically
# Check GitHub Actions tab for results
```

### 2. Production Deployment
```bash
# Create Pull Request to merge to main
# Review and merge PR

# production_automation.yml takes over
# Runs daily at 10 PM Berlin time
```

## Workflow Steps

Both workflows execute the same steps:

1. **Checkout code** - Get latest code
2. **Set up Python** - Install Python 3.12
3. **Install dependencies** - Install required packages
4. **Initialize database** - Create database and load symbols
5. **Run market data update** - Fetch latest market data
6. **Show results** - Display database status
7. **Commit and push changes** - Save updated data to repository

## Monitoring

### GitHub Actions
- Go to repository → Actions tab
- View workflow runs and logs
- Check for success/failure status

### Logs
- Workflow results: `analytics/logs/workflow_results.json`
- Automation logs: `analytics/logs/automation.log`

### Database
- Updated database: `analytics/database/etf_database.db`
- Automatically committed to repository

## Troubleshooting

### Common Issues

1. **Permission denied (403 error)**
   - Solution: Enable "Read and write permissions" in repository settings
   - Go to Settings → Actions → General → Workflow permissions

2. **Module not found errors**
   - Solution: PYTHONPATH is set correctly in workflows
   - No action needed

3. **Git push conflicts**
   - Solution: Workflows use `git pull --rebase` to handle conflicts
   - No action needed

### Testing Workflow Issues
- Check if running on correct branch (`automation-daily-update`)
- Verify workflow file exists and is valid
- Check GitHub Actions logs for specific errors

### Production Workflow Issues
- Verify workflow is on `main` branch
- Check schedule timing (10 PM Berlin time)
- Monitor via GitHub Actions tab

## Best Practices

1. **Always test on automation-daily-update branch first**
2. **Verify workflows run successfully before merging to main**
3. **Monitor GitHub Actions tab regularly**
4. **Check logs for any issues**
5. **Keep workflow files simple and maintainable**

## Configuration

### Repository Settings
- **Actions permissions**: "Allow all actions and reusable workflows"
- **Workflow permissions**: "Read and write permissions"
- **Branch protection**: Optional, but recommended for main branch

### Environment Variables
- `GITHUB_TOKEN`: Automatically provided by GitHub Actions
- No additional secrets required for basic functionality

## Maintenance

### Regular Tasks
- Monitor workflow success rates
- Check for any failed runs
- Review logs for performance issues
- Update dependencies as needed

### Updates
- Test changes on automation-daily-update branch
- Verify workflows run successfully
- Merge to main for production deployment
- Monitor production automation

## Support

For issues with automation:
1. Check GitHub Actions logs
2. Review workflow files for errors
3. Verify repository permissions
4. Test on automation-daily-update branch first
