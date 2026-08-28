import logging

from app.domain.models import LinkedInData, ResumeData, ValidationEvidence, ValidationStatus

logger = logging.getLogger(__name__)


class LinkedInValidator:
    async def validate(self, resume: ResumeData, linkedin: LinkedInData) -> ValidationEvidence:
        logger.info(
            "LinkedInValidator input: profile_url=%s, status_code=%s, profile_exists=%s",
            getattr(linkedin, "profile_url", None),
            getattr(linkedin, "status_code", None),
            getattr(linkedin, "profile_exists", None),
        )

        if not linkedin or not linkedin.profile_url:
            evidence = ValidationEvidence(
                status=ValidationStatus.SKIPPED,
                evidence=["No LinkedIn profile URL provided"],
                details={
                    "profile_url": None,
                    "username": None,
                    "profile_exists": False,
                    "valid": False,
                    "status_code": 0,
                    "checks_performed": ["Profile URL existence check"],
                },
            )
            logger.info("LinkedInValidator output: SKIPPED (no URL)")
            return evidence

        # IF valid and profile_exists -> PASSED, ELSE -> FAILED
        status = ValidationStatus.PASSED if (linkedin.valid and linkedin.profile_exists) else ValidationStatus.FAILED
        evidence_list = []
        if status == ValidationStatus.PASSED:
            evidence_list.append(f"LinkedIn profile verified: {linkedin.profile_url} (HTTP {linkedin.status_code})")
        else:
            evidence_list.append(f"LinkedIn profile verification failed for {linkedin.profile_url} (HTTP {linkedin.status_code})")

        result = ValidationEvidence(
            status=status,
            evidence=evidence_list,
            details={
                "profile_url": linkedin.profile_url,
                "username": linkedin.username,
                "profile_exists": linkedin.profile_exists,
                "valid": linkedin.valid,
                "status_code": linkedin.status_code,
                "checks_performed": ["HTTP profile existence check"],
            },
        )
        logger.info("LinkedInValidator decision: status=%s for %s", status, linkedin.profile_url)
        return result
