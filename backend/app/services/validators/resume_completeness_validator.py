import logging

from app.domain.models import ResumeData, ValidationEvidence, ValidationStatus

logger = logging.getLogger(__name__)


class ResumeCompletenessValidator:
    async def validate(self, resume: ResumeData) -> ValidationEvidence:
        evidence = []
        details = {}
        sections_found = []
        sections_missing = []
        critical_missing = []

        checks = {
            "Name": resume.name,
            "Email": resume.email,
            "Phone": resume.phone,
        }
        for label, value in checks.items():
            if value:
                sections_found.append(f"✓ {label} present: {value}")
            else:
                sections_missing.append(label)
                critical_missing.append(label)

        if resume.summary:
            sections_found.append("✓ Summary present")
        else:
            sections_missing.append("Summary")

        exp_count = len(resume.experience or [])
        if exp_count > 0:
            sections_found.append(f"✓ Experience section found ({exp_count} entr{'ies' if exp_count != 1 else 'y'})")
        else:
            sections_missing.append("Experience")

        edu_count = len(resume.education or [])
        if edu_count > 0:
            sections_found.append(f"✓ Education section found ({edu_count} entr{'ies' if edu_count != 1 else 'y'})")
        else:
            sections_missing.append("Education")

        skill_count = len(resume.skills or [])
        if skill_count > 0:
            sections_found.append(f"✓ Skills section found ({skill_count} skills)")
        else:
            sections_missing.append("Skills")

        for s in sections_found:
            evidence.append(s)

        warnings = []
        issues = []
        if sections_missing:
            warnings.append(f"Missing sections: {', '.join(sections_missing)}")
        if critical_missing:
            issues.append(f"Critical fields missing: {', '.join(critical_missing)}")

        status = ValidationStatus.PASSED
        failure_reason = ""
        if critical_missing:
            status = ValidationStatus.FAILED
            failure_reason = f"Missing critical fields: {', '.join(critical_missing)}"
        elif sections_missing:
            status = ValidationStatus.WARNING
            failure_reason = f"Missing non-critical sections: {', '.join(sections_missing)}"

        if status == ValidationStatus.PASSED:
            evidence.append("Verified")
            evidence.append("✓ All critical fields present (Name, Email, Phone)")
            evidence.append("✓ All recommended sections present (Summary, Experience, Education, Skills)")
            evidence.append("No critical fields are missing.")

        if exp_count > 0:
            empty_exp = [e for e in resume.experience if not e.company and not e.title]
            if empty_exp:
                n = len(empty_exp)
                msg = f"{n} experience entr{'ies' if n != 1 else 'y'} with no company or title"
                evidence.append(msg)
                warnings.append(msg)

        if edu_count > 0:
            empty_edu = [e for e in resume.education if not e.institution]
            if empty_edu:
                n = len(empty_edu)
                msg = f"{n} education entr{'ies' if n != 1 else 'y'} with no institution"
                evidence.append(msg)
                warnings.append(msg)

        details["sections_found"] = sections_found
        details["sections_missing"] = sections_missing
        details["critical_present"] = {k: bool(v) for k, v in checks.items()}
        details["experience_count"] = exp_count
        details["education_count"] = edu_count
        details["skill_count"] = skill_count
        details["checks_performed"] = ["Section presence check", "Critical field check", "Empty entry detection"]
        details["warnings"] = warnings
        details["issues"] = issues
        details["failure_reason"] = failure_reason
        details["missing_information"] = list(sections_missing)
        details["confidence"] = max(100.0 - len(sections_missing) * 10 - len(critical_missing) * 15, 0.0)

        return ValidationEvidence(
            status=status,
            evidence=evidence,
            details=details,
        )
