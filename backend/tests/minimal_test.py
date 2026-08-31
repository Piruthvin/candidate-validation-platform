"""
Minimal tests for the running backend.
Tests: empty resume, validators, edge cases.
"""
import asyncio
import httpx
import time
import json

BASE = "http://localhost:8000"

async def main():
    results = {}
    async with httpx.AsyncClient(timeout=10.0) as c:
        # 1. Health endpoint
        latencies = []
        for i in range(10):
            s = time.monotonic()
            r = await c.get(f"{BASE}/health")
            e = time.monotonic() - s
            latencies.append(e)
        hl = {"avg": round(sum(latencies)/len(latencies), 4), "status": r.status_code, "data": r.json()}
        results["health"] = hl
        print(f"Health avg: {hl['avg']}s, status: {r.status_code}")

        # 2. OpenAPI docs
        s = time.monotonic()
        r = await c.get(f"{BASE}/openapi.json")
        e = time.monotonic() - s
        results["openapi"] = {"time": round(e, 3), "status": r.status_code, "endpoints": list(r.json().get("paths", {}).keys())}
        print(f"OpenAPI: {e:.3f}s, {r.status_code}, paths={len(results['openapi']['endpoints'])}")

        # 3. Empty resume (no external enrichment)
        empty = {"name": "", "email": "", "phone": "", "skills": [], "experience": [], "education": []}
        s = time.monotonic()
        r = await c.post(f"{BASE}/api/v1/validation/validate", json={"candidate_id": "empty-001", "resume": empty})
        e = time.monotonic() - s
        if r.status_code == 200:
            d = r.json()
            results["empty_resume"] = {
                "time": round(e, 3),
                "status": r.status_code,
                "errors": d.get("errors", []),
                "failed_steps": d.get("failed_steps", []),
                "completed_steps": d.get("completed_steps", []),
                "skipped_steps": d.get("skipped_steps", []),
                "has_timeline_bug": any("timeline_validation" in str(err) for err in d.get("errors", [])),
                "validators_present": [k for k in d.keys() if k.endswith("_validation") or k in ("employment_pattern", "cross_field_validation", "fraud_detection", "resume_completeness")],
            }
            print(f"Empty resume: {e:.3f}s, errors={d.get('errors', [])}, failed={d.get('failed_steps', [])}")
        else:
            results["empty_resume"] = {"time": round(e, 3), "status": r.status_code}

        # 4. Validation with name only (no company = fast company verifier)
        minimal = {"name": "Minimal", "email": "", "phone": "", "skills": [], "experience": [], "education": []}
        s = time.monotonic()
        r = await c.post(f"{BASE}/api/v1/validation/validate", json={"candidate_id": "minimal-002", "resume": minimal})
        e = time.monotonic() - s
        results["minimal_name"] = {"time": round(e, 3), "status": r.status_code}
        print(f"Minimal (name only): {e:.3f}s, status={r.status_code}")

        # 5. ATS endpoint
        s = time.monotonic()
        r = await c.post(f"{BASE}/api/v1/ats/candidates", json={"page": 1, "page_size": 5})
        e = time.monotonic() - s
        results["ats_list"] = {"time": round(e, 3), "status": r.status_code}
        print(f"ATS list: {e:.3f}s, status={r.status_code}")

        # 6. Report generation (should fail - no Azure)
        s = time.monotonic()
        r = await c.post(f"{BASE}/api/v1/reports/generate", json={
            "candidate_id": "report-test",
            "candidate_info": {"name": "Test", "email": "t@t.com", "phone": "+1-555-0000", "position": "Dev"},
            "validation_result": {},
            "llm_analysis": {"overall_score": 85, "validation_score": 90, "recommendation": "REVIEW", "risk_level": "LOW"},
        })
        e = time.monotonic() - s
        results["report_gen"] = {"time": round(e, 3), "status": r.status_code}
        print(f"Report gen: {e:.3f}s, status={r.status_code}")

    # Save
    with open("minimal_test_results.json", "w") as f:
        json.dump(results, f, indent=2)
    print("\nDone! Results saved to minimal_test_results.json")

if __name__ == "__main__":
    asyncio.run(main())
