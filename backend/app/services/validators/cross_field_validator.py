from difflib import SequenceMatcher
import logging
import re
from typing import Any

from app.domain.models import AtsCandidate, CompanyData, LinkedInData, ResumeData, ValidationEvidence, ValidationStatus

logger = logging.getLogger(__name__)


def normalize_text(t: str) -> str:
    """Normalize text for cross-field comparison."""
    if not t or not isinstance(t, str):
        return ""
    return t.lower().replace("-", " ").strip()


def titles_match(t1: str, t2: str) -> bool:
    """Check if job titles match using substring or similarity ratio > 0.8."""
    n1 = normalize_text(t1)
    n2 = normalize_text(t2)
    if not n1 or not n2:
        return False
    if n1 in n2 or n2 in n1:
        return True
    return SequenceMatcher(None, n1, n2).ratio() > 0.8


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
                evidence.append("  Status")
                evidence.append("  NOT EVALUATED")
                evidence.append("  Reason")
                evidence.append(f"  {section['reason']}")
            elif section["status"] == "PASS":
                evidence.append("  PASS")
            elif section["status"] == "MISMATCH":
                has_mismatch = True
                evidence.append("  MISMATCH")

            for line in section.get("lines", []):
                evidence.append(f"  {line}")

            if section.get("reason") and section["status"] != "NOT_EVALUATED":
                overall_reasons.append(section["reason"])

            comparisons.extend(section.get("comparisons", []))

        evidence.append("")
        evidence.append("Overall")

        # Major vs Minor Mismatches
        major_mismatches = 0
        for comp in comparisons:
            if comp.get("result") == "MISMATCH":
                field = comp.get("source_field", "")
                if "Name" in field or "Email" in field or "Phone" in field:
                    major_mismatches += 2
                else:
                    major_mismatches += 1

        # Section 4: Only fail if major mismatch count >= 4
        if major_mismatches >= 4:
            status = ValidationStatus.FAILED
            evidence.append("  FAIL")
            reasons = [s.get("reason", "Major contradiction detected") for s in all_sections if s["status"] == "MISMATCH"]
            evidence.append("  Reason")
            evidence.append(f"  {'; '.join(reasons)}")
        elif has_mismatch or has_not_evaluated:
            status = ValidationStatus.WARNING
            evidence.append("  WARNING")
            reasons = [s["reason"] for s in all_sections if s.get("reason")]
            evidence.append("  Reason")
            evidence.append(f"  Cross-field validation completed with warnings: {'; '.join(reasons) if reasons else 'Minor discrepancies'}.")
        else:
            status = ValidationStatus.PASSED
            evidence.append("  PASS")

        mismatch_count = sum(1 for s in all_sections if s["status"] == "MISMATCH")
        not_evaluated_count = sum(1 for s in all_sections if s["status"] == "NOT_EVALUATED")

        failure_reason = ""
        if status == ValidationStatus.FAILED:
            reasons = [s.get("reason", "Major contradiction detected") for s in all_sections if s["status"] == "MISMATCH"]
            failure_reason = "; ".join(reasons)
        elif status == ValidationStatus.WARNING:
            failure_reason = "Cross-field validation completed with warnings"

        missing_information = []
        if candidate is None:
            missing_information.append(ats_error or "ATS candidate data not available for cross-checking")

        confidence = 100.0
        if mismatch_count > 0:
            confidence -= min(mismatch_count * 10, 40)
        if not_evaluated_count > 0:
            confidence -= min(not_evaluated_count * 10, 30)
        confidence = max(confidence, 0.0)

        checks_performed = [
            "Resume vs ATS",
        ]

        return ValidationEvidence(
            status=status,
            evidence=evidence,
            details={
                "total_comparisons": len(comparisons),
                "mismatches": mismatch_count,
                "major_mismatches": major_mismatches,
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

        sub_comparisons.extend(self._check_employers(resume, candidate))
        sub_comparisons.extend(self._check_experience_details(resume, candidate))
        sub_comparisons.extend(self._check_experience_years(resume, candidate))
        sub_comparisons.extend(self._check_projects(resume, candidate))

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

    def _check_employers(self, resume: ResumeData, candidate: AtsCandidate) -> list[dict]:
        results = []
        if not candidate.current_employer:
            return results

        ats_emp = candidate.current_employer.strip()
        resume_employers = [
            (exp.company or "").strip()
            for exp in (resume.experience or [])
            if (exp.company or "").strip()
        ]

        if not resume_employers:
            return results

        # Check if ATS current employer is present anywhere in resume employers
        matched = any(
            ats_emp.lower() in re_emp.lower() or re_emp.lower() in ats_emp.lower()
            for re_emp in resume_employers
        )

        results.append({
            "source_field": "Resume Employers",
            "source_value": ", ".join(resume_employers),
            "compare_to": "ATS Current Employer",
            "target_value": ats_emp,
            "result": "MATCH" if matched else "MISMATCH",
        })
        return results

    def _check_experience_details(self, resume: ResumeData, candidate: AtsCandidate) -> list[dict]:
        results = []
        if not candidate.experience_details or not resume.experience:
            return results

        for ats_exp in candidate.experience_details:
            if not ats_exp.company:
                continue

            ats_co = ats_exp.company.strip().lower()
            for res_exp in resume.experience:
                res_co = (res_exp.company or "").strip().lower()
                if not res_co:
                    continue

                if ats_co in res_co or res_co in ats_co:
                    # Compare Job Titles
                    if ats_exp.title and res_exp.title:
                        title_match = titles_match(res_exp.title, ats_exp.title)
                        results.append({
                            "source_field": f"Resume Title at {res_exp.company}",
                            "source_value": res_exp.title,
                            "compare_to": f"ATS Title at {ats_exp.company}",
                            "target_value": ats_exp.title,
                            "result": "MATCH" if title_match else "MISMATCH",
                        })

                    # Compare Start Dates (year comparison if both present)
                    if ats_exp.start_date and res_exp.start_date:
                        ats_yr = str(ats_exp.start_date)[:4]
                        res_yr = str(res_exp.start_date)[:4]
                        if ats_yr.isdigit() and res_yr.isdigit():
                            yr_match = abs(int(ats_yr) - int(res_yr)) <= 1
                            results.append({
                                "source_field": f"Resume Start Date at {res_exp.company}",
                                "source_value": str(res_exp.start_date),
                                "compare_to": f"ATS Start Date at {ats_exp.company}",
                                "target_value": str(ats_exp.start_date),
                                "result": "MATCH" if yr_match else "MISMATCH",
                            })
        return results

    def _check_experience_years(self, resume: ResumeData, candidate: AtsCandidate) -> list[dict]:
        results = []
        if candidate.total_experience_years is None:
            return results

        ats_years = candidate.total_experience_years
        resume_years = 0.0

        for exp in (resume.experience or []):
            if exp.start_date and exp.end_date:
                try:
                    s_yr = int(str(exp.start_date)[:4])
                    e_yr = int(str(exp.end_date)[:4])
                    if e_yr >= s_yr:
                        resume_years += (e_yr - s_yr)
                except (ValueError, TypeError):
                    pass

        if resume_years > 0:
            diff = abs(ats_years - resume_years)
            match = diff <= 2.5
            results.append({
                "source_field": "Resume Estimated Experience",
                "source_value": f"{resume_years:.1f} years",
                "compare_to": "ATS Total Experience",
                "target_value": f"{ats_years:.1f} years",
                "result": "MATCH" if match else "MISMATCH",
            })
        return results

    def _check_projects(self, resume: ResumeData, candidate: AtsCandidate) -> list[dict]:
        results = []
        if not candidate.experience_details or not resume.projects:
            return results

        all_summaries = " ".join((exp.summary or "").lower() for exp in candidate.experience_details)
        if not all_summaries.strip():
            return results

        for proj in resume.projects:
            p_name = (proj.name or "").strip()
            if len(p_name) >= 3 and p_name.lower() in all_summaries:
                results.append({
                    "source_field": f"Resume Project '{p_name}'",
                    "source_value": p_name,
                    "compare_to": "ATS Experience Summaries",
                    "target_value": "Referenced in ATS project summaries",
                    "result": "MATCH",
                })
        return results

