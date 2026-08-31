import asyncio
import logging
import time
from typing import Any

import httpx

from app.core.config import Settings
from app.core.exceptions import AtsCandidateNotFound, AtsException
from app.domain.models import AtsCandidate, AtsExperienceItem

logger = logging.getLogger(__name__)


class AtsService:
    REQUEST_TIMEOUT = 30.0

    def __init__(self, settings: Settings) -> None:
        self._proxy_base_url = settings.ats_proxy_base_url
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=self.REQUEST_TIMEOUT)
        return self._client

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None

    async def fetch_candidate(self, record_id: str, resume: Any = None) -> AtsCandidate:
        client = await self._get_client()

        url = f"{self._proxy_base_url}?path=/recruit/v2/Candidates/{record_id}"
        logger.info("ATS fetch_candidate via proxy: GET %s", url)

        resp = await client.get(url)

        if resp.status_code != 200:
            raise AtsException(f"Proxy fetch failed: HTTP {resp.status_code} - {resp.text[:300]}")

        data = resp.json().get("data", [{}])[0]
        raw_exp = data.get("Experience_Details") or []
        experience_details: list[AtsExperienceItem] = []
        for item in raw_exp:
            work_dur = item.get("Work_Duration") or {}
            experience_details.append(
                AtsExperienceItem(
                    company=item.get("Company"),
                    title=item.get("Occupation_Title"),
                    start_date=work_dur.get("from"),
                    end_date=work_dur.get("to"),
                    currently_works_here=bool(item.get("I_currently_work_here")),
                    summary=item.get("Summary"),
                    id=str(item.get("id")) if item.get("id") is not None else None,
                )
            )

        return self._record_to_candidate(
            record_id=str(record_id),
            candidate_id=data.get("Candidate_ID") or str(record_id),
            data=data,
            experience_details=experience_details,
        )

    async def fetch_attachments(self, record_id: str) -> list[dict]:
        client = await self._get_client()

        url = f"{self._proxy_base_url}?path=/recruit/v2/Candidates/{record_id}/attachments"

        resp = await client.get(url)

        if resp.status_code != 200:
            return []

        return resp.json().get("data", [])

    @staticmethod
    def _record_to_candidate(
        record_id: str,
        candidate_id: str,
        data: dict,
        attachments: list[dict] | None = None,
        experience_details: list[AtsExperienceItem] | None = None,
    ) -> AtsCandidate:
        skills_raw = data.get("Skill_Set")
        if isinstance(skills_raw, list):
            skills = [s.strip() for s in skills_raw if isinstance(s, str) and s.strip()]
        else:
            skills = [s.strip() for s in (skills_raw or "").split(",") if s.strip()]

        phone = data.get("Phone") or data.get("Mobile")
        location = (
            data.get("Location")
            or data.get("Current_Location")
            or f"{data.get('City', '') or ''} {data.get('State', '') or ''} {data.get('Country', '') or ''}".strip()
            or None
        )

        total_exp = AtsService._parse_float(data.get("Experience_in_Years"))
        if total_exp is None:
            total_exp = AtsService._parse_float(data.get("Total_Work_Experience"))

        return AtsCandidate(
            record_id=record_id,
            candidate_id=candidate_id,
            first_name=data.get("First_Name"),
            last_name=data.get("Last_Name"),
            email=data.get("Email"),
            phone=phone,
            skills=skills,
            total_experience_years=total_exp,
            current_employer=data.get("Current_Employer"),
            location=location,
            attachments=attachments or [],
            experience_details=experience_details or [],
        )

    async def check_connection(self) -> dict[str, Any]:
        started = time.monotonic()
        try:
            client = await self._get_client()
            url = f"{self._proxy_base_url}?path=/recruit/v2/Candidates/591003000063456008"
            resp = await client.get(url, timeout=15.0)
            elapsed = time.monotonic() - started
            connected = resp.status_code in (200, 204)
            logger.info("ATS connection check via proxy -> HTTP %d connected=%s (%.2fs)", resp.status_code, connected, elapsed)
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
