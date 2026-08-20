import asyncio
import logging
import re
from typing import Any

from apify_client import ApifyClient

from app.core.config import Settings
from app.domain.models import LinkedInData, ResumeData

logger = logging.getLogger(__name__)

LINKEDIN_PATTERN = re.compile(r"https?://(?:www\.)?linkedin\.com/in/(?P<username>[a-zA-Z0-9_-]+)/?", re.IGNORECASE)


class LinkedInService:
    def __init__(self, settings: Settings) -> None:
        self._token = settings.apify_token
        self._actor_id = settings.apify_actor_id
        self._timeout = settings.apify_timeout
        self._enabled = settings.linkedin_scraping_enabled

    async def enrich(self, linkedin_url: str | None, resume: ResumeData | None = None) -> LinkedInData:
        result = LinkedInData(profile_url=linkedin_url)
        if not linkedin_url or not self._enabled or not self._token:
            if linkedin_url and not self._enabled:
                logger.info("LinkedIn scraping disabled by configuration")
            elif linkedin_url and not self._token:
                logger.warning("LinkedIn scraping skipped: no Apify token configured")
            return result

        match = LINKEDIN_PATTERN.match(linkedin_url.strip())
        if not match:
            logger.warning("Invalid LinkedIn URL format: %s", linkedin_url)
            return result

        try:
            profile = await asyncio.to_thread(self._sync_fetch, linkedin_url)
            if profile:
                result = self._normalize(profile, linkedin_url, match.group("username"), resume)
                logger.info(
                    "LinkedIn fetch succeeded for %s: profile_exists=%s",
                    linkedin_url, result.profile_exists,
                )
            else:
                logger.warning("LinkedIn fetch returned no profile data for %s", linkedin_url)
        except Exception as e:
            logger.error("LinkedIn enrichment failed for %s: %s", linkedin_url, str(e))
            raise

        return result

    def _sync_fetch(self, url: str) -> dict[str, Any] | None:
        client = ApifyClient(self._token)
        run = client.actor(self._actor_id).call(run_input={"profiles": [url], "enrichContact": False}, wait_secs=min(self._timeout, 60))
        if run.get("status") in ("FAILED", "ABORTED", "TIMED-OUT"):
            return None
        dataset_id = run.get("defaultDatasetId")
        if not dataset_id:
            return None
        items = list(client.dataset(dataset_id).iterate_items())
        return items[0] if items else None

    def _normalize(self, data: dict[str, Any], url: str, username: str, resume: ResumeData | None = None) -> LinkedInData:
        def safe(key: str, *alts: str) -> Any:
            for k in [key, *alts]:
                v = data.get(k)
                if v is not None:
                    return v
            return None

        first = safe("firstName", "first_name")
        last = safe("lastName", "last_name")
        full = safe("fullName", "full_name", "fullname")
        if first and last:
            full = f"{first} {last}"

        ln_experience = [{"company": e.get("company"), "title": e.get("title")} for e in safe("experiences", "experience", "positions") or [] if isinstance(e, dict)]
        ln_education = [{"institution": e.get("school", e.get("schoolName")), "degree": e.get("degree")} for e in safe("educations", "education") or [] if isinstance(e, dict)]
        ln_skills = [s.get("name", s) if isinstance(s, dict) else s for s in safe("skills") or []]
        ln_location = safe("location", "geoLocation", "address")

        name_match = None
        employer_match = None
        location_match = None
        experience_match_count = None
        education_match_count = None
        skills_overlap_count = None

        if resume:
            res_name = (resume.name or "").lower().strip()
            ln_name = (full or "").lower().strip()
            name_match = res_name == ln_name or (res_name and ln_name and any(p in ln_name for p in res_name.split()))

            if resume.experience and ln_experience:
                first_employer = (resume.experience[0].company or "").lower().strip()
                ln_first_employer = None
                if ln_experience:
                    ln_first_employer = (ln_experience[0].get("company") or "").lower().strip()
                employer_match = first_employer == ln_first_employer if first_employer and ln_first_employer else None

            if resume.location and ln_location:
                location_match = resume.location.lower().strip() in (ln_location or "").lower().strip()

            if resume.experience and ln_experience:
                res_companies = set((e.company or "").lower().strip() for e in resume.experience if e.company)
                ln_companies = set((e.get("company") or "").lower().strip() for e in ln_experience if e.get("company"))
                experience_match_count = len(res_companies & ln_companies)

            if resume.education and ln_education:
                res_inst = set((e.institution or "").lower().strip() for e in resume.education if e.institution)
                ln_inst = set((e.get("institution") or "").lower().strip() for e in ln_education if e.get("institution"))
                education_match_count = len(res_inst & ln_inst)

            if resume.skills and ln_skills:
                res_skills = set(s.lower().strip() for s in resume.skills)
                ln_skills_set = set(s.lower().strip() for s in ln_skills)
                skills_overlap_count = len(res_skills & ln_skills_set)

        return LinkedInData(
            profile_url=url,
            username=username,
            profile_exists=True,
            profile_name=full,
            profile_headline=safe("headline"),
            experience=ln_experience,
            education=ln_education,
            skills=ln_skills,
            location=ln_location,
            name_match=name_match,
            employer_match=employer_match,
            location_match=location_match,
            experience_match_count=experience_match_count,
            education_match_count=education_match_count,
            skills_overlap_count=skills_overlap_count,
        )
