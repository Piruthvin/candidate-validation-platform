import logging

from app.domain.models import CompanyData, ResumeData, ValidationEvidence, ValidationStatus

logger = logging.getLogger(__name__)


class CompanyValidator:
    async def validate(self, resume: ResumeData, company: CompanyData) -> ValidationEvidence:
        evidence = []
        details = {}

        if not company.company_name:
            return ValidationEvidence(
                status=ValidationStatus.SKIPPED,
                evidence=["No company data available to verify"],
                details={"company_name": None},
            )

        details["company_name"] = company.company_name
        details["website"] = company.website
        details["domain"] = company.domain
        details["is_verified"] = company.is_verified

        evidence.append(f"Company: {company.company_name}")
        if company.website:
            evidence.append(f"Verified Website: {company.website}")
        if company.domain:
            evidence.append(f"Domain: {company.domain}")
        evidence.append("")

        if company.possible_matches:
            evidence.append("Possible Matches")
            for i, pm in enumerate(company.possible_matches, 1):
                evidence.append(f"  {i}.")
                evidence.append(f"     {pm.url}")
                status_parts = []
                if pm.reachable:
                    status_parts.append("Reachable")
                if pm.has_ssl:
                    status_parts.append("SSL")
                if pm.has_dns:
                    status_parts.append("DNS")
                if pm.has_mx:
                    status_parts.append("MX")
                if status_parts:
                    for sp in status_parts:
                        evidence.append(f"     {sp}")
                evidence.append(f"     Confidence {int(pm.confidence)}")
                evidence.append("")
        else:
            evidence.append("No candidate domains found.")
            evidence.append("")

        steps = [
            ("Find company website", company.website is not None),
            ("Resolve DNS", company.has_dns),
            ("Check HTTP/HTTPS", company.website_reachable),
            ("Check SSL", company.has_ssl),
            ("Check MX", company.has_mx),
        ]

        evidence.append("Verification Flow")
        all_passed = True
        failures = []
        for step_name, step_result in steps:
            if step_result is True:
                evidence.append(f"  {step_name} — passed")
            elif step_result is False:
                evidence.append(f"  {step_name} — failed")
                failures.append(step_name)
                all_passed = False
            else:
                evidence.append(f"  {step_name} — not checked")

        evidence.append("")
        if company.is_verified:
            evidence.append(f"Company '{company.company_name}' is verified.")
            evidence.append(f"All verification checks passed for {company.website or company.domain}.")
        else:
            evidence.append(f"Company '{company.company_name}' could not be fully verified.")
            if failures:
                evidence.append(f"Failed checks: {', '.join(failures)}.")

        if company.trust_evidence:
            evidence.append("")
            evidence.append("Trust Evidence")
            for te in company.trust_evidence:
                evidence.append(f"  {te}")

        status = ValidationStatus.PASSED if company.is_verified else ValidationStatus.WARNING

        checks_performed = ["Website reachability", "SSL check", "DNS check", "MX check", "Domain verification"]
        warnings = []
        if not company.is_verified:
            warnings.append(f"Company '{company.company_name}' could not be verified")
        if company.website_reachable is False:
            warnings.append("Company website is not reachable")
        if company.has_ssl is False:
            warnings.append("No valid SSL certificate on company website")
        if company.has_dns is False:
            warnings.append("Company domain has no DNS records")
        if company.has_mx is False:
            warnings.append("Company domain has no MX records")

        issues = []
        failure_reason = ""
        if not company.is_verified:
            failure_reason = f"Company '{company.company_name}' could not be verified"

        missing_information = []
        if not company.website:
            missing_information.append("Company website URL not available")

        confidence = company.confidence_score if company.confidence_score is not None else (100.0 if company.is_verified else 50.0)
        confidence = max(0.0, min(100.0, confidence))

        details["verification_steps"] = dict(steps)
        details["all_steps_passed"] = all_passed
        details["failed_steps"] = failures
        details["checks_performed"] = checks_performed
        details["warnings"] = warnings
        details["issues"] = issues
        details["failure_reason"] = failure_reason
        details["confidence"] = confidence
        details["missing_information"] = missing_information
        details["possible_matches"] = [pm.model_dump() for pm in company.possible_matches]

        return ValidationEvidence(status=status, evidence=evidence, details=details)
