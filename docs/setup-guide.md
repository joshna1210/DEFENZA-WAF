# Setup Guide

## 1. Local (no Docker)

### Backend
```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp ../.env.example ../.env
python run.py          # http://localhost:8000/docs
```

### Proxy
```bash
cd proxy
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
export TARGET_URL=http://localhost:3000   # the app you're protecting
export BACKEND_URL=http://localhost:8000
python run.py          # http://localhost:9000
```

### Frontend
```bash
cd frontend
npm install
npm run dev             # http://localhost:5173
```

### MongoDB
```bash
docker run -d -p 27017:27017 --name waf-mongo mongo:7
```

## 2. Docker Compose (everything at once)

```bash
sudo apt update
sudo apt install podman-compose
podman-compose up --build

cp .env.example .env
docker-compose up --build
```

## 3. First-time app setup

1. Open http://localhost:5173 → Register an `admin` account.
2. Point `TARGET_URL` in `.env` at the site you want protected, restart the proxy.
3. Send traffic through the proxy (`http://localhost:9000/...`) instead of hitting
   your app directly — watch it show up on the Dashboard within a few seconds.
4. Try `Settings → Analyze payload` with something like `id=1' OR '1'='1` in the
   query string to see the rule engine flag it as `sqli`.

## 4. Turning on ML (DistilBERT)

```bash
pip install torch transformers
# in .env:
ML_ENABLED=true
```
The classifier lazy-loads on first use. Out of the box it uses the base
`distilbert-base-uncased` weights with an untrained classification head —
fine-tune on a labeled HTTP-payload dataset before trusting its scores in
production; see `ml-engine/` structure in the original spec if you want to
train a dedicated model rather than doing it in-process.

## 5. Turning on the blockchain

```bash
# start a local chain
npx ganache --port 8545
# or: docker run -p 8545:8545 trufflesuite/ganache

cd blockchain
pip install -r requirements.txt
python scripts/deploy.py     # prints CONTRACT_ADDRESS
npx ganache --deterministic -p 8545

# in .env:
BLOCKCHAIN_ENABLED=true
WEB3_PROVIDER_URL=http://127.0.0.1:8545
CONTRACT_ADDRESS=<from deploy.py>
DEPLOYER_PRIVATE_KEY=<a ganache test account private key>
```
Batches are written automatically every `BATCH_LOG_INTERVAL_SECONDS` (default
5 min) by the APScheduler job in `backend/app/main.py`, or trigger one
immediately with `POST /api/blockchain/run-batch-now` (admin only).

```
testing
curl http://localhost:9000/get
curl "http://localhost:9000/get?id=1' OR '1'='1"
curl "http://localhost:9000/get?user=admin'--"
curl "http://localhost:9000/get?user=admin'--"
curl -X POST "http://localhost:9000/post" -d "query=SELECT * FROM users WHERE id=1 UNION SELECT username,password FROM admin"
curl "http://localhost:9000/get?q=<script>alert(1)</script>"
```