import logging
from datetime import datetime, timezone

from app.domain.models import AtsCandidate, ResumeData, ValidationEvidence, ValidationStatus
from app.services.validators.validation_utils import parse_flexible

logger = logging.getLogger(__name__)


def _normalize_datetime(value: str) -> datetime | None:
    if not value or not isinstance(value, str) or not value.strip():
        return None
    dt = parse_flexible(value)
    if dt is not None and dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def _format_date(dt: datetime) -> str:
    return dt.strftime("%Y-%m")


class TimelineValidator:
    async def validate(self, resume: ResumeData, ats_candidate: AtsCandidate | None = None) -> ValidationEvidence:
        entries = resume.experience or []
        evidence = []

        if not entries:
            return ValidationEvidence(
                status=ValidationStatus.SKIPPED,
                evidence=["No experience entries to validate timeline"],
                details={"gaps_found": 0, "overlaps_detected": False},
            )

        dated = []
        for exp in entries:
            if exp.start_date and exp.end_date:
                start = _normalize_datetime(exp.start_date)
                end = _normalize_datetime(exp.end_date)
                if start is not None and end is not None and start <= end:
                    dated.append((start, end, exp.company or "", exp.title or ""))
                elif start is not None and end is not None and start > end:
                    evidence.append(f"Employment at '{exp.company}': start date after end date ({_format_date(start)} > {_format_date(end)})")

        gaps_found = 0
        overlaps = 0
        future_end = 0
        total_gap_months = 0
        gap_details = []
        overlap_details = []

        now = datetime.now(timezone.utc)
        for start, end, company, title in dated:
            if end > now:
                future_end += 1
                evidence.append(f"Experience at '{company}' has a future end date: {end.date()}")

        dated.sort(key=lambda x: x[0])
        evidence.append("Employment")
        for start, end, company, title in dated:
            evidence.append(f"  {company}")
            if title:
                evidence.append(f"    {title}")
            evidence.append(f"    {_format_date(start)} → {_format_date(end)}")
        evidence.append("")

        has_education = bool(resume.education)
        if has_education:
            evidence.append("Education")
            for edu in resume.education:
                parts = []
                if edu.institution:
                    parts.append(edu.institution)
                if edu.degree:
                    parts.append(edu.degree)
                label = " — ".join(parts) if parts else "Entry"
                dates = []
                if edu.start_date:
                    dates.append(edu.start_date[:7] if len(edu.start_date) >= 7 else edu.start_date)
                if edu.end_date:
                    dates.append(edu.end_date[:7] if len(edu.end_date) >= 7 else edu.end_date)
                date_str = " → ".join(dates) if dates else ""
                evidence.append(f"  {label}")
                if date_str:
                    evidence.append(f"    {date_str}")
            evidence.append("")

        for i in range(1, len(dated)):
            prev_end = dated[i - 1][1]
            prev_company = dated[i - 1][2]
            curr_start = dated[i][0]
            curr_company = dated[i][2]

            if curr_start < prev_end:
                overlaps += 1
                overlap_details.append(f"{prev_company} and {curr_company}")
                evidence.append(f"Overlapping employment: {prev_company} and {curr_company}")

            gap = (curr_start.year - prev_end.year) * 12 + (curr_start.month - prev_end.month)
            if gap > 6:
                gaps_found += 1
                total_gap_months += gap
                gap_details.append({"between": f"{prev_company} and {curr_company}", "months": gap})
                if gap >= 12:
                    evidence.append(f"Employment gap of {gap} months between {prev_company} and {curr_company}")

        if gaps_found > 0 and total_gap_months > 0:
            evidence.append(f"Total gap period: {total_gap_months} months across {gaps_found} gap(s)")
        if overlaps > 0:
            evidence.append(f"{overlaps} overlapping employment period(s) detected")

        evidence.append("")
        evidence.append("Timeline Consistent")
        evidence.append(f"  {'YES' if gaps_found == 0 and overlaps == 0 else 'NO'}")
        evidence.append(f"Employment Gaps")
        evidence.append(f"  {gaps_found}")
        evidence.append(f"Overlap")
        evidence.append(f"  {overlaps}")
        evidence.append("")

        status = ValidationStatus.PASSED
        if overlaps > 0:
            status = ValidationStatus.WARNING
        elif gaps_found > 0 or future_end > 0:
            status = ValidationStatus.WARNING

        ats_dated = []
        if ats_candidate and ats_candidate.experience_details:
            evidence.append("")
            evidence.append("ATS Employment Timeline")
            for a_exp in ats_candidate.experience_details:
                s_val = a_exp.start_date
                e_val = a_exp.end_date
                s_dt = _normalize_datetime(s_val) if s_val else None
                e_dt = _normalize_datetime(e_val) if e_val else None
                if a_exp.currently_works_here:
                    e_dt = now

                line = f"  {a_exp.company or 'Unknown Company'}: {a_exp.title or 'Unknown Title'}"
                if s_dt and e_dt:
                    line += f" ({_format_date(s_dt)} to {'Present' if a_exp.currently_works_here else _format_date(e_dt)})"
                    ats_dated.append((s_dt, e_dt, a_exp.company, a_exp.title))
                elif s_dt:
                    line += f" (From {_format_date(s_dt)})"
                    ats_dated.append((s_dt, now if a_exp.currently_works_here else s_dt, a_exp.company, a_exp.title))
                evidence.append(line)

        checks_performed = ["Gap analysis", "Overlap detection", "Future date check", "Timeline consistency"]
        if ats_dated:
            checks_performed.append("ATS timeline consistency")
        warnings = []
        if gaps_found > 0:
            warnings.append(f"{gaps_found} employment gap(s) detected totaling {total_gap_months} months")
        if overlaps > 0:
            warnings.append(f"{overlaps} overlapping employment period(s) detected")
        if future_end > 0:
            warnings.append(f"Future end date detected for {future_end} entr{'ies' if future_end != 1 else 'y'}")
        issues = []
        failure_reason = ""
        if status == ValidationStatus.FAILED:
            parts = []
            if overlaps > 0:
                parts.append(f"{overlaps} overlapping employment period(s)")
            failure_reason = f"Timeline validation failed due to: {', '.join(parts)}"

        missing_information = []
        missing_no_dates = len(entries) - len(dated)
        if missing_no_dates > 0:
            missing_information.append(f"{missing_no_dates} experience entr{'ies' if missing_no_dates != 1 else 'y'} missing date information")

        confidence = 100.0
        if overlaps > 0:
            confidence -= min(overlaps * 20, 40)
        if future_end > 0:
            confidence -= min(future_end * 15, 30)
        if gaps_found > 0:
            confidence -= min(gaps_found * 10, 20)
        confidence = max(confidence, 0.0)

        return ValidationEvidence(
            status=status,
            evidence=evidence,
            details={
                "gaps_found": gaps_found,
                "total_gap_months": total_gap_months,
                "overlaps_detected": overlaps > 0,
                "overlap_count": overlaps,
                "overlap_details": overlap_details,
                "gap_details": gap_details,
                "future_end_dates": future_end,
                "entries_with_dates": len(dated),
                "checks_performed": checks_performed,
                "warnings": warnings,
                "issues": issues,
                "failure_reason": failure_reason,
                "confidence": confidence,
                "missing_information": missing_information,
            },
        )
