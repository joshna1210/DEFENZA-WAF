# DEFENZA — Intent-Aware AI Web Application Firewall

DEFENZA is an AI-powered Web Application Firewall (WAF) designed to
detect, analyze, and mitigate web-based threats using intent-aware request
analysis, machine learning, behavioral monitoring, risk scoring, and
adaptive security policies.

The system combines a high-speed rule-based security layer with AI-assisted
semantic and behavioral analysis to identify malicious and anomalous HTTP
traffic while maintaining low latency in the critical request path.

---

## Overview

Traditional Web Application Firewalls primarily depend on predefined
signatures and static security rules.

DEFENZA extends this approach by analyzing the **intent, context, and
behavior** of incoming requests and combining multiple security layers to
support intelligent threat detection and response.

### Core Capabilities

- Real-time HTTP request inspection
- Rule-based threat detection
- AI/ML-assisted risk analysis
- Intent and semantic analysis
- Behavioral monitoring
- IP activity monitoring
- Risk scoring
- Adaptive security policies
- Vulnerability insights
- Security event logging
- Blockchain-based tamper-evident audit logging
- Security monitoring dashboard
- Docker-based deployments

---

# Architecture

```text
                         ┌─────────────────────┐
                         │       CLIENT        │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │   DEFENZA PROXY     │
                         │   Request Gateway   │
                         └──────────┬──────────┘
                                    │
                                    ▼
                    ┌──────────────────────────────┐
                    │ Request Parsing &             │
                    │ Normalization                 │
                    └──────────────┬───────────────┘
                                   │
                                   ▼
                    ┌──────────────────────────────┐
                    │ Fast Security Detection Layer │
                    │                              │
                    │ SQL Injection                 │
                    │ XSS                          │
                    │ Path Traversal                │
                    │ Malicious Headers             │
                    │ Signature / Rule Detection    │
                    └──────────────┬───────────────┘
                                   │
                                   ▼
                     ┌─────────────────────────────┐
                     │ AI / ML Risk Analysis       │
                     │                             │
                     │ Semantic Analysis            │
                     │ Intent Analysis              │
                     │ Behavioral Analysis          │
                     │ ML Classification            │
                     └──────────────┬──────────────┘
                                    │
                                    ▼
                     ┌─────────────────────────────┐
                     │       RISK ENGINE           │
                     │                             │
                     │ Risk Score                  │
                     │ Threat Classification       │
                     │ Security Context            │
                     └──────────────┬──────────────┘
                                    │
                 ┌──────────────────┼──────────────────┐
                 │                  │                  │
                 ▼                  ▼                  ▼
          ┌────────────┐      ┌────────────┐     ┌──────────────┐
          │   BLOCK    │      │   ALLOW    │     │ RATE LIMIT / │
          │            │      │            │     │   MONITOR    │
          └────────────┘      └────────────┘     └──────────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │ Security Dashboard  │
                         │                     │
                         │ Traffic             │
                         │ Threats             │
                         │ Risk Scores         │
                         │ IP Activity         │
                         │ Reports             │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │ Blockchain Audit    │
                         │ Merkle Root Logs    │
                         └─────────────────────┘
```

---

# Security Processing Flow

```text
Incoming HTTP Request
          │
          ▼
Request Parsing
          │
          ▼
Normalization
          │
          ▼
Fast Rule-Based Detection
          │
          ▼
Threat / Anomaly Identification
          │
          ▼
AI-Assisted Risk Analysis
          │
          ▼
Risk Scoring
          │
          ▼
Security Policy Decision
          │
     ┌────┼─────┬────────────┐
     ▼    ▼     ▼            ▼
   ALLOW BLOCK RATE LIMIT  MONITOR
     │
     ▼
Traffic Logging
     │
     ▼
Dashboard & Analytics
     │
     ▼
Audit Logging
```

---

# Key Features

## 1. Intent-Aware Threat Detection

DEFENZA analyzes HTTP requests beyond simple keyword matching.

The system considers request characteristics and contextual indicators to
identify potentially malicious request intent.

---

## 2. Multi-Layer Security

DEFENZA uses multiple detection layers.

### Fast Layer

The fast layer operates directly in the proxy path and performs lightweight
security checks such as:

- SQL Injection patterns
- XSS patterns
- Path traversal
- Suspicious headers
- Known malicious signatures
- Request anomalies

This layer is designed for fast decisions with minimal request latency.

### AI Layer

Requests requiring deeper analysis can be processed by the AI/ML layer.

This layer can perform:

- Semantic analysis
- Intent classification
- ML-based risk scoring
- Behavioral analysis
- Anomaly detection

---

## 3. AI-Assisted Risk Scoring

DEFENZA can assign a risk score to incoming requests based on security
indicators and AI/ML analysis.

Risk information can be used by the policy engine to support decisions such
as:

```text
ALLOW
BLOCK
RATE LIMIT
MONITOR
```

---

## 4. Behavioral & IP Monitoring

DEFENZA tracks traffic and IP activity to identify suspicious behavior.

Monitoring can include:

- Request frequency
- Repeated suspicious requests
- IP activity
- Attack patterns
- Abnormal traffic behavior
- Security events

---

## 5. Adaptive Security Policies

The policy layer converts security analysis into an enforcement decision.

```text
Request
   ↓
Threat Analysis
   ↓
Risk Score
   ↓
Policy Evaluation
   ↓
┌─────────┬─────────┬─────────────┬─────────┐
│  ALLOW  │  BLOCK  │ RATE LIMIT  │ MONITOR │
└─────────┴─────────┴─────────────┴─────────┘
```

---

## 6. Vulnerability Insights

DEFENZA provides vulnerability-oriented analysis to help identify potential
security weaknesses and suspicious application behavior.

---

## 7. Blockchain Audit Logging

Security events can be recorded using blockchain-based audit logging.

Instead of writing every request individually to a blockchain, DEFENZA can
batch multiple events and calculate a **Merkle Root**.

```text
Request 1 ─┐
Request 2 ─┤
Request 3 ─┤
Request 4 ─┤──► Hashes ─► Merkle Tree ─► Merkle Root
Request 5 ─┤                                  │
Request N ─┘                                  ▼
                                      Blockchain Record
```

This provides tamper-evident verification while reducing the number of
blockchain transactions.

---

## 8. Security Dashboard

The React-based frontend provides visibility into:

- Incoming traffic
- Threat detections
- Risk scores
- IP activity
- Security events
- Vulnerability information
- Audit records
- System activity

---

# Threat Detection

DEFENZA is designed to detect common web attack patterns including:

- SQL Injection
- Cross-Site Scripting (XSS)
- Path Traversal
- Malicious Headers
- Suspicious Request Patterns
- Abnormal IP Activity
- Anomalous HTTP Traffic

---

# Technology Stack

## Frontend

- React
- Vite
- JavaScript / TypeScript
- REST API
- HTML5
- CSS

## Backend

- Python
- FastAPI
- MongoDB
- REST APIs

## AI / Machine Learning

- Python
- Machine Learning
- Transformer-based analysis
- BERT / DistilBERT experimentation
- Semantic analysis
- Behavioral analysis
- Risk scoring

## Security

- Reverse Proxy
- Rule-based WAF detection
- Request normalization
- Threat detection
- IP monitoring
- Security analytics

## Blockchain

- Merkle Trees
- Merkle Root Batching
- Tamper-Evident Audit Logging

## Infrastructure

- Docker
- Docker Compose
- MongoDB
- Reverse Proxy Architecture

---

# Project Structure

```text
DEFENZA-WAF/
│
├── backend/
│   ├── ai/
│   │   └── training/
│   │       ├── config.py
│   │       ├── evaluate.py
│   │       ├── predict.py
│   │       ├── preprocess.py
│   │       ├── train.py
│   │       └── utils.py
│   │
│   └── app/
│       ├── config/
│       │   ├── settings.py
│       │   └── risk_config.py
│       │
│       └── services/
│           ├── analysis_service.py
│           ├── ip_monitor.py
│           └── traffic_service.py
│
├── blockchain/
│
├── docs/
│
├── frontend/
│
├── infrastructure/
│
├── proxy/
│   └── app/
│       ├── handlers/
│       │   └── request_handler.py
│       │
│       ├── services/
│       │   └── forwarder.py
│       │
│       └── proxy_server.py
│
├── scripts/
│
├── docker-compose.yml
├── .env.example
├── .gitignore
├── LICENSE
└── README.md
```

---

# Setup & Installation

## Prerequisites

Install the following before running DEFENZA:

- Git
- Docker
- Docker Compose
- Node.js 18+
- Python 3.11+

Verify the installations:

```bash
git --version
docker --version
docker compose version
node --version
python --version
```

---

# 1. Clone the Repository

```bash
git clone https://github.com/joshna1210/DEFENZA-WAF.git
```

Navigate into the project:

```bash
cd DEFENZA-WAF
```

---

# 2. Configure Environment Variables

Create the environment configuration from the example file.

### Linux / macOS

```bash
cp .env.example .env
```

### Windows PowerShell

```powershell
Copy-Item .env.example .env
```

Open `.env` and configure the required values.

Example:

```env
TARGET_URL=http://target-application:3000
MONGO_URI=mongodb://mongodb:27017/defenza

ML_ENABLED=false
BLOCKCHAIN_ENABLED=false
```

> **Important:** Never commit `.env` to GitHub.
> Store credentials, API keys, passwords, and private keys only in your
> local environment configuration.

---

# 3. Run with Docker

Build and start the complete DEFENZA stack:

```bash
docker compose up --build
```

To run in detached mode:

```bash
docker compose up --build -d
```

Check running services:

```bash
docker compose ps
```

---

# 4. Access DEFENZA

After the services are running:

| Service | Address |
|---|---|
| Frontend Dashboard | http://localhost:5173 |
| Backend API | http://localhost:8000 |
| API Documentation | http://localhost:8000/docs |
| WAF Proxy | http://localhost:9000 |
| MongoDB | localhost:27017 |

The WAF proxy acts as the gateway between the client and the configured
target application.

---

# 5. Stop DEFENZA

Stop the application:

```bash
docker compose down
```

To remove containers and associated volumes:

```bash
docker compose down -v
```

---

# Local Development Setup

Docker is recommended for running the complete stack.

For development, individual components can also be started locally.

---

## Backend Setup

Navigate to the backend directory:

```bash
cd backend
```

Create a Python virtual environment:

```bash
python -m venv .venv
```

### Windows PowerShell

```powershell
.venv\Scripts\Activate.ps1
```

### Linux / macOS

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Start the backend:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend API:

```text
http://localhost:8000
```

API documentation:

```text
http://localhost:8000/docs
```

---

# Frontend Setup

Open a new terminal.

Navigate to the frontend:

```bash
cd frontend
```

Install dependencies:

```bash
npm install
```

Start the development server:

```bash
npm run dev
```

Frontend dashboard:

```text
http://localhost:5173
```

---

# Proxy Setup

The DEFENZA proxy acts as the security gateway for incoming HTTP traffic.

The default proxy endpoint is:

```text
http://localhost:9000
```

The proxy:

1. Receives incoming HTTP requests
2. Parses and normalizes the request
3. Applies fast security rules
4. Performs security analysis
5. Applies the configured policy
6. Logs security events
7. Forwards permitted requests to the target application

The target application is configured through environment variables.

---

# AI / ML Module

The AI module is located under:

```text
backend/ai/
```

Training utilities are located under:

```text
backend/ai/training/
```

The training module includes:

```text
config.py
evaluate.py
predict.py
preprocess.py
train.py
utils.py
```

These components support the ML workflow including:

```text
Dataset
   ↓
Preprocessing
   ↓
Feature Preparation
   ↓
Model Training
   ↓
Evaluation
   ↓
Prediction
   ↓
Risk Analysis
```

The AI/ML layer can be enabled through environment configuration.

For development and testing, DEFENZA can operate with the rule-based
security layer while the AI components are configured separately.

---

# Blockchain Audit Logging

The blockchain module provides tamper-evident security event logging.

Instead of writing every request individually to a blockchain, events can
be grouped into batches.

```text
Security Events
      │
      ▼
Event Hashing
      │
      ▼
Merkle Tree
      │
      ▼
Merkle Root
      │
      ▼
Blockchain Record
```

This approach reduces the number of blockchain transactions while
maintaining verifiability of individual records.

Blockchain functionality can be enabled using:

```env
BLOCKCHAIN_ENABLED=true
```

---

# ML Configuration

The ML functionality can be controlled through environment variables.

Example:

```env
ML_ENABLED=false
```

When enabled:

```env
ML_ENABLED=true
```

the AI/ML layer can participate in request risk analysis according to the
configured implementation.

---

# Blockchain Configuration

Blockchain functionality can similarly be controlled using:

```env
BLOCKCHAIN_ENABLED=false
```

Enable it when the required blockchain infrastructure is available:

```env
BLOCKCHAIN_ENABLED=true
```

---

# API

The backend exposes REST APIs for interacting with DEFENZA services.

Once the backend is running, interactive API documentation is available at:

```text
http://localhost:8000/docs
```

The API can be used to:

- Access traffic information
- Retrieve security analysis
- Monitor IP activity
- Access security events
- Retrieve risk information
- Support dashboard operations

---

# Development Workflow

```text
Clone Repository
       │
       ▼
Configure .env
       │
       ▼
Start Docker / Services
       │
       ▼
Start Backend
       │
       ▼
Start Frontend
       │
       ▼
Start DEFENZA Proxy
       │
       ▼
Send HTTP Traffic
       │
       ▼
Request Inspection
       │
       ▼
Rule-Based Detection
       │
       ▼
AI / Behavioral Analysis
       │
       ▼
Risk Scoring
       │
       ▼
Security Policy
       │
       ├──────────────┐
       ▼              ▼
    BLOCK          ALLOW
                      │
                      ▼
                 Target App
                      │
                      ▼
              Logging & Analytics
                      │
                      ▼
              Audit Verification
```

---

# Why AI Analysis Is Separated from the Critical Path

Running a transformer-sized model synchronously for every request can add
significant processing latency, particularly on CPU-based deployments.

DEFENZA therefore separates lightweight inline security checks from deeper
analysis.

### Fast Security Layer

```text
Request
   ↓
Proxy
   ↓
Rule-Based Detection
   ↓
Immediate Security Decision
```

This layer handles security checks that can be performed quickly.

### AI Analysis Layer

```text
Request / Event
      ↓
Backend
      ↓
AI / ML Analysis
      ↓
Risk Score
      ↓
Dashboard / Alerts / Analytics
```

This architecture allows deeper analysis without requiring every request to
wait for expensive ML inference.

---

# Security Considerations

DEFENZA is designed as a security research and development project.

For production deployment:

- Use HTTPS/TLS
- Secure all environment variables
- Rotate credentials regularly
- Restrict database access
- Apply network segmentation
- Use authenticated APIs
- Protect blockchain credentials
- Configure appropriate logging policies
- Validate all incoming data
- Keep dependencies updated

Never commit sensitive information such as:

```text
.env
API keys
Passwords
Database credentials
Private keys
Cloud credentials
Authentication tokens
```

---

# Troubleshooting

## Check Docker Services

```bash
docker compose ps
```

---

## View Backend Logs

```bash
docker compose logs backend
```

Follow logs:

```bash
docker compose logs -f backend
```

---

## View Proxy Logs

```bash
docker compose logs proxy
```

---

## View All Logs

```bash
docker compose logs -f
```

---

## Rebuild the Application

```bash
docker compose down
docker compose up --build
```

---

## Frontend Dependency Issues

Navigate to the frontend:

```bash
cd frontend
```

Install dependencies:

```bash
npm install
```

Start the development server:

```bash
npm run dev
```

---

## Python Environment Issues

Check Python:

```bash
python --version
```

Create a new environment:

```bash
python -m venv .venv
```

Activate it on Windows:

```powershell
.venv\Scripts\Activate.ps1
```

Install dependencies:

```bash
pip install -r requirements.txt
```

---

# Future Enhancements

Planned improvements include:

- Advanced transformer-based intent classification
- Explainable AI for security decisions
- Adaptive rule generation
- Continuous model improvement
- Advanced anomaly detection
- Attack-path analysis
- Threat intelligence integration
- Distributed security intelligence
- Advanced threat correlation
- Automated security policy generation
- Enhanced blockchain verification
- Production-scale deployment

---

# Project Goal

DEFENZA aims to extend traditional signature-based web protection by
combining:

```text
Rule-Based Security
        +
AI / ML Analysis
        +
Intent Detection
        +
Behavioral Intelligence
        +
Risk Scoring
        +
Adaptive Policy Enforcement
        +
Tamper-Evident Auditing
```

into a unified Web Application Firewall architecture.

---

# License

This project is licensed under the MIT License.

See the [LICENSE](LICENSE) file for details.

---

# Author

**Joshna Rose J.N.**

Project Repository:  
https://github.com/joshna1210/DEFENZA-WAF
