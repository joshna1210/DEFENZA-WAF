# AI-Powered WAF with Blockchain Audit Logging

A transformer/ML-assisted Web Application Firewall with a reverse proxy layer,
real-time traffic analysis, IP monitoring, vulnerability suggestions, and
tamper-evident audit logging via blockchain (Merkle-root batching).

## Architecture

```
Client → Proxy (9000) → Backend logs + rule engine → Target site
                             │
                             ├─► MongoDB (traffic_logs, analysis_results, ip_activity)
                             ├─► ML Engine (async risk scoring, keyword+BERT)
                             └─► Blockchain batch logger (Merkle root every N logs)

Frontend (React/Vite) → Backend REST API → Dashboard, Reports, Vulnerability views
```

## Why the proxy doesn't call ML synchronously

Running a BERT-sized model in the critical request path adds 50-300ms+ latency
per request on CPU, which is unacceptable for a live WAF. Instead:

1. **Fast layer** (proxy, inline, <5ms): regex/signature rules for SQLi, XSS,
   path traversal, known-bad headers. Can block immediately.
2. **Slow layer** (backend, async, queued): ML/keyword classifier scores traffic
   that passed the fast layer but looks anomalous, updating risk retro-actively
   and feeding the dashboard + alerts.

## Why blockchain writes are batched

Writing every request to a chain is slow, costly, and serializes on nonce/block
time. Instead we batch N logs (or every X seconds), compute a Merkle root over
their hashes, and write **one** transaction per batch. Anyone can verify a log
belongs to a batch with a Merkle proof, without per-request chain writes.

## Quickstart

```bash
cp .env.example .env
docker-compose up --build
```

- Backend API: http://localhost:8000/docs
- Proxy:       http://localhost:9000  (forwards to TARGET_URL)
- Frontend:    http://localhost:5173
- MongoDB:     localhost:27017

## Build phases (recommended order)

1. Proxy + logging → MongoDB (no ML)
2. Rule-based fast-layer detection + live dashboard
3. Async ML risk scoring (DistilBERT, behind `ML_ENABLED` flag)
4. IP monitoring + reports
5. Blockchain batched audit logging (behind `BLOCKCHAIN_ENABLED` flag)
6. Vulnerability suggestion module

Everything below `ML_ENABLED=false` / `BLOCKCHAIN_ENABLED=false` in `.env` runs
in **mock mode** by default so you can boot the whole stack immediately without
a trained model or a running Ganache instance, then flip flags on as each
piece is ready.
