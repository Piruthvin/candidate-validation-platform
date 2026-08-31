from fastapi import APIRouter, Depends, HTTPException

from app.core.dependencies import get_ats_service
from app.domain.models import (
    AtsCandidate,
    CandidateAttachmentsRequest,
    CandidateAttachmentsResponse,
    CandidateDetailRequest,
    CandidateDetailResponse,
    CandidateSearchRequest,
    CandidateSearchResponse,
)
from app.infrastructure.retry import retry_async
from app.services.ats_service import AtsService

router = APIRouter(prefix="/api/v1/ats", tags=["ATS"])


@router.post(
    "/candidate",
    response_model=CandidateDetailResponse,
    response_model_exclude_none=True,
    summary="Get Candidate Details",
    description="Returns full candidate details from ATS by record ID.",
    operation_id="get_ats_candidate",
)
async def get_candidate(
    request: CandidateDetailRequest,
    ats: AtsService = Depends(get_ats_service),
) -> CandidateDetailResponse:
    record_id = request.record_id
    if not record_id:
        raise HTTPException(status_code=400, detail="record_id is required")

    result = await retry_async(
        lambda: ats.fetch_candidate(record_id),
        max_retries=2,
        name="get_candidate",
    )
    if isinstance(result, dict) and "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return CandidateDetailResponse(**result.model_dump())


@router.post(
    "/attachments",
    response_model=CandidateAttachmentsResponse,
    response_model_exclude_none=True,
    summary="Get Candidate Attachments",
    description="Returns all attachments for a candidate from ATS by record ID.",
    operation_id="get_ats_candidate_attachments",
)
async def get_candidate_attachments(
    request: CandidateAttachmentsRequest,
    ats: AtsService = Depends(get_ats_service),
) -> CandidateAttachmentsResponse:
    record_id = request.record_id
    if not record_id:
        raise HTTPException(status_code=400, detail="record_id is required")

    attachments = await retry_async(
        lambda: ats.fetch_attachments(record_id),
        max_retries=2,
        name="get_attachments",
    )
    if isinstance(attachments, dict) and "error" in attachments:
        raise HTTPException(status_code=404, detail=attachments["error"])
    return CandidateAttachmentsResponse(total=len(attachments), data=attachments)


@router.post(
    "/search",
    response_model=CandidateSearchResponse,
    response_model_exclude_none=True,
    summary="Search Candidates",
    description="Search candidate by record_id. Returns matching ATS record.",
    operation_id="search_ats_candidates",
)
async def search_candidates(
    request: CandidateSearchRequest,
    ats: AtsService = Depends(get_ats_service),
) -> CandidateSearchResponse:
    record_id = request.record_id
    if not record_id:
        raise HTTPException(
            status_code=400,
            detail="Only record_id supported",
        )

    results: list[AtsCandidate] = []
    result = await retry_async(
        lambda: ats.fetch_candidate(record_id),
        max_retries=2,
        name="search_by_id",
    )
    if isinstance(result, dict) and "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    results.append(result)
    return CandidateSearchResponse(total=len(results), data=results)
