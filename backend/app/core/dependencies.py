from fastapi import Depends

from app.core.config import Settings
from app.infrastructure.azure_blob import AzureBlobService
from app.infrastructure.sas_generator import SASGenerator
from app.services.ats_service import AtsService
from app.services.company_verifier import CompanyVerifierService
from app.services.fraud_detector import FraudDetector
from app.services.linkedin_service import LinkedInService
from app.services.report_generator import ReportGenerator
from app.services.validation_engine import ValidationEngine
from app.services.validators.certification_validator import CertificationValidator
from app.services.validators.contact_validator import ContactValidator
from app.services.validators.cross_field_validator import CrossFieldValidator
from app.services.validators.education_validator import EducationValidator
from app.services.validators.employment_pattern_validator import EmploymentPatternValidator
from app.services.validators.experience_validator import ExperienceValidator
from app.services.validators.project_validator import ProjectValidator
from app.services.validators.resume_completeness_validator import ResumeCompletenessValidator
from app.services.validators.skills_validator import SkillsValidator
from app.services.validators.timeline_validator import TimelineValidator


def get_settings() -> Settings:
    return Settings()


def get_ats_service(settings: Settings = Depends(get_settings)) -> AtsService:
    return AtsService(settings)


def get_linkedin_service(settings: Settings = Depends(get_settings)) -> LinkedInService:
    return LinkedInService(settings)


def get_company_verifier(settings: Settings = Depends(get_settings)) -> CompanyVerifierService:
    return CompanyVerifierService(settings)


def get_fraud_detector() -> FraudDetector:
    return FraudDetector()


def get_azure_blob_service(settings: Settings = Depends(get_settings)) -> AzureBlobService:
    return AzureBlobService(settings)


def get_sas_generator(settings: Settings = Depends(get_settings)) -> SASGenerator:
    return SASGenerator(settings)


def get_contact_validator() -> ContactValidator:
    return ContactValidator()


def get_education_validator() -> EducationValidator:
    return EducationValidator()


def get_experience_validator() -> ExperienceValidator:
    return ExperienceValidator()


def get_timeline_validator() -> TimelineValidator:
    return TimelineValidator()


def get_skills_validator() -> SkillsValidator:
    return SkillsValidator()


def get_project_validator() -> ProjectValidator:
    return ProjectValidator()


def get_certification_validator() -> CertificationValidator:
    return CertificationValidator()


def get_employment_pattern_validator() -> EmploymentPatternValidator:
    return EmploymentPatternValidator()


def get_resume_completeness_validator() -> ResumeCompletenessValidator:
    return ResumeCompletenessValidator()


def get_cross_field_validator() -> CrossFieldValidator:
    return CrossFieldValidator()


def get_validation_engine(
    ats_service: AtsService = Depends(get_ats_service),
    linkedin_service: LinkedInService = Depends(get_linkedin_service),
    company_verifier: CompanyVerifierService = Depends(get_company_verifier),
    fraud_detector: FraudDetector = Depends(get_fraud_detector),
    azure_blob_service: AzureBlobService = Depends(get_azure_blob_service),
    contact_validator: ContactValidator = Depends(get_contact_validator),
    education_validator: EducationValidator = Depends(get_education_validator),
    experience_validator: ExperienceValidator = Depends(get_experience_validator),
    timeline_validator: TimelineValidator = Depends(get_timeline_validator),
    skills_validator: SkillsValidator = Depends(get_skills_validator),
    project_validator: ProjectValidator = Depends(get_project_validator),
    certification_validator: CertificationValidator = Depends(get_certification_validator),
    employment_pattern_validator: EmploymentPatternValidator = Depends(get_employment_pattern_validator),
    resume_completeness_validator: ResumeCompletenessValidator = Depends(get_resume_completeness_validator),
    cross_field_validator: CrossFieldValidator = Depends(get_cross_field_validator),
) -> ValidationEngine:
    return ValidationEngine(
        ats_service=ats_service,
        linkedin_service=linkedin_service,
        company_verifier=company_verifier,
        fraud_detector=fraud_detector,
        azure_blob_service=azure_blob_service,
        contact_validator=contact_validator,
        education_validator=education_validator,
        experience_validator=experience_validator,
        timeline_validator=timeline_validator,
        skills_validator=skills_validator,
        project_validator=project_validator,
        certification_validator=certification_validator,
        employment_pattern_validator=employment_pattern_validator,
        resume_completeness_validator=resume_completeness_validator,
        cross_field_validator=cross_field_validator,
    )


def get_report_generator(
    azure_blob_service: AzureBlobService = Depends(get_azure_blob_service),
    sas_generator: SASGenerator = Depends(get_sas_generator),
    settings: Settings = Depends(get_settings),
    ats_service: AtsService = Depends(get_ats_service),
) -> ReportGenerator:
    return ReportGenerator(
        azure_blob_service=azure_blob_service,
        sas_generator=sas_generator,
        settings=settings,
        ats_service=ats_service,
    )
