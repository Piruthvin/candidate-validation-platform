from fastapi import APIRouter, Depends

from app.core.dependencies import get_validation_engine
from app.domain.models import ValidateRequest, ValidationResult
from app.services.validation_engine import ValidationEngine

router = APIRouter(prefix="/api/v1/validation", tags=["Validation"])


@router.post(
    "/validate",
    response_model=ValidationResult,
    response_model_exclude_none=True,
    summary="Validate Candidate Profile",
    description="Runs all validators plus enrichment (ATS, LinkedIn, Company) on a candidate resume.",
    operation_id="validate_candidate",
)
async def validate_candidate(
    request: ValidateRequest,
    engine: ValidationEngine = Depends(get_validation_engine),
) -> ValidationResult:
    resume_data = request.resume
    if request.linkedin_url and isinstance(resume_data, dict):
        if "linkedin_url" not in resume_data or not resume_data.get("linkedin_url"):
            resume_data["linkedin_url"] = request.linkedin_url
    result = await engine.validate(
        candidate_id=request.candidate_id,
        resume_data=resume_data,
    )
    return result
