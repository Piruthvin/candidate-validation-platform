import asyncio
import logging
import time
from typing import Any

import httpx

from app.core.config import Settings
from app.core.exceptions import AtsCandidateNotFound, AtsException
from app.domain.models import AtsCandidate, AtsCandidateList, AtsCandidateListItem, AtsSearchParams

logger = logging.getLogger(__name__)


class AtsService:
    REQUEST_TIMEOUT = 30.0

    def __init__(self, settings: Settings) -> None:
        self._client_id = settings.zoho_client_id
        self._client_secret = settings.zoho_client_secret
        self._refresh_token = settings.zoho_refresh_token
        self._accounts_url = settings.zoho_accounts_url
        self._api_base_url = settings.zoho_api_base_url
        self._access_token: str | None = None
        self._token_lock = asyncio.Lock()
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=self.REQUEST_TIMEOUT)
        return self._client

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None

    async def _ensure_token(self, client: httpx.AsyncClient) -> str:
        async with self._token_lock:
            if self._access_token:
                return self._access_token
            if not self._refresh_token:
                raise AtsException("Zoho refresh token not configured")
            logger.info("ATS refreshing OAuth token from %s", self._accounts_url)
            started = time.monotonic()
            resp = await client.post(
                f"{self._accounts_url}/oauth/v2/token",
                data={
                    "refresh_token": self._refresh_token,
                    "client_id": self._client_id,
                    "client_secret": self._client_secret,
                    "grant_type": "refresh_token",
                },
            )
            elapsed = time.monotonic() - started
            if resp.status_code != 200:
                logger.error("ATS token refresh failed: HTTP %d after %.2fs - %s", resp.status_code, elapsed, resp.text[:300])
                raise AtsException(f"Zoho token refresh failed: HTTP {resp.status_code}")
            data = resp.json()
            self._access_token = data.get("access_token", "")
            if not self._access_token:
                raise AtsException("No access_token in Zoho token refresh response")
            logger.info("ATS token refreshed successfully (%.2fs)", elapsed)
            return self._access_token

    async def fetch_candidate(self, candidate_id: str, resume: Any = None) -> AtsCandidate:
        started = time.monotonic()
        logger.info("ATS fetch_candidate: candidate_id=%s", candidate_id)

        record_id = await self._resolve_candidate_id(candidate_id, resume)
        if not record_id:
            elapsed = time.monotonic() - started
            logger.error("ATS candidate_id=%s could not be resolved to any Record ID (%.2fs)", candidate_id, elapsed)
            raise AtsException(f"Candidate {candidate_id} not found")

        ats_candidate = await self._fetch_by_record_id(record_id, candidate_id)
        elapsed = time.monotonic() - started
        logger.info(
            "ATS fetch_candidate success: candidate_id=%s record_id=%s name=%s %s (%.2fs)",
            candidate_id, record_id,
            ats_candidate.first_name, ats_candidate.last_name, elapsed,
        )
        return ats_candidate

    async def _resolve_candidate_id(self, candidate_id: str, resume: Any = None) -> str | None:
        if candidate_id.isdigit():
            logger.info("ATS candidate_id=%s is numeric, treating as Record ID", candidate_id)
            return candidate_id

        result = await self._search_candidates("Candidate_ID", candidate_id)
        if result:
            return result

        if resume:
            email = getattr(resume, "email", None) or (resume.get("email") if isinstance(resume, dict) else None)
            if email:
                result = await self._search_candidates("Email", email)
                if result:
                    return result

            phone = getattr(resume, "phone", None) or (resume.get("phone") if isinstance(resume, dict) else None)
            if phone:
                result = await self._search_candidates("Phone", phone)
                if result:
                    return result

        return None

    async def _search_candidates(self, field: str, value: str) -> str | None:
        started = time.monotonic()
        client = await self._get_client()
        token = await self._ensure_token(client)
        headers = {"Authorization": f"Zoho-oauthtoken {token}"}
        criteria = f"({field}:equals:{value})"
        url = f"{self._api_base_url}/Candidates/search"
        params = {"criteria": criteria}

        logger.info("ATS search: GET %s criteria=%s", url, criteria)
        resp = await client.get(url, headers=headers, params=params)
        elapsed = time.monotonic() - started

        if resp.status_code == 200:
            body = resp.json()
            records = body.get("data", [])
            if records:
                record_id = str(records[0].get("id", ""))
                logger.info(
                    "ATS search by %s=%s found: record_id=%s, name=%s %s (%.2fs)",
                    field, value, record_id,
                    records[0].get("First_Name"), records[0].get("Last_Name"),
                    elapsed,
                )
                return record_id
            logger.info("ATS search by %s=%s returned 0 results (%.2fs)", field, value, elapsed)
            return None

        if resp.status_code == 204:
            logger.info("ATS search by %s=%s returned 204 (no content)", field, value)
            return None

        body_snippet = resp.text[:300]
        if resp.status_code == 401:
            self._access_token = None
            raise AtsException(f"ATS authentication failed: HTTP 401 during search by {field}")
        if resp.status_code == 403:
            raise AtsException(f"ATS permission denied: HTTP 403 during search by {field}")
        if resp.status_code == 429:
            raise AtsException(f"ATS rate limit exceeded: HTTP 429 during search by {field}")
        logger.error(
            "ATS search by %s=%s failed: HTTP %d - %s (%.2fs)",
            field, value, resp.status_code, body_snippet, elapsed,
        )
        raise AtsException(f"ATS search error: HTTP {resp.status_code} for criteria ({field}:equals:{value})")

    async def _fetch_by_record_id(self, record_id: str, original_candidate_id: str) -> AtsCandidate:
        started = time.monotonic()
        client = await self._get_client()
        token = await self._ensure_token(client)
        headers = {"Authorization": f"Zoho-oauthtoken {token}"}
        url = f"{self._api_base_url}/Candidates/{record_id}"

        logger.info("ATS fetch: GET %s", url)
        resp = await client.get(url, headers=headers)
        elapsed = time.monotonic() - started

        if resp.status_code == 200:
            data = resp.json().get("data", [{}])[0]
            candidate_id = data.get("Candidate_ID", original_candidate_id)
            logger.info(
                "ATS fetch record_id=%s -> Candidate_ID=%s, name=%s %s (%.2fs)",
                record_id, candidate_id,
                data.get("First_Name"), data.get("Last_Name"), elapsed,
            )
            return self._record_to_candidate(candidate_id, data)

        body_snippet = resp.text[:500]
        if resp.status_code == 401:
            self._access_token = None
            raise AtsException(f"ATS authentication failed: HTTP 401 for record {record_id}")
        if resp.status_code == 403:
            raise AtsException(f"ATS permission denied: HTTP 403 for record {record_id}")
        if resp.status_code == 404:
            logger.warning("ATS fetch record_id=%s -> 404. Body: %s", record_id, body_snippet)
            raise AtsException(f"Candidate Record ID {record_id} not found (HTTP 404)")
        if resp.status_code == 429:
            raise AtsException(f"ATS rate limit exceeded: HTTP 429 for record {record_id}")
        logger.error(
            "ATS fetch record_id=%s failed: HTTP %d - %s (%.2fs)",
            record_id, resp.status_code, body_snippet, elapsed,
        )
        raise AtsException(f"ATS request failed: HTTP {resp.status_code} for record {record_id}")

    @staticmethod
    def _record_to_candidate(candidate_id: str, data: dict) -> AtsCandidate:
        skills_raw = data.get("Skill_Set")
        if isinstance(skills_raw, list):
            skills = [s.strip() for s in skills_raw if isinstance(s, str) and s.strip()]
        else:
            skills = [s.strip() for s in (skills_raw or "").split(",") if s.strip()]

        return AtsCandidate(
            candidate_id=candidate_id,
            first_name=data.get("First_Name"),
            last_name=data.get("Last_Name"),
            email=data.get("Email"),
            phone=data.get("Phone"),
            skills=skills,
            total_experience_years=AtsService._parse_float(data.get("Experience_in_Years")),
            current_employer=data.get("Current_Employer"),
            location=data.get("Location") or f"{data.get('City', '') or ''} {data.get('State', '') or ''} {data.get('Country', '') or ''}".strip(),
            report_url=data.get("Report_URL"),
            blob_id=data.get("Blob_ID"),
            validation_status=data.get("Validation_Status"),
            recommendation=data.get("Recommendation"),
            validation_timestamp=data.get("Validation_Timestamp"),
        )

    async def update_candidate(self, candidate_id: str, fields: dict[str, Any]) -> bool:
        started = time.monotonic()
        record_id = await self._resolve_candidate_id(candidate_id)

        client = await self._get_client()
        token = await self._ensure_token(client)
        headers = {"Authorization": f"Zoho-oauthtoken {token}", "Content-Type": "application/json"}
        payload = {"data": [fields]}
        url = f"{self._api_base_url}/Candidates/{record_id}"
        logger.info("ATS PUT %s fields=%s", url, list(fields.keys()))
        resp = await client.put(url, headers=headers, json=payload)
        elapsed = time.monotonic() - started
        if resp.status_code not in (200, 201):
            logger.error("ATS PUT %s failed: HTTP %d - %s (%.2fs)", url, resp.status_code, resp.text[:200], elapsed)
            raise AtsException(f"Failed to update candidate {candidate_id}: HTTP {resp.status_code}")
        logger.info("ATS PUT %s -> HTTP %d success (%.2fs)", url, resp.status_code, elapsed)
        return True

    async def update_report_metadata(
        self,
        candidate_id: str,
        report_url: str,
        blob_id: str,
        validation_status: str,
        recommendation: str,
    ) -> bool:
        from datetime import datetime, timezone

        fields = {
            "Report_URL": report_url,
            "Blob_ID": blob_id,
            "Validation_Status": validation_status,
            "Recommendation": recommendation,
            "Validation_Timestamp": datetime.now(timezone.utc).isoformat(),
        }
        return await self.update_candidate(candidate_id, fields)

    async def list_candidates(self, params: AtsSearchParams = AtsSearchParams()) -> AtsCandidateList:
        started = time.monotonic()
        client = await self._get_client()
        token = await self._ensure_token(client)
        headers = {"Authorization": f"Zoho-oauthtoken {token}"}
        request_params = {
            "page": params.page,
            "per_page": params.page_size,
            "sort_by": params.sort_by,
            "sort_order": params.sort_order,
        }
        if params.search:
            request_params["criteria"] = f"(First_Name:starts_with:{params.search})"
        url = f"{self._api_base_url}/Candidates"
        logger.info("ATS list: GET %s params=%s", url, request_params)
        resp = await client.get(url, headers=headers, params=request_params)
        elapsed = time.monotonic() - started
        if resp.status_code != 200:
            raise AtsException(f"Zoho list API error: HTTP {resp.status_code} - {resp.text[:300]}")
        data = resp.json()
        items = [
            AtsCandidateListItem(
                candidate_id=record.get("Candidate_ID", record.get("id", "")),
                first_name=record.get("First_Name"),
                last_name=record.get("Last_Name"),
                email=record.get("Email"),
                phone=record.get("Phone"),
                current_employer=record.get("Current_Employer"),
                location=record.get("Location") or f"{record.get('City', '') or ''} {record.get('State', '') or ''} {record.get('Country', '') or ''}".strip(),
                created_time=record.get("Created_Time"),
                validation_status=record.get("Validation_Status"),
                recommendation=record.get("Recommendation"),
                report_url=record.get("Report_URL"),
            )
            for record in data.get("data", [])
        ]
        total = data.get("info", {}).get("count", len(items))
        logger.info("ATS list returned %d items of %d total (%.2fs)", len(items), total, elapsed)
        return AtsCandidateList(total=total, data=items)

    async def check_connection(self) -> dict[str, Any]:
        started = time.monotonic()
        try:
            client = await self._get_client()
            token = await self._ensure_token(client)
            headers = {"Authorization": f"Zoho-oauthtoken {token}"}
            resp = await client.get(
                f"{self._api_base_url}/Candidates",
                headers=headers,
                params={"page": 1, "per_page": 1},
                timeout=10.0,
            )
            elapsed = time.monotonic() - started
            connected = resp.status_code == 200
            logger.info("ATS connection check -> HTTP %d connected=%s (%.2fs)", resp.status_code, connected, elapsed)
            return {"connected": connected}
        except Exception as e:
            logger.error("ATS connection check failed: %s", e)
            return {"connected": False, "error": str(e)}

    @staticmethod
    def _parse_float(val: Any) -> float | None:
        if val is None:
            return None
        try:
            return float(val)
        except (ValueError, TypeError):
            return None
