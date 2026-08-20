import logging
from datetime import datetime

from app.domain.models import ResumeData, ValidationEvidence, ValidationStatus

logger = logging.getLogger(__name__)


class ExperienceValidator:
    async def validate(self, resume: ResumeData) -> ValidationEvidence:
        entries = resume.experience or []
        evidence = []

        if not entries:
            return ValidationEvidence(
                status=ValidationStatus.SKIPPED,
                evidence=["No experience entries to validate"],
                details={"experience_count": 0},
            )

        entry_details = []
        missing_company = 0
        missing_title = 0
        invalid_dates = 0
        duplicate_employers = set()
        seen = set()

        for exp in entries:
            entry = {
                "company": exp.company or "N/A",
                "title": exp.title or "N/A",
                "start_date": exp.start_date or "N/A",
                "end_date": exp.end_date or "N/A",
                "issues": [],
            }

            if not exp.company:
                missing_company += 1
                entry["issues"].append("Missing company name")
            if not exp.title:
                missing_title += 1
                entry["issues"].append("Missing job title")
            if exp.company:
                key = exp.company.lower().strip()
                if key in seen:
                    duplicate_employers.add(exp.company)
                    entry["issues"].append(f"Duplicate employer: {exp.company}")
                seen.add(key)

            if exp.start_date and exp.end_date:
                try:
                    start = datetime.fromisoformat(exp.start_date.replace("Z", "+00:00"))
                    end = datetime.fromisoformat(exp.end_date.replace("Z", "+00:00"))
                    if start > end:
                        invalid_dates += 1
                        entry["issues"].append(f"Start date after end date ({exp.start_date} > {exp.end_date})")
                    else:
                        duration_months = (end.year - start.year) * 12 + (end.month - start.month)
                        entry["duration_months"] = duration_months
                        entry["duration"] = f"{duration_months} months"
                except (ValueError, TypeError):
                    entry["issues"].append("Unparseable date format")

            entry_details.append(entry)

        evidence.append("Experience Entries")
        for ed in entry_details:
            evidence.append(f"  Company: {ed['company']}")
            evidence.append(f"  Title: {ed['title']}")
            evidence.append(f"  Start: {ed['start_date']}")
            evidence.append(f"  End: {ed['end_date']}")
            if "duration" in ed:
                evidence.append(f"  Duration: {ed['duration']}")
            dates_valid = not any("Start date after" in i for i in ed["issues"])
            evidence.append(f"  Dates Valid: {'YES' if dates_valid else 'NO'}")
            if ed["issues"]:
                for issue in ed["issues"]:
                    evidence.append(f"  ⚠ {issue}")
            evidence.append("")

        status = ValidationStatus.PASSED
        if invalid_dates > 0:
            status = ValidationStatus.FAILED
        elif missing_company > 0 or missing_title > 0 or duplicate_employers or len(entries) >= 6:
            status = ValidationStatus.WARNING

        if status == ValidationStatus.PASSED:
            evidence.append(f"Experience validation passed. All {len(entries)} entr{'ies' if len(entries) != 1 else 'y'} have valid company, title, and dates.")

        checks_performed = ["Company presence check", "Title presence check", "Date validity check", "Duplicate employer detection", "Tenure analysis"]
        warnings = []
        if invalid_dates > 0:
            warnings.append(f"{invalid_dates} entr{'ies' if invalid_dates != 1 else 'y'} with start date after end date")
        if duplicate_employers:
            warnings.append(f"Duplicate employer(s) found: {', '.join(duplicate_employers)}")
        if len(entries) >= 6:
            warnings.append(f"Large number of employers ({len(entries)}) — may indicate frequent job changes")
        issues = []
        if missing_company > 0:
            issues.append(f"{missing_company} entr{'ies' if missing_company != 1 else 'y'} missing company name")
        if missing_title > 0:
            issues.append(f"{missing_title} entr{'ies' if missing_title != 1 else 'y'} missing job title")
        failure_reason = ""
        if status == ValidationStatus.FAILED:
            failure_reason = f"Experience validation failed due to {invalid_dates} invalid date range(s)"

        missing_information = []
        if missing_company > 0:
            missing_information.append(f"{missing_company} entr{'ies' if missing_company != 1 else 'y'} missing company name")
        if missing_title > 0:
            missing_information.append(f"{missing_title} entr{'ies' if missing_title != 1 else 'y'} missing job title")

        confidence = 100.0
        if invalid_dates > 0:
            confidence -= min(invalid_dates * 20, 50)
        if missing_company > 0:
            confidence -= min(missing_company * 10, 20)
        if missing_title > 0:
            confidence -= min(missing_title * 5, 10)
        if len(entries) >= 6:
            confidence -= 10
        confidence = max(confidence, 0.0)

        return ValidationEvidence(
            status=status,
            evidence=evidence,
            details={
                "experience_count": len(entries),
                "entries": entry_details,
                "missing_company": missing_company,
                "missing_title": missing_title,
                "invalid_date_ranges": invalid_dates,
                "duplicate_employers": list(duplicate_employers),
                "checks_performed": checks_performed,
                "warnings": warnings,
                "issues": issues,
                "failure_reason": failure_reason,
                "confidence": confidence,
                "missing_information": missing_information,
            },
        )
