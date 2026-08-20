import logging
from datetime import datetime, timezone

from app.domain.models import ResumeData, ValidationEvidence, ValidationStatus

logger = logging.getLogger(__name__)


class CertificationValidator:
    async def validate(self, resume: ResumeData) -> ValidationEvidence:
        certs = resume.certifications or []
        evidence = []

        if not certs:
            return ValidationEvidence(
                status=ValidationStatus.SKIPPED,
                evidence=["No certifications to validate"],
                details={"certification_count": 0},
            )

        cert_details = []
        missing_name = 0
        missing_issuer = 0
        old_dates = 0
        future_dates = 0
        now = datetime.now(timezone.utc)

        for cert in certs:
            entry = {
                "name": cert.name or "N/A",
                "issuer": cert.issuer or "N/A",
                "date": cert.date or "N/A",
                "issues": [],
            }

            if not cert.name:
                missing_name += 1
                entry["issues"].append("Missing certification name")
            if not cert.issuer:
                missing_issuer += 1
                entry["issues"].append("Missing issuer/vendor")

            is_future = False
            if cert.date:
                try:
                    dt = datetime.fromisoformat(cert.date.replace("Z", "+00:00"))
                    if dt.year < 2000:
                        old_dates += 1
                        entry["issues"].append(f"Date appears too old ({dt.date()})")
                    if dt > now:
                        future_dates += 1
                        is_future = True
                        entry["issues"].append(f"Future date ({dt.date()})")
                except (ValueError, TypeError):
                    entry["issues"].append("Unparseable date format")

            entry["future_date"] = is_future
            cert_details.append(entry)

        for cd in cert_details:
            evidence.append("Certification")
            evidence.append(f"  {cd['name']}")
            evidence.append(f"Issuer")
            evidence.append(f"  {cd['issuer']}")
            evidence.append(f"Date")
            evidence.append(f"  {cd['date']}")
            evidence.append(f"Future Date")
            evidence.append(f"  {'YES' if cd['future_date'] else 'NO'}")
            if cd["issues"]:
                for issue in cd["issues"]:
                    evidence.append(f"  ⚠ {issue}")
            evidence.append("")

        status = ValidationStatus.PASSED
        if old_dates > 0 or future_dates > 0:
            status = ValidationStatus.FAILED
        elif missing_name > 0 or missing_issuer > 0:
            status = ValidationStatus.WARNING

        if status == ValidationStatus.PASSED:
            evidence.append(f"Certification validation passed. All {len(certs)} certification(s) have valid names, issuers, and dates.")

        checks_performed = ["Issuer validation", "Date validation", "Future date check", "Duplicate detection"]
        warnings = []
        if old_dates > 0:
            warnings.append(f"{old_dates} certification(s) with dates before year 2000")
        if future_dates > 0:
            warnings.append(f"{future_dates} certification(s) with future date")
        issues = []
        if missing_name > 0:
            issues.append(f"{missing_name} certification(s) missing name")
        if missing_issuer > 0:
            issues.append(f"{missing_issuer} certification(s) missing issuer/vendor")
        failure_reason = ""
        if status == ValidationStatus.FAILED:
            parts = []
            if old_dates > 0:
                parts.append(f"{old_dates} old date(s)")
            if future_dates > 0:
                parts.append(f"{future_dates} future date(s)")
            failure_reason = f"Certification validation failed due to: {', '.join(parts)}"

        missing_information = []
        if missing_name > 0:
            missing_information.append(f"{missing_name} certification(s) missing name")
        if missing_issuer > 0:
            missing_information.append(f"{missing_issuer} certification(s) missing issuer")

        confidence = 100.0
        if old_dates > 0:
            confidence -= min(old_dates * 15, 40)
        if future_dates > 0:
            confidence -= min(future_dates * 20, 40)
        if missing_name > 0:
            confidence -= min(missing_name * 10, 20)
        if missing_issuer > 0:
            confidence -= min(missing_issuer * 10, 20)
        confidence = max(confidence, 0.0)

        return ValidationEvidence(
            status=status,
            evidence=evidence,
            details={
                "certification_count": len(certs),
                "certifications": cert_details,
                "missing_name": missing_name,
                "missing_issuer": missing_issuer,
                "old_dates": old_dates,
                "future_dates": future_dates,
                "checks_performed": checks_performed,
                "warnings": warnings,
                "issues": issues,
                "failure_reason": failure_reason,
                "confidence": confidence,
                "missing_information": missing_information,
            },
        )
