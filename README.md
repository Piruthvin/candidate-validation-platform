# Candidate Validation Platform

An AI-powered recruiter assistant that validates job candidates. A recruiter uploads a PDF resume (or asks questions in a chat interface), an AI agent system parses the resume, a FastAPI backend runs a battery of deterministic validation checks, enriches the profile with external data, and the system produces a recruiter-ready HTML report.

## Overview

- **Frontend** — React + Vite + TypeScript SPA. Chat interface, PDF upload/resume text extraction, report viewer.
- **Backend** — FastAPI (Python 3.12+) service. Runs 12+ rule-based validators, enriches candidate data (Zoho Recruit ATS, Apify LinkedIn, company website, email/DNS), and generates HTML reports stored in Azure Blob Storage.
- **Proxy** — Azure Functions (Node.js) that forwards frontend requests to an external AI "executor" platform hosting LLM agents.
- **Agents** — Markdown prompt definitions for the group chat manager, validation agent, and conversation agent.

> **Note:** Scoring, recommendations, and summaries are intentionally produced by the LLM agent, not the backend. The backend only returns structured, deterministic validation evidence.

## Architecture

```
React Frontend ──► Azure Function Proxy ──► iGentic Executor (LLM agents)
                       │                        ├─ Group Chat Manager
                       │                        ├─ Validation Agent
                       │                        └─ Conversation Agent
                       └──────────────► FastAPI Backend
                                          ├─ Zoho Recruit ATS
                                          ├─ Apify LinkedIn
                                          ├─ Company / DNS verifiers
                                          ├─ 12 rule-based validators
                                          └─ Azure Blob Storage (reports)
```

## Repository Structure

```
├── agent-prompts/                  # LLM agent prompt definitions
│                                   #   (Group Chat Manager, Validation Agent, Conversation Agent)
├── backend/                        # FastAPI validation service
│   ├── app/
│   │   ├── api/v1/                 # Route handlers (validation, reports, ats)
│   │   ├── core/                   # Config, DI, exceptions, logging, rate limiter
│   │   ├── domain/                 # Pydantic models / DTOs
│   │   ├── infrastructure/         # Azure Blob, email/DNS verifier, retry, SAS
│   │   ├── services/               # Validation engine, ATS, LinkedIn, company, fraud
│   │   │   └── validators/         # 12 rule-based validation modules
│   │   └── templates/              # Jinja2 HTML report template
│   ├── tests/                      # unit / integration / e2e tests
│   ├── docs/                       # Functional specification
│   ├── scripts/                    # Azure deployment script
│   ├── Dockerfile / docker-compose.yml / Makefile
│   └── .env.example                # Backend environment template
├── CandidateValidationProxy/       # Azure Function (Node.js) executor proxy
│   ├── src/functions/              # ExecutorProxy function
│   └── local.settings.example.json # Local settings template
├── frontend/                       # React + Vite SPA
│   ├── src/                        # Components, contexts, services, pages
│   └── .env.example                # Frontend environment template
├── documentation.md                # Deep codebase analysis & architecture docs
└── AI_Candidate_Validation_Platform.pptx
```

## Prerequisites

| Tool | Version | Used by |
|------|---------|---------|
| Python | 3.12+ | Backend |
| Node.js | 18+ (LTS) | Frontend & Proxy |
| npm | 9+ | Frontend & Proxy |
| Azure Functions Core Tools | 4.x | Proxy (`func start`) |
| Docker | optional | Backend container / compose |

External services (credentials go in the relevant `.env`, never committed):

- **Azure Blob Storage** — stores generated HTML reports.
- **Zoho Recruit API** — ATS candidate data (OAuth refresh token).
- **Apify** — LinkedIn scraping (optional, disabled by default).
- **iGentic executor** — external LLM agent platform (used by the proxy).

## Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/<your-org>/<your-repo>.git
cd <your-repo>
```

### 2. Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # Linux / macOS

pip install -r requirements.txt
cp .env.example .env
# Edit .env with your Azure / Zoho / Apify credentials

uvicorn app.main:app --reload
```

The API is available at `http://localhost:8000` (Swagger UI at `/docs`).

### 3. Frontend

```bash
cd frontend
npm install
cp .env.example .env
# Edit .env with your proxy URL / credentials

npm run dev
```

The app is available at `http://localhost:5173`. Build for production with `npm run build`.

### 4. Proxy (optional, needed only for the LLM agent flow)

```bash
cd CandidateValidationProxy
npm install
cp local.settings.example.json local.settings.json
# Edit local.settings.json with your iGentic executor credentials

func start
```

## Security Notes

- **Never commit secrets.** All `.env` files, `env.txt`, and `local.settings.json` are git-ignored.
- Copy example files to `.env` / `local.settings.json` and fill in your own credentials.
- Rotate any credentials that have previously been shared or exposed.

## License

# Proprietary License

© 2026 Piruthvin. All rights reserved.

## Ownership

This project, including all source code, assets, documentation, and related materials, is the exclusive property of Piruthvin.

## Restrictions

* You are NOT allowed to  sell any part of this project.
* You are NOT allowed to use this project for commercial or personal purposes without explicit written permission from the owner.
* Unauthorized use, reproduction, or distribution is strictly prohibited.

## Permission

To request permission for usage :
## 📞 Contact

**Owner:** Piruthvin  
**Phone:** [+91 8754481778](tel:+918754481778)  
**Email:** [piruthvinarun@gmail.com](mailto:piruthvinarun@gmail.com)

## Liability

The author is not liable for any damages arising from the use or misuse of this project.

---

**By accessing this repository, you agree to these terms.**
