# Architecture

```
                     ┌────────────────┐
   Client requests → │  Reverse Proxy │ ── fast regex scan (sync, <5ms)
                     │   (FastAPI)    │ ── forwards to TARGET_URL
                     └───────┬────────┘
                             │ async log event (fire-and-forget)
                             ▼
                     ┌────────────────┐
                     │    Backend     │
                     │   (FastAPI)    │
                     └───────┬────────┘
                async analysis pipeline:
                 1. rule_engine (regex)
                 2. keyword_engine
                 3. ml_engine (DistilBERT, optional)
                             │
                             ▼
                     ┌────────────────┐
                     │    MongoDB     │  traffic_logs, analysis_results,
                     │                │  ip_activity, alerts, vulnerability_reports
                     └───────┬────────┘
                             │ every N logs / X seconds
                             ▼
                     ┌────────────────┐
                     │ Blockchain     │  Merkle root of batch → WAFLogger.sol
                     │ batch logger   │  (mock mode if BLOCKCHAIN_ENABLED=false)
                     └────────────────┘

                     ┌────────────────┐
                     │ React Dashboard│  polls backend REST API
                     │ (Vite+Tailwind)│  auth via JWT, admin / soc_analyst roles
                     └────────────────┘
```

## Key design decisions

- **Two-tier detection**: a synchronous fast-layer regex scan in the proxy
  (blocks obvious attacks immediately, <5ms) and an asynchronous slow-layer
  pipeline in the backend (rules + keywords + optional BERT) that never adds
  latency to real traffic but produces the richer risk score shown on the
  dashboard.
- **Batched blockchain writes**: individual requests are never written
  on-chain. The backend batches unbatched logs on a schedule, hashes each,
  computes a Merkle root, and writes one transaction per batch to
  `WAFLogger.sol`. This keeps chain costs and latency bounded regardless of
  traffic volume.
- **Everything runs without ML/blockchain configured**: `ML_ENABLED=false`
  and `BLOCKCHAIN_ENABLED=false` are the defaults, so `docker-compose up`
  gives you a fully working proxy + rule engine + dashboard immediately.
  Flip the flags on once you've trained a model / deployed the contract.
