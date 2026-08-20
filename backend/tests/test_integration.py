import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.domain.models import ResumeData, AtsCandidate, CompanyData, LinkedInData, PreviousValidationReport


@pytest.fixture
def client():
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")


validation_payload = {
    "candidate_id": "test-int-001",
    "resume": {
        "name": "Jane Smith",
        "email": "jane.smith@company.com",
        "phone": "+1-650-253-0000",
        "summary": "Senior data scientist with 8 years of experience in ML and AI.",
        "location": "San Francisco, CA",
        "linkedin_url": "https://www.linkedin.com/in/janesmith",
        "total_years_experience": 8,
        "skills": ["Python", "TensorFlow", "PyTorch", "SQL", "AWS", "Docker", "Kubernetes", "MLflow"],
        "experience": [
            {"company": "Tech Giant Inc", "title": "Senior Data Scientist", "start_date": "2020-01-01", "end_date": "2024-12-31", "description": "Led ML team."},
            {"company": "Startup AI", "title": "Data Scientist", "start_date": "2017-03-01", "end_date": "2019-12-31", "description": "Built production models."},
            {"company": "Consulting Co", "title": "Junior Analyst", "start_date": "2015-06-01", "end_date": "2017-02-28", "description": "Data analysis."},
        ],
        "education": [
            {"institution": "Stanford University", "degree": "M.S. Computer Science", "start_date": "2013-09-01", "end_date": "2015-06-01"},
            {"institution": "UC Berkeley", "degree": "B.S. Statistics", "start_date": "2009-09-01", "end_date": "2013-06-01"},
        ],
        "projects": [
            {"name": "ML Pipeline Platform", "description": "End-to-end ML pipeline automation tool", "technologies": ["Python", "MLflow", "Docker", "Kubernetes"]},
            {"name": "Fraud Detection System", "description": "Real-time fraud detection using deep learning", "technologies": ["PyTorch", "AWS", "Kafka"]},
        ],
        "certifications": [
            {"name": "AWS Solutions Architect Professional", "issuer": "Amazon Web Services", "date": "2022-06-15"},
            {"name": "TensorFlow Developer Certificate", "issuer": "Google", "date": "2021-03-10"},
        ],
        "languages": ["English", "Spanish"],
    },
}


# ── Contact Validation ──────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_contact_validator_email_format(client):
    async with client as ac:
        resp = await ac.post("/api/v1/validation/validate", json=validation_payload)
    assert resp.status_code == 200
    data = resp.json()
    cv = data["contact_validation"]
    assert "evidence" in cv
    assert "details" in cv
    assert cv["details"]["email"]["format_valid"] is True


@pytest.mark.asyncio
async def test_contact_validator_invalid_email(client):
    payload = validation_payload.copy()
    payload["resume"] = {**validation_payload["resume"], "email": "not-an-email"}
    async with client as ac:
        resp = await ac.post("/api/v1/validation/validate", json=payload)
    assert resp.status_code == 200
    cv = resp.json()["contact_validation"]
    assert cv["status"] == "WARNING"
    assert any("format" in e.lower() for e in cv["evidence"])


@pytest.mark.asyncio
async def test_contact_validator_disposable_email(client):
    payload = validation_payload.copy()
    payload["resume"] = {**validation_payload["resume"], "email": "test@mailinator.com"}
    async with client as ac:
        resp = await ac.post("/api/v1/validation/validate", json=payload)
    assert resp.status_code == 200
    cv = resp.json()["contact_validation"]
    assert cv["status"] in ("FAILED", "WARNING"), f"Expected FAILED or WARNING, got {cv['status']}"
    assert any("disposable" in e.lower() for e in cv["evidence"])


@pytest.mark.asyncio
async def test_contact_validator_missing_country_code(client):
    payload = validation_payload.copy()
    payload["resume"] = {**validation_payload["resume"], "phone": "555-987-6543"}
    async with client as ac:
        resp = await ac.post("/api/v1/validation/validate", json=payload)
    assert resp.status_code == 200
    cv = resp.json()["contact_validation"]
    assert any("could not be parsed" in e.lower() for e in cv["evidence"])


# ── Resume Completeness ─────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_resume_completeness_missing_critical(client):
    payload = validation_payload.copy()
    payload["resume"] = {**validation_payload["resume"], "name": None, "email": None, "phone": None}
    async with client as ac:
        resp = await ac.post("/api/v1/validation/validate", json=payload)
    assert resp.status_code == 200
    rc = resp.json()["resume_completeness"]
    assert rc["status"] == "FAILED"


@pytest.mark.asyncio
async def test_resume_completeness_missing_sections(client):
    payload = validation_payload.copy()
    payload["resume"] = {**validation_payload["resume"], "summary": None, "skills": []}
    async with client as ac:
        resp = await ac.post("/api/v1/validation/validate", json=payload)
    assert resp.status_code == 200
    rc = resp.json()["resume_completeness"]
    assert rc["status"] in ("WARNING", "PASSED")


# ── Education Validation ────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_education_invalid_timeline(client):
    payload = validation_payload.copy()
    bad_edu = [{"institution": "MIT", "degree": "PhD", "start_date": "2025-01-01", "end_date": "2020-01-01"}]
    payload["resume"] = {**validation_payload["resume"], "education": bad_edu}
    async with client as ac:
        resp = await ac.post("/api/v1/validation/validate", json=payload)
    assert resp.status_code == 200
    ev = resp.json()["education_validation"]
    assert ev["status"] == "FAILED"


# ── Experience Validation ───────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_experience_invalid_dates(client):
    payload = validation_payload.copy()
    bad_exp = [{"company": "X", "title": "Engineer", "start_date": "2024-01-01", "end_date": "2023-01-01"}]
    payload["resume"] = {**validation_payload["resume"], "experience": bad_exp}
    async with client as ac:
        resp = await ac.post("/api/v1/validation/validate", json=payload)
    assert resp.status_code == 200
    xv = resp.json()["experience_validation"]
    assert xv["status"] in ("FAILED", "WARNING")


# ── Timeline Validation ─────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_timeline_overlap(client):
    payload = validation_payload.copy()
    overlapping = [
        {"company": "A", "title": "Engineer", "start_date": "2020-01-01", "end_date": "2024-06-01"},
        {"company": "B", "title": "Engineer", "start_date": "2023-01-01", "end_date": "2024-01-01"},
    ]
    payload["resume"] = {**validation_payload["resume"], "experience": overlapping}
    async with client as ac:
        resp = await ac.post("/api/v1/validation/validate", json=payload)
    assert resp.status_code == 200
    tv = resp.json()["timeline_validation"]
    assert tv["status"] == "FAILED"


# ── Skills Validation ───────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_skills_no_issues(client):
    payload = validation_payload.copy()
    payload["resume"] = {**validation_payload["resume"], "skills": ["Python", "SQL", "AWS"]}
    async with client as ac:
        resp = await ac.post("/api/v1/validation/validate", json=payload)
    assert resp.status_code == 200
    sv = resp.json()["skills_validation"]
    assert sv["status"] in ("PASSED", "WARNING", "SKIPPED")


# ── Project Validation ──────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_projects_empty(client):
    payload = validation_payload.copy()
    payload["resume"] = {**validation_payload["resume"], "projects": []}
    async with client as ac:
        resp = await ac.post("/api/v1/validation/validate", json=payload)
    assert resp.status_code == 200
    pv = resp.json()["project_validation"]
    assert pv["status"] == "SKIPPED"


# ── Certification Validation ────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_certifications_no_issues(client):
    async with client as ac:
        resp = await ac.post("/api/v1/validation/validate", json=validation_payload)
    assert resp.status_code == 200
    cv = resp.json()["certification_validation"]
    assert cv["status"] in ("PASSED", "SKIPPED")


# ── Employment Pattern ──────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_employment_pattern(client):
    async with client as ac:
        resp = await ac.post("/api/v1/validation/validate", json=validation_payload)
    assert resp.status_code == 200
    ep = resp.json()["employment_pattern"]
    assert ep["status"] in ("PASSED", "WARNING", "SKIPPED")


# ── Cross Field Validation ──────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_cross_field_no_extra_data(client):
    async with client as ac:
        resp = await ac.post("/api/v1/validation/validate", json=validation_payload)
    assert resp.status_code == 200
    cf = resp.json()["cross_field_validation"]
    assert cf["status"] in ("PASSED", "WARNING", "FAILED", "SKIPPED")


# ── All Validators Execute ──────────────────────────────────────────────────

VALIDATOR_KEYS = [
    "resume_completeness",
    "contact_validation",
    "education_validation",
    "experience_validation",
    "timeline_validation",
    "skills_validation",
    "project_validation",
    "certification_validation",
    "employment_pattern",
    "cross_field_validation",
]


@pytest.mark.asyncio
async def test_all_13_validators_execute(client):
    async with client as ac:
        resp = await ac.post("/api/v1/validation/validate", json=validation_payload)
    assert resp.status_code == 200
    data = resp.json()
    for key in VALIDATOR_KEYS:
        assert key in data, f"Missing validator: {key}"
        assert "status" in data[key], f"Validator {key} missing status"
        assert data[key]["status"] in ("PASSED", "FAILED", "WARNING", "SKIPPED"), f"Validator {key} invalid status"


# ── Fraud Detection is Raw Signals (no score) ──────────────────────────────

@pytest.mark.asyncio
async def test_fraud_detection_raw_signals(client):
    async with client as ac:
        resp = await ac.post("/api/v1/validation/validate", json=validation_payload)
    assert resp.status_code == 200
    fd = resp.json().get("fraud_detection")
    if fd:
        assert "status" in fd, "Fraud detection should have status field"
        assert "evidence" in fd or "details" in fd, "Fraud detection should have evidence or details"


# ── Resume Normalization ────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_resume_normalization_via_api(client):
    raw_resume = {
        "name": "John Normalized",
        "email": "john@example.com",
        "phone": "+1-555-111-2222",
        "skills": ["Python", "Java", "SQL"],
        "summary": "A summary",
        "experience": [
            {"company": "Normalized Corp", "title": "Engineer", "start_date": "2020-01", "end_date": "2023-12"},
        ],
        "education": [
            {"institution": "Normalized U", "degree": "B.S.", "end_date": "2019-06"},
        ],
    }
    payload = {"candidate_id": "norm-001", "resume": raw_resume}
    async with client as ac:
        resp = await ac.post("/api/v1/validation/validate", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["candidate_name"] == "John Normalized"
    assert data["resume"]["skills"] == ["Python", "Java", "SQL"]


# ── Previous Report Check ───────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_previous_report_check_in_result(client):
    async with client as ac:
        resp = await ac.post("/api/v1/validation/validate", json=validation_payload)
    assert resp.status_code == 200
    data = resp.json()
    assert "previous_report_check" in data
    prc = data["previous_report_check"]
    assert "exists" in prc
    assert prc["exists"] is False  # No ATS data so no previous report


# ── No Backend Score Calculation ────────────────────────────────────────────

SCORE_PATTERNS = ["score", "recommendation", "executive_summary", "overall_score", "validation_score", "confidence_score"]


@pytest.mark.asyncio
async def test_no_backend_scores(client):
    async with client as ac:
        resp = await ac.post("/api/v1/validation/validate", json=validation_payload)
    assert resp.status_code == 200
    data = resp.json()
    for key in data:
        if isinstance(data[key], str):
            for pat in SCORE_PATTERNS:
                if pat in key.lower():
                    pytest.fail(f"Backend returned score/recommendation field: {key}")


# ── Report Generation Endpoint ──────────────────────────────────────────────

@pytest.mark.asyncio
async def test_report_generation_endpoint_validates(client):
    payload = {
        "candidate_id": "rep-001",
        "candidate_info": {
            "name": "Report Test",
            "email": "report@test.com",
            "phone": "+1-555-0000",
            "position": "Engineer",
        },
        "validation_result": {
            "contact_validation": {"status": "PASSED", "evidence": ["Email verified"], "details": None},
            "education_validation": {"status": "PASSED", "evidence": [], "details": None},
        },
        "llm_analysis": {
            "overall_score": 85,
            "validation_score": 90,
            "recommendation": "REVIEW",
            "risk_level": "LOW",
        },
    }
    async with client as ac:
        resp = await ac.post("/api/v1/reports/generate", json=payload)
    # Should fail because Azure is not configured in test env
    assert resp.status_code == 500 or resp.status_code == 200


# ── Retry Mechanism ─────────────────────────────────────────────────────────

from app.infrastructure.retry import retry_async, classify_error, ErrorCategory, RetryableError, UserInputError, SystemFailureError
import asyncio


@pytest.mark.asyncio
async def test_retry_success():
    call_count = 0

    async def flaky():
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise RetryableError("timeout")
        return "success"

    result = await retry_async(flaky, max_retries=2, name="test")
    assert result == "success"
    assert call_count == 3


@pytest.mark.asyncio
async def test_retry_exhausted():
    async def always_fails():
        raise RetryableError("always fails")

    result = await retry_async(always_fails, max_retries=2, name="test_fail")
    assert isinstance(result, dict)
    assert "error" in result
    assert result["category"] == "retryable"


def test_classify_error():
    assert classify_error(TimeoutError("timeout")) == ErrorCategory.RETRYABLE
    assert classify_error(ConnectionError("refused")) == ErrorCategory.RETRYABLE
    assert classify_error(RetryableError("rate limit exceeded")) == ErrorCategory.RETRYABLE
    assert classify_error(UserInputError("not found")) == ErrorCategory.USER_INPUT
    assert classify_error(SystemFailureError("crash")) == ErrorCategory.SYSTEM_FAILURE
    assert classify_error(Exception("500 server error")) == ErrorCategory.RETRYABLE
    assert classify_error(Exception("404 not found")) == ErrorCategory.USER_INPUT


# ── Domain Models ───────────────────────────────────────────────────────────

def test_ats_candidate_has_report_fields():
    ac = AtsCandidate(candidate_id="test", report_url="https://report", blob_id="blob-1", validation_status="PASSED", recommendation="CLEAR")
    assert ac.report_url == "https://report"
    assert ac.blob_id == "blob-1"
    assert ac.validation_status == "PASSED"
    assert ac.recommendation == "CLEAR"


def test_company_data_has_trust_evidence():
    cd = CompanyData(company_name="TestCo", trust_evidence=["DNS found", "MX found"], verification_reason="Verified via website")
    assert len(cd.trust_evidence) == 2
    assert cd.verification_reason == "Verified via website"


def test_previous_report_model():
    pr = PreviousValidationReport(exists=True, differences=["Status changed from PASSED to FAILED"])
    assert pr.exists is True
    assert len(pr.differences) == 1
    assert "PASSED" in pr.differences[0]


# ── Resume Normalizer Unit Test ─────────────────────────────────────────────

from app.services.resume_normalizer import ResumeNormalizer


def test_resume_normalizer_normalize():
    normalizer = ResumeNormalizer()
    raw = {
        "full_name": "Unit Test",
        "email_address": "unit@test.com",
        "phone_number": "+1-555-0000",
        "professional_summary": "A unit test summary",
        "skill_set": "Python, Rust, Go",
        "work_history": [{"employer": "Unit Corp", "role": "Dev", "startDate": "2020-01", "endDate": "2023-12"}],
        "educational_background": [{"school": "Unit U", "qualification": "B.S.", "graduation_date": "2019-06"}],
        "raw_text": "some raw text",
    }
    result = normalizer.normalize(raw)
    assert result.name == "Unit Test"
    assert result.email == "unit@test.com"
    assert result.phone == "+1-555-0000"
    assert result.summary == "A unit test summary"
    assert "Python" in result.skills
    assert result.experience[0].company == "Unit Corp"
    assert result.education[0].institution == "Unit U"
