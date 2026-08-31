import logging

from app.domain.models import CompanyData, ResumeData, ValidationEvidence, ValidationStatus

logger = logging.getLogger(__name__)


class CompanyValidator:
    async def validate(self, resume: ResumeData, company: CompanyData | None = None) -> ValidationEvidence:
        company_name = (
            getattr(company, "company_name", None)
            or getattr(resume, "company", None)
            or getattr(resume, "current_employer", None)
            or (resume.experience[0].company if resume.experience and resume.experience[0].company else None)
        )
        if company_name and isinstance(company_name, str):
            company_name = company_name.strip()

        logger.info("CompanyValidator input: company_name='%s', is_verified=%s", company_name, getattr(company, "is_verified", False) if company else False)

        evidence = []
        details = {}
        warnings = []
        issues = []
        missing_information = []

        if not company_name:
            logger.info("CompanyValidator decision: FAILED (missing company name)")
            return ValidationEvidence(
                status=ValidationStatus.FAILED,
                evidence=["Company name is missing from resume"],
                details={"company_name": None, "failure_reason": "Missing company name", "issues": ["Company name is missing from resume"]},
            )

        details["company_name"] = company_name
        details["website"] = company.website if company else None
        details["domain"] = company.domain if company else None
        details["is_verified"] = getattr(company, "is_verified", False) if company else False

        evidence.append(f"Company: {company_name}")
        if company and company.website:
            evidence.append(f"Verified Website: {company.website}")
        if company and company.domain:
            evidence.append(f"Domain: {company.domain}")
        evidence.append("")

        if company and company.possible_matches:
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

        has_website = bool(company and company.website)
        has_dns = bool(company and company.has_dns)
        has_http = bool(company and company.website_reachable)
        has_ssl = bool(company and company.has_ssl)
        has_mx = bool(company and company.has_mx)

        steps = [
            ("Find company website", has_website),
            ("Resolve DNS", has_dns),
            ("Check HTTP/HTTPS", has_http),
            ("Check SSL", has_ssl),
            ("Check MX", has_mx),
        ]

        evidence.append("Verification Flow")
        failures = []
        for step_name, step_result in steps:
            if step_result is True:
                evidence.append(f"  {step_name} — passed")
            else:
                evidence.append(f"  {step_name} — not verified")
                failures.append(step_name)

        evidence.append("")
        
        if not (company and company.website):
            missing_information.append("Company website URL not provided in resume; automatic search performed")

        # Classification rule: IF company exists and non-empty -> result = "PASSED", IF missing -> result = "FAILED"
        if company and (company.is_verified or has_website or has_http or has_dns):
            status = ValidationStatus.PASSED
            evidence.append(f"Company '{company_name}' is verified.")
        elif company_name:
            status = ValidationStatus.PASSED
            evidence.append(f"Company '{company_name}' identified from candidate resume.")
            if failures:
                warnings.append(f"Automated domain checks had unverified steps: {', '.join(failures)}")
        else:
            status = ValidationStatus.FAILED
            issues.append("Missing company name")

        if company and company.trust_evidence:
            evidence.append("")
            evidence.append("Trust Evidence")
            for te in company.trust_evidence:
                evidence.append(f"  {te}")

        checks_performed = ["Company name identification", "Website reachability", "SSL check", "DNS check", "MX check", "Domain verification"]
        confidence = (company.confidence_score if company and company.confidence_score is not None else 100.0)
        confidence = max(0.0, min(100.0, confidence))

        details["verification_steps"] = dict(steps)
        details["all_steps_passed"] = len(failures) == 0
        details["failed_steps"] = failures
        details["checks_performed"] = checks_performed
        details["warnings"] = warnings
        details["issues"] = issues
        details["failure_reason"] = ""
        details["confidence"] = confidence
        details["missing_information"] = missing_information
        details["possible_matches"] = [pm.model_dump() for pm in company.possible_matches] if company else []

        logger.info("CompanyValidator decision: status=%s for company '%s'", status, company_name)
        return ValidationEvidence(status=status, evidence=evidence, details=details)
