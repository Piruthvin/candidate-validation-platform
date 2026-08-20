import logging

from app.domain.models import LinkedInData, ResumeData, ValidationEvidence, ValidationStatus

logger = logging.getLogger(__name__)


class LinkedInValidator:
    async def validate(self, resume: ResumeData, linkedin: LinkedInData) -> ValidationEvidence:
        evidence = []
        details = {}

        if not linkedin.profile_exists:
            return ValidationEvidence(
                status=ValidationStatus.SKIPPED,
                evidence=["LinkedIn profile not found or could not be fetched"],
                details={"profile_exists": False},
            )

        details["profile_url"] = linkedin.profile_url
        details["profile_headline"] = linkedin.profile_headline

        evidence.append("Profile Found")
        evidence.append(f"  Profile URL: {linkedin.profile_url}")
        if linkedin.profile_headline:
            evidence.append(f"  Headline: {linkedin.profile_headline}")
        evidence.append("")

        evidence.append("Resume Name")
        evidence.append(f"  ↓ {resume.name or 'N/A'}")
        evidence.append("LinkedIn Name")
        evidence.append(f"  ↓ {linkedin.profile_name or 'N/A'}")
        if linkedin.name_match is True:
            evidence.append("  MATCH")
        elif linkedin.name_match is False:
            evidence.append("  MISMATCH")
            evidence.append(f"  Resume: '{resume.name}' vs LinkedIn: '{linkedin.profile_name}'")
        else:
            evidence.append("  NOT CHECKED")
        evidence.append("")

        first_employer = resume.experience[0].company if resume.experience else None
        linkedin_employer = linkedin.experience[0].get("company") if linkedin.experience else None

        if first_employer or linkedin_employer:
            evidence.append("Resume Employer")
            evidence.append(f"  ↓ {first_employer or 'N/A'}")
            evidence.append("LinkedIn Employer")
            evidence.append(f"  ↓ {linkedin_employer or 'N/A'}")
            if linkedin.employer_match is True:
                evidence.append("  MATCH")
            elif linkedin.employer_match is False:
                evidence.append("  MISMATCH")
            else:
                evidence.append("  NOT CHECKED")
            evidence.append("")

        resume_skills = set(s.lower().strip() for s in (resume.skills or []))
        linkedin_skills = set(s.lower().strip() for s in (linkedin.skills or []))

        if resume_skills or linkedin_skills:
            evidence.append("Resume Skills")
            evidence.append(f"  {len(resume_skills) if resume_skills else 'N/A'}")
            evidence.append("LinkedIn Skills")
            evidence.append(f"  {len(linkedin_skills) if linkedin_skills else 'N/A'}")

            if resume_skills and linkedin_skills:
                matched = sorted(resume_skills & linkedin_skills)
                missing = sorted(resume_skills - linkedin_skills)
                additional = sorted(linkedin_skills - resume_skills)

                evidence.append(f"Matched Skills")
                evidence.append(f"  {len(matched)}")
                if len(matched) <= 15:
                    for s in matched:
                        evidence.append(f"    - {s}")
                else:
                    evidence.append(f"    ({', '.join(matched[:10])}, ...)")

                if missing:
                    evidence.append(f"Missing Skills")
                    evidence.append(f"  {len(missing)}")
                    for s in missing[:10]:
                        evidence.append(f"    - {s}")
                    if len(missing) > 10:
                        evidence.append(f"    ... and {len(missing) - 10} more")

                if additional:
                    evidence.append(f"Additional LinkedIn Skills")
                    evidence.append(f"  {len(additional)}")
                    for s in additional[:10]:
                        evidence.append(f"    - {s}")
                    if len(additional) > 10:
                        evidence.append(f"    ... and {len(additional) - 10} more")

                overlap_pct = (len(matched) / max(len(resume_skills | linkedin_skills), 1)) * 100
                evidence.append(f"Skill overlap: {overlap_pct:.0f}%")
            elif resume_skills and not linkedin_skills:
                evidence.append("  No LinkedIn skills data available for comparison")

        if linkedin.experience:
            details["linkedin_experience_count"] = len(linkedin.experience)

        evidence.append("")

        name_mismatch = linkedin.name_match is False
        employer_mismatch = linkedin.employer_match is False
        low_overlap = False
        if resume_skills and linkedin_skills:
            matched_skill_set = resume_skills & linkedin_skills
            if len(matched_skill_set) < min(len(resume_skills), len(linkedin_skills)) * 0.3:
                low_overlap = True

        status = ValidationStatus.PASSED
        if name_mismatch or employer_mismatch or low_overlap:
            status = ValidationStatus.WARNING

        checks_performed = ["Profile existence check", "Name match verification", "Employer match verification", "Skill overlap analysis"]
        warnings = []
        if name_mismatch:
            warnings.append("LinkedIn name does not match resume name")
        if employer_mismatch:
            warnings.append("Current employer on LinkedIn does not match resume")
        if low_overlap:
            warnings.append("Low skill overlap between resume and LinkedIn")

        issues = []
        failure_reason = ""
        if name_mismatch:
            failure_reason = "LinkedIn name does not match resume name"

        missing_information = []
        if not linkedin.skills:
            missing_information.append("LinkedIn skills data not available for comparison")
        if not linkedin.experience:
            missing_information.append("LinkedIn experience data not available for comparison")

        confidence = 100.0
        if name_mismatch:
            confidence -= 30
        if employer_mismatch:
            confidence -= 20
        if low_overlap:
            confidence -= 15
        confidence = max(confidence, 0.0)

        if status == ValidationStatus.PASSED:
            evidence.append("LinkedIn validation passed. All checks consistent with resume data.")

        details["checks_performed"] = checks_performed
        details["warnings"] = warnings
        details["issues"] = issues
        details["failure_reason"] = failure_reason
        details["confidence"] = confidence
        details["missing_information"] = missing_information

        return ValidationEvidence(status=status, evidence=evidence, details=details)
