import logging
from datetime import datetime

from app.domain.models import AtsCandidate, ResumeData, ValidationEvidence, ValidationStatus
from app.services.company_discovery import discover_and_verify_company
from app.services.validators.validation_utils import parse_flexible

logger = logging.getLogger(__name__)


class ExperienceValidator:
    async def validate(self, resume: ResumeData, ats_candidate: AtsCandidate | None = None) -> ValidationEvidence:
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
        unverified_companies = 0
        duplicate_employers = set()
        seen = set()

        now = datetime.now()
        future_dates = 0

        for exp in entries:
            comp_verification = await discover_and_verify_company(exp.company)
            entry = {
                "company": exp.company or "N/A",
                "title": exp.title or "N/A",
                "start_date": exp.start_date or "N/A",
                "end_date": exp.end_date or "N/A",
                "company_verification": comp_verification,
                "future_date": False,
                "issues": [],
            }

            if not exp.company:
                missing_company += 1
                entry["issues"].append("Missing company name")
            else:
                comp_status = comp_verification.get("status")
                if comp_status == "UNVERIFIED":
                    unverified_companies += 1
                    entry["issues"].append(f"Company '{exp.company}' unverified via search (UNVERIFIED)")
                elif comp_status == "POSSIBLE_MATCHES":
                    entry["issues"].append(f"Multiple possible matches found for '{exp.company}'")

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
                start = parse_flexible(exp.start_date)
                end = parse_flexible(exp.end_date)
                if start and end:
                    # Strip timezone info for safe comparison
                    start_naive = start.replace(tzinfo=None) if hasattr(start, "tzinfo") else start
                    end_naive = end.replace(tzinfo=None) if hasattr(end, "tzinfo") else end

                    if end_naive > now:
                        entry["future_date"] = True
                        entry["issues"].append("Future end date detected")
                        future_dates += 1

                    if start_naive > end_naive:
                        invalid_dates += 1
                        entry["issues"].append(f"Start date after end date ({exp.start_date} > {exp.end_date})")
                    else:
                        duration_months = (end_naive.year - start_naive.year) * 12 + (end_naive.month - start_naive.month)
                        entry["duration_months"] = duration_months
                        entry["duration"] = f"{duration_months} months"
                else:
                    entry["issues"].append("Unparseable date format")

            entry_details.append(entry)

        evidence.append("Experience Entries")
        for ed in entry_details:
            evidence.append(f"  Company: {ed['company']}")
            cv = ed.get("company_verification", {})
            if cv:
                evidence.append(f"  Company Verification: {cv.get('status', 'UNVERIFIED')} (Website: {cv.get('website') or 'None'}, Confidence: {cv.get('confidence', 0.0)})")
            evidence.append(f"  Title: {ed['title']}")
            evidence.append(f"  Start: {ed['start_date']}")
            evidence.append(f"  End: {ed['end_date']}")
            if ed.get("future_date"):
                evidence.append("  Future End Date: YES (Warning)")
            if "duration" in ed:
                evidence.append(f"  Duration: {ed['duration']}")
            dates_valid = not any("Start date after" in i for i in ed["issues"])
            evidence.append(f"  Dates Valid: {'YES' if dates_valid else 'NO'}")
            if ed["issues"]:
                for issue in ed["issues"]:
                    evidence.append(f"  ⚠ {issue}")
            evidence.append("")

        ats_entry_details = []
        # Process ATS experience records if available
        if ats_candidate and ats_candidate.experience_details:
            evidence.append("ATS Experience Records")
            for a_exp in ats_candidate.experience_details:
                a_entry = {
                    "company": a_exp.company or "N/A",
                    "title": a_exp.title or "N/A",
                    "start_date": a_exp.start_date or "N/A",
                    "end_date": "Present" if a_exp.currently_works_here else (a_exp.end_date or "N/A"),
                    "currently_works_here": a_exp.currently_works_here,
                    "issues": [],
                }
                if not a_exp.company:
                    a_entry["issues"].append("Missing company in ATS record")
                if not a_exp.title:
                    a_entry["issues"].append("Missing title in ATS record")
                ats_entry_details.append(a_entry)
                evidence.append(f"  Company: {a_entry['company']}")
                evidence.append(f"  Title: {a_entry['title']}")
                evidence.append(f"  Tenure: {a_entry['start_date']} to {a_entry['end_date']}")
                if a_entry["issues"]:
                    for issue in a_entry["issues"]:
                        evidence.append(f"  ⚠ {issue}")
                evidence.append("")

        checks_performed = [
            "Web search company discovery",
            "Domain verification and filtering",
            "Company presence check",
            "Title presence check",
            "Date validity check",
            "Duplicate employer detection",
            "Tenure analysis",
        ]
        if ats_entry_details:
            checks_performed.append("ATS experience records analysis")

        warnings = []
        if invalid_dates > 0:
            warnings.append(f"{invalid_dates} entr{'ies' if invalid_dates != 1 else 'y'} with start date after end date")
        if future_dates > 0:
            warnings.append(f"Future end date detected for {future_dates} entr{'ies' if future_dates != 1 else 'y'}")
        if unverified_companies > 0:
            warnings.append(f"{unverified_companies} company entr{'ies' if unverified_companies != 1 else 'y'} unverified via web search")
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
        # Section 11: Failure Rule (DO NOT OVERFAIL):
        # Only fail if ALL companies are UNVERIFIED or invalid_dates > 0 or all missing company/title
        if unverified_companies > 0 and unverified_companies == len(entries) and missing_company == 0:
            status = ValidationStatus.FAILED
            failure_reason = f"Experience validation failed: All {len(entries)} company entries unverified"
        elif invalid_dates > 0:
            status = ValidationStatus.FAILED
            failure_reason = f"Experience validation failed due to {invalid_dates} invalid date range(s)"
        elif (missing_company > 0 and missing_company == len(entries)) or (missing_title > 0 and missing_title == len(entries)):
            status = ValidationStatus.FAILED
            failure_reason = "All experience entries are missing company name or job title"
        elif unverified_companies > 0 or missing_company > 0 or missing_title > 0 or duplicate_employers or len(entries) >= 6 or future_dates > 0:
            status = ValidationStatus.WARNING
        elif any("Unparseable" in i for entry in entry_details for i in entry["issues"]):
            status = ValidationStatus.WARNING
        else:
            status = ValidationStatus.PASSED

        if status == ValidationStatus.PASSED:
            evidence.append(f"Experience validation passed. All {len(entries)} entr{'ies' if len(entries) != 1 else 'y'} have verified companies, titles, and dates.")
        elif status == ValidationStatus.WARNING:
            evidence.append(f"Experience validation completed with warnings for {len(entries)} entr{'ies' if len(entries) != 1 else 'y'}.")
        elif status == ValidationStatus.FAILED:
            evidence.append(f"Experience validation failed: {failure_reason}")

        missing_information = []
        if missing_company > 0:
            missing_information.append(f"{missing_company} entr{'ies' if missing_company != 1 else 'y'} missing company name")
        if missing_title > 0:
            missing_information.append(f"{missing_title} entr{'ies' if missing_title != 1 else 'y'} missing job title")

        confidence = 100.0
        if unverified_companies > 0:
            confidence -= min(unverified_companies * 25, 60)
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
                "unverified_companies": unverified_companies,
                "ats_experience_count": len(ats_entry_details),
                "ats_entries": ats_entry_details,
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
