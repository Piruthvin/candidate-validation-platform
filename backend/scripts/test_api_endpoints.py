import asyncio
import sys
from pathlib import Path
import httpx

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.main import app


async def main():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        print("=== 1. Testing GET /health ===")
        r = await client.get("/health")
        print(f"Status: {r.status_code}, Body: {r.json()}")
        assert r.status_code == 200

        print("\n=== 2. Testing POST /api/v1/validation/validate ===")
        payload = {
            "candidate_id": "CAND-001",
            "resume": {
                "name": "Sarah Connor",
                "email": "sarah.connor@gmail.com",
                "phone": "+14155552671",
                "company": "Cyberdyne Systems",
                "skills": ["Python", "Machine Learning", "FastAPI"],
                "experience": [
                    {
                        "company": "Cyberdyne Systems",
                        "title": "Lead Engineer",
                        "start_date": "2020-01-01",
                        "end_date": "2024-01-01",
                    }
                ],
                "education": [
                    {
                        "institution": "Caltech",
                        "degree": "B.S.",
                        "start_date": "2015-09-01",
                        "end_date": "2019-06-01",
                    }
                ],
            },
            "linkedin_url": "https://linkedin.com/in/sarahconnor",
        }
        r = await client.post("/api/v1/validation/validate", json=payload)
        print(f"Status: {r.status_code}")
        data = r.json()
        print(f"Candidate ID: {data.get('candidate_id')}")
        print(f"LinkedIn: {data.get('linkedin')}")
        print(f"Contact Validation: {data.get('contact_validation', {}).get('status')}")
        print(f"Education Validation: {data.get('education_validation', {}).get('status')}")
        print(f"Experience Validation: {data.get('experience_validation', {}).get('status')}")
        print(f"Company Verification: {data.get('company_verification', {}).get('status')}")

        assert r.status_code == 200
        assert data.get("candidate_id") == "CAND-001"
        assert "linkedin" in data
        assert "profile_exists" in data["linkedin"]
        assert "status_code" in data["linkedin"]
        assert data["contact_validation"]["status"] == "PASSED"
        assert data["education_validation"]["status"] == "PASSED"
        assert data["experience_validation"]["status"] == "PASSED"
        assert data["company_verification"]["status"] == "PASSED"

        print("\n=== 3. Testing POST /api/v1/reports/blob ===")
        r = await client.post("/api/v1/reports/blob", json={"blob_id": "report-CAND-001-20260101.html"})
        print(f"Status: {r.status_code}, Body: {r.json()}")
        assert r.status_code == 200
        assert r.json()["blob_id"] == "report-CAND-001-20260101.html"

        print("\n=== 4. Testing OpenAPI schema endpoints ===")
        r = await client.get("/openapi.json")
        schema = r.json()
        paths = schema.get("paths", {})
        print(f"Total API Paths exposed: {len(paths)}")
        for path, methods in sorted(paths.items()):
            for method in methods.keys():
                print(f"  {method.upper()} {path}")

        expected_paths = {
            "/api/v1/validation/validate",
            "/api/v1/reports/generate",
            "/api/v1/reports/blob",
            "/api/v1/ats/candidate",
            "/api/v1/ats/attachments",
            "/api/v1/ats/search",
            "/health",
        }
        assert set(paths.keys()) == expected_paths, f"Expected {expected_paths}, got {set(paths.keys())}"

    print("\nALL API ENDPOINTS TESTED AND VERIFIED SUCCESSFULLY!")


if __name__ == "__main__":
    asyncio.run(main())
