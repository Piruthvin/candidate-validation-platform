"""
Comprehensive Load, Stress, Chaos, Security, and Concurrency Tests
Targets the running backend at http://localhost:8000
"""
import asyncio
import json
import time
import statistics
import sys
import httpx
from datetime import datetime, timezone
from typing import Any

BASE_URL = "http://localhost:8000"
TIMEOUT = 30.0

SAMPLE_RESUME = {
    "name": "Load Test Candidate",
    "email": "loadtest@company.com",
    "phone": "+1-650-253-0000",
    "summary": "Senior software engineer with 10+ years of experience.",
    "location": "San Francisco, CA",
    "skills": ["Python", "FastAPI", "Docker", "Kubernetes", "AWS", "React", "PostgreSQL", "Redis", "Kafka", "TensorFlow"],
    "experience": [
        {"company": "Tech Corp", "title": "Senior Engineer", "start_date": "2020-01-01", "end_date": "2024-12-31", "description": "Led backend team."},
        {"company": "Startup Inc", "title": "Engineer", "start_date": "2016-03-01", "end_date": "2019-12-31", "description": "Built core features."},
        {"company": "Consulting Co", "title": "Junior Dev", "start_date": "2014-06-01", "end_date": "2016-02-28", "description": "Maintained apps."},
    ],
    "education": [
        {"institution": "Stanford University", "degree": "M.S. Computer Science", "start_date": "2012-09-01", "end_date": "2014-06-01"},
        {"institution": "UC Berkeley", "degree": "B.S. CS", "start_date": "2008-09-01", "end_date": "2012-06-01"},
    ],
    "projects": [
        {"name": "ML Pipeline", "description": "Automated ML pipeline", "technologies": ["Python", "MLflow", "Docker"]},
    ],
    "certifications": [
        {"name": "AWS Solutions Architect", "issuer": "Amazon", "date": "2020-03-15"},
    ],
    "languages": ["English", "Spanish"],
}

class TestResults:
    def __init__(self):
        self.latencies: list[float] = []
        self.errors: list[tuple[int, str]] = []
        self.status_codes: dict[int, int] = {}
        self.timeouts: int = 0
        self.start_time: float = 0.0
        self.end_time: float = 0.0

    def add(self, status: int, latency: float, error: str = ""):
        self.latencies.append(latency)
        self.status_codes[status] = self.status_codes.get(status, 0) + 1
        if status >= 400 or error:
            self.errors.append((status, error))

    @property
    def total(self) -> int:
        return len(self.latencies)

    @property
    def avg_latency(self) -> float:
        return statistics.mean(self.latencies) if self.latencies else 0

    @property
    def p50(self) -> float:
        return statistics.median(self.latencies) if self.latencies else 0

    @property
    def p95(self) -> float:
        if not self.latencies:
            return 0
        sorted_l = sorted(self.latencies)
        idx = int(len(sorted_l) * 0.95)
        return sorted_l[min(idx, len(sorted_l) - 1)]

    @property
    def p99(self) -> float:
        if not self.latencies:
            return 0
        sorted_l = sorted(self.latencies)
        idx = int(len(sorted_l) * 0.99)
        return sorted_l[min(idx, len(sorted_l) - 1)]

    @property
    def max_latency(self) -> float:
        return max(self.latencies) if self.latencies else 0

    @property
    def rps(self) -> float:
        duration = self.end_time - self.start_time
        return self.total / duration if duration > 0 else 0

    @property
    def error_rate(self) -> float:
        return (len(self.errors) / self.total * 100) if self.total > 0 else 0


async def health_check(client: httpx.AsyncClient) -> dict[str, Any]:
    resp = await client.get(f"{BASE_URL}/health", timeout=5.0)
    return resp.json()


async def validate_resume(client: httpx.AsyncClient, resume_data: dict, candidate_id: str, timeout: float = TIMEOUT) -> tuple[int, dict | str, float]:
    payload = {"candidate_id": candidate_id, "resume": resume_data}
    start = time.monotonic()
    try:
        resp = await client.post(f"{BASE_URL}/api/v1/validation/validate", json=payload, timeout=timeout)
        elapsed = time.monotonic() - start
        return resp.status_code, resp.json(), elapsed
    except httpx.TimeoutException:
        elapsed = time.monotonic() - start
        return 0, {"error": "timeout"}, elapsed
    except Exception as e:
        elapsed = time.monotonic() - start
        return 0, {"error": str(e)}, elapsed


async def generate_report(client: httpx.AsyncClient, timeout: float = TIMEOUT) -> tuple[int, dict | str, float]:
    payload = {
        "candidate_id": "report-test-001",
        "candidate_info": {"name": "Report Test", "email": "report@test.com", "phone": "+1-555-0000", "position": "Engineer"},
        "validation_result": {"contact_validation": {"status": "PASSED", "evidence": ["Ok"], "details": None}},
        "llm_analysis": {"overall_score": 85, "validation_score": 90, "recommendation": "REVIEW", "risk_level": "LOW"},
    }
    start = time.monotonic()
    try:
        resp = await client.post(f"{BASE_URL}/api/v1/reports/generate", json=payload, timeout=timeout)
        elapsed = time.monotonic() - start
        return resp.status_code, resp.json(), elapsed
    except httpx.TimeoutException:
        elapsed = time.monotonic() - start
        return 0, {"error": "timeout"}, elapsed
    except Exception as e:
        elapsed = time.monotonic() - start
        return 0, {"error": str(e)}, elapsed


async def load_test(concurrent: int, duration_seconds: int = 10) -> TestResults:
    results = TestResults()
    results.start_time = time.monotonic()
    end_time = results.start_time + duration_seconds

    async def worker():
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            while time.monotonic() < end_time:
                cid = f"load-{concurrent}-{int(time.monotonic() * 1000)}"
                status, data, elapsed = await validate_resume(client, SAMPLE_RESUME, cid, timeout=min(TIMEOUT, end_time - time.monotonic() + 2))
                error = ""
                if isinstance(data, dict) and "error" in data:
                    error = str(data.get("error", ""))
                elif isinstance(data, str):
                    error = data[:200]
                results.add(status, elapsed, error)

    workers = [asyncio.create_task(worker()) for _ in range(concurrent)]
    await asyncio.gather(*workers)
    results.end_time = time.monotonic()
    return results


async def stress_test() -> dict[str, Any]:
    """Gradually increase load until failure."""
    report = {"levels": {}}
    for concurrent in [1, 5, 10, 20, 30, 50]:
        print(f"  Stress level: {concurrent} concurrent...")
        results = await load_test(concurrent, duration_seconds=5)
        report["levels"][concurrent] = {
            "total": results.total,
            "avg_latency": round(results.avg_latency, 3),
            "p95": round(results.p95, 3),
            "p99": round(results.p99, 3),
            "error_rate": round(results.error_rate, 2),
            "rps": round(results.rps, 2),
            "timeouts": results.timeouts,
            "status_codes": dict(sorted(results.status_codes.items())),
        }
        if results.error_rate > 50:
            report["failure_point"] = concurrent
            break
    return report


async def chaos_test() -> dict[str, Any]:
    """Simulate various failure scenarios."""
    report = {}
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        # Test massive payload
        print("  Chaos: Oversized payload...")
        large_resume = dict(SAMPLE_RESUME)
        large_resume["raw_text"] = "A" * 500_000  # 500KB
        status, data, elapsed = await validate_resume(client, large_resume, "chaos-large", timeout=10.0)
        report["oversized_payload"] = {"status": status, "elapsed": round(elapsed, 3), "error": isinstance(data, dict) and data.get("errors", [])}

        # Test missing required fields
        print("  Chaos: Missing fields...")
        for field in ["candidate_id"]:
            payload = {"candidate_id": "chaos-missing", "resume": {"name": "Test"}}
            del payload[field]
            try:
                resp = await client.post(f"{BASE_URL}/api/v1/validation/validate", json=payload, timeout=5.0)
                report[f"missing_{field}"] = {"status": resp.status_code}
            except Exception as e:
                report[f"missing_{field}"] = {"error": str(e)}

        # Test invalid JSON
        print("  Chaos: Invalid JSON...")
        try:
            resp = await client.post(f"{BASE_URL}/api/v1/validation/validate", content=b"not json", headers={"Content-Type": "application/json"}, timeout=5.0)
            report["invalid_json"] = {"status": resp.status_code}
        except Exception as e:
            report["invalid_json"] = {"error": str(e)}

        # Test GET on POST endpoints
        print("  Chaos: Method not allowed...")
        for path in ["/api/v1/validation/validate", "/api/v1/reports/generate", "/api/v1/ats/candidates"]:
            try:
                resp = await client.get(f"{BASE_URL}{path}", timeout=5.0)
                report[f"get_{path.replace('/', '_')}"] = {"status": resp.status_code}
            except Exception as e:
                report[f"get_{path.replace('/', '_')}"] = {"error": str(e)}

        # Concurrent duplicate requests
        print("  Chaos: Concurrent duplicate...")
        async def dup_validate():
            return await validate_resume(client, SAMPLE_RESUME, "chaos-dup-001", timeout=15.0)

        dup_results = await asyncio.gather(*[dup_validate() for _ in range(10)])
        statuses = [r[0] for r in dup_results]
        report["concurrent_duplicate"] = {
            "statuses": dict((s, statuses.count(s)) for s in set(statuses)),
            "all_200": all(s == 200 for s in statuses),
        }

    return report


async def security_test() -> dict[str, Any]:
    """Run security-oriented tests."""
    report = {}
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        # SQL injection
        print("  Security: SQL injection...")
        sqli_resume = dict(SAMPLE_RESUME)
        sqli_resume["name"] = "Robert'); DROP TABLE Candidates;--"
        status, data, elapsed = await validate_resume(client, sqli_resume, "sqli-001", timeout=15.0)
        report["sql_injection"] = {"status": status, "elapsed": round(elapsed, 3)}

        # XSS
        print("  Security: XSS...")
        xss_resume = dict(SAMPLE_RESUME)
        xss_resume["name"] = "<script>alert('XSS')</script>"
        xss_resume["summary"] = "<img src=x onerror=alert(1)>"
        status, data, elapsed = await validate_resume(client, xss_resume, "xss-001", timeout=15.0)
        report["xss"] = {"status": status, "elapsed": round(elapsed, 3)}

        # NoSQL injection via email
        print("  Security: NoSQL injection...")
        nosqli_resume = dict(SAMPLE_RESUME)
        nosqli_resume["email"] = '{"$gt": ""}'
        status, data, elapsed = await validate_resume(client, nosqli_resume, "nosqli-001", timeout=15.0)
        report["nosql_injection"] = {"status": status, "elapsed": round(elapsed, 3)}

        # Command injection
        print("  Security: Command injection...")
        cmdi_resume = dict(SAMPLE_RESUME)
        cmdi_resume["name"] = "$(cat /etc/passwd)"
        status, data, elapsed = await validate_resume(client, cmdi_resume, "cmdi-001", timeout=15.0)
        report["command_injection"] = {"status": status, "elapsed": round(elapsed, 3)}

        # SSRF attempt
        print("  Security: SSRF attempt...")
        ssrf_resume = dict(SAMPLE_RESUME)
        ssrf_resume["linkedin_url"] = "http://169.254.169.254/latest/meta-data/"
        status, data, elapsed = await validate_resume(client, ssrf_resume, "ssrf-001", timeout=15.0)
        report["ssrf_attempt"] = {"status": status, "elapsed": round(elapsed, 3)}

        # Path traversal
        print("  Security: Path traversal...")
        pt_resume = dict(SAMPLE_RESUME)
        pt_resume["name"] = "../../../etc/passwd"
        status, data, elapsed = await validate_resume(client, pt_resume, "pt-001", timeout=15.0)
        report["path_traversal"] = {"status": status, "elapsed": round(elapsed, 3)}

        # Empty payload
        print("  Security: Empty payload...")
        try:
            resp = await client.post(f"{BASE_URL}/api/v1/validation/validate", json={}, timeout=5.0)
            report["empty_payload"] = {"status": resp.status_code}
        except Exception as e:
            report["empty_payload"] = {"error": str(e)}

        # Unicode bombs
        print("  Security: Unicode...")
        unicode_resume = dict(SAMPLE_RESUME)
        unicode_resume["name"] = "\u0000\uFFFF\u202E\u202D" + "A" * 1000
        status, data, elapsed = await validate_resume(client, unicode_resume, "unicode-001", timeout=15.0)
        report["unicode_bomb"] = {"status": status, "elapsed": round(elapsed, 3)}

    return report


async def concurrency_test() -> dict[str, Any]:
    """Test race conditions with parallel validations."""
    report = {}
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        for num_parallel in [20, 50]:
            print(f"  Concurrency: {num_parallel} parallel...")
            start = time.monotonic()
            tasks = []
            for i in range(num_parallel):
                cid = f"concur-{num_parallel}-{i}"
                tasks.append(validate_resume(client, SAMPLE_RESUME, cid, timeout=30.0))
            results = await asyncio.gather(*tasks)
            elapsed = time.monotonic() - start

            statuses = [r[0] for r in results]
            errors = [r[1] for r in results if isinstance(r[1], dict) and r[1].get("errors")]
            latencies = [r[2] for r in results]

            report[num_parallel] = {
                "total_time": round(elapsed, 3),
                "avg_latency": round(statistics.mean(latencies), 3) if latencies else 0,
                "p95_latency": round(sorted(latencies)[int(len(latencies) * 0.95)], 3) if len(latencies) > 1 else 0,
                "max_latency": round(max(latencies), 3) if latencies else 0,
                "status_200": statuses.count(200),
                "status_errors": sum(1 for s in statuses if s != 200),
                "error_count": len(errors),
                "all_successful": all(s == 200 for s in statuses) and all(not (isinstance(r[1], dict) and r[1].get("errors")) for r in results),
            }
    return report


async def report_generation_test() -> dict[str, Any]:
    """Test report generation with various resume types."""
    report = {}
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        test_scenarios = [
            ("small", {"name": "Small", "email": "small@test.com", "phone": "+1-555-0000", "skills": ["Python"], "experience": [{"company": "C1", "title": "Dev", "start_date": "2020-01", "end_date": "2024-12"}], "education": [{"institution": "U1", "degree": "B.S."}]}),
            ("unicode_tamil", {"name": "தமிழ் பெயர்", "email": "tamil@test.com", "phone": "+1-555-0001", "skills": ["Python"], "experience": [{"company": "நிறுவனம்", "title": "பொறியாளர்", "start_date": "2020-01", "end_date": "2024-12"}], "education": [{"institution": "பல்கலைக்கழகம்", "degree": "இளங்கலை"}]}),
            ("unicode_chinese", {"name": "张三", "email": "zhang@test.com", "phone": "+1-555-0002", "skills": ["Python"], "experience": [{"company": "科技公司", "title": "工程师", "start_date": "2020-01", "end_date": "2024-12"}], "education": [{"institution": "清华大学", "degree": "学士"}]}),
            ("unicode_japanese", {"name": "山田太郎", "email": "yamada@test.com", "phone": "+1-555-0003", "skills": ["Python"], "experience": [{"company": "株式会社", "title": "エンジニア", "start_date": "2020-01", "end_date": "2024-12"}], "education": [{"institution": "東京大学", "degree": "学士"}]}),
            ("unicode_arabic", {"name": "محمد أحمد", "email": "arabic@test.com", "phone": "+1-555-0004", "skills": ["Python"], "experience": [{"company": "شركة", "title": "مهندس", "start_date": "2020-01", "end_date": "2024-12"}], "education": [{"institution": "جامعة", "degree": "بكالوريوس"}]}),
            ("emoji", {"name": "Test 😊 🚀", "email": "emoji@test.com", "phone": "+1-555-0005", "skills": ["Python", "🔥"], "experience": [{"company": "Cool Co 🎉", "title": "Ninja 🥷", "start_date": "2020-01", "end_date": "2024-12"}], "education": [{"institution": "Uni 💡", "degree": "BS"}]}),
            ("100_skills", {"name": "Skills Heavy", "email": "skills@test.com", "phone": "+1-555-0006", "skills": [f"Skill-{i}" for i in range(100)], "experience": [{"company": "C1", "title": "Dev", "start_date": "2020-01", "end_date": "2024-12"}], "education": [{"institution": "U1", "degree": "B.S."}]}),
            ("null_values", {"name": None, "email": None, "phone": None, "skills": [], "experience": [], "education": []}),
        ]

        for name, resume in test_scenarios:
            print(f"  Report: {name}...")
            status, data, elapsed = await validate_resume(client, resume, f"report-{name}", timeout=15.0)
            errors_list = data.get("errors", []) if isinstance(data, dict) else []
            report[name] = {
                "status": status,
                "elapsed": round(elapsed, 3),
                "error_count": len(errors_list),
            }
    return report


async def main():
    print("=" * 60)
    print("COMPREHENSIVE PRODUCTION READINESS TEST SUITE")
    print("=" * 60)
    print()
    full_report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "target": BASE_URL,
    }

    # 1. Health Check
    print("\n[1] Health Check")
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            health = await health_check(client)
        print(f"  Status: {health}")
        full_report["health"] = health
    except Exception as e:
        print(f"  FAILED: {e}")
        full_report["health"] = {"error": str(e)}

    # 2. Baseline Latency
    print("\n[2] Baseline Latency (single request)")
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        latencies = []
        for i in range(5):
            status, data, elapsed = await validate_resume(client, SAMPLE_RESUME, f"baseline-{i}", timeout=30.0)
            latencies.append(elapsed)
            print(f"  Request {i+1}: status={status}, latency={elapsed:.3f}s")
        full_report["baseline"] = {
            "avg": round(statistics.mean(latencies), 3),
            "min": round(min(latencies), 3),
            "max": round(max(latencies), 3),
            "last_status": status,
        }

    # 3. Load Tests
    print("\n[3] Load Tests")
    load_results = {}
    for concurrent in [1, 5, 20, 50]:
        print(f"  Testing {concurrent} concurrent users...")
        results = await load_test(concurrent, duration_seconds=5)
        load_results[concurrent] = {
            "total_requests": results.total,
            "avg_latency": round(results.avg_latency, 3),
            "p50": round(results.p50, 3),
            "p95": round(results.p95, 3),
            "p99": round(results.p99, 3),
            "max_latency": round(results.max_latency, 3),
            "rps": round(results.rps, 2),
            "error_rate": round(results.error_rate, 2),
            "timeouts": results.timeouts,
            "status_codes": dict(sorted(results.status_codes.items())),
        }
        print(f"    RPS: {load_results[concurrent]['rps']}, Errors: {load_results[concurrent]['error_rate']}%")
        print(f"    P50: {load_results[concurrent]['p50']}s, P95: {load_results[concurrent]['p95']}s, P99: {load_results[concurrent]['p99']}s")
    full_report["load_test"] = load_results

    # 4. Stress Test
    print("\n[4] Stress Test")
    full_report["stress_test"] = await stress_test()

    # 5. Chaos Test
    print("\n[5] Chaos Test")
    full_report["chaos_test"] = await chaos_test()

    # 6. Security Test
    print("\n[6] Security Test")
    full_report["security_test"] = await security_test()

    # 7. Concurrency Test
    print("\n[7] Concurrency Test")
    full_report["concurrency_test"] = await concurrency_test()

    # 8. Report Generation Test
    print("\n[8] Report Generation Test")
    full_report["report_generation_test"] = await report_generation_test()

    # Print summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    lr = load_results
    for c in sorted(lr.keys()):
        r = lr[c]
        print(f"  {c:3d} concurrent: {r['total_requests']:4d} req, {r['rps']:6.2f} RPS, "
              f"avg={r['avg_latency']:.3f}s, p95={r['p95']:.3f}s, p99={r['p99']:.3f}s, "
              f"errors={r['error_rate']:.1f}%, statuses={r['status_codes']}")

    # Save report
    report_path = "production_readiness_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(full_report, f, indent=2, ensure_ascii=False)
    print(f"\nFull report saved to: {report_path}")
    return full_report


if __name__ == "__main__":
    report = asyncio.run(main())
