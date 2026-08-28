import logging
import re
from typing import Any

import httpx

from app.core.config import Settings
from app.domain.models import LinkedInData, ResumeData

logger = logging.getLogger(__name__)

LINKEDIN_PATTERN = re.compile(r"https?://(?:www\.)?linkedin\.com/in/(?P<username>[a-zA-Z0-9_-]+)/?", re.IGNORECASE)

BROWSER_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "en-US,en;q=0.9",
    "Connection": "keep-alive",
}


class LinkedInService:
    def __init__(self, settings: Settings) -> None:
        self._timeout = float(settings.linkedin_timeout or 5)

    async def verify_profile(self, linkedin_url: str | None) -> LinkedInData:
        logger.info("LinkedIn verification input: url=%s", linkedin_url)
        if not linkedin_url or not linkedin_url.strip():
            logger.info("LinkedIn verification skipped: empty URL")
            return LinkedInData(
                profile_url=linkedin_url,
                username=None,
                profile_exists=False,
                valid=False,
                status_code=0,
            )

        url = linkedin_url.strip()
        match = LINKEDIN_PATTERN.match(url)
        username = match.group("username") if match else None

        status_code = 0
        try:
            async with httpx.AsyncClient(timeout=self._timeout, follow_redirects=True, headers=BROWSER_HEADERS) as client:
                # 1. Use HEAD request first (faster, lighter, less likely to be blocked)
                try:
                    head_resp = await client.head(url)
                    status_code = head_resp.status_code
                    logger.info("LinkedIn HEAD response: status_code=%d for %s", status_code, url)
                except httpx.TimeoutException:
                    logger.warning("LinkedIn HEAD request timed out for %s", url)
                    status_code = 408
                except (httpx.NetworkError, httpx.ConnectError) as e:
                    logger.warning("LinkedIn HEAD network error for %s: %s", url, e)
                    status_code = 503
                except Exception as e:
                    logger.warning("LinkedIn HEAD request error for %s: %s", url, e)
                    status_code = 500

                # 3. Fallback to GET only if HEAD fails or returns 999
                if status_code == 999 or status_code in (405, 408, 500, 502, 503) or status_code == 0:
                    logger.info("Retrying LinkedIn check with GET for %s (previous status=%d)", url, status_code)
                    try:
                        get_resp = await client.get(url)
                        status_code = get_resp.status_code
                        logger.info("LinkedIn GET response: status_code=%d for %s", status_code, url)
                    except httpx.TimeoutException:
                        logger.warning("LinkedIn GET request timed out for %s -> status_code 408", url)
                        status_code = 408
                    except (httpx.NetworkError, httpx.ConnectError) as e:
                        logger.warning("LinkedIn GET network error for %s -> status_code 503: %s", url, e)
                        status_code = 503
                    except Exception as e:
                        logger.warning("LinkedIn GET request unexpected error for %s: %s -> status_code 500", url, e)
                        status_code = 500
        except Exception as e:
            logger.warning("LinkedIn client error for %s: %s", url, e)
            if status_code == 0:
                status_code = 500

        # 4. Final decision logic
        if status_code == 200:
            profile_exists = True
            valid = True
        elif status_code in (301, 302):
            profile_exists = True
            valid = True
        elif status_code == 999:
            # Treat as reachable but blocked by LinkedIn anti-bot protection
            profile_exists = True
            valid = True
        elif status_code == 404:
            profile_exists = False
            valid = False
        else:
            profile_exists = False
            valid = False

        logger.info(
            "LinkedIn verification decision: url=%s status_code=%d profile_exists=%s valid=%s",
            url, status_code, profile_exists, valid,
        )

        return LinkedInData(
            profile_url=url,
            username=username,
            profile_exists=profile_exists,
            valid=valid,
            status_code=status_code,
        )

    async def enrich(self, linkedin_url: str | None, resume: ResumeData | None = None) -> LinkedInData:
        return await self.verify_profile(linkedin_url)
