import asyncio
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.config import Settings
from app.services.ats_service import AtsService
from app.domain.models import ResumeData, ResumeExperience, ResumeProject
from app.services.validators.cross_field_validator import CrossFieldValidator
from app.services.validators.experience_validator import ExperienceValidator
from app.services.validators.timeline_validator import TimelineValidator
from app.services.validators.project_validator import ProjectValidator


async def main():
    settings = Settings()
    print("Testing ATS Proxy with URL:", settings.ats_proxy_base_url)
    service = AtsService(settings)

    print("\n1. Testing check_connection...")
    conn = await service.check_connection()
    print("check_connection result:", conn)
    assert conn.get("connected") is True, f"Connection failed: {conn}"

    record_id = "591003000063456008"
    print(f"\n2. Testing fetch_candidate with record_id={record_id}...")
    candidate = await service.fetch_candidate(record_id)
    print("Candidate fetched successfully:")
    print(" - Candidate ID:", candidate.candidate_id)
    print(" - First Name:", candidate.first_name)
    print(" - Last Name:", candidate.last_name)
    print(" - Email:", candidate.email)
    print(" - Phone:", candidate.phone)
    print(" - Current Employer:", candidate.current_employer)
    print(" - Experience Years:", candidate.total_experience_years)
    print(" - Location:", candidate.location)
    print(" - Attachments count:", len(candidate.attachments))

    assert candidate.first_name == "Rajesh Kanna"
    assert candidate.last_name == "Chitravel"
    assert candidate.current_employer == "Tech Mahindra"
    assert candidate.phone == "+917373514143"
    assert len(candidate.attachments) > 0
    assert len(candidate.experience_details) >= 3
    print(" - Experience Details count:", len(candidate.experience_details))
    for exp in candidate.experience_details:
        print(f"    * {exp.company}: {exp.title} ({exp.start_date} to {exp.end_date})")

    print("\n3. Testing fetch_attachments...")
    attachments = await service.fetch_attachments(record_id)
    pdfs = [a for a in attachments if "pdf" in a.get("File_Name", "").lower()]
    print(f"Found {len(attachments)} total attachments, {len(pdfs)} PDFs.")
    for p in pdfs[:3]:
        print("   * PDF:", p.get("File_Name"), "(size:", p.get("Size"), ")")

    from app.domain.models import ResumeData, ResumeExperience, ResumeProject
    from app.services.validators.cross_field_validator import CrossFieldValidator
    from app.services.validators.experience_validator import ExperienceValidator
    from app.services.validators.timeline_validator import TimelineValidator
    from app.services.validators.project_validator import ProjectValidator

    sample_resume = ResumeData(
        name="Rajesh Kanna Chitravel",
        email="rajeshcvel@gmail.com",
        phone="+917373514143",
        skills=["Augmented Reality", "Unity Engine", "Python Programming"],
        experience=[
            ResumeExperience(
                company="Tech Mahindra",
                title="Technical Lead- XR",
                start_date="2022-01-01",
                end_date="2024-01-01",
            ),
            ResumeExperience(
                company="Concentrix Catalyst",
                title="Senior Software Engineer - Immersive",
                start_date="2020-01-01",
                end_date="2022-01-01",
            ),
        ],
        projects=[
            ResumeProject(
                name="AR Tech Application",
                technologies=["Unity", "Vuforia"],
            )
        ],
    )

    # Cross-field validator
    cf_res = await CrossFieldValidator().validate(sample_resume, candidate)
    print("CrossFieldValidator result status:", cf_res.status)
    for line in cf_res.evidence[:10]:
        print("   [CF]", line)
    assert cf_res.status is not None

    # Experience validator
    exp_res = await ExperienceValidator().validate(sample_resume, candidate)
    print("ExperienceValidator result status:", exp_res.status)
    assert exp_res.status.value == "PASSED"
    assert exp_res.details.get("ats_experience_count", 0) > 0

    # Timeline validator
    tl_res = await TimelineValidator().validate(sample_resume, candidate)
    print("TimelineValidator result status:", tl_res.status)
    assert tl_res.status.value in ("PASSED", "WARNING")

    # Project validator
    proj_res = await ProjectValidator().validate(sample_resume, candidate)
    print("ProjectValidator result status:", proj_res.status)
    assert proj_res.status.value == "PASSED"

    await service.close()
    print("\nAll direct tests PASSED successfully!")


if __name__ == "__main__":
    asyncio.run(main())
