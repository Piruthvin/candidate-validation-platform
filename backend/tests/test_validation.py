import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app


@pytest.fixture
def client():
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")


validation_payload = {
    "candidate_id": "test-001",
    "resume": {
        "name": "John Doe",
        "email": "john.doe@example.com",
        "phone": "+1-555-123-4567",
        "summary": "Experienced software engineer with 10+ years in full-stack development.",
        "total_years_experience": 10,
        "skills": ["Python", "FastAPI", "React", "Docker", "AWS"],
        "experience": [
            {
                "company": "Tech Corp",
                "title": "Senior Software Engineer",
                "start_date": "2019-01-01",
                "end_date": "2024-12-31",
                "description": "Led backend team.",
            },
            {
                "company": "Startup Inc",
                "title": "Software Engineer",
                "start_date": "2016-03-01",
                "end_date": "2018-12-31",
                "description": "Built core product features.",
            },
        ],
        "education": [
            {
                "institution": "MIT",
                "degree": "B.S. Computer Science",
                "start_date": "2011-09-01",
                "end_date": "2015-06-01",
            }
        ],
        "projects": [
            {
                "name": "Open Source Project",
                "description": "A popular open-source tool",
                "technologies": ["Python", "FastAPI"],
            }
        ],
        "certifications": [
            {
                "name": "AWS Solutions Architect",
                "issuer": "Amazon",
                "date": "2020-03-15",
            }
        ],
    },
}


@pytest.mark.asyncio
async def test_validation_success(client):
    async with client as ac:
        response = await ac.post("/api/v1/validation/validate", json=validation_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["candidate_id"] == "test-001"
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
    assert data["resume_completeness"]["status"] in ("PASSED", "WARNING", "FAILED", "SKIPPED")


@pytest.mark.asyncio
async def test_validation_missing_candidate_id(client):
    payload = validation_payload.copy()
    del payload["candidate_id"]
    async with client as ac:
        response = await ac.post("/api/v1/validation/validate", json=payload)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_validation_missing_resume(client):
    payload = {"candidate_id": "test-002"}
    async with client as ac:
        response = await ac.post("/api/v1/validation/validate", json=payload)
    assert response.status_code == 422
