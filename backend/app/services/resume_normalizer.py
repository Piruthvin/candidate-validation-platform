import logging
import re
from typing import Any

from app.domain.models import (
    ResumeCertification,
    ResumeData,
    ResumeEducation,
    ResumeExperience,
    ResumeProject,
)

logger = logging.getLogger(__name__)


class ResumeNormalizer:
    def normalize(self, raw_data: dict[str, Any]) -> ResumeData:
        name = self._extract_name(raw_data)
        email = self._extract_email(raw_data)
        phone = self._extract_phone(raw_data)
        summary = self._extract_summary(raw_data)
        location = self._extract_location(raw_data)
        linkedin_url = self._extract_linkedin(raw_data)
        skills = self._extract_skills(raw_data)
        total_years = self._extract_total_years(raw_data)
        sections = self._detect_sections(raw_data)

        return ResumeData(
            name=name,
            email=email,
            phone=phone,
            summary=summary,
            location=location,
            linkedin_url=linkedin_url,
            skills=skills,
            experience=self._extract_experience(raw_data),
            education=self._extract_education(raw_data),
            certifications=self._extract_certifications(raw_data),
            projects=self._extract_projects(raw_data),
            languages=self._extract_languages(raw_data),
            total_years_experience=total_years,
            raw_text=raw_data.get("raw_text", raw_data.get("text", "")),
            sections_present=sections,
        )

    def _extract_name(self, d: dict) -> str | None:
        return d.get("name") or d.get("full_name") or d.get("candidate_name") or d.get("fullName")

    def _extract_email(self, d: dict) -> str | None:
        val = d.get("email") or d.get("email_address") or d.get("e_mail")
        if val:
            return str(val).strip()
        text = d.get("raw_text", d.get("text", ""))
        match = re.search(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", text)
        return match.group(0) if match else None

    def _extract_phone(self, d: dict) -> str | None:
        val = d.get("phone") or d.get("phone_number") or d.get("mobile") or d.get("telephone")
        if val:
            return str(val).strip()
        text = d.get("raw_text", d.get("text", ""))
        match = re.search(r"\+?\d[\d\s\-\(\)]{7,}\d", text)
        return match.group(0).strip() if match else None

    def _extract_summary(self, d: dict) -> str | None:
        return d.get("summary") or d.get("profile_summary") or d.get("professional_summary") or d.get("objective")

    def _extract_location(self, d: dict) -> str | None:
        return d.get("location") or d.get("address") or d.get("city") or d.get("current_location")

    def _extract_linkedin(self, d: dict) -> str | None:
        val = d.get("linkedin_url") or d.get("linkedin") or d.get("linkedin_profile") or d.get("linkedIn")
        if val:
            return str(val).strip()
        text = d.get("raw_text", d.get("text", ""))
        match = re.search(r"https?://(?:www\.)?linkedin\.com/in/[a-zA-Z0-9_-]+/?", text)
        return match.group(0) if match else None

    def _extract_skills(self, d: dict) -> list[str]:
        skills = d.get("skills") or d.get("skill_set") or d.get("technologies") or []
        if isinstance(skills, str):
            skills = [s.strip() for s in skills.split(",") if s.strip()]
        return list(dict.fromkeys(s.strip() for s in skills if s and isinstance(s, str)))[:50]

    def _extract_experience(self, d: dict) -> list[ResumeExperience]:
        raw = d.get("experience") or d.get("work_experience") or d.get("employment") or d.get("work_history") or []
        if isinstance(raw, str):
            return []
        result = []
        seen = set()
        for item in raw if isinstance(raw, list) else []:
            if not isinstance(item, dict):
                continue
            company = (item.get("company") or item.get("employer") or item.get("organization") or "").strip()
            title = (item.get("title") or item.get("role") or item.get("position") or item.get("job_title") or "").strip()
            key = (company + title).lower()
            if key in seen:
                continue
            seen.add(key)
            result.append(ResumeExperience(
                company=company or None,
                title=title or None,
                start_date=(item.get("start_date") or item.get("startDate") or item.get("from") or "").strip() or None,
                end_date=(item.get("end_date") or item.get("endDate") or item.get("to") or "").strip() or None,
                description=(item.get("description") or item.get("summary") or item.get("details") or "").strip() or None,
            ))
        return result

    def _extract_education(self, d: dict) -> list[ResumeEducation]:
        raw = d.get("education") or d.get("educational_background") or d.get("academic") or []
        if isinstance(raw, str):
            return []
        result = []
        seen = set()
        for item in raw if isinstance(raw, list) else []:
            if not isinstance(item, dict):
                continue
            inst = (item.get("institution") or item.get("school") or item.get("university") or item.get("college") or "").strip()
            degree = (item.get("degree") or item.get("qualification") or item.get("certification") or "").strip()
            key = (inst + degree).lower()
            if key in seen:
                continue
            seen.add(key)
            result.append(ResumeEducation(
                institution=inst or None,
                degree=degree or None,
                field_of_study=(item.get("field_of_study") or item.get("field") or item.get("major") or "").strip() or None,
                start_date=(item.get("start_date") or item.get("startDate") or "").strip() or None,
                end_date=(item.get("end_date") or item.get("endDate") or item.get("graduation_date") or "").strip() or None,
            ))
        return result

    def _extract_certifications(self, d: dict) -> list[ResumeCertification]:
        raw = d.get("certifications") or d.get("certificates") or d.get("licenses") or d.get("credentials") or []
        if isinstance(raw, str):
            return []
        result = []
        for item in raw if isinstance(raw, list) else []:
            if not isinstance(item, dict):
                continue
            name = (item.get("name") or item.get("title") or item.get("certification_name") or "").strip()
            issuer = (item.get("issuer") or item.get("vendor") or item.get("organization") or item.get("issuing_organization") or "").strip()
            if name:
                result.append(ResumeCertification(
                    name=name or None,
                    issuer=issuer or None,
                    date=(item.get("date") or item.get("issue_date") or item.get("completion_date") or "").strip() or None,
                ))
        return result

    def _extract_projects(self, d: dict) -> list[ResumeProject]:
        raw = d.get("projects") or d.get("project_experience") or []
        if isinstance(raw, str):
            return []
        result = []
        for item in raw if isinstance(raw, list) else []:
            if not isinstance(item, dict):
                continue
            name = (item.get("name") or item.get("project_name") or item.get("title") or "").strip()
            desc = (item.get("description") or item.get("summary") or "").strip()
            techs = item.get("technologies") or item.get("tech_stack") or item.get("tools") or []
            if isinstance(techs, str):
                techs = [t.strip() for t in techs.split(",") if t.strip()]
            result.append(ResumeProject(
                name=name or None,
                description=desc or None,
                technologies=[str(t).strip() for t in techs if t and isinstance(t, str)][:20],
            ))
        return result

    def _extract_languages(self, d: dict) -> list[str]:
        langs = d.get("languages") or d.get("language_proficiency") or []
        if isinstance(langs, str):
            langs = [l.strip() for l in langs.split(",") if l.strip()]
        return [str(l).strip() for l in langs if l and isinstance(l, str)]

    def _extract_total_years(self, d: dict) -> float | None:
        val = d.get("total_years_experience") or d.get("years_of_experience") or d.get("experience_years")
        if val is not None:
            try:
                return float(val)
            except (ValueError, TypeError):
                pass
        return None

    def _detect_sections(self, d: dict) -> list[str]:
        sections = []
        checks = [
            ("skills", ["skills", "skill_set", "technologies"]),
            ("experience", ["experience", "work_experience", "employment", "work_history"]),
            ("education", ["education", "educational_background", "academic"]),
            ("projects", ["projects", "project_experience"]),
            ("certifications", ["certifications", "certificates", "licenses"]),
            ("languages", ["languages", "language_proficiency"]),
            ("summary", ["summary", "profile_summary", "professional_summary", "objective"]),
        ]
        for section_name, keys in checks:
            if any(k in d and d[k] for k in keys):
                sections.append(section_name)
        return sections
