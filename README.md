# TTC Subway Alerts — TRMNL Plugin

Pushes live TTC subway alerts (Lines 1, 2, 5) to a TRMNL e-ink device using GitHub Actions. Runs every 5 minutes during weekday commute windows only (6–8 AM and 3–5 PM ET). Completely free — public repos get unlimited GitHub Actions minutes.

---

## Setup

### 1. Fork / push this repo to GitHub (must be public for unlimited free minutes)

### 2. Add the webhook secret

In your repo: **Settings → Secrets and variables → Actions → New repository secret**

| Name | Value |
|------|-------|
| `TRMNL_WEBHOOK_URL` | Your TRMNL Private Plugin webhook URL |

### 3. Create the TRMNL Private Plugin

1. Open your TRMNL dashboard → **Plugins** → **Private Plugin**
2. Create a new plugin and copy the webhook URL into the secret above
3. Paste the HTML template below into the plugin's **Markup** editor
4. Save

### 4. Test it

Trigger a manual run: **Actions → Push TTC Alerts to TRMNL → Run workflow**

---

## TRMNL HTML Template

Paste this into the Private Plugin's **Markup** field:

```html
<style>
  .ttc-wrap {
    display: flex;
    flex-direction: column;
    height: 100%;
    padding: 10px 12px 8px;
    font-family: var(--font-family, sans-serif);
    color: var(--color-primary, #000);
  }

  .ttc-header {
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    border-bottom: 2px solid currentColor;
    padding-bottom: 6px;
    margin-bottom: 8px;
  }

  .ttc-title {
    font-size: 15px;
    font-weight: 700;
    letter-spacing: 0.5px;
    text-transform: uppercase;
  }

  .ttc-time {
    font-size: 11px;
  }

  .ttc-lines {
    display: flex;
    gap: 8px;
    flex: 1;
  }

  .ttc-line {
    flex: 1;
    display: flex;
    flex-direction: column;
    border: 1.5px solid currentColor;
    border-radius: 6px;
    overflow: hidden;
  }

  .ttc-line-head {
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 5px 8px;
    border-bottom: 1.5px solid currentColor;
    background: var(--color-primary, #000);
    color: var(--color-background, #fff);
  }

  .ttc-badge {
    width: 20px;
    height: 20px;
    border-radius: 50%;
    border: 1.5px solid var(--color-background, #fff);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 10px;
    font-weight: 800;
    flex-shrink: 0;
  }

  .ttc-line-name {
    font-size: 10px;
    font-weight: 700;
    line-height: 1.2;
  }

  .ttc-line-sub {
    font-size: 8px;
    opacity: 0.75;
    line-height: 1;
  }

  .ttc-line-body {
    padding: 6px 8px;
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 5px;
  }

  .ttc-ok {
    font-size: 10px;
    font-weight: 600;
    display: flex;
    align-items: center;
    gap: 4px;
  }

  .ttc-alert {
    border-left: 2.5px solid currentColor;
    padding-left: 5px;
  }

  .ttc-sev {
    font-size: 8px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.4px;
    opacity: 0.7;
  }

  .ttc-alert-title {
    font-size: 9px;
    font-weight: 600;
    line-height: 1.3;
  }

  .ttc-alert-meta {
    font-size: 8px;
    opacity: 0.65;
    line-height: 1.3;
  }
</style>

<div class="ttc-wrap">
  <div class="ttc-header">
    <span class="ttc-title">TTC Subway</span>
    <span class="ttc-time">{{ merge_variables.updated_at }} · #{{ merge_variables.run_number }}</span>
  </div>

  <div class="ttc-lines">

    <!-- Line 1 -->
    <div class="ttc-line">
      <div class="ttc-line-head">
        <div class="ttc-badge">1</div>
        <div>
          <div class="ttc-line-name">Line 1</div>
          <div class="ttc-line-sub">Yonge–University</div>
        </div>
      </div>
      <div class="ttc-line-body">{{ merge_variables.line1_html }}</div>
    </div>

    <!-- Line 2 -->
    <div class="ttc-line">
      <div class="ttc-line-head">
        <div class="ttc-badge">2</div>
        <div>
          <div class="ttc-line-name">Line 2</div>
          <div class="ttc-line-sub">Bloor–Danforth</div>
        </div>
      </div>
      <div class="ttc-line-body">{{ merge_variables.line2_html }}</div>
    </div>

    <!-- Line 5 -->
    <div class="ttc-line">
      <div class="ttc-line-head">
        <div class="ttc-badge">5</div>
        <div>
          <div class="ttc-line-name">Line 5</div>
          <div class="ttc-line-sub">Eglinton Crosstown</div>
        </div>
      </div>
      <div class="ttc-line-body">{{ merge_variables.line5_html }}</div>
    </div>

  </div>
</div>
```

---

## How It Works

- **GitHub Actions** runs on cron every 5 minutes, but only during two UTC windows that cover the ET commute hours with DST tolerance
- **`fetch_and_push.py`** double-checks the current time in `America/Toronto` — if outside 6–8 AM or 3–5 PM ET (weekdays), it exits silently without making any API calls
- TTC alerts are fetched from `alerts.ttc.ca/api/alerts/live-alerts`, filtered to subway Lines 1/2/5, and pushed to TRMNL via the Private Plugin webhook

## Local Testing

```bash
pip install -r requirements.txt
TRMNL_WEBHOOK_URL="https://usetrmnl.com/api/custom_plugins/YOUR_UUID" python fetch_and_push.py
```

To test outside a commute window, temporarily comment out the `in_commute_window()` check in `main()`.
