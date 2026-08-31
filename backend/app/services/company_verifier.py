import logging
from typing import Any

from app.core.config import Settings
from app.domain.models import CompanyData, PossibleMatch
from app.services.company_discovery import discover_and_verify_company

logger = logging.getLogger(__name__)


class CompanyVerifierService:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings

    async def close(self) -> None:
        pass

    async def verify(self, company_name: str | None) -> CompanyData:
        """Verify company using web search discovery."""
        if not company_name:
            return CompanyData(company_name=company_name, is_verified=False)

        res = await discover_and_verify_company(company_name)
        status = res.get("status")
        website = res.get("website")
        confidence = float(res.get("confidence", 0.0)) * 100.0
        checks = res.get("checks", {})

        is_verified = status in ("VERIFIED", "PARTIALLY_VERIFIED")
        domain = website.replace("https://", "").replace("http://", "").split("/")[0] if website else None

        possible_matches = []
        for pm_url in res.get("possible_matches", []):
            possible_matches.append(PossibleMatch(
                url=pm_url,
                reachable=checks.get("http_reachable", False) or False,
                has_ssl=checks.get("ssl_valid", False) or False,
                has_dns=checks.get("dns_resolves", False) or False,
                has_mx=False,
                confidence=confidence,
            ))

        trust_evidence = []
        if checks.get("dns_resolves"):
            trust_evidence.append(f"DNS records found for {domain}")
        if checks.get("http_reachable"):
            trust_evidence.append(f"Website {website} is reachable")
        if checks.get("ssl_valid"):
            trust_evidence.append("HTTPS/SSL is enabled")

        return CompanyData(
            company_name=company_name,
            website=f"https://{domain}" if domain else None,
            domain=domain,
            is_verified=is_verified,
            verification_method="web_search",
            confidence_score=confidence,
            website_reachable=checks.get("http_reachable"),
            has_ssl=checks.get("ssl_valid"),
            has_dns=checks.get("dns_resolves"),
            has_mx=checks.get("dns_resolves"),
            trust_evidence=trust_evidence,
            verification_reason=f"Status: {status}",
            possible_matches=possible_matches,
        )
