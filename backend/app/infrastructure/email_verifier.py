import asyncio
import logging
import re
from typing import Any

import dns.asyncresolver

from app.domain.models import EmailDomainVerification

logger = logging.getLogger(__name__)

RESERVED_EXAMPLE_DOMAINS = {"example.com", "example.org", "example.net", "example.edu", "test.com", "test.org", "test.net", "localhost"}
COMMON_PROVIDERS = {"gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "aol.com", "protonmail.com", "icloud.com", "mail.com", "zoho.com", "yandex.com", "gmx.com"}
DISPOSABLE_DOMAINS = {"tempmail.com", "mailinator.com", "guerrillamail.com", "10minutemail.com", "throwaway.com", "yopmail.com", "sharklasers.com", "trashmail.com", "mailnesia.com", "getairmail.com", "temp-mail.org", "fakeinbox.com", "dispostable.com", "spambox.us", "mailexpire.com", "mailmoat.com", "spamgourmet.com", "sneakemail.com", "mytempemail.com"}


class EmailDomainVerifier:
    def __init__(self, dns_timeout: float = 1.0):
        self._dns_timeout = dns_timeout

    async def verify(self, email: str | None) -> EmailDomainVerification:
        result = EmailDomainVerification()
        if not email or "@" not in email:
            return result

        domain = email.split("@")[-1].lower().strip()
        result.domain = domain
        result.is_disposable = domain in DISPOSABLE_DOMAINS
        result.is_reserved = domain in RESERVED_EXAMPLE_DOMAINS
        if result.is_reserved:
            result.is_corporate = False
        else:
            result.is_corporate = domain not in COMMON_PROVIDERS

        if not result.is_reserved:
            await self._check_dns(domain, result)

        return result

    async def _check_dns(self, domain: str, result: EmailDomainVerification) -> None:
        resolver = dns.asyncresolver.Resolver()
        resolver.timeout = self._dns_timeout
        resolver.lifetime = self._dns_timeout

        try:
            a_records = await resolver.resolve(domain, "A")
            result.has_dns = True
            result.dns_records = [str(r) for r in a_records][:5]
        except Exception as e:
            logger.debug("DNS A lookup failed for %s: %s", domain, e)
            result.has_dns = False

        try:
            mx_records = await resolver.resolve(domain, "MX")
            result.has_mx = True
            result.mx_records = [str(r) for r in mx_records][:5]
        except Exception as e:
            logger.debug("DNS MX lookup failed for %s: %s", domain, e)
            result.has_mx = False
