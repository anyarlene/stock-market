# Metabase Dashboard Integration - Recommendations

## Executive Summary

**Recommendation: Use self-hosted Metabase with PostgreSQL database**

- ✅ **100% Free** - Open source, no licensing costs
- ✅ **Daily Updates** - Integrates seamlessly with existing GitHub Actions workflow
- ✅ **Professional Dashboards** - Rich visualization capabilities
- ✅ **No Impact on Website** - Website remains unchanged
- ✅ **Scalable** - Can grow with your needs

---

## 1. Deployment Options Comparison

### Option A: Self-Hosted Metabase (RECOMMENDED) ⭐

**Pros:**
- Completely free (open source)
- Full control over data and infrastructure
- No user limits
- Can run on GitHub Actions runner, local machine, or cloud server
- Best for long-term use

**Cons:**
- Requires initial setup (Docker makes this easy)
- You manage updates and maintenance

**Cost:** $0/month

### Option B: Metabase Cloud

**Pros:**
- Managed service (no setup)
- Automatic updates

**Cons:**
- Free tier: Only 5 users, 1 database
- Paid tier starts at $85/month
- Less control over data

**Cost:** $0/month (limited) or $85+/month (full features)

**Recommendation:** Use Option A (Self-Hosted)

---

## 2. Data Connection Strategy

### Current Setup
- **SQLite Database** (`analytics/database/etf_database.db`)
- **JSON Files** (`website/data/*.json`)
- **Market Insights Data** (`website/data/fear_greed_index.json`, etc.)

### Recommended Approach: PostgreSQL

**Why PostgreSQL?**
- Metabase works best with PostgreSQL
- Better performance for dashboards
- Supports more advanced queries
- Industry standard for analytics

**Implementation:**
1. Add PostgreSQL to Docker Compose (alongside Metabase)
2. Create daily sync script: SQLite → PostgreSQL
3. Metabase connects to PostgreSQL
4. Dashboards auto-refresh from PostgreSQL

**Alternative (Simpler):** Direct SQLite connection
- Metabase can connect to SQLite directly
- Good for testing/development
- Limited features compared to PostgreSQL

---

## 3. Directory Structure

```
dashboard/
├── docker-compose.yml              # Metabase + PostgreSQL setup
├── metabase-config/
│   └── .env                        # Environment variables
├── data-export/
│   ├── sqlite_to_postgres.py      # Daily sync script
│   └── market_insights_to_db.py   # Export market insights to DB
├── docs/
│   ├── setup_guide.md             # Setup instructions
│   └── dashboard_design.md        # Dashboard design notes
└── README.md                       # Quick start guide
```

---

## 4. Daily Update Integration

### Current Workflow
```
GitHub Actions (Mon-Fri, 21:15 UTC)
  ↓
1. Run incremental market data update
2. Export website data (JSON files)
3. Export market insights data (JSON files)
4. Commit and push changes
```

### Enhanced Workflow
```
GitHub Actions (Mon-Fri, 21:15 UTC)
  ↓
1. Run incremental market data update
2. Export website data (JSON files) ← Website unchanged
3. Export market insights data (JSON files) ← Website unchanged
4. Sync SQLite → PostgreSQL ← NEW
5. Export market insights to PostgreSQL ← NEW
6. Commit and push changes
```

**Metabase automatically refreshes** from PostgreSQL, so dashboards stay up-to-date!

---

## 5. Cost Breakdown

### Self-Hosted Metabase (Recommended)

| Component | Cost | Notes |
|-----------|------|-------|
| Metabase (Docker) | $0 | Open source |
| PostgreSQL (Docker) | $0 | Open source |
| GitHub Actions | $0 | Free tier sufficient |
| Hosting (if needed) | $0-5/month | Optional: Only if you want 24/7 access |

**Total: $0/month** (if running on GitHub Actions or locally)

### If You Want 24/7 Access

You can deploy to:
- **Railway.app** - Free tier available
- **Render.com** - Free tier available
- **Fly.io** - Free tier available
- **Your own server** - One-time cost

---

## 6. Implementation Steps

### Phase 1: Setup (One-time)
1. Create `dashboard/` directory
2. Set up Docker Compose with Metabase + PostgreSQL
3. Create database schema in PostgreSQL
4. Test Metabase connection

### Phase 2: Data Sync
1. Create SQLite → PostgreSQL sync script
2. Create market insights → PostgreSQL export script
3. Test data sync locally

### Phase 3: Workflow Integration
1. Add sync step to `enhanced_workflow.py`
2. Update GitHub Actions workflow
3. Test end-to-end

### Phase 4: Dashboard Creation
1. Design dashboards in Metabase
2. Create visualizations:
   - Fear & Greed Index gauge chart
   - S&P 500 sector performance
   - ETF holdings distribution
   - Market trends over time
3. Set up auto-refresh schedules

---

## 7. Technical Requirements

### New Dependencies
```python
# requirements.txt additions
psycopg2-binary>=2.9.0  # PostgreSQL connector
sqlalchemy>=2.0.0       # Already installed
```

### Docker Requirements
- Docker Desktop (for local development)
- Docker Compose (included with Docker Desktop)

### GitHub Actions
- No changes needed to runner (uses existing Ubuntu runner)
- PostgreSQL runs in Docker container during workflow

---

## 8. Advantages Over Website Dashboard

| Feature | Website (Current) | Metabase Dashboard |
|---------|------------------|-------------------|
| **Setup Complexity** | Low | Medium (one-time) |
| **Visualization Options** | Limited (Chart.js) | Extensive (built-in) |
| **Interactivity** | Basic | Advanced (filters, drill-downs) |
| **Data Refresh** | Manual page reload | Auto-refresh |
| **Sharing** | Public URL | Shareable dashboards |
| **Mobile Support** | Responsive | Native mobile app |
| **Cost** | Free | Free (self-hosted) |

---

## 9. Recommended Next Steps

1. **Review this document** - Confirm approach
2. **Create `dashboard/` directory** - Start setup
3. **Set up Docker Compose** - Metabase + PostgreSQL
4. **Test locally** - Verify everything works
5. **Create sync scripts** - SQLite → PostgreSQL
6. **Integrate with workflow** - Add to GitHub Actions
7. **Build dashboards** - Create visualizations
8. **Deploy** - Choose hosting option (optional)

---

## 10. Questions to Consider

1. **Where to host Metabase?**
   - Option A: Run on GitHub Actions (free, but only during workflow runs)
   - Option B: Deploy to cloud (Railway/Render/Fly.io) for 24/7 access
   - Option C: Run locally for personal use

2. **Do you need 24/7 access?**
   - If yes: Deploy to cloud service
   - If no: GitHub Actions is sufficient

3. **How many users?**
   - Self-hosted: Unlimited
   - Metabase Cloud free tier: 5 users max

---

## Conclusion

**Recommended Path:**
1. ✅ Use self-hosted Metabase (free, unlimited)
2. ✅ Use PostgreSQL for better performance
3. ✅ Integrate with existing GitHub Actions workflow
4. ✅ Keep website unchanged
5. ✅ Start with local setup, deploy to cloud later if needed

**Total Cost: $0/month** (if using GitHub Actions or free cloud tier)

**Time Investment:**
- Initial setup: 2-3 hours
- Dashboard creation: 2-4 hours
- Total: ~1 day of work

Would you like me to proceed with this approach?

