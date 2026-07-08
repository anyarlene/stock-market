# Get Metabase Live — Oracle Cloud Setup

> **⚠️ SUPERSEDED** by `stock-market-v2-reporting-layer.md` (v3 DuckDB-only roadmap).
> The Oracle Cloud VM + Metabase infrastructure is retired; this document is kept for historical reference only.

**Goal:** dashboard accessible from any browser, always on, zero cost, zero daily work.

**Time needed:** ~20 minutes (one time only).

---

## Step 1 — Create your Oracle Cloud account (5 min)

1. Go to [cloud.oracle.com](https://cloud.oracle.com)
2. Click **Start for free**
3. Fill in your details — **no credit card required** for Always Free resources
4. Verify your email and complete signup

---

## Step 2 — Create the VM (5 min)

1. Log in → click **Create a VM instance**
2. Change the name to `etf-metabase` (optional)
3. Under **Image and shape**, click **Change shape**
   - Select **Ampere** tab
   - Choose `VM.Standard.A1.Flex`
   - Set **OCPUs: 2**, **Memory: 12 GB**
   - Click **Select shape**
4. Confirm the image is **Ubuntu 22.04**
5. Under **Add SSH keys**, choose **Generate a key pair for me** and download both files (you may need them later)
6. Scroll down to **Advanced options → Management**
7. Under **User data**, paste the entire contents of [`scripts/oracle-cloud-init.yml`](../../scripts/oracle-cloud-init.yml)
8. Click **Create**

The VM will be ready in about 2 minutes.

---

## Step 3 — Open port 3000 in Oracle's firewall (5 min)

Oracle has a separate network-level firewall you must open manually.

1. On the instance detail page, click the **Subnet** link
2. Click **Default Security List**
3. Click **Add Ingress Rules**
4. Fill in:
   - Source CIDR: `0.0.0.0/0`
   - IP Protocol: TCP
   - Destination Port Range: `3000`
5. Click **Add Ingress Rules**

---

## Step 4 — Wait for Metabase to start (~3 min)

Find your VM's **Public IP address** on the instance detail page.

Open in your browser:
```
http://<your-public-ip>:3000
```

If you see a loading screen, wait 2–3 minutes — Metabase (Java) takes a moment on first boot.

---

## Step 5 — Connect Metabase to Supabase (5 min)

1. Complete the Metabase setup wizard (create your admin account)
2. When asked about data, choose **I'll add my data later**
3. Go to **Admin → Databases → Add a database**

Fill in these fields:

| Field | Value |
|---|---|
| Database type | PostgreSQL |
| Display name | ETF Analytics |
| Host | your Supabase host (from the Session Pooler URL: `aws-0-[region].pooler.supabase.com`) |
| Port | `5432` |
| Database name | `postgres` |
| Username | `postgres.[your-project-ref]` |
| Password | your Supabase DB password |
| SSL mode | Required |

> Your Supabase Session Pooler URL has this format:
> `postgresql://postgres.[ref]:[password]@aws-0-[region].pooler.supabase.com:5432/postgres`
> The username is everything between `//` and `:`, the host is after `@`.

4. Click **Save** — Metabase will sync the schema (~1 minute)
5. You should see the 3 mart tables: `mart_price_history`, `mart_52week_metrics`, `mart_entry_thresholds`

---

## Step 6 — Build the dashboard with Cursor AI (optional)

Enable MCP in Metabase so Cursor can build the dashboard for you:

1. Go to **Admin → AI → MCP** → toggle **MCP server ON**
2. Enable **Cursor and VS Code**

Add to Cursor settings (Settings → MCP Servers):

```json
{
  "mcpServers": {
    "metabase": {
      "url": "http://<your-oracle-ip>:3000/api/metabase-mcp",
      "transport": "streamable-http"
    }
  }
}
```

Then in Cursor chat, use the prompt in [`analytics/docs/metabase_setup.md`](metabase_setup.md#6-build-the-dashboard-with-cursor-ai).

---

## Done

Your dashboard is live at `http://<your-oracle-ip>:3000`.

GitHub Actions refreshes the data every weekday night at 21:15 UTC.
You open the URL, see today's data, close the browser. Nothing to run.

---

## Troubleshooting

**Browser shows "connection refused"**
- Wait another 2–3 minutes — Metabase starts slowly on first boot
- Check Oracle security list has port 3000 open (Step 3)

**Metabase loads but shows no tables**
- Go to Admin → Databases → click your DB → Sync database schema
- Check the connection credentials match your Supabase Session Pooler URL exactly

**VM public IP changed after reboot**
- Oracle Always Free VMs use ephemeral IPs by default
- Assign a **Reserved Public IP** (free) to make the IP permanent:
  Instance details → Primary VNIC → IP address → Reserve
