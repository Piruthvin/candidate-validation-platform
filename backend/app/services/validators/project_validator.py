import logging

from app.domain.models import ResumeData, ValidationEvidence, ValidationStatus

logger = logging.getLogger(__name__)


class ProjectValidator:
    async def validate(self, resume: ResumeData) -> ValidationEvidence:
        projects = resume.projects or []
        evidence = []

        if not projects:
            return ValidationEvidence(
                status=ValidationStatus.SKIPPED,
                evidence=["No projects to validate"],
                details={"project_count": 0},
            )

        entry_details = []
        generic = 0
        no_tech = 0
        seen_names = {}

        for proj in projects:
            entry = {
                "name": (proj.name or "").strip() or "Unnamed",
                "technologies": list(proj.technologies) if proj.technologies else [],
                "issues": [],
            }

            name = (proj.name or "").strip()
            desc = (proj.description or "").strip()
            if len(name) < 3 and len(desc) < 10:
                generic += 1
                entry["issues"].append("Generic or empty project entry")
            if not proj.technologies:
                no_tech += 1
                entry["issues"].append("No technologies listed")
            if name:
                key = name.lower()
                seen_names[key] = seen_names.get(key, 0) + 1

            entry_details.append(entry)

        evidence.append("Project Entries")
        for ed in entry_details:
            evidence.append(f"  Project: {ed['name']}")
            if ed["technologies"]:
                evidence.append(f"  Technologies: {', '.join(ed['technologies'])}")
            else:
                evidence.append(f"  Technologies: None listed")
            if ed["issues"]:
                for issue in ed["issues"]:
                    evidence.append(f"  ⚠ {issue}")
            evidence.append("")

        dupes = [k for k, v in seen_names.items() if v > 1]
        if dupes:
            evidence.append(f"Duplicate project names: {', '.join(dupes)}")
            evidence.append("")

        status = ValidationStatus.PASSED
        if generic >= 2:
            status = ValidationStatus.FAILED
        elif generic > 0 or no_tech > 0 or dupes:
            status = ValidationStatus.WARNING

        if status == ValidationStatus.PASSED:
            evidence.append(f"Project validation passed. All {len(projects)} project(s) have proper descriptions and technologies.")

        checks_performed = ["Generic description detection", "Technology presence check", "Duplicate project detection"]
        warnings = []
        if no_tech > 0 and no_tech < len(projects):
            warnings.append(f"{no_tech} project(s) with no technologies listed")
        issues = []
        if generic > 0:
            issues.append(f"{generic} generic or empty project entr{'ies' if generic != 1 else 'y'} found")
        if dupes:
            issues.append(f"Duplicate project names: {', '.join(dupes)}")
        failure_reason = ""
        if status == ValidationStatus.FAILED:
            failure_reason = f"Project validation failed due to {generic} generic entr{'ies' if generic != 1 else 'y'}"

        missing_information = []
        if no_tech > 0:
            missing_information.append(f"{no_tech} project(s) missing technology information")

        confidence = 100.0
        if generic > 0:
            confidence -= min(generic * 20, 50)
        if no_tech > 0:
            confidence -= min(no_tech * 10, 30)
        if dupes:
            confidence -= 10
        confidence = max(confidence, 0.0)

        return ValidationEvidence(
            status=status,
            evidence=evidence,
            details={
                "project_count": len(projects),
                "entries": entry_details,
                "generic_entries": generic,
                "no_technologies": no_tech,
                "duplicate_names": dupes,
                "checks_performed": checks_performed,
                "warnings": warnings,
                "issues": issues,
                "failure_reason": failure_reason,
                "confidence": confidence,
                "missing_information": missing_information,
            },
        )
