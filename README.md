# Smart Money Tracker

> Open-source financial intelligence terminal — track what insiders, Congress members, and institutions are buying and selling before it hits the news.

![License](https://img.shields.io/badge/license-MIT-green)
![Python](https://img.shields.io/badge/python-3.12-blue)
![React](https://img.shields.io/badge/react-19-61dafb)
![Security](https://img.shields.io/badge/security-OWASP%20hardened-red)

---

## What it tracks

| Signal | Source | Frequency |
|--------|--------|-----------|
| SEC Form 4 insider trades | EDGAR RSS + XML | Every 30 min (market hours) |
| Congressional STOCK Act disclosures | house.gov / senate.gov | Daily |
| Unusual options flow | FINRA flat files | Daily |
| Dark pool prints | FINRA ATS data | Daily |
| 13F institutional positions | SEC EDGAR quarterly | Quarterly |

ML anomaly detection (Isolation Forest) flags cluster-buying, Congress+options combos, and unusual volume spikes in real time via WebSocket alerts.

---

## Stack

```
frontend/     React 19 · TypeScript · Vite 6 · Tailwind CSS 4 · PWA (mobile-first)
backend/      FastAPI · SQLAlchemy 2 async · Pydantic v2 · Alembic
workers/      Celery + Celery Beat (Redis broker)
database/     SQLite (dev) · TimescaleDB / PostgreSQL (prod)
ml/           scikit-learn Isolation Forest
security/     OWASP ZAP · Bandit · pip-audit · Trivy · slowapi
infra/        Docker Compose · GitHub Actions CI
```

---

## Security posture

- **Auth**: JWT (HS256) + bcrypt password hashing
- **Rate limiting**: slowapi — 100 req/min per IP by default
- **Secure headers**: `X-Frame-Options DENY`, `X-Content-Type-Options nosniff`, `Strict-Transport-Security`, `Content-Security-Policy`, `Permissions-Policy`
- **SSRF protection**: domain allowlist — only `sec.gov`, `finra.org`, `house.gov`, `senate.gov` are reachable from the HTTP client
- **Input validation**: Pydantic v2 strict schemas + regex-constrained query params on every endpoint
- **CORS**: strict origin allowlist via `ALLOWED_ORIGINS` env var
- **Secrets**: zero defaults — `SECRET_KEY` and `DATABASE_URL` are required env vars with no fallback
- **CI scanning**: Bandit (SAST) · pip-audit (CVE) · npm audit · Trivy (container) · OWASP ZAP DAST on every push

---

## Quick start (local dev)

### Prerequisites

- Python 3.12+
- Node.js 20+
- Redis *(optional — only needed to run Celery workers)*

### 1 — Backend

```bash
cd backend

# Create virtual environment
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and generate SECRET_KEY:
#   openssl rand -hex 32

# Run migrations
alembic upgrade head

# Seed dev database
python scripts/seed.py

# Start API server
uvicorn app.main:app --reload --port 8001
```

API docs available at `http://localhost:8001/api/docs` (only when `DEBUG=true`).

### 2 — Frontend

```bash
cd frontend
npm install
npm run dev          # http://localhost:5173
```

The Vite dev server proxies `/api/*` to the backend automatically (no CORS config needed locally).

---

## Environment variables

| Variable | Required | Description |
|----------|----------|-------------|
| `SECRET_KEY` | **yes** | JWT signing key — generate: `openssl rand -hex 32` |
| `DATABASE_URL` | **yes** | SQLAlchemy async URL (`sqlite+aiosqlite:///./dev.db` for dev) |
| `REDIS_URL` | no | Celery broker (`redis://localhost:6379/0`) |
| `ALLOWED_ORIGINS` | no | JSON array of CORS-allowed origins |
| `DEBUG` | no | Enables `/api/docs` and verbose errors (default `false`) |
| `RATE_LIMIT_DEFAULT` | no | slowapi limit string (default `100/minute`) |

---

## API reference

```
GET  /api/v1/insiders           Form 4 insider trades  (filter: ticker, type, page)
GET  /api/v1/congress           STOCK Act disclosures  (filter: chamber, party, ticker)
GET  /api/v1/options/unusual    Unusual options flow
GET  /api/v1/darkpool           Dark pool prints
GET  /api/v1/alerts             Active anomaly alerts
WS   /api/v1/ws/feed            Real-time WebSocket push feed
GET  /health                    Health check
```

All list endpoints return paginated JSON:
```json
{ "data": [...], "total": 84, "page": 1, "pageSize": 20, "hasNext": true }
```

---

## Running Celery workers

```bash
cd backend

# Worker process
celery -A app.workers.celery_app worker --loglevel=info

# Beat scheduler (separate terminal)
celery -A app.workers.celery_app beat --loglevel=info
```

Beat schedule:
- Form 4 collection — every 30 min, weekdays 09:00–20:00 UTC
- Congress disclosures — daily at 08:00 UTC
- FINRA data — daily at 21:00 UTC
- Anomaly detection — hourly
- 13F filings — quarterly

---

## Running tests

```bash
cd backend
pytest -v

# With coverage
pytest --cov=app --cov-report=term-missing

# Security scans (requires bandit, pip-audit, trivy installed)
bandit -r app -ll
pip-audit -r requirements.txt
cd ../frontend && npm audit --audit-level=high
```

---

## Docker

```bash
docker compose up --build
# API → http://localhost:8000
# Frontend → http://localhost:5173
```

---

## Production checklist

- [ ] Set `DEBUG=false`
- [ ] Generate `SECRET_KEY` with `openssl rand -hex 32`
- [ ] Switch to TimescaleDB: `DATABASE_URL=postgresql+asyncpg://...`
- [ ] Set `ALLOWED_ORIGINS` to your production domain
- [ ] Enable HTTPS — `Strict-Transport-Security` header is already configured
- [ ] Run Celery worker + beat containers
- [ ] Review `Content-Security-Policy` for your specific domain

---

## Project structure

```
smart-money-tracker/
├── backend/
│   ├── app/
│   │   ├── api/v1/routes/     # FastAPI routers
│   │   ├── core/              # Config, database, SSRF-protected HTTP client
│   │   ├── models/            # SQLAlchemy ORM models
│   │   ├── parsers/           # SEC EDGAR, Congress XML/JSON, FINRA flat-file parsers
│   │   ├── schemas/           # Pydantic v2 schemas (camelCase serialization)
│   │   ├── services/          # Isolation Forest anomaly detection
│   │   └── workers/           # Celery tasks + beat schedule
│   ├── migrations/            # Alembic async migrations
│   ├── scripts/seed.py        # Dev data seeder (84 insider + 40 congress trades)
│   └── tests/                 # pytest async suite + OWASP security tests
├── frontend/
│   ├── src/
│   │   ├── components/        # AppShell, BottomNav, TradeCard, Badge
│   │   ├── pages/             # Feed, Insiders, Congress, Watchlist
│   │   ├── lib/               # Typed API client, formatters
│   │   ├── store/             # Zustand (watchlist + WS state, persisted)
│   │   └── types/             # TypeScript interfaces
│   └── vite.config.ts
├── infra/                     # Docker Compose, Nginx
├── .github/workflows/         # CI: lint · test · Bandit · pip-audit · ZAP · Trivy
└── docker-compose.yml
```

---

## Data sources & legal

All data is sourced from **public government and regulatory filings**:

- SEC EDGAR — public domain (17 CFR Part 232)
- FINRA ATS/OTC — public regulatory disclosure
- House financial disclosures — 5 U.S.C. App. 4 § 103
- Senate financial disclosures — 5 U.S.C. App. 4 § 103

This project does **not** provide investment advice.

---

## License

MIT — see [LICENSE](LICENSE) for details.

---

*Built as an open-source portfolio project. Not affiliated with the SEC, FINRA, or any government agency.*
