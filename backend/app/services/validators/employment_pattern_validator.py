import logging
from datetime import datetime

from app.domain.models import ResumeData, ValidationEvidence, ValidationStatus

logger = logging.getLogger(__name__)


class EmploymentPatternValidator:
    async def validate(self, resume: ResumeData) -> ValidationEvidence:
        entries = resume.experience or []
        evidence = []

        if not entries:
            return ValidationEvidence(
                status=ValidationStatus.SKIPPED,
                evidence=["No employment data to analyze"],
                details={"employment_entries": 0},
            )

        tenure_details = []
        tenures = []
        for exp in entries:
            if exp.start_date and exp.end_date:
                try:
                    start = datetime.fromisoformat(exp.start_date.replace("Z", "+00:00"))
                    end = datetime.fromisoformat(exp.end_date.replace("Z", "+00:00"))
                    if start < end:
                        months = (end.year - start.year) * 12 + (end.month - start.month)
                        tenures.append((months, exp.company or "", exp.title or ""))
                        tenure_details.append({
                            "company": exp.company or "N/A",
                            "title": exp.title or "N/A",
                            "duration_months": months,
                            "duration_label": f"{months} months",
                        })
                except (ValueError, TypeError):
                    pass

        if not tenures:
            return ValidationEvidence(
                status=ValidationStatus.WARNING,
                evidence=["Could not calculate employment tenures from available dates"],
                details={"employment_entries": len(entries)},
            )

        evidence.append("Tenure Analysis")
        for td in tenure_details:
            evidence.append(f"  {td['company']} — {td['title']}")
            evidence.append(f"    {td['duration_label']}")
            if td["duration_months"] < 6:
                evidence.append(f"    ⚠ Short tenure (under 6 months)")
            elif td["duration_months"] < 12:
                evidence.append(f"    ~ Moderate tenure (under 12 months)")
            else:
                evidence.append(f"    ✓ Stable tenure (12+ months)")
        evidence.append("")

        avg_tenure = sum(m for m, _, _ in tenures) / len(tenures)
        evidence.append(f"  Average tenure: {avg_tenure:.1f} months")
        evidence.append("")

        short_tenures = [(m, c) for m, c, _ in tenures if m < 6]
        job_hop = [(m, c) for m, c, _ in tenures if m < 12]

        if short_tenures:
            for months, company in short_tenures:
                evidence.append(f"Very short tenure at '{company}': {months} months")
        if len(job_hop) >= len(tenures) * 0.5 and len(job_hop) >= 3:
            evidence.append(f"Job hopping pattern: {len(job_hop)}/{len(tenures)} positions lasted less than 12 months")
        if avg_tenure < 12:
            evidence.append(f"Low average tenure: {avg_tenure:.1f} months")

        if not short_tenures and not (len(job_hop) >= len(tenures) * 0.5 and len(job_hop) >= 3) and avg_tenure >= 12:
            evidence.append("Employment pattern is stable. No job hopping indicators detected.")

        status = ValidationStatus.PASSED
        if len(job_hop) >= 2:
            status = ValidationStatus.FAILED
        elif short_tenures or (len(job_hop) >= len(tenures) * 0.5 and len(job_hop) >= 3) or avg_tenure < 12:
            status = ValidationStatus.WARNING

        checks_performed = ["Tenure calculation", "Job hopping analysis", "Stability assessment"]
        warnings = []
        if short_tenures:
            for months, company in short_tenures:
                warnings.append(f"Very short tenure at '{company}': {months} months")
        if len(job_hop) >= len(tenures) * 0.5 and len(job_hop) >= 3:
            warnings.append(f"Job hopping pattern: {len(job_hop)}/{len(tenures)} positions lasted less than 12 months")
        if avg_tenure < 12:
            warnings.append(f"Low average tenure: {avg_tenure:.1f} months")
        issues = []
        failure_reason = ""
        if status == ValidationStatus.FAILED:
            failure_reason = f"Employment pattern indicates instability: {len(job_hop)}/{len(tenures)} position(s) under 12 months"

        missing_information = []
        if not tenures:
            missing_information.append("Could not calculate tenures from available date information")

        confidence = 100.0
        if short_tenures:
            confidence -= min(len(short_tenures) * 10, 30)
        if len(job_hop) >= len(tenures) * 0.5 and len(job_hop) >= 3:
            confidence -= 20
        if avg_tenure < 12:
            confidence -= 15
        confidence = max(confidence, 0.0)

        return ValidationEvidence(
            status=status,
            evidence=evidence,
            details={
                "employment_entries": len(entries),
                "tenure_details": tenure_details,
                "average_tenure_months": round(avg_tenure, 1),
                "short_tenures_under_6mo": len(short_tenures),
                "short_tenures_under_12mo": len(job_hop),
                "checks_performed": checks_performed,
                "warnings": warnings,
                "issues": issues,
                "failure_reason": failure_reason,
                "confidence": confidence,
                "missing_information": missing_information,
            },
        )
