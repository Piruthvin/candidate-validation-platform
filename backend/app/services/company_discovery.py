import asyncio
from difflib import SequenceMatcher
import logging
import re
import socket
import ssl
from typing import Any
from urllib.parse import parse_qs, unquote, urlparse

import httpx

logger = logging.getLogger(__name__)

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

BLOCKLIST = [
    "linkedin.com",
    "glassdoor.com",
    "ambitionbox.com",
    "indeed.com",
    "facebook.com",
    "instagram.com",
    "twitter.com",
    "x.com",
    "wikipedia.org",
    "youtube.com",
    "github.com",
    "zoominfo.com",
    "crunchbase.com",
    "google.com",
    "duckduckgo.com",
    "bing.com",
    "yahoo.com",
    "naukri.com",
    "shine.com",
    "foundit.in",
    "monster.com",
    "quora.com",
    "reddit.com",
    "medium.com",
    "bloomberg.com",
    "reuters.com",
    "forbes.com",
]


def normalize_company_name(name: str) -> str:
    """Normalize company name by removing common entity suffixes."""
    if not name or not isinstance(name, str):
        return ""
    REMOVE_WORDS = [
        "pvt", "ltd", "private", "limited",
        "technologies", "technology",
        "solutions", "systems", "corp", "inc"
    ]
    name_str = name.lower()
    for word in REMOVE_WORDS:
        name_str = name_str.replace(word, "")
    s = re.sub(r"[^\w\s-]", " ", name_str)
    s = re.sub(r"\s+", " ", s).strip()
    return s or name.strip().lower()


def extract_domain(url: str) -> str | None:
    """Extract clean domain name from URL."""
    if not url or not isinstance(url, str):
        return None
    url_str = url.strip()
    if not url_str.startswith("http://") and not url_str.startswith("https://"):
        url_str = "https://" + url_str
    try:
        parsed = urlparse(url_str)
        netloc = parsed.netloc.lower().split(":")[0]
        netloc = re.sub(r"^www\.", "", netloc)
        return netloc if "." in netloc else None
    except Exception:
        return None


def is_valid_candidate(domain: str) -> bool:
    """Check if domain is valid and not in blocklist."""
    if not domain or not isinstance(domain, str):
        return False
    d = domain.lower().strip()
    for blocked in BLOCKLIST:
        if d == blocked or d.endswith("." + blocked):
            return False
    if "." not in d or d.replace(".", "").isdigit():
        return False
    return True


def domain_matches_company(domain: str, company_name: str) -> bool:
    """Check if domain matches company name using substring, word, and fuzzy matching (>0.6)."""
    if not domain or not company_name:
        return False
    normalized = normalize_company_name(company_name).lower()
    norm_clean = re.sub(r"[^a-z0-9]", "", normalized)
    if not norm_clean:
        return False

    dom_main = domain.lower().split(".")[0]
    dom_clean = re.sub(r"[^a-z0-9]", "", dom_main)

    # 1. Exact / Substring match (e.g. "igold" in "igoldtech.com" or "concentrix" in "concentrix.com")
    if norm_clean in dom_clean or dom_clean in norm_clean:
        return True

    # 2. Word match (e.g. "concentrix" for "Concentrix Catalyst")
    words = [w for w in normalized.split() if len(w) >= 3]
    if any(w in dom_clean for w in words):
        return True

    # 3. Fuzzy similarity check (> 0.6)
    sim = SequenceMatcher(None, norm_clean, dom_clean).ratio()
    if sim > 0.6:
        return True

    return False


async def web_search(query: str, top_k: int = 5) -> list[str]:
    """Search the web for company websites using DuckDuckGo POST HTML search."""
    urls: list[str] = []
    headers = {"User-Agent": USER_AGENT}

    # Method 1: DuckDuckGo HTML POST Search
    try:
        async with httpx.AsyncClient(timeout=5.0, follow_redirects=True) as client:
            resp = await client.post(
                "https://html.duckduckgo.com/html/",
                data={"q": query},
                headers=headers,
            )
            if resp.status_code == 200:
                for m in re.finditer(r'href=["\']([^"\']+)["\']', resp.text):
                    raw_href = m.group(1)
                    if "/l/?uddg=" in raw_href:
                        parsed_q = parse_qs(urlparse(raw_href).query)
                        if "uddg" in parsed_q:
                            target_url = parsed_q["uddg"][0]
                            urls.append(target_url)
                    elif raw_href.startswith("http") and "duckduckgo.com" not in raw_href:
                        urls.append(raw_href)
    except Exception as e:
        logger.debug("DuckDuckGo HTML POST search error: %s", e)

    # Method 2: Fallback DuckDuckGo Lite search if needed
    if not urls:
        try:
            async with httpx.AsyncClient(timeout=5.0, follow_redirects=True) as client:
                resp = await client.post(
                    "https://lite.duckduckgo.com/lite/",
                    data={"q": query},
                    headers=headers,
                )
                if resp.status_code == 200:
                    for m in re.finditer(r'class="result-link"\s+href="([^"]+)"', resp.text):
                        urls.append(m.group(1))
        except Exception as e:
            logger.debug("DuckDuckGo Lite search error: %s", e)

    seen = set()
    deduped_urls = []
    for u in urls:
        if u not in seen:
            seen.add(u)
            deduped_urls.append(u)
            if len(deduped_urls) >= top_k:
                break

    return deduped_urls


async def dns_lookup(domain: str, retries: int = 2, timeout: float = 5.0) -> bool | None:
    """Check if domain resolves via DNS."""
    for attempt in range(retries):
        try:
            loop = asyncio.get_event_loop()
            await asyncio.wait_for(
                loop.run_in_executor(None, socket.getaddrinfo, domain, None),
                timeout=timeout,
            )
            return True
        except (socket.gaierror, socket.herror):
            return False
        except asyncio.TimeoutError:
            if attempt == retries - 1:
                return None
        except Exception:
            if attempt == retries - 1:
                return False
    return False


async def http_check(domain: str, retries: int = 2, timeout: float = 5.0) -> bool | None:
    """Check if domain is reachable via HTTP/HTTPS."""
    headers = {"User-Agent": USER_AGENT}
    for attempt in range(retries):
        try:
            async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
                resp = await client.get(f"https://{domain}", headers=headers)
                if resp.status_code < 500:
                    return True
        except Exception:
            try:
                async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
                    resp = await client.get(f"http://{domain}", headers=headers)
                    if resp.status_code < 500:
                        return True
            except Exception:
                if attempt == retries - 1:
                    return False
    return False


async def ssl_check(domain: str, retries: int = 2, timeout: float = 5.0) -> bool | None:
    """Check if domain has a valid SSL certificate."""
    for attempt in range(retries):
        try:
            loop = asyncio.get_event_loop()
            def _check_ssl():
                ctx = ssl.create_default_context()
                with socket.create_connection((domain, 443), timeout=timeout) as sock:
                    with ctx.wrap_socket(sock, server_hostname=domain) as ssock:
                        cert = ssock.getpeercert()
                        return bool(cert)
            result = await asyncio.wait_for(
                loop.run_in_executor(None, _check_ssl),
                timeout=timeout,
            )
            return result
        except Exception:
            if attempt == retries - 1:
                return False
    return False


async def discover_and_verify_company(company_name: str | None) -> dict[str, Any]:
    """Discover and verify company strictly via web search."""
    if not company_name or not isinstance(company_name, str) or not company_name.strip():
        logger.info("Company discovery: missing company name")
        checks = {
            "name_match": False,
            "dns_resolves": False,
            "http_reachable": False,
            "ssl_valid": False,
        }
        return {
            "status": "UNVERIFIED",
            "confidence": 0.0,
            "website": None,
            "source": "search",
            "possible_matches": [],
            "checks": checks,
            "error": "Missing company name",
        }

    try:
        normalized_name = normalize_company_name(company_name)
        query = f"{normalized_name} company official website"
        logger.info("Company discovery query: '%s' for company='%s' (normalized='%s')", query, company_name, normalized_name)

        # Step 2 & 3: Search query & Domain extraction
        search_results = await web_search(query, top_k=5)
        logger.info("Raw search results for '%s': %s", query, search_results)

        candidate_domains: list[str] = []
        for url in search_results:
            dom = extract_domain(url)
            if dom and is_valid_candidate(dom) and dom not in candidate_domains:
                candidate_domains.append(dom)

        logger.info("Filtered candidate domains for '%s': %s", company_name, candidate_domains)

        if not candidate_domains:
            checks = {
                "name_match": False,
                "dns_resolves": False,
                "http_reachable": False,
                "ssl_valid": False,
            }
            return {
                "status": "UNVERIFIED",
                "confidence": 0.0,
                "website": None,
                "source": "search",
                "possible_matches": [],
                "checks": checks,
                "error": None,
            }

        # Step 7: Filter candidate domains by domain_matches_company and select best domain
        matching_domains = [d for d in candidate_domains if domain_matches_company(d, company_name)]

        if not matching_domains:
            checks = {
                "name_match": False,
                "dns_resolves": False,
                "http_reachable": False,
                "ssl_valid": False,
            }
            return {
                "status": "UNVERIFIED",
                "confidence": 0.0,
                "website": None,
                "source": "search",
                "possible_matches": candidate_domains,
                "checks": checks,
                "error": None,
            }

        norm_clean = re.sub(r"[^a-z0-9]", "", normalized_name.lower())

        # Ranking priority:
        # 1. Full exact slug match vs partial word match
        # 2. Shortest domain
        # 3. .com / .in preferred
        def rank_domain(d: str) -> tuple[int, int, int]:
            d_main = d.lower().split(".")[0]
            d_clean = re.sub(r"[^a-z0-9]", "", d_main)
            full_match_score = 2 if (norm_clean and norm_clean in d_clean) else 1
            len_penalty = -len(d)
            tld_score = 2 if d.endswith((".com", ".in", ".co.in")) else (1 if d.endswith((".org", ".net", ".io", ".tech")) else 0)
            return (full_match_score, len_penalty, tld_score)

        ranked = sorted(matching_domains, key=rank_domain, reverse=True)
        selected_domain = ranked[0]
        logger.info("Selected domain for '%s': %s", company_name, selected_domain)

        # Step 8: Verification Checks
        name_match = domain_matches_company(selected_domain, company_name)
        dns_res = await dns_lookup(selected_domain)
        http_res = await http_check(selected_domain, timeout=5.0) if dns_res is not False else False
        ssl_res = await ssl_check(selected_domain, timeout=5.0) if http_res is not False else False

        checks = {
            "name_match": name_match,
            "dns_resolves": dns_res,
            "http_reachable": http_res,
            "ssl_valid": ssl_res,
        }

        # Step 9: Scoring (RELAXED)
        weights = {
            "name_match": 0.5,
            "dns_resolves": 0.2,
            "http_reachable": 0.2,
            "ssl_valid": 0.1,
        }

        score = sum(weights[k] for k, v in checks.items() if v is True)
        confidence = round(score, 2)
        logger.info("Match score and checks for '%s' (%s): %s, confidence=%.2f", company_name, selected_domain, checks, confidence)

        # Step 10: Status Logic (FIXED)
        if not selected_domain:
            status = "UNVERIFIED"
        elif confidence >= 0.7:
            status = "VERIFIED"
        elif confidence >= 0.3:
            status = "PARTIALLY_VERIFIED"
        else:
            status = "UNVERIFIED"

        logger.info("Company discovery final status for '%s': %s (confidence=%.2f, website=%s)", company_name, status, confidence, selected_domain)

        return {
            "status": status,
            "confidence": confidence,
            "website": selected_domain if status != "UNVERIFIED" else None,
            "source": "search",
            "possible_matches": candidate_domains,
            "checks": checks,
            "error": None,
        }

    except Exception as e:
        logger.exception("Company discovery exception for '%s': %s", company_name, e)
        return {
            "status": "NOT_EVALUATED",
            "confidence": 0.0,
            "website": None,
            "source": "search",
            "possible_matches": [],
            "checks": {},
            "error": str(e),
        }
