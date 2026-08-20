# Candidate Validation Platform — Backend

Enterprise-grade backend for the Candidate Validation Platform.
Validates candidate resumes using multi-module checks, generates recruiter reports, and integrates with Zoho Recruit ATS.

## Architecture

```
[Agent Layer]                 [Backend API]              [External Services]
                                                              
Group Chat Manager   ──►     POST /api/v1/validation/validate   ──►  Zoho Recruit ATS
                       │                                              Apify LinkedIn
Conversation Agent    ├──   POST /api/v1/ats/candidates              DNS/MX Verifier
  (ATS Operations)    ├──   POST /api/v1/ats/candidate              
                       │     POST /api/v1/ats/search                 
                       │                                             
Conversation Agent    ├──   POST /api/v1/reports/latest       ──►  Azure Blob Storage
  (Report Operations) ├──   POST /api/v1/reports/blob              
                       │     POST /api/v1/reports/search            
                       │                                             
Validation Agent      ├──   POST /api/v1/validation/validate  ──►  All validators +
                       │     POST /api/v1/reports/generate          Azure Blob
```

All endpoints accept only `POST` with `application/json`. No path or query parameters.

## Setup

### Prerequisites

- Python 3.12+
- Docker (optional)
- Azure Storage account (for report blobs)
- Zoho Recruit API credentials (for ATS integration)

### Local Development

```bash
python -m venv .venv
.venv\Scripts\activate    # Windows
source .venv/bin/activate # Linux/Mac
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your credentials
uvicorn app.main:app --reload
```

### Docker

```bash
docker build -t candidate-validation-backend .
docker run -p 8000:8000 --env-file .env candidate-validation-backend
```

### Docker Compose

```bash
docker-compose up --build
```

## API Documentation

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/docs` | GET | Swagger UI |
| `/redoc` | GET | ReDoc UI |
| `/api/v1/validation/validate` | POST | Run full candidate validation |
| `/api/v1/reports/generate` | POST | Generate recruiter HTML report |
| `/api/v1/reports/latest` | POST | Get latest report for candidate |
| `/api/v1/reports/blob` | POST | Get report by blob ID |
| `/api/v1/reports/search` | POST | Search reports |
| `/api/v1/ats/candidates` | POST | List ATS candidates |
| `/api/v1/ats/candidate` | POST | Get candidate details |
| `/api/v1/ats/search` | POST | Search ATS candidates |

Every request uses `POST` with `Content-Type: application/json`.

## Environment Variables

See `.env.example` for all required variables.

Key variables:
- `AZURE_STORAGE_CONNECTION_STRING` — Azure Blob Storage
- `ZOHO_CLIENT_ID` / `ZOHO_CLIENT_SECRET` / `ZOHO_REFRESH_TOKEN` — Zoho Recruit API
- `APIFY_TOKEN` — LinkedIn scraping (optional)

## Project Structure

```
backend/
├── app/
│   ├── api/v1/           # API route handlers
│   │   ├── validation.py
│   │   ├── reports.py
│   │   └── ats.py
│   ├── core/             # Config, DI, exceptions, logging
│   ├── domain/           # Models and DTOs
│   ├── infrastructure/   # Azure, email, retry, SAS
│   ├── services/         # Business logic
│   │   └── validators/   # 11+ validation modules
│   └── templates/        # Jinja2 HTML report template
├── tests/
│   ├── unit/
│   ├── integration/
│   └── e2e/
├── docs/
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── pyproject.toml
├── pytest.ini
├── Makefile
└── .env.example
```

## Deployment

### Azure Container Apps

```bash
./scripts/deploy-azure.ps1
```

## Testing

```bash
pytest tests/
pytest tests/unit/
pytest tests/integration/
pytest tests/e2e/
```
