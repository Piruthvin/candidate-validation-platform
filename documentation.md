# Candidate Validation Platform — Project Documentation

*(Strictly derived from the codebase. Anything not present in code is marked "Not found in codebase".)*

---

## 1. PROJECT OVERVIEW

### Project Name
**Candidate Validation Platform** — `APP_NAME` in `backend/app/core/config.py:13` (`app_version` = `2.0.0`, `pyproject.toml:7`).

### What this project is (in simple terms)
An AI-powered recruiter assistant that validates job candidates. A recruiter uploads a PDF resume or asks questions in a chat interface. An AI agent system parses the resume, a FastAPI backend runs a battery of rule-based checks (contact, education, experience, timeline, skills, projects, certifications, employment pattern, cross-field consistency), enriches the profile with external data (ATS, LinkedIn, company websites, email/DNS), and finally generates a recruiter HTML report stored in Azure Blob Storage.

### Core objective
Automate candidate background validation and produce a recruiter-ready report with scores, risks, and a recommendation — reducing manual verification effort (`frontend/src/pages/AboutPage.tsx:91`).

### Type of system
A **multi-tier web application**: React frontend → Azure Functions proxy → external AI "executor" hosting LLM agents → FastAPI (Python) backend → external SaaS integrations (Zoho Recruit ATS, Apify, Azure Blob Storage).

---

## 2. PROBLEM STATEMENT

### What problem this system is solving
Recruiters must manually verify candidate claims on resumes (identity, contact details, education, employment history, company legitimacy, LinkedIn presence) before making hiring decisions. This is slow, error-prone, and inconsistent.

### Why this problem is important
Fraudulent or inaccurate resumes cause bad hires. The system encodes recruiter verification logic into repeatable, deterministic rules (`backend/app/services/validators/*`) so every candidate is checked the same way.

### Current challenges (based on code behavior)
- **Resume data quality**: missing critical fields (name/email/phone) block validation (`resume_completeness_validator.py:63`).
- **Data inconsistency**: resume vs ATS vs LinkedIn vs company data can contradict each other, detected by `CrossFieldValidator`.
- **External API fragility**: Zoho, Apify, DNS, and company-URL checks can fail; the code retries and degrades gracefully rather than crashing (`retry.py`, `ats_service.py`, `company_verifier.py`).
- **Fraud indicators**: keyword stuffing, AI-generated text, template placeholders, and repeated phrases are heuristically detected (`fraud_detector.py`).

---

## 3. SOLUTION OVERVIEW

### How the system solves the problem
A pipeline of **enrichment → deterministic rule validation → LLM scoring → report generation**:

1. LLM agent normalizes the resume into structured JSON.
2. Backend fetches candidate data from Zoho ATS, LinkedIn (Apify), and verifies the employer's company website.
3. Backend runs 12+ deterministic validator modules against the structured resume.
4. The LLM agent reads the evidence, calculates scores, and decides a recommendation.
5. Backend renders an HTML report, stores it in Azure Blob, and returns a SAS URL.

### Key components involved
| Component | Location |
|---|---|
| Frontend UI | `frontend/` (React + Vite + TS) |
| Executor proxy (Azure Function) | `CandidateValidationProxy/` (Node.js) |
| AI agents | `agent-prompts/` (markdown prompts, executed by external iGentic executor) |
| Backend API | `backend/app/` (FastAPI) |
| External services | Zoho Recruit, Apify, Azure Blob Storage, DNS resolvers, DuckDuckGo |

---

## 4. HOW THE SYSTEM WORKS (SIMPLIFIED)

```
Recruiter uploads PDF
  ↓  Frontend: pdfjs extracts raw text + candidate_id
  ↓  User confirms Candidate ID
  ↓  Payload {"candidate_id", "raw_resume_text"} POSTed to Azure Function proxy
  ↓  Proxy forwards to iGentic Executor (LLM platform)
  ↓  Group Chat Manager routes to Validation Agent
  ↓  Validation Agent: LLM normalizes resume → structured JSON
  ↓  Validation Agent calls POST /api/v1/validation/validate
        ├─ ATS enrichment (Zoho)      ├─ LinkedIn enrichment (Apify)
        ├─ Company verifier           ├─ Fraud detector
        └─ Email domain verification
  ↓  10 core rule validators run (completeness, contact, education, experience,
       timeline, skills, projects, certifications, employment pattern, cross-field)
  ↓  Validation Agent: LLM analyzes evidence → scores → recommendation →
     interview questions
  ↓  Validation Agent calls POST /api/v1/reports/generate
        └─ HTML rendered → uploaded to Azure Blob → SAS URL returned
  ↓  Frontend renders summary + "Open Report" link; report saved to localStorage
```

---

## 5. WHY THIS SOLUTION

### Why a rule engine is used alongside AI
The backend **explicitly refuses to calculate scores**. Per `Validation_Agent.md:120-129`: *"The backend MUST NOT calculate: Validation Score, Confidence Score, Fraud Score... These are calculated by the LLM."* The backend produces **only deterministic, structured validation evidence**; the LLM interprets it. This keeps validation reproducible while allowing flexible judgment.

### Why FastAPI is used
Codebase evidence: async endpoints (`async def`), Pydantic request/response models (`domain/models.py`), dependency injection (`core/dependencies.py`), middleware support (`core/logging.py`, `core/rate_limiter.py`), auto-generated Swagger/ReDoc (`main.py:31-33`).

### Why services are separated
The `services/` layer is split into enrichment services (`ats_service.py`, `linkedin_service.py`, `company_verifier.py`, `fraud_detector.py`), the orchestration engine (`validation_engine.py`), `validators/` (one file per check), and `report_generator.py`. `core/` holds cross-cutting concerns (config, DI, exceptions, logging, rate limiting), `infrastructure/` wraps external systems (Azure Blob, email/DNS, retries, SAS), and `domain/` holds DTOs. Each validator is independently injectable via `core/dependencies.py:52-89` — allowing the engine to be assembled with or without any validator (`validation_engine.py:57-72`, all params optional with runtime fallbacks).

---

## 6. FEATURES & CAPABILITIES

| Feature | Backend endpoint | Agent responsibility |
|---|---|---|
| Full candidate validation (all validators + enrichment) | `POST /api/v1/validation/validate` | Validation Agent (Step 3–7) |
| Resume normalization (raw text → JSON) | Not found in codebase (done by LLM per `Validation_Agent.md:27-59`; `ResumeNormalizer` exists but is only exercised in tests — see §10) | Validation Agent (Step 1) |
| LLM scoring / recommendation / summary | Not in backend (deliberately) | Validation Agent (Step 5–7) |
| Technical interview question generation | Not in backend | Validation Agent (Step 9) |
| Recruiter HTML report generation + Blob upload + SAS URL | `POST /api/v1/reports/generate` | Validation Agent (Step 10) |
| Get latest report by candidate | `POST /api/v1/reports/latest` | Conversation Agent (Tool 4) |
| Fetch report by blob ID | `POST /api/v1/reports/blob` | Conversation Agent (Tool 5) |
| Search reports | `POST /api/v1/reports/search` | Conversation Agent (Tool 6) |
| List ATS candidates | `POST /api/v1/ats/candidates` | Conversation Agent (Tool 1) |
| Get ATS candidate details | `POST /api/v1/ats/candidate` | Conversation Agent (Tool 2) |
| Search ATS candidates | `POST /api/v1/ats/search` | Conversation Agent (Tool 3) |
| Health check | `GET /health` | — |
| Chat + PDF upload + report tracking (local) | N/A (frontend, via proxy) | Group Chat Manager routing |

---

## 7. SYSTEM ARCHITECTURE

### Backend architecture (layers)
```
app/
├── api/v1/            → route handlers (validation, reports, ats)
├── core/              → config (Settings), DI (dependencies), exceptions,
│                        logging (correlation IDs), rate limiter
├── domain/            → Pydantic models/DTOs + COUNTRY_CODES table
├── infrastructure/    → Azure Blob, DNS/email verifier, retry/error-classify, SAS generator
├── services/          → validation_engine (orchestrator), ats_service, linkedin_service,
│                        company_verifier, fraud_detector, report_generator, resume_normalizer
│   └── validators/    → 10 always-run rule validators + linkedin_validator + company_validator
└── templates/         → Jinja2 HTML report template
```

### Agent architecture (roles & interaction)
- **Group Chat Manager** — decides which agent speaks next; outputs only a participant name based on conversation history (`Group_Chat_Manager.md`).
- **Validation Agent** — owns the validation workflow (normalize → validate → score → report); returns a final result object (`Validation_Agent.md`).
- **Conversation Agent** — read-only recruiter assistant; answers questions using 6 ATS/report tools; explicitly forbidden from validating (`Conversation_Agent.md`).

### External integrations (all present in code)
- **Zoho Recruit ATS** — OAuth refresh-token flow + Candidates REST API (`ats_service.py:38-64`, `_api_base_url` = `https://recruit.zoho.in/recruit/v2`).
- **Apify LinkedIn scraper** — actor `inexhaustible_glass/linkedin-scraper` (`linkedin_service.py:55`), gated by `LINKEDIN_SCRAPING_ENABLED` (default `false`, `config.py:39`).
- **Azure Blob Storage** — report upload/download/delete, SAS URL generation (`azure_blob.py`, `sas_generator.py`).
- **DNS / MX** — `dns.asyncresolver` for email and company domains (`email_verifier.py:41`, `company_verifier.py:167`).
- **DuckDuckGo HTML search** — fallback company-website discovery (`company_verifier.py:198-202`).

---

## 8. BACKEND STRUCTURE ANALYSIS

```
backend/
├── app/
│   ├── main.py                      → FastAPI app factory, middleware, health check
│   ├── api/v1/
│   │   ├── validation.py            → POST /api/v1/validation/validate
│   │   ├── reports.py               → generate / latest / blob / search
│   │   └── ats.py                   → candidates / candidate / search
│   ├── core/
│   │   ├── config.py                → Settings (env-driven, pydantic-settings)
│   │   ├── dependencies.py          → DI factories for all services
│   │   ├── exceptions.py            → AppException hierarchy (502/503/404)
│   │   ├── logging.py               → CorrelationMiddleware + structured log formatter
│   │   └── rate_limiter.py          → ASGI rate-limit middleware + in-memory storage
│   ├── domain/models.py             → All Pydantic DTOs + COUNTRY_CODES
│   ├── infrastructure/
│   │   ├── azure_blob.py            → Blob upload/download/delete/list + retry decorator
│   │   ├── email_verifier.py        → DNS/MX/disposable/corporate classification
│   │   ├── retry.py                 → retry_async + error classification
│   │   └── sas_generator.py         → 24h read-only SAS URL generation
│   ├── services/
│   │   ├── validation_engine.py     → orchestrates enrichment + all validators
│   │   ├── ats_service.py           → Zoho Recruit client
│   │   ├── linkedin_service.py      → Apify LinkedIn scraper client
│   │   ├── company_verifier.py      → company domain discovery/verification
│   │   ├── fraud_detector.py        → resume fraud heuristics
│   │   ├── report_generator.py      → Jinja2 render + upload + SAS + ATS metadata
│   │   ├── resume_normalizer.py     → standalone normalizer (test-only usage)
│   │   └── validators/              → 12 rule validator classes
│   └── templates/validation_report.html → report template (embeds validationData JSON)
├── tests/            → unit/, integration/, e2e/, plus standalone test files
├── docs/             → functional-specification.md (2238 lines)
├── Dockerfile, docker-compose.yml, Makefile, pyproject.toml, pytest.ini
└── scripts/deploy-azure.ps1
```

### Per-file summary (key files)

| File | What it does | Why it exists | Key classes/functions |
|---|---|---|---|
| `main.py` | App factory: middleware stack (Correlation → RateLimiter → CORS), routers, `/health` | Single entry point | `create_application`, `lifespan`, `get_rate_limit_storage`, `health` |
| `config.py` | Reads env into typed `Settings` (Zoho, Azure, Apify, CORS) | Centralized config | `Settings`, `parse_cors_origins` validator |
| `dependencies.py` | FastAPI DI providers for every service | Wiring | `get_*_validator`, `get_validation_engine`, `get_report_generator` |
| `exceptions.py` | Typed errors | HTTP mapping (502/503/404) | `AtsException`, `AzureStorageException`, `ReportNotFound` |
| `logging.py` | Correlation ID propagation + structured logs | Traceability across services | `CorrelationMiddleware`, `StructuredFormatter`, `setup_logging` |
| `rate_limiter.py` | Per-path sliding-window throttling | Protect external APIs | `MemoryRateLimitStorage`, `RateLimiterMiddleware`, `DEFAULT_LIMITS` |
| `models.py` | All request/response/domain DTOs + country code map | Contract typing | `ResumeData`, `ValidationResult`, `ValidationEvidence`, `LLMAnalysis`, `ReportResult`, `AtsCandidate`, `COUNTRY_CODES` |
| `azure_blob.py` | Blob operations with retry + verification | Report persistence | `AzureBlobService.upload_blob/download_blob`, `retry_async` decorator |
| `email_verifier.py` | Email domain analysis | Contact + domain checks | `EmailDomainVerifier.verify`, DNS/MX lookups, `DISPOSABLE_DOMAINS` |
| `retry.py` | Retryable-error classification + async retry | Resilient external calls | `classify_error`, `retry_async`, `ErrorCategory` |
| `sas_generator.py` | Read-only SAS URL for blobs | Report access links | `SASGenerator.generate_sas_url` |
| `validation_engine.py` | Orchestrates enrichment + validators | Core pipeline | `ValidationEngine.validate`, `_validate_email_domain`, `_fraud_to_evidence` |
| `ats_service.py` | Zoho Recruit client | ATS enrichment/ops | `fetch_candidate`, `_resolve_candidate_id`, `list_candidates`, `update_report_metadata`, `check_connection` |
| `linkedin_service.py` | Apify LinkedIn client | LinkedIn enrichment | `enrich`, `_sync_fetch`, `_normalize` |
| `company_verifier.py` | Company website verification | Employer legitimacy check | `verify`, `_search_candidates`, `_score_metadata` |
| `fraud_detector.py` | Resume fraud heuristics | Fraud evidence | `analyze`, `_check_*` methods |
| `report_generator.py` | HTML report pipeline | Report feature | `generate`, `_extract_status`, `_log_mappings` |
| `resume_normalizer.py` | Standalone structured normalizer | Reference/utility (test-only wiring) | `ResumeNormalizer.normalize` + `_extract_*` methods |
| `validators/*.py` | 12 deterministic check modules | Rule engine | one `validate()` per class |

---

## 9. API DOCUMENTATION

> All endpoints except `/health` accept only `POST` with `application/json` (`backend/README.md:25`). No path/query params.

### GET /health
- **What it does**: checks external network (HTTP GET to `https://google.com`, 5s timeout) and returns overall status.
- **Response**: `{ "status": "healthy"|"degraded", "checks": { "external_network": "ok"|"degraded", "uptime": "ok" } }` (`main.py:60-74`).

### POST /api/v1/validation/validate
- **What it does**: runs all validators + enrichment (ATS, LinkedIn, company, fraud, email domain) (`validation.py:10-29`).
- **Request** (`ValidateRequest`, `models.py:207`):
```json
{ "candidate_id": "ZR_0001", "resume": { "...normalized resume JSON..." }, "linkedin_url": "https://linkedin.com/in/x" }
```
- **Validation rules**: `candidate_id` required (Pydantic); `linkedin_url` is merged into `resume["linkedin_url"]` if the resume lacks it (`validation.py:22-24`).
- **Response**: full `ValidationResult` (candidate + enrichments + per-module `ValidationEvidence` + completed/skipped/failed steps).

### POST /api/v1/reports/generate
- **What it does**: renders HTML report, uploads to Azure Blob, generates SAS URL, updates ATS record (`reports.py:35-64`).
- **Request** (`ReportGenerationRequest`, `models.py:270`): `candidate_id`, `candidate_info` (name/email/phone/position), `validation_result` (dict), `llm_analysis` (scores, recommendation, summary, interview questions).
- **Errors**: `AzureStorageException` → 500 "Report upload failed"; other exceptions → 500 with message.
- **Response**: `{ blob_id, report_url, created_time, candidate_id }`.

### POST /api/v1/reports/latest
- **What it does**: fetches ATS candidate; returns report URL (regenerates SAS if only `blob_id` exists) (`reports.py:74-97`).
- **Rules**: 404 if candidate missing; 404 if no `report_url`/`blob_id`; wrapped in `retry_async(2)`.

### POST /api/v1/reports/blob
- **What it does**: generates a SAS URL for a given `blob_id` (`reports.py:107-116`).
- **Request**: `{ "blob_id": "report-ZR_0001-....html" }`.

### POST /api/v1/reports/search
- **What it does**: lists up to `max(page_size, 200)` ATS candidates, then filters in-memory by `candidate_id`/`candidate_name` (substring) and `recommendation`/`validation_status` (exact, case-insensitive); returns only items having a report (`reports.py:126-160`).
- **Note**: `date_from`/`date_to` are accepted in the request DTO (`models.py:381-382`) but **not applied** in the filter logic — documented as present-but-unused in code.

### POST /api/v1/ats/candidates
- **What it does**: paginated candidate list with search/status/recommendation/validation filters (`ats.py:26-49`).
- **Rules**: `page ≥ 1`, `page_size 1–100` (`AtsSearchParams`, `models.py:286-294`); search uses `(First_Name:starts_with:{search})` (`ats_service.py:267`).

### POST /api/v1/ats/candidate
- **What it does**: full candidate detail by `candidate_id` (`ats.py:59-70`); 404 if not found.

### POST /api/v1/ats/search
- **What it does**: if `candidate_id` given → fetch directly; otherwise lists (up to `max(page_size,100)`) and filters by name/email/phone/company (substring) + recommendation/validation_status (exact), fetching full detail per match (`ats.py:80-121`).

---

## 10. CORE LOGIC EXPLANATION

### 🔹 ValidationEngine orchestrator — `services/validation_engine.py:74`
Step-by-step:
1. `resume = ResumeData(**resume_data)`; `candidate_id` assigned; accepts `raw_resume_text` alias (`:78-79`).
2. **ATS enrichment** (if service present): `fetch_candidate` with retries; on error stores `ats_error` (`:91-100`).
3. **Previous report check** (if ATS record has report): downloads previous HTML blob, extracts embedded `var validationData = {...};` JSON via regex, stores as `previous_validation` (`:104-120`).
4. **LinkedIn enrichment** (if service present): retried; sets `linkedin_error` if profile not found (`:124-139`).
5. **Company verification** (if present): company name taken from first experience entry else candidate name; retried; sets `company_error` (`:143-155`).
6. **Fraud detection**: run in a thread via `asyncio.to_thread` (`:157-164`).
7. **Email domain verification** → `_validate_email_domain` (`:170`, `:239-278`).
8. **10 validators** run concurrently via `asyncio.gather(..., return_exceptions=True)` (`:174-185`, `:222`); a validator exception becomes a failed step rather than aborting the run (`:224-228`).
9. **Conditional validators**: `LinkedInValidator` only when LinkedIn data exists (`:187-188`); `CompanyValidator` only when company data exists (`:190-191`).
10. Every non-SKIPPED validator's `evidence` list is merged into `result.warnings` (`:234-235`).
11. Result assembled into `ValidationResult` with `completed_steps`, `skipped_steps`, `failed_steps`, `errors`, `warnings` (`:197-237`).

> Note: `ResumeNormalizer` (in `services/resume_normalizer.py`) is **not wired into the runtime pipeline** — it is referenced only in `tests/test_integration.py:420-424`. The engine builds `ResumeData` directly from the incoming dict.

### 🔹 Email Format Validation — `validators/contact_validator.py:41-77`
- Input email received on the resume.
- Regex applied: `^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$` → sets `details.email.format_valid`.
- Domain classified against three hardcoded sets: `DISPOSABLE_DOMAINS` (11 entries, `:11`), `COMMON_PROVIDERS` (11 providers, `:12`), `RESERVED_EXAMPLE_DOMAINS` (from `email_verifier.py:12`).
- DNS + MX checked via `EmailDomainVerifier` (unless domain is disposable, where a stub result is used, `:63-66`).
- Output: PASSED/FAILED/WARNING per status logic in `:141-153` (FAILED if reserved-example, disposable, unparseable, or ≥2 serious issues).

### 🔹 Email Domain Verification — `validation_engine.py:239`
- Splits email on `@`, takes domain.
- `EmailDomainVerifier.verify` (`email_verifier.py:21-38`): classifies disposable/reserved/corporate; if not reserved, does DNS `A` lookup and `MX` lookup via `dns.asyncresolver` (timeout 1s).
- Output status: `FAILED` if disposable; `WARNING` if no DNS; else `PASSED` (`:266-271`). Details embed full `EmailDomainVerification` dump.

### 🔹 Phone / Contact Validation — `validators/contact_validator.py:83-134`
- Raw phone passed to `phonenumbers.parse(raw, None)`.
- If valid: extracts country code, national number, `is_valid_number`, region code, number type (mapped to names via `PHONE_TYPE_NAMES`), country via `COUNTRY_CODES`, INTERNATIONAL and E164 formats (`:96-123`).
- `NumberParseException` → `format_valid=false` + error message (`:127-129`).
- Duplicate check: flags emails that appear inside experience descriptions (`_detect_duplicate_contacts`, `:160-175`).
- Status: FAILED if any phone failed libphonenumber validation or serious issues ≥ 2; else WARNING; PASSED if clean.

### 🔹 Resume Completeness — `validators/resume_completeness_validator.py:9`
- Critical fields: `name`, `email`, `phone` — any missing → **FAILED** (`:63-65`).
- Optional sections: summary, experience, education, skills — any missing → **WARNING**.
- Also counts experience entries with no company/title and education entries with no institution.
- Confidence = `100 - missing_sections*10 - missing_critical*15` (clamped ≥ 0).

### 🔹 Education Validator — `validators/education_validator.py:10`
- Missing institution/degree counted.
- Dates parsed via `datetime.fromisoformat` (handles `Z`): `start > end` → invalid timeline; `end > now` → future graduation (`:49-60`).
- Duplicate institutions detected.
- Status: **FAILED** if any invalid timeline or future date; **WARNING** if missing fields or duplicates; else **PASSED**.

### 🔹 Experience Validator — `validators/experience_validator.py:10`
- Missing company/title counted; duplicate employers flagged; date-range validity; duration in months computed (`:50-62`).
- ≥6 entries → warning (frequent job changes) (`:84`, `:96-97`).
- Status: **FAILED** if any invalid date range; **WARNING** if missing company/title/duplicates/≥6 entries.

### 🔹 Timeline Validator — `validators/timeline_validator.py:31`
- `_normalize_datetime` handles `Z`, bare dates (`YYYY-MM-DD`), and naive → UTC.
- Flags start-after-end and future end dates (`:49`, `:60-63`).
- Sorts by start date; detects **overlaps** (`curr_start < prev_end`) and **gaps > 6 months** (≥12 months explicitly noted) (`:95-112`).
- Status: **FAILED** if overlaps or future end dates; **WARNING** if gaps; else **PASSED**.

### 🔹 Skills Validator — `validators/skills_validator.py:9`
- Compares resume `skills` against technologies used in `projects`: matched / missing lists (`:38-51`).
- >30 skills → warning; skill-density ratio > 5 skills/year → warning (`:58`, `:68-72`).
- Status: PASSED only if no warnings; else WARNING.

### 🔹 Project Validator — `validators/project_validator.py:9`
- Generic/empty entries (name < 3 chars **and** description < 10 chars) counted; projects without technologies counted; duplicate names detected.
- Status: **FAILED** if ≥2 generic entries; **WARNING** if any generic/no-tech/duplicate.

### 🔹 Certification Validator — `validators/certification_validator.py:10`
- Missing name/issuer; date before year 2000 (too old) or future date.
- Status: **FAILED** if old or future dates; **WARNING** if missing name/issuer.

### 🔹 Employment Pattern Validator — `validators/employment_pattern_validator.py:10`
- Computes tenure in months for dated entries.
- `short_tenures` (<6 months), `job_hop` (<12 months), average tenure.
- Status: **FAILED** if ≥2 job-hop entries; **WARNING** if short tenures / ≥50% under 12 months (min 3) / avg < 12; else **PASSED**.

### 🔹 Cross-Field Validator — `validators/cross_field_validator.py:11`
Five comparison sections, each producing PASS / MISMATCH / NOT_EVALUATED:
1. **Resume vs ATS** — name (exact or first-name substring, `:314`), email (exact), phone (digit-stripped comparison, `:347-348`), skills (percentage overlap, `:389`).
2. **Resume vs LinkedIn** — first-employer equality (`:374`).
3. **Resume vs Company** — first employer vs verified company name (`:359`).
4. **Resume vs Timeline** — education end-year vs experience start-year; internships skipped; valid iff `start_year >= grad_year - 1` (`:413-443`).
5. **Resume vs Contact** — presence of name/email/phone.
- Overall: any MISMATCH → **FAILED**; any NOT_EVALUATED → **WARNING**; else **PASSED** (`:80-96`).

### 🔹 LinkedIn Validator — `validators/linkedin_validator.py:9`
- Uses match flags computed in `linkedin_service._normalize`: `name_match`, `employer_match`, and skills overlap percentage.
- Status: **WARNING** if name mismatch, employer mismatch, or skill overlap < 30% of the smaller set (`:109-116`); else **PASSED**.
- LinkedIn data only exists when scraping is enabled and the URL matches `https?://(?:www\.)?linkedin\.com/in/<username>` (`linkedin_service.py:13`, `:25-35`).

### 🔹 Company Validator — `validators/company_validator.py:9`
- Renders the verification flow steps (website found → DNS → HTTP/HTTPS → SSL → MX) from `CompanyData` flags.
- Status: **PASSED** if `company.is_verified`; else **WARNING**.

### 🔹 Company Verifier — `services/company_verifier.py:50`
- `_normalize` removes non-alphanumerics.
- In-process cache (TTL 86,400s) + request coalescing via `asyncio.Future` (`:57-83`).
- `_search_candidates`: builds slug, probes `https://{slug}.{tld}` and `https://www.{slug}.{tld}` across **55 TLDs** (`:141-149`) with concurrency cap 20; per URL checks status <500, DNS `A`, `MX`, SSL; confidence score = reachable 40 + DNS 25 + MX 20 + SSL 15 (cap 100) (`:260-270`).
- Fallback: DuckDuckGo HTML search `https://html.duckduckgo.com/html/?q={name}+official+website`, regex-matching the slug (`:196-215`).
- `is_verified = best.reachable`, `verification_method = "website_resolution"` (`:125-127`).

### 🔹 Fraud Detector — `services/fraud_detector.py:11`
- **Keyword stuffing**: 14 buzzwords (`team player`, `results-driven`, …) counted; >3 occurrences → indicator + `keyword_stuffing` signal (`:34-45`).
- **AI generation**: 7 AI phrases + transitional-phrase density >25% of sentences → `ai_generated_content` (`:47-63`).
- **Templates**: `[insert`, `[your name]`, `lorem ipsum`, etc. → `template_abuse` (`:65-70`).
- **Repeated phrases**: identical sentences appearing >2 times (`:72-78`).
- **Placeholders**: regexes like `[\s*insert\s*.*?]`, `xxxx+`, `click here` (`:80-88`).
- Aggregation (`validation_engine.py:280`): ≥3 signals → **FAILED**; 1–2 → **WARNING**; 0 → **PASSED**; confidence = `100 - signals*20` (min 0).

### 🔹 Report Generation — `services/report_generator.py:34`
- Renders Jinja2 template `validation_report.html` with `candidate_id`, `candidate_name`, `generated_at`, `candidate_info`, `validation_result`, `llm_analysis`.
- Blob name: `report-{candidate_id}-{YYYYMMDDHHMMSS}.html` (`:61`).
- Upload with `overwrite=True`, `content_type="text/html"`, metadata `candidate_id` + `generated_at`; blob existence re-verified after upload (`azure_blob.py:86-94`).
- SAS URL: read-only, expiry `AZURE_SAS_EXPIRY_HOURS` (default 24h) (`sas_generator.py:21-28`).
- ATS metadata update: `Report_URL`, `Blob_ID`, `Validation_Status`, `Recommendation`, `Validation_Timestamp` (`ats_service.py:244-253`). Status derived in `_extract_status`: 0 FAILED → PASSED, ≤2 → WARNING, else FAILED (`report_generator.py:163-172`).

### 🔹 Retry & Error Classification — `infrastructure/retry.py`
- `classify_error` keys on keywords: timeout/connection/unavailable/rate limit/5xx → `RETRYABLE`; not found/invalid/4xx → `USER_INPUT`; else `SYSTEM_FAILURE` (`:34-39`).
- `retry_async` retries only RETRYABLE errors, exponential backoff `1.0 * 2^attempt`; exhausted → returns `{ "error", "category", "attempts" }` dict (which callers treat as a failure marker, e.g., `ats.py:47`).

### 🔹 Rate Limiting — `core/rate_limiter.py`
- Path rules (`DEFAULT_LIMITS`): `/api/v1/validation/` 30/60s; `/api/v1/reports/` 20/60s; `/api/v1/ats/` 60/60s.
- Exclusions (`EXCLUDED_PATHS`): `/health`, `/openapi.json`, `/docs`, `/redoc` — checked before limits, so the `/health` entry in `DEFAULT_LIMITS` is unreachable.
- Key = `rl:{x-api-key or client_ip}:{path}`; sliding window; injects `X-RateLimit-Limit`/`X-RateLimit-Remaining`; 429 response with `Retry-After`.

---

## 11. AGENT PROMPT ANALYSIS

### Group Chat Manager (`agent-prompts/Group_Chat_Manager.md`)
- **Role**: conversation router.
- **Responsibilities**: decide which agent takes the next turn from the two participants.
- **Workflow**: reads `{{$history}}`, picks a name.
- **Input**: conversation history.
- **Output**: exactly one participant name — `Conversation_Agent` or `Validation_Agent`.

### Validation Agent (`agent-prompts/Validation_Agent.md`)
- **Role**: owns the full candidate-validation workflow.
- **Responsibilities** (steps 1–10):
  1. LLM-normalize `raw_resume_text` → flat snake_case JSON (empty strings/arrays for missing values; LinkedIn URL extracted, never guessed) (`:27-59`).
  2. Build backend payload `{candidate_id, resume, linkedin_url}` — **never** send raw text (`:60-73`).
  3. Call **Tool 1** `POST /api/v1/validation/validate`; retries up to 2.
  4. LLM analyzes all evidence (`:131-142`).
  5. Dynamically computes scores (validation, confidence, fraud, company, overall) — **no hardcoded thresholds** (`:144-171`).
  6. Executive summary (2–4 sentences) (`:172-178`).
  7. Recommendation: `CLEAR` | `REVIEW` | `REJECT` with reasoning (`:180-190`).
  8. Recruiter explanation (strengths, weaknesses, risk, hiring rec, next steps) (`:191-198`).
  9. Generate 5–15 technical interview questions **only from resume-listed technologies**; each with `category`, `difficulty`, `question`, `reason` (`:200-251`).
  10. Call **Tool 2** `POST /api/v1/reports/generate` with full evidence + LLM analysis; report must include every validation module; footer = generated time, candidate ID, validation version, report version, blob ID (`:253-349`).
- **Input**: `{ candidate_id, raw_resume_text }` from frontend.
- **Output**: final result JSON `{ candidate_id, work_id, execution_id, blob_id, report_url, validation_status, recommendation, overall_score, executive_summary }` plus `TERMINATE THE PROCESS` (`:367-383`, `:444`).

### Conversation Agent (`agent-prompts/Conversation_Agent.md`)
- **Role**: read-only recruiter assistant.
- **Tools (6)**: list candidates, get candidate details, search candidates, get latest report, fetch report by blob ID, search reports — all matching backend endpoints (`:29-126`).
- **Responsibilities**: answer queries about candidates/status/reports; present candidate lists in a readable format; summarize when many results (`:170-190`).
- **Forbidden**: validate, generate reports, parse resumes, calculate scores, call validation APIs, modify records, expose internals (`:9-17`, `:236-249`).
- **Input**: recruiter natural-language questions.
- **Output**: recruiter-friendly text, ending with `TERMINATE THE PROCESS`.

---

## 12. EXECUTION FLOW (END-TO-END)

1. **User action** — Upload PDF in `ChatPage` → `UploadZone` → `ResumeService.validateFile` (PDF only, ≤10MB, `resume.service.ts:54-62`).
2. **Text extraction** — `pdfjs-dist` reads each page's text items, joined by `\n\n` (`resume.service.ts:18-37`).
3. **Candidate ID** — dialog prompts user; ID optionally auto-detected from text (`Candidate ID|ID|CandidateId` regex → email → `candidate_{filename}`) (`resume.service.ts:39-52`).
4. **Payload build** — `submitCandidateId` serializes `{ candidate_id, raw_resume_text }` and sends it as the chat message (`ChatContext.tsx:324-347`).
5. **Proxy call** — `ExecutorService.execute` POSTs to `VITE_EXECUTOR_URL` (`https://candidatevalidationproxyfunc.azurewebsites.net/api/executorproxy`) with auth headers and SSE `Accept` (`executor.service.ts:44-55`).
6. **Proxy forward** — `ExecutorProxy.js` validates origin, injects `Authorization`/`x-api-key`/`x-app-id`/`x-username` + session/execution/connection headers, forwards to `IGENTIC_EXECUTOR_URL` (`ExecutorProxy.js:26-42`); streams `text/event-stream` back if enabled.
7. **Agent processing** — iGentic executor runs Group Chat Manager → Validation Agent (normalize → validate → score → report) or Conversation Agent (ATS/report queries).
8. **Backend API call** — Validation Agent calls `/api/v1/validation/validate`.
9. **Service execution** — engine enriches (ATS/LinkedIn/Company/Fraud/Email) then runs validators concurrently.
10. **Rule validation** — each validator returns `ValidationEvidence` (status + evidence + details).
11. **Report** — agent calls `/api/v1/reports/generate`; blob uploaded; SAS URL returned; ATS record updated.
12. **Response generation** — `formatResult` in `ChatContext.tsx:114-175` parses the completion payload into a markdown summary (score emoji: ≥80 🟢, ≥60 🟡, else 🔴) + `[Open Report](url)`; report saved to localStorage (`STORAGE_KEYS.REPORTS`), dedup by `candidate_id+blob_id`, `reports-updated` event dispatched.
13. **Reports page** — `ReportsPage` lists locally stored reports with Open/Delete actions.

---

## 13. DATA FLOW

```
INPUT: candidate_id + raw_resume_text
  ↓ (LLM) normalized resume JSON (snake_case)
  ↓ POST /validate
     ├─ ATS record (Zoho Candidates) ──┐
     ├─ LinkedIn profile (Apify)       ├─→ enrichment objects
     ├─ Company verification           │
     ├─ Fraud signals                  │
     └─ Email domain evidence          ┘
     ↓ 10 validators → ValidationEvidence per module
  ↓ ValidationResult (no storage, in-memory response)
  ↓ (LLM) LLMAnalysis (scores, summary, recommendation, interview questions)
  ↓ POST /reports/generate
     ├─ Jinja2 HTML report rendered
     ├─ UPLOAD → Azure Blob (candidate-reports container)
     ├─ SAS URL generated (24h)
     └─ OUTPUT: Report_URL / Blob_ID / Status written back to Zoho ATS
  ↓ Frontend: summary + report link shown; report metadata cached in localStorage
```

**Storage summary**: reports → Azure Blob Storage (HTML blobs, metadata `candidate_id`/`generated_at`); report pointers + validation status → Zoho Recruit ATS fields (`Report_URL`, `Blob_ID`, `Validation_Status`, `Recommendation`, `Validation_Timestamp`); frontend chat/report history → browser `localStorage`. No database found in codebase.

---

## 14. DESIGN DECISIONS (as visible in code)

1. **Rule-based validation + LLM interpretation split** — Backend returns evidence only; all scoring/recommendation is LLM-owned (`Validation_Agent.md:120-129`).
2. **Service-based, injectable architecture** — every service/validator is a constructor-injected dependency (`core/dependencies.py`), all optional (`validation_engine.py:39-56`), enabling partial assembly and testability.
3. **POST-only, JSON-only API** — uniform contract for LLM tools; no path/query params (`README.md:25`).
4. **All-POST search endpoints** (rather than REST GET) — accommodates tool-calling agents.
5. **Defensive external integration** — retries with error classification, per-path rate limiting, correlation IDs, blob upload verification, in-process caching for company lookups.
6. **Degrade-don't-crash** — enrichment failures become `*_error` strings feeding cross-field NOT_EVALUATED status; validator exceptions become failed steps, not request failures.
7. **No raw resume text to backend** — the LLM normalizes first; backend only ever sees structured JSON (`Validation_Agent.md:9`, `:72`).
8. **HTML blob + SAS** — reports are static HTML blobs with short-lived read-only SAS links rather than a reporting service.

---

## 15. ADVANTAGES

- **Deterministic, auditable validation** — every module emits evidence strings, checks performed, and failure reasons.
- **Resilience** — retry/backoff, error classification, per-path rate limits, and concurrency limits (semaphore 20) on external calls.
- **Graceful degradation** — missing/incomplete external data yields WARNING/NOT_EVALUATED instead of failures.
- **Traceability** — correlation IDs across requests and structured logging; report log mappings in `report_generator._log_mappings`.
- **Clear separation of concerns** — validators are small, single-purpose, independently testable classes.
- **Portable deployment** — Docker/Docker Compose, Azure Container Apps deploy script, and a build-dist frontend static web app config.

---

## 16. LIMITATIONS (observable in code)

- **Scoring/recommendation are not in the backend** — the system depends on the external iGentic executor + LLM; without it, no final report scores are produced. The backend alone cannot produce an overall score.
- **`ResumeNormalizer` is not wired into runtime** — production flow relies on the LLM agent to normalize; the class exists but is only used in tests.
- **In-memory rate-limit storage** — `MemoryRateLimitStorage` resets on restart; interface exists for Redis but no Redis implementation is present (`rate_limiter.py:35-40`).
- **Company verification is heuristic** — slug+TLD guessing and DuckDuckGo scraping; `is_verified` is website-reachability, not legal-entity verification.
- **LinkedIn scraping is opt-in and external** — disabled by default (`LINKEDIN_SCRAPING_ENABLED=false`); needs Apify token.
- **`/health` rate-limit rule is dead code** — `/health` appears in both `DEFAULT_LIMITS` and `EXCLUDED_PATHS`; exclusion wins.
- **Report search `date_from`/`date_to` not applied** — fields accepted in DTO but ignored in filtering logic.
- **Previous-report comparison** is extracted from blob HTML via regex; if a prior report doesn't embed `validationData`, comparison data is absent (no error, just missing).
- **No authentication on backend endpoints** — only the proxy forwards agent credentials; backend relies on rate limiting (CORS from `settings.cors_origins`). No auth middleware found in codebase.
- **No database** — no persistence layer beyond Blob Storage and ATS.
- **Frontend reports are local-only** — the Reports page reads `localStorage`, not the backend search APIs (`ReportContext.tsx`).

---

## 17. FUTURE EXTENSIBILITY (based on current structure)

- **Pluggable rate-limit storage** — swap `MemoryRateLimitStorage` for a Redis implementation without touching app code (`rate_limiter.py` docstrings state this intent).
- **Add validators** — register a new class in `validators/`, add a DI factory in `dependencies.py`, and add one dict entry in `validation_engine.py`; the `asyncio.gather` loop handles it automatically.
- **Wire `ResumeNormalizer`** into the engine as an offline/non-LLM fallback path.
- **Extend report template** — `validation_report.html` is Jinja2 with embedded JSON; new evidence sections can be added via template blocks.
- **Backend-driven search pagination** — replace in-memory filtering in `reports/search` and `ats/search` with ATS-side filters/pagination as Zoho allows.
- **Apply `date_from`/`date_to`** in report search filtering.
- **Add real auth** (e.g., API-key validation middleware) now that CORS and rate limiting are in place.
- **Persist candidate detail enrichment** in a database for replayable, versioned validation history.

---

*Documentation generated strictly from the codebase at `P:\Projects\CandidateValidationProject` (frontend, backend, CandidateValidationProxy, agent-prompts). All referenced behavior maps to actual code; items absent from the code are explicitly flagged.*
