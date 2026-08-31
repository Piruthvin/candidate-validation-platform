"""
Isolated validator and enrichment performance tests.
"""
import asyncio
import httpx
import time
import json

BASE = "http://localhost:8000"

async def measure(method: str, path: str, json_data: dict = None, timeout: float = 30.0, label: str = ""):
    async with httpx.AsyncClient(timeout=timeout) as c:
        s = time.monotonic()
        try:
            if method == "GET":
                r = await c.get(f"{BASE}{path}")
            else:
                r = await c.post(f"{BASE}{path}", json=json_data)
            elapsed = time.monotonic() - s
            data = r.json() if r.status_code == 200 else {}
            errors = data.get("errors", []) if isinstance(data, dict) else []
            return {"status": r.status_code, "time": round(elapsed, 3), "errors": errors, "error_count": len(errors)}
        except Exception as e:
            elapsed = time.monotonic() - s
            return {"status": 0, "time": round(elapsed, 3), "errors": [str(e)], "error_count": 1}

async def main():
    print("=" * 70)
    print("VALIDATOR ISOLATION & ENRICHMENT PERFORMANCE TEST")
    print("=" * 70)
    report = {}

    # 1. Health endpoint (10x)
    print("\n[1] Health endpoint (10 requests)")
    results = []
    for i in range(10):
        r = await measure("GET", "/health", timeout=5.0)
        results.append(r["time"])
    avg = sum(results) / len(results)
    report["health_10x"] = {"times": results, "avg": round(avg, 4), "min": round(min(results), 4), "max": round(max(results), 4)}
    print(f"  Avg: {avg:.4f}s, Min: {min(results):.4f}s, Max: {max(results):.4f}s")

    # 2. Validation only (no enrichment - empty strings for company)
    print("\n[2] Validation-only (empty enrichment fields)")
    base = {"name": "Test User", "email": "test@example.com", "phone": "+1-650-253-0000",
            "skills": ["Python", "FastAPI"], "experience": [], "education": []}
    results = []
    for i in range(5):
        r = await measure("POST", "/api/v1/validation/validate", json_data={"candidate_id": f"val-only-{i}", "resume": base}, timeout=15.0)
        results.append(r)
    times = [r["time"] for r in results]
    report["validation_only"] = {"results": results, "avg": round(sum(times)/len(times), 3) if times else 0}
    print(f"  Avg: {sum(times)/len(times):.3f}s, Last errors: {results[-1]['errors'][:2] if results else []}")

    # 3. Company verifier performance (various inputs)
    print("\n[3] Company verifier performance")
    for company in ["Google", "Microsoft", "Apple", "Amazon", "xyzcompanythatdoesnotexist12345"]:
        resume = {"name": company, "email": "", "phone": "", "skills": [], "experience": [{"company": company, "title": "Engineer", "start_date": "2020-01", "end_date": "2024-12"}], "education": []}
        r = await measure("POST", "/api/v1/validation/validate", json_data={"candidate_id": f"company-{company}", "resume": resume}, timeout=30.0)
        print(f"  Company '{company}': {r['time']:.3f}s, status={r['status']}, errors={r['error_count']}")
        report[f"company_{company}"] = r

    # 4. Complete resume with all sections
    print("\n[4] Full resume (all validators)")
    full = {"name": "Full Test", "email": "full@example.com", "phone": "+1-650-253-0000",
            "summary": "Experienced engineer with 10 years in software development.",
            "location": "San Francisco, CA", "skills": ["Python", "FastAPI", "Docker", "Kubernetes", "AWS"],
            "experience": [
                {"company": "Tech Corp", "title": "Senior Engineer", "start_date": "2020-01-01", "end_date": "2024-12-31"},
                {"company": "Startup Inc", "title": "Engineer", "start_date": "2016-03-01", "end_date": "2019-12-31"}],
            "education": [{"institution": "MIT", "degree": "B.S. CS", "start_date": "2011-09-01", "end_date": "2015-06-01"}],
            "projects": [{"name": "Project X", "description": "AI platform", "technologies": ["Python", "ML"]}],
            "certifications": [{"name": "AWS SA", "issuer": "Amazon", "date": "2020-03-15"}],
            "languages": ["English"]}
    results = []
    for i in range(3):
        r = await measure("POST", "/api/v1/validation/validate", json_data={"candidate_id": f"full-{i}", "resume": full}, timeout=30.0)
        results.append(r)
    times = [r["time"] for r in results]
    report["full_resume"] = {"results": results, "avg": round(sum(times)/len(times), 3) if times else 0}
    print(f"  Avg: {sum(times)/len(times):.3f}s" if times else "  No results")

    # 5. Remote procedure: ATS endpoints
    print("\n[5] ATS endpoints")
    r = await measure("POST", "/api/v1/ats/candidates", json_data={"page": 1, "page_size": 5}, timeout=30.0)
    print(f"  ATS list: {r['time']:.3f}s, status={r['status']}")
    report["ats_list"] = r

    r = await measure("POST", "/api/v1/ats/candidate", json_data={"candidate_id": "test-001"}, timeout=30.0)
    print(f"  ATS detail: {r['time']:.3f}s, status={r['status']}")
    report["ats_detail"] = r

    r = await measure("POST", "/api/v1/ats/search", json_data={"candidate_id": "test-001"}, timeout=30.0)
    print(f"  ATS search: {r['time']:.3f}s, status={r['status']}")
    report["ats_search"] = r

    # 6. Report endpoints
    print("\n[6] Report endpoints")
    r = await measure("POST", "/api/v1/reports/blob", json_data={"blob_id": "test-blob-id"}, timeout=30.0)
    print(f"  Report blob: {r['time']:.3f}s, status={r['status']}")
    report["report_blob"] = r

    # Save
    with open("isolated_test_results.json", "w") as f:
        json.dump(report, f, indent=2)
    print("\nDone!")

asyncio.run(main())
