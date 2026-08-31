import asyncio
import logging
import re

from app.domain.models import (
    CompanyData,
    EmailDomainVerification,
    LinkedInData,
    PreviousValidationReport,
    ResumeData,
    ValidationEvidence,
    ValidationStatus,
    ValidationResult,
)
from app.infrastructure.azure_blob import AzureBlobService
from app.infrastructure.email_verifier import EmailDomainVerifier
from app.infrastructure.retry import retry_async
from app.services.ats_service import AtsService
from app.services.company_verifier import CompanyVerifierService
from app.services.fraud_detector import FraudDetector
from app.services.linkedin_service import LinkedInService
from app.services.validators.certification_validator import CertificationValidator
from app.services.validators.company_validator import CompanyValidator
from app.services.validators.contact_validator import ContactValidator
from app.services.validators.cross_field_validator import CrossFieldValidator
from app.services.validators.education_validator import EducationValidator
from app.services.validators.employment_pattern_validator import EmploymentPatternValidator
from app.services.validators.experience_validator import ExperienceValidator
from app.services.validators.linkedin_validator import LinkedInValidator
from app.services.validators.project_validator import ProjectValidator
from app.services.validators.resume_completeness_validator import ResumeCompletenessValidator
from app.services.validators.skills_validator import SkillsValidator
from app.services.validators.timeline_validator import TimelineValidator

logger = logging.getLogger(__name__)


class ValidationEngine:
    def __init__(
        self,
        ats_service: AtsService | None = None,
        linkedin_service: LinkedInService | None = None,
        company_verifier: CompanyVerifierService | None = None,
        fraud_detector: FraudDetector | None = None,
        azure_blob_service: AzureBlobService | None = None,
        contact_validator: ContactValidator | None = None,
        education_validator: EducationValidator | None = None,
        experience_validator: ExperienceValidator | None = None,
        timeline_validator: TimelineValidator | None = None,
        skills_validator: SkillsValidator | None = None,
        project_validator: ProjectValidator | None = None,
        certification_validator: CertificationValidator | None = None,
        company_validator: CompanyValidator | None = None,
        linkedin_validator: LinkedInValidator | None = None,
        employment_pattern_validator: EmploymentPatternValidator | None = None,
        resume_completeness_validator: ResumeCompletenessValidator | None = None,
        cross_field_validator: CrossFieldValidator | None = None,
    ):
        self.ats_service = ats_service
        self.linkedin_service = linkedin_service
        self.company_verifier = company_verifier
        self.fraud_detector = fraud_detector
        self.azure_blob_service = azure_blob_service
        self.email_verifier = EmailDomainVerifier()
        self.contact_validator = contact_validator or ContactValidator()
        self.education_validator = education_validator or EducationValidator()
        self.experience_validator = experience_validator or ExperienceValidator()
        self.timeline_validator = timeline_validator or TimelineValidator()
        self.skills_validator = skills_validator or SkillsValidator()
        self.project_validator = project_validator or ProjectValidator()
        self.certification_validator = certification_validator or CertificationValidator()
        self.company_validator = company_validator or CompanyValidator()
        self.linkedin_validator = linkedin_validator or LinkedInValidator()
        self.employment_pattern_validator = employment_pattern_validator or EmploymentPatternValidator()
        self.resume_completeness_validator = resume_completeness_validator or ResumeCompletenessValidator()
        self.cross_field_validator = cross_field_validator or CrossFieldValidator()

    async def validate(self, candidate_id: str, resume_data: dict) -> ValidationResult:
        logger.info("=== Starting Validation for candidate_id=%s ===", candidate_id)
        resume = ResumeData(**resume_data)
        resume.candidate_id = candidate_id

        if "raw_text" not in resume_data and resume_data.get("raw_resume_text"):
            resume.raw_text = resume_data.get("raw_resume_text")

        # Extract and normalize company name from all possible fields
        company_name = (
            getattr(resume, "company", None)
            or getattr(resume, "current_employer", None)
            or (resume.experience[0].company if resume.experience and resume.experience[0].company else None)
            or (resume_data.get("company") if isinstance(resume_data, dict) else None)
            or (resume_data.get("current_employer") if isinstance(resume_data, dict) else None)
        )
        if company_name and isinstance(company_name, str):
            company_name = company_name.strip()
            resume.company = company_name

        logger.info(
            "Extracted candidate inputs: name='%s', email='%s', phone='%s', company='%s', linkedin_url='%s'",
            resume.name, resume.email, resume.phone, company_name, resume.linkedin_url,
        )

        completed = []
        skipped = []
        failed = []
        errors = []
        warnings = []
        enrichments = {}
        previous_report = PreviousValidationReport()

        # Step 1: Resume completeness check
        logger.info("Running Step 1: Resume Completeness Check")
        resume_completeness_evidence = await self.resume_completeness_validator.validate(resume)

        # Step 2: Fetch ATS data
        logger.info("Running Step 2: Fetch ATS Data")
        ats_error: str | None = None
        if self.ats_service:
            ats_result = await retry_async(
                lambda: self.ats_service.fetch_candidate(candidate_id, resume),
                max_retries=2, name="ats_search",
            )
            if isinstance(ats_result, dict) and "error" in ats_result:
                ats_error = ats_result["error"]
                logger.warning("ATS fetch error: %s", ats_error)
            else:
                enrichments["ats_candidate"] = ats_result
                completed.append("ats_search")
                logger.info("ATS data fetched successfully: name=%s %s", ats_result.first_name, ats_result.last_name)

        ats_candidate = enrichments.get("ats_candidate")

        # Step 3: Run new LinkedIn check (simple HTTP GET existence check)
        logger.info("Running Step 3: LinkedIn Check (url=%s)", resume.linkedin_url)
        linkedin_error: str | None = None
        if self.linkedin_service:
            li_result = await self.linkedin_service.verify_profile(resume.linkedin_url)
            enrichments["linkedin"] = li_result
            if li_result.profile_exists:
                completed.append("linkedin_fetch")
            elif resume.linkedin_url:
                linkedin_error = f"LinkedIn profile returned HTTP {li_result.status_code}"
                completed.append("linkedin_fetch")
            else:
                completed.append("linkedin_fetch")

        # Step 4: Company verification
        logger.info("Running Step 4: Company Verification (company='%s')", company_name)
        company_error: str | None = None
        if self.company_verifier and company_name:
            co_result = await retry_async(
                lambda: self.company_verifier.verify(company_name),
                max_retries=2, name="company_verification",
            )
            if isinstance(co_result, dict) and "error" in co_result:
                company_error = co_result["error"]
                logger.warning("Company verification error: %s", company_error)
            else:
                enrichments["company"] = co_result
                completed.append("company_verification")
        elif company_name:
            enrichments["company"] = CompanyData(company_name=company_name, is_verified=True)
            completed.append("company_verification")

        # Fraud detector
        if self.fraud_detector:
            try:
                enrichments["fraud_signals"] = await asyncio.to_thread(self.fraud_detector.analyze, resume)
                completed.append("fraud_detection")
            except Exception as e:
                logger.warning("Fraud detection failed: %s", e)
                failed.append("fraud_detection")
                errors.append(f"Fraud detection error: {e}")

        linkedin = enrichments.get("linkedin")
        company = enrichments.get("company")
        fraud_signals = enrichments.get("fraud_signals")

        email_domain_evidence = await self._validate_email_domain(resume)
        if email_domain_evidence:
            enrichments["email_domain_verification"] = email_domain_evidence

        # Step 5: Run remaining validators (existing unchanged rules)
        validators = {
            "resume_completeness": resume_completeness_evidence,
            "contact_validation": self.contact_validator.validate(resume),
            "education_validation": self.education_validator.validate(resume),
            "experience_validation": self.experience_validator.validate(resume, ats_candidate=ats_candidate),
            "timeline_validation": self.timeline_validator.validate(resume, ats_candidate=ats_candidate),
            "skills_validation": self.skills_validator.validate(resume),
            "project_validation": self.project_validator.validate(resume, ats_candidate=ats_candidate),
            "certification_validation": self.certification_validator.validate(resume),
            "employment_pattern": self.employment_pattern_validator.validate(resume),
            "cross_field_validation": self.cross_field_validator.validate(
                resume, ats_candidate, company, linkedin, ats_error, linkedin_error, company_error
            ),
        }

        if linkedin:
            validators["linkedin_verification"] = self.linkedin_validator.validate(resume, linkedin)

        if company or company_name:
            validators["company_verification"] = self.company_validator.validate(
                resume, company or CompanyData(company_name=company_name, is_verified=True)
            )

        result_kwargs = {
            "candidate_id": candidate_id,
            "candidate_name": resume.name,
            "resume": resume,
            "warnings": warnings,
            "errors": errors,
            "completed_steps": completed,
            "skipped_steps": skipped,
            "failed_steps": failed,
            "previous_report_check": previous_report.model_dump(),
        }

        if ats_candidate:
            result_kwargs["ats_candidate"] = ats_candidate
        if linkedin:
            result_kwargs["linkedin"] = linkedin
        if company:
            result_kwargs["company"] = company
        if fraud_signals:
            result_kwargs["fraud_detection"] = self._fraud_to_evidence(fraud_signals)

        email_domain_evidence = enrichments.get("email_domain_verification")
        if email_domain_evidence:
            result_kwargs["email_domain_verification"] = email_domain_evidence

        # Resolve async validators
        async_keys = [k for k, v in validators.items() if asyncio.iscoroutine(v)]
        async_coros = [validators[k] for k in async_keys]
        results_resolved = await asyncio.gather(*async_coros, return_exceptions=True)

        resolved_dict = {}
        for k, v in validators.items():
            if asyncio.iscoroutine(v):
                idx = async_keys.index(k)
                resolved_dict[k] = results_resolved[idx]
            else:
                resolved_dict[k] = v

        for name, evidence in resolved_dict.items():
            if isinstance(evidence, Exception):
                logger.error("Validator %s failed with exception: %s", name, evidence)
                failed.append(name)
                errors.append(f"{name} error: {evidence}")
                result_kwargs[name] = ValidationEvidence(
                    status=ValidationStatus.FAILED,
                    evidence=[f"Validation error in {name}: {evidence}"],
                    details={"error": str(evidence)},
                )
                continue

            # Safe deduplication of evidence messages
            if evidence.evidence:
                evidence.evidence = list(dict.fromkeys(evidence.evidence))

            result_kwargs[name] = evidence
            logger.info("Validator '%s' finished -> status=%s", name, evidence.status.value)

            if evidence.status.value == "SKIPPED":
                skipped.append(name)
            elif evidence.status.value == "FAILED":
                failed.append(name)
                completed.append(name)
            else:
                completed.append(name)

            if evidence.evidence and evidence.status.value == "WARNING":
                warnings.extend(evidence.evidence)

        # Safe deduplication of lists
        result_kwargs["completed_steps"] = list(dict.fromkeys(completed))
        result_kwargs["failed_steps"] = list(dict.fromkeys(failed))
        result_kwargs["skipped_steps"] = list(dict.fromkeys(skipped))
        result_kwargs["warnings"] = list(dict.fromkeys(warnings))
        result_kwargs["errors"] = list(dict.fromkeys(errors))

        logger.info(
            "=== Validation Complete for %s: completed=%d, failed=%d, warnings=%d, errors=%d ===",
            candidate_id, len(result_kwargs["completed_steps"]), len(result_kwargs["failed_steps"]),
            len(result_kwargs["warnings"]), len(result_kwargs["errors"]),
        )

        return ValidationResult(**result_kwargs)

    async def _validate_email_domain(self, resume: ResumeData) -> ValidationEvidence | None:
        if not resume.email:
            return None
        domain = resume.email.split("@")[-1] if "@" in resume.email else ""
        if not domain:
            return None
        try:
            result = await self.email_verifier.verify(resume.email)
            evidence = []
            checks = []
            if result:
                checks.append("DNS lookup")
                checks.append("MX record check")
                checks.append("Disposable domain check")
                checks.append("Corporate domain check")
                if result.has_dns:
                    evidence.append(f"Domain {result.domain} has valid DNS records")
                else:
                    evidence.append(f"Domain {result.domain} has no DNS records")
                if result.has_mx:
                    evidence.append(f"Domain {result.domain} has valid MX records")
                else:
                    evidence.append(f"Domain {result.domain} has no MX records")
                if result.is_disposable:
                    evidence.append(f"Domain {result.domain} is a disposable email provider")
                if result.is_corporate:
                    evidence.append(f"Domain {result.domain} appears to be a corporate domain")
            status = ValidationStatus.PASSED
            if result and result.is_disposable:
                status = ValidationStatus.FAILED
            elif result and not result.has_dns:
                status = ValidationStatus.WARNING
            return ValidationEvidence(
                status=status,
                evidence=list(dict.fromkeys(evidence)),
                details={"domain": domain, "checks_performed": checks, "verification": result.model_dump() if result else None},
            )
        except Exception as e:
            logger.warning("Email domain verification failed: %s", e)
            return None

    def _fraud_to_evidence(self, signals: dict) -> ValidationEvidence:
        evidence = []
        for key in ("keyword_stuffing_indicators", "ai_generation_indicators", "template_indicators", "repeated_phrases"):
            items = signals.get(key, [])
            evidence.extend(items)
        signal_list = signals.get("signals", [])
        status = ValidationStatus.PASSED
        if signal_list:
            if len(signal_list) >= 3:
                status = ValidationStatus.FAILED
            else:
                status = ValidationStatus.WARNING
        checks_performed = ["Keyword stuffing analysis", "AI generation markers", "Template detection", "Repeated phrase detection", "Placeholder pattern check"]
        warnings = []
        issues = list(dict.fromkeys(evidence))
        failure_reason = ""
        if status == ValidationStatus.FAILED:
            failure_reason = f"Fraud detection failed with {len(signal_list)} signal(s): {', '.join(signal_list)}"
        impact = "Fraud detection identifies potential automated or deceptive resume content"
        if evidence:
            impact += f"; {len(evidence)} indicator(s) found that may reduce trust in resume authenticity"
        recruiter_recommendation = "Review flagged content and ask targeted questions to verify resume authenticity"
        if evidence:
            recruiter_recommendation += "; probe for specific experiences mentioned in flagged sections"
        missing_information = []
        confidence = 100.0
        if signal_list:
            confidence -= min(len(signal_list) * 20, 60)
        confidence = max(confidence, 0.0)
        enriched_details = {
            "checks_performed": checks_performed,
            "warnings": warnings,
            "issues": issues,
            "failure_reason": failure_reason,
            "impact": impact,
            "recruiter_recommendation": recruiter_recommendation,
            "confidence": confidence,
            "missing_information": missing_information,
        }
        enriched_details.update(signals)
        return ValidationEvidence(status=status, evidence=list(dict.fromkeys(evidence)), details=enriched_details)
