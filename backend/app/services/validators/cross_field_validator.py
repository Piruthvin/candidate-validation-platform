import logging
import re
from datetime import datetime

from app.domain.models import AtsCandidate, CompanyData, LinkedInData, ResumeData, ValidationEvidence, ValidationStatus

logger = logging.getLogger(__name__)


class CrossFieldValidator:
    async def validate(
        self,
        resume: ResumeData,
        candidate: AtsCandidate | None = None,
        company: CompanyData | None = None,
        linkedin: LinkedInData | None = None,
        ats_error: str | None = None,
        linkedin_error: str | None = None,
        company_error: str | None = None,
    ) -> ValidationEvidence:
        evidence = []
        comparisons: list[dict] = []
        warnings = []
        issues = []

        evidence.append("Checks Performed")
        evidence.append("")

        all_sections = []

        resume_vs_ats = self._build_ats_section(resume, candidate, ats_error)
        all_sections.append(resume_vs_ats)

        resume_vs_linkedin = self._build_linkedin_section(resume, linkedin, linkedin_error)
        all_sections.append(resume_vs_linkedin)

        resume_vs_company = self._build_company_section(resume, company, company_error)
        all_sections.append(resume_vs_company)

        timeline_section = self._build_timeline_section(resume)
        all_sections.append(timeline_section)

        resume_vs_contact = self._build_contact_section(resume)
        all_sections.append(resume_vs_contact)

        evidence.append("Evidence")

        has_not_evaluated = False
        has_mismatch = False
        overall_reasons = []

        for section in all_sections:
            evidence.append("")
            evidence.append(section["header"])
            evidence.append("")

            if section["status"] == "NOT_EVALUATED":
                has_not_evaluated = True
                evidence.append(f"  Status")
                evidence.append(f"  NOT EVALUATED")
                evidence.append(f"  Reason")
                evidence.append(f"  {section['reason']}")
            elif section["status"] == "PASS":
                evidence.append(f"  PASS")
            elif section["status"] == "MISMATCH":
                has_mismatch = True
                evidence.append(f"  MISMATCH")

            for line in section.get("lines", []):
                evidence.append(f"  {line}")

            if section.get("reason") and section["status"] != "NOT_EVALUATED":
                overall_reasons.append(section["reason"])

            comparisons.extend(section.get("comparisons", []))

        evidence.append("")
        evidence.append("Overall")

        if has_mismatch:
            status = ValidationStatus.FAILED
            evidence.append("  FAIL")
            reasons = [s.get("reason", "Contradiction detected") for s in all_sections if s["status"] == "MISMATCH"]
            evidence.append(f"  Reason")
            evidence.append(f"  {'; '.join(reasons)}")
        elif has_not_evaluated:
            status = ValidationStatus.WARNING
            evidence.append("  WARNING")
            not_evaled = [s["header"] for s in all_sections if s["status"] == "NOT_EVALUATED"]
            reasons = [s["reason"] for s in all_sections if s["status"] == "NOT_EVALUATED"]
            evidence.append("  Reason")
            evidence.append(f"  Cross-field validation is incomplete because {' and '.join(reasons)}.")
        else:
            status = ValidationStatus.PASSED
            evidence.append("  PASS")

        mismatch_count = sum(1 for s in all_sections if s["status"] == "MISMATCH")
        not_evaluated_count = sum(1 for s in all_sections if s["status"] == "NOT_EVALUATED")

        failure_reason = ""
        if has_mismatch:
            reasons = [s.get("reason", "Contradiction detected") for s in all_sections if s["status"] == "MISMATCH"]
            failure_reason = "; ".join(reasons)
        elif has_not_evaluated:
            reasons = [s["reason"] for s in all_sections if s["status"] == "NOT_EVALUATED"]
            failure_reason = f"Cross-field validation is incomplete because {' and '.join(reasons)}."

        missing_information = []
        if candidate is None:
            missing_information.append(ats_error or "ATS candidate data not available for cross-checking")
        if linkedin is None:
            missing_information.append(linkedin_error or "LinkedIn data not available for cross-checking")
        if company is None:
            missing_information.append(company_error or "Company data not available for cross-checking")

        confidence = 100.0
        if mismatch_count > 0:
            confidence -= min(mismatch_count * 15, 50)
        if not_evaluated_count > 0:
            confidence -= min(not_evaluated_count * 10, 30)
        confidence = max(confidence, 0.0)

        checks_performed = [
            "Resume vs ATS",
            "Resume vs LinkedIn",
            "Resume vs Company",
            "Resume vs Timeline",
            "Resume vs Contact",
        ]

        return ValidationEvidence(
            status=status,
            evidence=evidence,
            details={
                "total_comparisons": len(comparisons),
                "mismatches": mismatch_count,
                "not_evaluated": not_evaluated_count,
                "comparisons": comparisons,
                "checks_performed": checks_performed,
                "warnings": warnings,
                "issues": issues,
                "failure_reason": failure_reason,
                "confidence": confidence,
                "missing_information": missing_information,
            },
        )

    def _build_ats_section(
        self, resume: ResumeData, candidate: AtsCandidate | None, ats_error: str | None
    ) -> dict:
        section: dict = {"header": "Resume vs ATS", "status": "", "lines": [], "comparisons": [], "reason": ""}

        if candidate is None:
            section["status"] = "NOT_EVALUATED"
            section["reason"] = ats_error or "ATS data unavailable"
            return section

        sub_comparisons = []
        sub_comparisons.extend(self._check_name(resume, candidate))
        sub_comparisons.extend(self._check_email(resume, candidate))
        sub_comparisons.extend(self._check_phone(resume, candidate))

        skills_comp = self._check_skills(resume, candidate)
        if skills_comp:
            sub_comparisons.append(skills_comp)

        has_mismatch = False
        for comp in sub_comparisons:
            source_field = comp.get("source_field", "")
            compare_to = comp.get("compare_to", "")
            result = comp.get("result", "")
            source_value = comp.get("source_value", "")
            target_value = comp.get("target_value", "")

            section["comparisons"].append(comp)

            if result == "MATCH":
                section["lines"].append(f"{source_field} matches {compare_to}.")
            elif result == "MISMATCH":
                has_mismatch = True
                section["lines"].append(f"{source_field} differs from {compare_to}: '{source_value}' vs '{target_value}'")
            elif result == "SKILLS_COMPARISON":
                matched = comp.get("matched_skills", [])
                missing = comp.get("missing_skills", [])
                additional = comp.get("additional_skills", [])
                match_pct = comp.get("match_percentage", 0)
                total = comp.get("total_skills", 0)
                section["lines"].append(f"Skills: {match_pct:.0f}% match ({len(matched)}/{total} skills)")
                if missing:
                    section["lines"].append(f"  Missing from ATS: {', '.join(missing)}")
                if additional:
                    section["lines"].append(f"  In ATS only: {', '.join(additional)}")

        if has_mismatch:
            section["status"] = "MISMATCH"
            section["reason"] = "Discrepancies found between Resume and ATS data"
        else:
            section["status"] = "PASS"

        return section

    def _build_linkedin_section(
        self, resume: ResumeData, linkedin: LinkedInData | None, linkedin_error: str | None
    ) -> dict:
        section: dict = {"header": "Resume vs LinkedIn", "status": "", "lines": [], "comparisons": [], "reason": ""}

        if linkedin is None:
            section["status"] = "NOT_EVALUATED"
            section["reason"] = linkedin_error or "LinkedIn profile unavailable"
            return section

        comps = self._check_linkedin_employer(resume, linkedin)
        section["comparisons"].extend(comps)

        for comp in comps:
            result = comp.get("result", "")
            source_value = comp.get("source_value", "")
            target_value = comp.get("target_value", "")
            compare_to = comp.get("compare_to", "")

            if result == "MATCH":
                section["lines"].append(f"Resume Employer '{source_value}' matches {compare_to}.")
                section["status"] = "PASS"
            elif result == "MISMATCH":
                section["status"] = "MISMATCH"
                section["reason"] = f"Resume Employer differs from LinkedIn: '{source_value}' vs '{target_value}'"
                section["lines"].append(f"Resume Employer differs from LinkedIn: '{source_value}' vs '{target_value}'")

        if not section["status"]:
            section["status"] = "PASS"

        return section

    def _build_company_section(
        self, resume: ResumeData, company: CompanyData | None, company_error: str | None
    ) -> dict:
        section: dict = {"header": "Resume vs Company", "status": "", "lines": [], "comparisons": [], "reason": ""}

        if company is None:
            section["status"] = "NOT_EVALUATED"
            section["reason"] = company_error or "Company data unavailable"
            return section

        comps = self._check_company_employer(resume, company)
        section["comparisons"].extend(comps)

        for comp in comps:
            result = comp.get("result", "")
            source_value = comp.get("source_value", "")
            target_value = comp.get("target_value", "")

            if result == "MATCH":
                section["status"] = "PASS"
                if company.website:
                    section["lines"].append(f"Employer '{source_value}'")
                    section["lines"].append(f"Verified Website '{company.website}'")
            elif result == "MISMATCH":
                section["status"] = "MISMATCH"
                section["reason"] = f"Resume Employer '{source_value}' does not match verified company '{target_value}'"
                section["lines"].append(f"Employer '{source_value}'")
                section["lines"].append(f"Verified '{target_value}'")

        if not section["status"]:
            section["status"] = "PASS"

        return section

    def _build_timeline_section(self, resume: ResumeData) -> dict:
        section: dict = {"header": "Resume vs Timeline", "status": "", "lines": [], "comparisons": [], "reason": ""}

        comps = self._check_graduation_vs_employment(resume)
        section["comparisons"].extend(comps)

        has_issue = False
        for comp in comps:
            if comp.get("valid", True):
                section["lines"].append(f"Graduation: {comp['grad_year']}")
                section["lines"].append(f"Employment: {comp['start_year']}")
                section["lines"].append(f"Timeline PASS")
            else:
                has_issue = True
                section["lines"].append(f"Employment start ({comp['start_year']}) precedes graduation ({comp['grad_year']})")

        if has_issue:
            section["status"] = "MISMATCH"
            section["reason"] = "Employment started before graduation"
        else:
            section["status"] = "PASS"

        return section

    def _build_contact_section(self, resume: ResumeData) -> dict:
        section: dict = {"header": "Resume vs Contact", "status": "", "lines": [], "comparisons": [], "reason": ""}

        issues = []
        if not resume.email:
            issues.append("No email address in resume")
        if not resume.phone:
            issues.append("No phone number in resume")
        if not resume.name:
            issues.append("No name in resume")

        if issues:
            section["status"] = "NOT_EVALUATED"
            section["reason"] = "; ".join(issues)
        else:
            section["status"] = "PASS"
            section["lines"].append(f"Name: {resume.name}")
            section["lines"].append(f"Email: {resume.email}")
            section["lines"].append(f"Phone: {resume.phone}")

        return section

    def _check_name(self, resume: ResumeData, candidate: AtsCandidate) -> list[dict]:
        results = []
        if candidate.first_name and resume.name:
            cand_full = f"{candidate.first_name} {candidate.last_name or ''}".strip().lower()
            res_name = resume.name.lower().strip()
            match = cand_full and res_name == cand_full
            if not match:
                match = candidate.first_name.lower() in res_name
            results.append({
                "source_field": "Resume Name",
                "source_value": resume.name,
                "compare_to": "ATS Name",
                "target_value": cand_full,
                "result": "MATCH" if match else "MISMATCH",
            })
        return results

    def _check_email(self, resume: ResumeData, candidate: AtsCandidate) -> list[dict]:
        results = []
        if candidate.email and resume.email:
            match = candidate.email.lower() == resume.email.lower()
            results.append({
                "source_field": "Resume Email",
                "source_value": resume.email,
                "compare_to": "ATS Email",
                "target_value": candidate.email,
                "result": "MATCH" if match else "MISMATCH",
            })
        return results

    def _check_phone(self, resume: ResumeData, candidate: AtsCandidate) -> list[dict]:
        results = []
        if candidate.phone and resume.phone:
            cand = re.sub(r"[\s\-\+\(\)]", "", candidate.phone)
            res = re.sub(r"[\s\-\+\(\)]", "", resume.phone)
            match = cand and res and cand == res
            results.append({
                "source_field": "Resume Phone",
                "source_value": resume.phone,
                "compare_to": "ATS Phone",
                "target_value": candidate.phone,
                "result": "MATCH" if match else "MISMATCH",
            })
        return results

    def _check_company_employer(self, resume: ResumeData, company: CompanyData) -> list[dict]:
        results = []
        if company.is_verified and resume.experience:
            first_employer = resume.experience[0].company
            if first_employer and company.company_name:
                match = first_employer.lower().strip() == company.company_name.lower().strip()
                results.append({
                    "source_field": "Resume Employer",
                    "source_value": first_employer,
                    "compare_to": "Verified Company",
                    "target_value": company.company_name,
                    "result": "MATCH" if match else "MISMATCH",
                })
        return results

    def _check_linkedin_employer(self, resume: ResumeData, linkedin: LinkedInData) -> list[dict]:
        results = []
        if linkedin.employer_match is not None and resume.experience:
            first_employer = resume.experience[0].company
            if first_employer:
                match = linkedin.employer_match
                results.append({
                    "source_field": "Resume Employer",
                    "source_value": first_employer,
                    "compare_to": "LinkedIn Employer",
                    "target_value": linkedin.experience[0].get("company", "unknown") if linkedin.experience else "unknown",
                    "result": "MATCH" if match else "MISMATCH",
                })
        return results

    def _check_skills(self, resume: ResumeData, candidate: AtsCandidate | None) -> dict | None:
        if not candidate or not candidate.skills or not resume.skills:
            return None
        ats_skills = set(s.lower().strip() for s in candidate.skills if s)
        resume_skills = set(s.lower().strip() for s in resume.skills if s)
        if not ats_skills:
            return None

        matched = sorted(resume_skills & ats_skills)
        missing = sorted(resume_skills - ats_skills)
        additional = sorted(ats_skills - resume_skills)
        match_pct = (len(matched) / max(len(ats_skills | resume_skills), 1)) * 100

        return {
            "source_field": "Resume Skills",
            "compare_to": "ATS Skills",
            "result": "SKILLS_COMPARISON",
            "matched_skills": matched,
            "missing_skills": missing,
            "additional_skills": additional,
            "match_percentage": match_pct,
            "total_skills": max(len(ats_skills | resume_skills), 1),
        }

    def _check_graduation_vs_employment(self, resume: ResumeData) -> list[dict]:
        results = []
        for edu in resume.education or []:
            if not edu.end_date:
                continue
            try:
                grad_year = int(edu.end_date[:4])
                for exp in resume.experience or []:
                    if not exp.start_date:
                        continue
                    try:
                        start_year = int(exp.start_date[:4])
                        if "intern" in (exp.title or "").lower():
                            continue
                        valid = start_year >= grad_year - 1
                        results.append({
                            "source_field": "Resume Graduation Date",
                            "source_value": edu.end_date[:4],
                            "compare_to": "Employment Start Date",
                            "target_value": exp.start_date[:4],
                            "result": "TIMELINE",
                            "valid": valid,
                            "grad_year": grad_year,
                            "start_year": start_year,
                            "company": exp.company or "unknown",
                            "institution": edu.institution or "unknown",
                        })
                    except (ValueError, TypeError):
                        pass
            except (ValueError, TypeError):
                pass
        return results
