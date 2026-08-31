"""End-to-end validation pipeline test.

Tests the complete flow:
1. Resume normalization → validate endpoint → report generation → ATS update
"""

import os

import pytest
from httpx import ASGITransport, AsyncClient

os.environ["AZURE_STORAGE_CONNECTION_STRING"] = "DefaultEndpointsProtocol=https;AccountName=test;AccountKey=dGVzdA==;EndpointSuffix=core.windows.net"
os.environ["AZURE_STORAGE_CONTAINER_NAME"] = "test-container"
os.environ["CORS_ORIGINS"] = '["*"]'

from app.main import app  # noqa: E402


@pytest.fixture
def client():
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")


validation_payload = {
    "candidate_id": "e2e-001",
    "resume": {
        "name": "E2E Test Candidate",
        "email": "e2e@example.com",
        "phone": "+1-555-000-0000",
        "summary": "End-to-end test candidate.",
        "skills": ["Python", "FastAPI"],
        "experience": [
            {"company": "Test Corp", "title": "Engineer", "start_date": "2020-01", "end_date": "2024-12", "description": "Built things."}
        ],
        "education": [
            {"institution": "Test U", "degree": "B.S.", "field_of_study": "CS", "end_date": "2019-06"}
        ],
    },
}


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_validation_endpoint_returns_all_modules(client):
    async with client as ac:
        resp = await ac.post("/api/v1/validation/validate", json=validation_payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["candidate_id"] == "e2e-001"
    assert data["candidate_name"] == "E2E Test Candidate"
    assert "resume_completeness" in data
    assert "contact_validation" in data
    assert "education_validation" in data
    assert "experience_validation" in data
    assert "timeline_validation" in data
    assert "skills_validation" in data
    assert "project_validation" in data
    assert "certification_validation" in data
    assert "employment_pattern" in data
    assert "cross_field_validation" in data
    assert "previous_report_check" in data
    assert data["previous_report_check"]["exists"] is False
    for key in ("resume_completeness", "contact_validation", "education_validation", "experience_validation", "timeline_validation", "skills_validation", "project_validation", "certification_validation", "employment_pattern", "cross_field_validation"):
        assert "status" in data[key]
        assert data[key]["status"] in ("PASSED", "FAILED", "WARNING", "SKIPPED")


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_validation_has_no_scoring(client):
    async with client as ac:
        resp = await ac.post("/api/v1/validation/validate", json=validation_payload)
    assert resp.status_code == 200
    data = resp.json()
    score_keys = ["validation_score", "confidence_score", "fraud_score", "company_score", "overall_score", "recommendation", "executive_summary"]
    for key in data:
        if isinstance(data[key], str):
            for pat in score_keys:
                assert pat not in key.lower(), f"Backend returned score field: {key}"


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_all_endpoints_accept_only_post_json(client):
    endpoints = [
        ("/api/v1/validation/validate", 422),
        ("/api/v1/reports/generate", 422),
        ("/api/v1/reports/blob", 422),
        ("/api/v1/ats/candidate", 422),
        ("/api/v1/ats/attachments", 422),
        ("/api/v1/ats/search", 422),
    ]
    async with client as ac:
        for path, expected in endpoints:
            resp = await ac.get(path)
            assert resp.status_code in (405, expected), f"GET {path} returned {resp.status_code}"


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_health_endpoint(client):
    async with client as ac:
        resp = await ac.get("/health")
    assert resp.status_code == 200
    assert resp.json().get("status") == "healthy"


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_candidate_detail_post(client):
    payload = {"candidate_id": "591003000063456008"}
    async with client as ac:
        resp = await ac.post("/api/v1/ats/candidate", json=payload)
    assert resp.status_code in (200, 404, 502)


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_blob_report_post(client):
    payload = {"blob_id": "report-e2e-001-20260101.html"}
    async with client as ac:
        resp = await ac.post("/api/v1/reports/blob", json=payload)
    assert resp.status_code in (200, 404, 500, 502)



@pytest.mark.e2e
@pytest.mark.asyncio
async def test_ats_proxy_candidate_detail_success(client):
    payload = {"record_id": "591003000063456008"}
    async with client as ac:
        resp = await ac.post("/api/v1/ats/candidate", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("first_name") == "Rajesh Kanna"
    assert data.get("current_employer") == "Tech Mahindra"
    assert len(data.get("experience_details", [])) >= 3


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_ats_proxy_attachments(client):
    payload = {"record_id": "591003000063456008"}
    async with client as ac:
        resp = await ac.post("/api/v1/ats/attachments", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("total", 0) > 0
    assert len(data.get("data", [])) > 0


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_ats_proxy_search(client):
    async with client as ac:
        # Without record_id -> 400
        resp_err = await ac.post("/api/v1/ats/search", json={"name": "Rajesh"})
        assert resp_err.status_code == 400
        assert "Only record_id supported" in resp_err.json().get("detail", "")

        # With record_id -> 200
        resp_ok = await ac.post("/api/v1/ats/search", json={"record_id": "591003000063456008"})
        assert resp_ok.status_code == 200
        data = resp_ok.json()
        assert data.get("total") == 1
        assert len(data.get("data", [])) == 1


