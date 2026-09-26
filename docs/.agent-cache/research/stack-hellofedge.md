# Stack Research for Hellofedge — Sept 2026

**Target:** Greenfield single-user trading-analysis app. 24/7 uptime, under 30 EUR/month total.  
**Location:** Benin (UTC+1).

---

## 1. Cheap Always-On Hosting

### Small VPS (2 vCPU, 4 GB RAM)

#### Hetzner Cloud
- **Current:** CX23 (2 vCPU, 4 GB RAM) after June 2026 price adjustment.
- **Pricing:** €7.99/month (or €0.0060/hour) — was €3.79 for older CX22 model.
- **Status:** Fits under 10 EUR if in Germany datacenter.
- **Source:** [Hetzner price adjustment June 2026](https://docs.hetzner.com/general/infrastructure-and-availability/price-adjustment/)

#### OVH / Contabo
- Not detailed in current 2026 searches; Hetzner remains most cited for under-10-EUR VPS at this spec.

### Managed Always-On Options (1 worker + Postgres)

#### Fly.io
- **Always-on 24/7 worker:** Shared-cpu-1x with 256 MB RAM ≈ $2.02/month.
- **Postgres managed:** Not offered; must self-host on app VPS.
- **Cost:** App only $2.02/mo, but Postgres storage adds cost if separate.
- **Status:** Cheapest for app alone; Postgres requires workaround.
- **Source:** [Render vs Railway vs Fly.io pricing 2026](https://render.com/articles/railway-vs-fly-io)

#### Railway
- **No free tier.** Metered: $20/vCPU + $10/GB-month minimum.
- **1 vCPU / 2 GB always-on:** ~$40/month (worker + Postgres ~$42/mo).
- **Status:** Over budget for this app size.

#### Render
- **Starter instance:** ~$7/month (0.5 CPU, 512 MB).
- **Standard instance:** ~$25/month (1 CPU, 2 GB).
- **Postgres managed:** Included from paid tier onward.
- **Status:** Starter alone fits; combined with Postgres, ~$25–30/mo depending on storage.
- **Source:** [Render vs Railway vs Fly.io: Pricing Compared](https://dev.to/pavel-hostim/render-vs-railway-vs-flyio-pricing-compared-2026-2e5p)

#### Verdict
- **Under ~10 EUR:** Hetzner CX23 VPS (€7.99) + self-hosted Postgres on same server.
- **Under ~25–30 EUR:** Render Starter/Standard with managed Postgres.
- **Fly.io** works if you run Postgres externally (e.g., separate Postgres-as-a-Service).

---

## 2. Real-Time USD/JPY Price Source (No OANDA)

### Twelve Data
- **USD/JPY:** Yes, 1,300+ currency pairs across 140 currencies.
- **Live:** WebSocket real-time feed available.
- **Historical:** 20+ years.
- **Free tier:** Exists; limits not specified in search results.
- **Paid:** Per-subscription model; no hidden fees.
- **Status:** Strong candidate; WebSocket support confirmed.
- **Source:** [Twelve Data Forex](https://twelvedata.com/exchanges/physical_currency)

### Finnhub
- **USD/JPY:** Yes, real-time forex rates via REST API.
- **Live:** REST endpoint (websocket status not confirmed).
- **Free tier:** Generous; well-structured.
- **Historical:** Not specified for forex depth.
- **Status:** Viable alternative; generous free tier.
- **Source:** [Finnhub API docs](https://finnhub.io/docs/api/forex-rates)

### Polygon (Massive)
- **USD/JPY:** Limited to major pairs; unclear if USD/JPY included.
- **Live:** High-frequency US market data; forex coverage limited.
- **Status:** Not ideal for global forex pairs.
- **Source:** [The 2026 Market Data API Scorecard](https://eodhd.com/financial-academy/financial-faq/the-2026-market-data-api-scorecard-comparing-6-leading-providers/)

### Dukascopy
- **USD/JPY:** Yes; 1600+ instruments.
- **Live:** Free historical tick/M1 data via public export tool + REST API.
- **API:** Free API key via Dukascopy account.
- **Plugins:** MT5, cTrader, Sierra Chart supported.
- **Status:** Free historical robust; live feed via REST API (rate limits unknown).
- **Source:** [Dukascopy Historical Data](https://www.dukascopy.com/swiss/english/marketwatch/historical/), [Dukascopy API](https://www.dukascopy.com/trading-tools/api/apply)

### cTrader Open API
- **USD/JPY:** Via cTrader brokers (e.g., IC Markets, Pepperstone, Deriv).
- **Live:** WebSocket + REST streaming via cTrader Open API.
- **Demo account:** Free tier available at many cTrader brokers.
- **Status:** Viable if broker demo remains active.

### MetaTrader 5
- **USD/JPY:** Yes.
- **Live:** WebSocket + REST via MT5 API or broker plugin.
- **Free demo:** Available via most brokers.
- **Status:** Viable; similar to cTrader.

### OANDA Account Restriction by Country
- **Benin:** Not explicitly mentioned in search results; OANDA typically restricts based on EU/US regulation. West Africa restrictions unclear; **requires direct inquiry with OANDA**.

### Verdict
- **Recommended:** **Twelve Data** (WebSocket confirmed, no broker needed) or **Dukascopy** (free historical + free API, no account restriction known).
- **Alternative:** **Finnhub** (generous free tier, REST only; no WebSocket).
- **Avoid:** Polygon (limited forex), Dukascopy live rate-limits unknown.

---

## 3. TimescaleDB Licensing & Suitability

### License
- **Core:** Apache-2.0 (fully free, open-source).
- **Advanced features:** Timescale License (TSL) for compression policies, continuous aggregate automation.
  - **Restriction:** TSL applies only if offering TimescaleDB as a hosted Database-as-a-Service.
  - **Self-hosted:** You may use all features freely; no restrictions.
- **Summary:** Fully free for self-hosted single-user app.
- **Source:** [Timescale License (TSL)](https://www.tigerdata.com/legal/licenses), [How Timescale Builds a Self-Sustaining Open-Source Business](https://medium.com/timescale/how-we-are-building-a-self-sustaining-open-source-business-in-the-cloud-era-a7701516a480)

### Suitability for ~3M Rows (USD/JPY M1 over years)
- **Storage:** ~3M rows × 64 bytes/row (timestamp, OHLCV, indicators) ≈ 192 MB uncompressed.
  - Compression: Further ~50–70% reduction possible.
- **Performance:** Plain PostgreSQL handles this easily; TimescaleDB hypertables not strictly necessary.
- **Recommendation:** **Plain PostgreSQL is sufficient.** TimescaleDB adds zero benefit at this scale.
  - Use TimescaleDB if: (a) you plan to add more symbols, (b) you need automated retention policies, or (c) you anticipate terabyte-scale later.
  - Cost: Same (both free self-hosted).
- **Source:** [TimescaleDB Review 2026](https://www.softwares.com/software/timescaledb), [TimescaleDB for Self-Hosted](https://www.supascale.app/blog/timescaledb-for-selfhosted-supabase-time-series-data-guide)

---

## Recommended Stack Summary

| Component | Option | Cost | Notes |
|-----------|--------|------|-------|
| **VPS** | Hetzner CX23 (€7.99/mo) | €7.99 | 2 vCPU, 4 GB RAM, 40 GB SSD |
| **OS + Postgres** | Self-hosted on VPS | Included | Plain PostgreSQL (TimescaleDB optional, free if added) |
| **Forex data** | Twelve Data or Dukascopy | €0–5 | Free tier for prototyping; Dukascopy completely free for historical + REST |
| **Telegram alerts** | Built-in (no cost) | €0 | Bot API via VPS |
| **Claude API** | As-needed | ~€5–10/mo | Per usage; budget ~100 calls/day at $0.001/call |
| **Domain (optional)** | Namecheap, Gandi | €0–3/yr | Not critical for internal app |
| **Total** | | ~€15–20/mo | Well under 30 EUR; leaves headroom for scaling |

---

## Next Steps
1. **Confirm OANDA Benin restriction:** Contact OANDA support directly.
2. **Test Twelve Data / Dukascopy free tier:** Start with live paper trading to validate data quality.
3. **Validate VPS specs:** Hetzner 2 vCPU sufficient for 24/7 Python analysis + Telegram + small web UI.
4. **Prototype Postgres schema:** 3M rows fit easily; design retention policy for rolling 2–3 years of data.

