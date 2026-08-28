import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.config import Settings
from app.domain.models import ResumeData, ResumeExperience, ResumeEducation, ResumeProject, ResumeCertification, LinkedInData, CompanyData
from app.services.validation_engine import ValidationEngine
from app.services.validators.contact_validator import ContactValidator
from app.services.validators.education_validator import EducationValidator
from app.services.validators.experience_validator import ExperienceValidator
from app.services.validators.timeline_validator import TimelineValidator
from app.services.validators.skills_validator import SkillsValidator
from app.services.validators.project_validator import ProjectValidator
from app.services.validators.certification_validator import CertificationValidator
from app.services.validators.employment_pattern_validator import EmploymentPatternValidator
from app.services.validators.resume_completeness_validator import ResumeCompletenessValidator
from app.services.validators.cross_field_validator import CrossFieldValidator
from app.services.validators.company_validator import CompanyValidator
from app.services.validators.linkedin_validator import LinkedInValidator
from app.services.linkedin_service import LinkedInService


async def main():
    print("--- Testing Validators Directly ---")
    settings = Settings()
    engine = ValidationEngine()

    # 1. Test Valid Contact Validator (should be PASSED)
    cv = ContactValidator()
    valid_resume = ResumeData(
        candidate_id="CAND-001",
        name="John Doe",
        email="johndoe@gmail.com",
        phone="+14155552671",
        skills=["Python", "SQL"],
        experience=[ResumeExperience(company="Acme Corp", title="Software Engineer", start_date="2020-01-01", end_date="2023-01-01")],
        education=[ResumeEducation(institution="Stanford University", degree="BS CS", start_date="2015-09-01", end_date="2019-06-01")],
    )
    contact_result = await cv.validate(valid_resume)
    print(f"ContactValidator status: {contact_result.status.value}")
    assert contact_result.status.value == "PASSED", f"Expected PASSED, got {contact_result.status.value}"

    # 2. Test Invalid Contact (disposable email)
    disp_resume = ResumeData(name="Jane", email="jane@tempmail.com", phone="+14155552671")
    disp_result = await cv.validate(disp_resume)
    print(f"Disposable Email status: {disp_result.status.value}")
    assert disp_result.status.value == "FAILED", f"Expected FAILED, got {disp_result.status.value}"

    # 3. Test LinkedIn Validator (200 -> PASSED, other -> FAILED, no warning)
    lv = LinkedInValidator()
    li_pass = LinkedInData(profile_url="https://linkedin.com/in/johndoe", status_code=200, profile_exists=True, valid=True)
    li_pass_result = await lv.validate(valid_resume, li_pass)
    print(f"LinkedIn 200 status: {li_pass_result.status.value}")
    assert li_pass_result.status.value == "PASSED", f"Expected PASSED, got {li_pass_result.status.value}"

    li_fail = LinkedInData(profile_url="https://linkedin.com/in/johndoe", status_code=404, profile_exists=False, valid=False)
    li_fail_result = await lv.validate(valid_resume, li_fail)
    print(f"LinkedIn 404 status: {li_fail_result.status.value}")
    assert li_fail_result.status.value == "FAILED", f"Expected FAILED, got {li_fail_result.status.value}"

    li_timeout = LinkedInData(profile_url="https://linkedin.com/in/johndoe", status_code=408, profile_exists=False, valid=False)
    li_timeout_result = await lv.validate(valid_resume, li_timeout)
    print(f"LinkedIn 408 (timeout) status: {li_timeout_result.status.value}")
    assert li_timeout_result.status.value == "FAILED", f"Expected FAILED, got {li_timeout_result.status.value}"

    # 4. Test Company Validator (non-empty company -> PASSED, missing -> FAILED)
    comp_v = CompanyValidator()
    comp_data = CompanyData(company_name="Google", is_verified=True, website="https://google.com")
    comp_pass = await comp_v.validate(valid_resume, comp_data)
    print(f"Company present status: {comp_pass.status.value}")
    assert comp_pass.status.value == "PASSED", f"Expected PASSED, got {comp_pass.status.value}"

    comp_missing_data = CompanyData(company_name="")
    empty_resume = ResumeData(candidate_id="CAND-002", name="No Company")
    comp_fail = await comp_v.validate(empty_resume, comp_missing_data)
    print(f"Company missing status: {comp_fail.status.value}")
    assert comp_fail.status.value == "FAILED", f"Expected FAILED, got {comp_fail.status.value}"

    # 5. Full Validation Engine run
    full_resume_data = {
        "candidate_id": "CAND-100",
        "name": "Alex Smith",
        "email": "alex.smith@gmail.com",
        "phone": "+14155552671",
        "company": "Tech Corp",
        "skills": ["Python", "FastAPI", "PostgreSQL"],
        "experience": [
            {
                "company": "Tech Corp",
                "title": "Senior Engineer",
                "start_date": "2021-01-01",
                "end_date": "2024-01-01",
                "description": "Building backend APIs",
            }
        ],
        "education": [
            {
                "institution": "MIT",
                "degree": "B.S. Computer Science",
                "start_date": "2016-09-01",
                "end_date": "2020-06-01",
            }
        ],
        "projects": [
            {
                "name": "Validation Platform",
                "technologies": ["Python", "FastAPI"],
                "description": "Automated candidate validation engine",
            }
        ],
    }

    full_result = await engine.validate("CAND-100", full_resume_data)
    print(f"Full Validation Engine Result:")
    print(f"  candidate_id: {full_result.candidate_id}")
    print(f"  candidate_name: {full_result.candidate_name}")
    print(f"  contact_validation: {full_result.contact_validation.status.value}")
    print(f"  education_validation: {full_result.education_validation.status.value}")
    print(f"  experience_validation: {full_result.experience_validation.status.value}")
    print(f"  skills_validation: {full_result.skills_validation.status.value}")
    print(f"  project_validation: {full_result.project_validation.status.value}")
    print(f"  company_verification: {full_result.company_verification.status.value if full_result.company_verification else 'None'}")
    print(f"  completed_steps: {full_result.completed_steps}")
    print(f"  warnings count: {len(full_result.warnings)}")
    print(f"  errors count: {len(full_result.errors)}")

    assert full_result.contact_validation.status.value == "PASSED"
    assert full_result.education_validation.status.value == "PASSED"
    assert full_result.experience_validation.status.value == "PASSED"
    assert full_result.company_verification.status.value == "PASSED"

    print("\nALL DIRECT VALIDATOR TESTS PASSED!")


if __name__ == "__main__":
    asyncio.run(main())
