# Stock Scanner Website — Free Starter

This project turns the four supplied Google Colab notebooks into a GitHub Actions + Supabase + GitHub Pages workflow.

## What is included

- Hourly scanner: `scanner_hourly_v2 (1).ipynb`
- Daily scanner: `scanner_daily_stockbee_updated (1).ipynb` (daily section)
- EOD volume scanner: `scanner_volume_EOD_v5 (1).ipynb`
- Stockbee US scanner: `Stockbee_US_Screener (1).ipynb`
- Static dashboard with tabs
- Supabase PostgreSQL schema for history
- GitHub Actions schedules
- JSON fallback: the site still works if Supabase is not configured

## Important

This is a migration kit, not a claim that the external services have been connected for you. You must create your own GitHub repository and Supabase project and add the required secrets.

For a genuinely £0 setup, use a **public GitHub repository** so standard GitHub-hosted Actions runners are free. Do not put private credentials in the repository.

## Quick setup

1. Create a public GitHub repository.
2. Upload this project.
3. Create a free Supabase project.
4. Run `supabase/schema.sql` in Supabase SQL Editor.
5. In GitHub repository Settings → Secrets and variables → Actions, add:
   - `SUPABASE_URL`
   - `SUPABASE_SERVICE_ROLE_KEY`
6. Enable GitHub Pages from the repository's Actions/Pages settings using the provided workflow.
7. Run the hourly workflow manually once before relying on the schedule.
8. Open the Pages URL.

If Supabase secrets are absent, scanner results are still written to `public/data/*.json` and the dashboard can display them.

## Schedule

The schedules are deliberately separated:

- hourly: one run near the top of each hour during the week
- daily: once per weekday
- EOD volume: once per weekday
- Stockbee: once per weekday

The exact market-time scheduling should be adjusted after the first live test because GitHub Actions cron is UTC and market daylight-saving rules change.

## Source-derived scanner scope

The dashboard labels preserve the terminology from the supplied notebooks. The hourly notebook contains Option Sell, Rathod Bullish, NR7, Momentum, Dual BB 15m/1h Bull/Bear, BullBhai, Short Term Breakout, Potential Breakout, 100% Buy Breakout, and Possible Bottom Out. The daily notebook contains Bearish Momentum, VCP, Satish, Hardik, NR6, Rocket Base, EP Breakout, 20-day High, 2-month High, Gap Up and Up 4%. The EOD notebook is the high-volume scan. The Stockbee notebook contains Extreme Sales Growth, Sales Growth, Growth/Turnaround, Earnings + Sales and ATR Momentum.

## Safety / financial-content note

The website should clearly state that scanner results are informational, not investment advice. Before AdSense application, add original educational articles, About, Contact, Privacy Policy, Terms/Disclaimer and clear navigation. Do not publish copied financial content.
