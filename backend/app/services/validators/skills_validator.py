import logging

from app.domain.models import ResumeData, ValidationEvidence, ValidationStatus

logger = logging.getLogger(__name__)


class SkillsValidator:
    async def validate(self, resume: ResumeData) -> ValidationEvidence:
        skills = resume.skills or []
        evidence = []

        if not skills:
            return ValidationEvidence(
                status=ValidationStatus.SKIPPED,
                evidence=["No skills listed"],
                details={"skill_count": 0},
            )

        project_techs = set()
        for proj in resume.projects or []:
            project_techs.update(t.strip() for t in proj.technologies if t)

        skills_lower = set(s.lower().strip() for s in skills)
        project_techs_lower = set(t.lower().strip() for t in project_techs)

        evidence.append("Resume Skills")
        for s in skills:
            evidence.append(f"  • {s}")
        evidence.append("")

        if project_techs:
            evidence.append("Projects")
            for t in project_techs:
                evidence.append(f"  • {t}")
            evidence.append("")

            matched_techs = sorted(project_techs_lower & skills_lower)
            missing_techs = sorted(project_techs_lower - skills_lower)

            if matched_techs:
                evidence.append("Matched")
                for t in matched_techs:
                    evidence.append(f"  ✓ {t}")

            if missing_techs:
                evidence.append("Missing from Resume")
                for t in missing_techs[:10]:
                    evidence.append(f"  ✗ {t}")
                if len(missing_techs) > 10:
                    evidence.append(f"  ... and {len(missing_techs) - 10} more")

            if not missing_techs:
                evidence.append("All project technologies are listed in skills.")
        evidence.append("")

        warnings = []
        if len(skills) > 30:
            warnings.append(f"Large number of skills ({len(skills)}) — verify relevance")

        missing_techs_list = []
        if project_techs:
            missing_techs_list = [t for t in project_techs_lower if t not in skills_lower]
            if missing_techs_list:
                warnings.append(f"{len(missing_techs_list)} project technolog{'y' if len(missing_techs_list) == 1 else 'ies'} not listed in skills")

        skill_density_warning = False
        if resume.total_years_experience and resume.total_years_experience > 0:
            ratio = round(len(skills) / resume.total_years_experience, 2)
            if ratio > 5:
                warnings.append(f"High skill density: {len(skills)} skills / {resume.total_years_experience} years ({ratio:.1f} skills/year)")
                skill_density_warning = True

        status = ValidationStatus.PASSED if not warnings else ValidationStatus.WARNING

        if status == ValidationStatus.PASSED:
            if project_techs:
                evidence.append("Skills validation passed. All project technologies are represented in the skills section.")
            else:
                evidence.append("Skills validation passed.")

        checks_performed = ["Skill count check", "Project-technology alignment", "Skill density analysis"]
        issues = []
        failure_reason = ""

        missing_information = []
        if project_techs:
            if missing_techs_list:
                missing_information.append(f"Technologies used in projects but not listed in skills: {', '.join(missing_techs_list[:5])}")

        confidence = 100.0
        if len(skills) > 30:
            confidence -= 10
        if missing_techs_list:
            confidence -= min(len(missing_techs_list) * 10, 30)
        if skill_density_warning:
            confidence -= min((ratio - 5) * 5, 20)
        confidence = max(confidence, 0.0)

        return ValidationEvidence(
            status=status,
            evidence=evidence,
            details={
                "skill_count": len(skills),
                "skill_names": skills[:50],
                "project_technologies": list(project_techs),
                "matched_technologies": list(project_techs_lower & skills_lower) if project_techs else [],
                "missing_technologies": missing_techs_list,
                "checks_performed": checks_performed,
                "warnings": warnings,
                "issues": issues,
                "failure_reason": failure_reason,
                "confidence": confidence,
                "missing_information": missing_information,
            },
        )
