import logging
from datetime import datetime, timezone

from app.domain.models import ResumeData, ValidationEvidence, ValidationStatus

logger = logging.getLogger(__name__)


class EducationValidator:
    async def validate(self, resume: ResumeData) -> ValidationEvidence:
        entries = resume.education or []
        evidence = []

        if not entries:
            return ValidationEvidence(
                status=ValidationStatus.SKIPPED,
                evidence=["No education entries to validate"],
                details={"education_count": 0},
            )

        entry_details = []
        invalid_timelines = 0
        future_dates = 0
        missing_fields = 0
        duplicates = {}

        now = datetime.now(timezone.utc)

        for edu in entries:
            entry = {
                "institution": edu.institution or "N/A",
                "degree": edu.degree or "N/A",
                "field_of_study": edu.field_of_study or "N/A",
                "start_date": edu.start_date or "N/A",
                "end_date": edu.end_date or "N/A",
                "issues": [],
            }

            if not edu.institution:
                missing_fields += 1
                entry["issues"].append("Missing institution name")
            if not edu.degree:
                missing_fields += 1
                entry["issues"].append("Missing degree")
            if edu.institution:
                inst = edu.institution.lower().strip()
                duplicates[inst] = duplicates.get(inst, 0) + 1

            if edu.start_date and edu.end_date:
                try:
                    start = datetime.fromisoformat(edu.start_date.replace("Z", "+00:00"))
                    end = datetime.fromisoformat(edu.end_date.replace("Z", "+00:00"))
                    if start > end:
                        invalid_timelines += 1
                        entry["issues"].append(f"Start date after end date ({edu.start_date} > {edu.end_date})")
                    if end > now:
                        future_dates += 1
                        entry["issues"].append(f"Future graduation date ({edu.end_date})")
                except (ValueError, TypeError):
                    entry["issues"].append("Unparseable date format")

            entry_details.append(entry)

        evidence.append("Education Entries")
        for ed in entry_details:
            evidence.append(f"  Institution: {ed['institution']}")
            evidence.append(f"  Degree: {ed['degree']}")
            evidence.append(f"  Field: {ed['field_of_study']}")
            evidence.append(f"  Start: {ed['start_date']}")
            evidence.append(f"  End: {ed['end_date']}")
            if ed["issues"]:
                for issue in ed["issues"]:
                    evidence.append(f"  ⚠ {issue}")
            evidence.append("")

        dupes = [k for k, v in duplicates.items() if v > 1]
        if dupes:
            evidence.append(f"Duplicate institutions: {', '.join(dupes)}")
            evidence.append("")

        status = ValidationStatus.PASSED
        if invalid_timelines > 0 or future_dates > 0:
            status = ValidationStatus.FAILED
        elif missing_fields > 0 or dupes:
            status = ValidationStatus.WARNING

        if status == ValidationStatus.PASSED:
            evidence.append(f"Education validation passed. All {len(entries)} entr{'ies' if len(entries) != 1 else 'y'} have valid institution, degree, and dates.")

        checks_performed = ["Institution name check", "Degree presence check", "Date validity check", "Duplicate detection"]
        warnings = []
        if invalid_timelines > 0:
            warnings.append(f"{invalid_timelines} education entr{'ies' if invalid_timelines != 1 else 'y'} with start date after end date")
        if future_dates > 0:
            warnings.append(f"{future_dates} education entr{'ies' if future_dates != 1 else 'y'} with future graduation date")
        if dupes:
            warnings.append(f"Duplicate institutions found: {', '.join(dupes)}")
        issues = []
        failure_reason = ""
        if status == ValidationStatus.FAILED:
            parts = []
            if invalid_timelines > 0:
                parts.append("invalid timelines")
            if future_dates > 0:
                parts.append("future dates")
            failure_reason = f"Education validation failed due to: {', '.join(parts)}"

        missing_information = []
        if missing_fields > 0:
            missing_information.append(f"{missing_fields} education field(s) missing")

        confidence = 100.0
        if invalid_timelines > 0:
            confidence -= min(invalid_timelines * 15, 40)
        if future_dates > 0:
            confidence -= min(future_dates * 15, 30)
        if missing_fields > 0:
            confidence -= min(missing_fields * 10, 20)
        confidence = max(confidence, 0.0)

        return ValidationEvidence(
            status=status,
            evidence=evidence,
            details={
                "education_count": len(entries),
                "entries": entry_details,
                "invalid_timelines": invalid_timelines,
                "future_dates": future_dates,
                "missing_fields": missing_fields,
                "duplicate_institutions": dupes,
                "checks_performed": checks_performed,
                "warnings": warnings,
                "issues": issues,
                "failure_reason": failure_reason,
                "confidence": confidence,
                "missing_information": missing_information,
            },
        )
