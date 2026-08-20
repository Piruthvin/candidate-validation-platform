import asyncio
import logging
import re
import time
from typing import Any

import httpx

from app.core.config import Settings
from app.domain.models import CompanyData, PossibleMatch

logger = logging.getLogger(__name__)

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

_MAX_CONCURRENCY = 20
_CACHE_TTL = 86400
_OVERALL_TIMEOUT = 15.0


class CompanyVerifierService:
    REQUEST_TIMEOUT = 10.0

    def __init__(self, settings: Settings) -> None:
        self._timeout = settings.company_request_timeout
        self._client: httpx.AsyncClient | None = None
        self._semaphore: asyncio.Semaphore | None = None
        self._cache: dict[str, tuple[float, CompanyData]] = {}
        self._pending: dict[str, asyncio.Future] = {}
        self._lock: asyncio.Lock = asyncio.Lock()

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(self._timeout),
                follow_redirects=True,
            )
            self._semaphore = asyncio.Semaphore(_MAX_CONCURRENCY)
        return self._client

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None

    @staticmethod
    def _normalize(name: str) -> str:
        return re.sub(r"[^a-z0-9]", "", name.lower())

    async def verify(self, company_name: str | None) -> CompanyData:
        result = CompanyData(company_name=company_name)
        if not company_name:
            return result

        key = self._normalize(company_name)

        async with self._lock:
            now = time.monotonic()
            cached = self._cache.get(key)
            if cached is not None and now - cached[0] < _CACHE_TTL:
                return cached[1]

            pending = self._pending.get(key)
            if pending is not None:
                return await pending

            future = asyncio.get_event_loop().create_future()
            self._pending[key] = future

        try:
            result = await self._execute_verify(company_name, key)
            async with self._lock:
                self._cache[key] = (time.monotonic(), result)
            if not future.done():
                future.set_result(result)
            return result
        except Exception as e:
            if not future.done():
                future.set_exception(e)
            raise
        finally:
            async with self._lock:
                self._pending.pop(key, None)

    async def _execute_verify(self, company_name: str, key: str) -> CompanyData:
        result = CompanyData(company_name=company_name)
        trust_evidence = []

        try:
            client = await self._get_client()
            async with asyncio.timeout(_OVERALL_TIMEOUT):
                candidates = await self._search_candidates(client, company_name)

            result.possible_matches = candidates

            if not candidates:
                result.is_verified = False
                result.verification_reason = f"Unable to verify company '{company_name}'"
                return result

            best = candidates[0]
            result.website = best.url
            result.domain = self._extract_domain(best.url)
            result.is_verified = best.reachable
            result.has_ssl = best.has_ssl
            result.has_dns = best.has_dns
            result.has_mx = best.has_mx
            result.website_reachable = best.reachable
            result.confidence_score = best.confidence

            if best.has_dns:
                trust_evidence.append(f"DNS records found for {result.domain}")
            if best.has_mx:
                trust_evidence.append(f"MX records found for {result.domain}")
            if best.reachable:
                trust_evidence.append(f"Website {best.url} is reachable")
            if best.has_ssl:
                trust_evidence.append("HTTPS/SSL is enabled")
                ssl_valid = await self._verify_ssl(result.domain or "")
                if ssl_valid:
                    trust_evidence.append(f"SSL certificate is valid for {result.domain}")
                else:
                    trust_evidence.append("SSL certificate validation failed")

            if result.is_verified:
                result.verification_method = "website_resolution"
                result.verification_reason = f"Company '{company_name}' verified via website {best.url} (DNS={best.has_dns}, MX={best.has_mx}, SSL={best.has_ssl})"
            else:
                result.verification_reason = f"Company '{company_name}' could not be verified - website {best.url} unreachable"
        except Exception as e:
            logger.warning("Company verification failed for '%s': %s", company_name, str(e))
            result.verification_reason = f"Verification error: {e}"

        result.trust_evidence = trust_evidence
        return result

    async def _search_candidates(self, client: httpx.AsyncClient, name: str) -> list[PossibleMatch]:
        slug = name.lower().replace(" ", "").replace(".", "").replace(",", "")
        slug = re.sub(r"[^a-z0-9-]", "", slug)

        tlds = [
            "com", "io", "ai", "tech", "dev", "org", "net",
            "co.in", "in", "co.uk", "com.au", "at", "de", "fr",
            "eu", "jp", "sg", "app", "cloud", "digital",
            "co.jp", "co.kr", "co.nz", "co.za", "com.br", "com.mx",
            "com.sg", "com.hk", "com.tr", "com.pl", "com.ar",
            "org.uk", "ac.in", "gov.in", "edu.in", "net.au",
            "info", "biz", "pro", "name", "me", "tv", "cc",
        ]
        urls = []
        for tld in tlds:
            urls.append(f"https://{slug}.{tld}")
            urls.append(f"https://www.{slug}.{tld}")

        async def check_url(url: str) -> PossibleMatch | None:
            try:
                async with self._semaphore:
                    resp = await client.get(url, headers={"User-Agent": USER_AGENT})
                    if resp.status_code < 500:
                        has_ssl = url.startswith("https://")
                        has_dns = False
                        has_mx = False
                        domain = self._extract_domain(url)
                        if domain:
                            try:
                                import dns.asyncresolver
                                resolver = dns.asyncresolver.Resolver()
                                resolver.timeout = 3
                                resolver.lifetime = 3
                                await resolver.resolve(domain, "A")
                                has_dns = True
                                try:
                                    await resolver.resolve(domain, "MX")
                                    has_mx = True
                                except Exception:
                                    pass
                            except Exception:
                                pass
                        confidence = self._score_metadata({
                            "is_reachable": True, "has_dns": has_dns, "has_mx": has_mx,
                        }, has_ssl)
                        return PossibleMatch(url=url, reachable=True, has_ssl=has_ssl, has_dns=has_dns, has_mx=has_mx, confidence=confidence)
            except Exception:
                pass
            return None

        tasks = [check_url(url) for url in urls]
        done = await asyncio.gather(*tasks)
        found = [pm for pm in done if pm is not None]

        found.sort(key=lambda pm: pm.confidence, reverse=True)

        if found:
            return found

        try:
            query = name.replace(" ", "+")
            async with self._semaphore:
                resp = await client.get(
                    f"https://html.duckduckgo.com/html/?q={query}+official+website",
                    headers={"User-Agent": USER_AGENT},
                )
            if resp.status_code == 200:
                seen = set()
                for match in re.finditer(
                    r"https?://(?:www\.)?" + re.escape(slug) + r"\.\S+",
                    resp.text,
                    re.IGNORECASE,
                ):
                    url = match.group(0).rstrip(".,;:!?)'\"")
                    if url not in seen:
                        seen.add(url)
                        found.append(PossibleMatch(url=url, reachable=False, confidence=0.0))
        except Exception:
            pass

        return found

    async def _extract_metadata(self, client: httpx.AsyncClient, url: str) -> dict[str, Any]:
        result: dict[str, Any] = {"is_reachable": False, "has_dns": False, "has_mx": False, "title": None}
        try:
            async with self._semaphore:
                resp = await client.get(url, headers={"User-Agent": USER_AGENT})
            result["is_reachable"] = resp.status_code < 500
            if result["is_reachable"]:
                title_match = re.search(r"<title[^>]*>([^<]+)</title>", resp.text, re.IGNORECASE)
                result["title"] = title_match.group(1).strip()[:200] if title_match else None
                domain = self._extract_domain(url)
                if domain:
                    try:
                        import dns.asyncresolver
                        resolver = dns.asyncresolver.Resolver()
                        resolver.timeout = 5
                        resolver.lifetime = 5
                        await resolver.resolve(domain, "A")
                        result["has_dns"] = True
                        try:
                            await resolver.resolve(domain, "MX")
                            result["has_mx"] = True
                        except Exception:
                            pass
                    except Exception:
                        pass
        except Exception:
            pass
        return result

    async def _verify_ssl(self, domain: str) -> bool:
        try:
            url = f"https://{domain}"
            async with self._semaphore:
                client = await self._get_client()
                await client.get(url, headers={"User-Agent": USER_AGENT})
            return True
        except Exception:
            logger.warning("SSL verification failed for %s", domain)
            return False

    @staticmethod
    def _score_metadata(metadata: dict[str, Any], has_ssl: bool) -> float:
        score = 0.0
        if metadata.get("is_reachable"):
            score += 40.0
        if metadata.get("has_dns"):
            score += 25.0
        if metadata.get("has_mx"):
            score += 20.0
        if has_ssl:
            score += 15.0
        return min(score, 100.0)

    @staticmethod
    def _extract_domain(website: str) -> str | None:
        if not website:
            return None
        domain = re.sub(r"^https?://", "", website.strip().lower()).split("/")[0]
        domain = re.sub(r"^www\.", "", domain)
        return domain if "." in domain else None
