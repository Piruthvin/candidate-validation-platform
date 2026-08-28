from fastapi import APIRouter, Depends, HTTPException

from app.core.dependencies import get_ats_service
from app.domain.models import (
    AtsCandidate,
    CandidateDetailRequest,
    CandidateDetailResponse,
    CandidateListRequest,
    CandidateListResponse,
    CandidateSearchRequest,
    CandidateSearchResponse,
)
from app.infrastructure.retry import retry_async
from app.services.ats_service import AtsService

router = APIRouter(prefix="/api/v1/ats", tags=["ATS"])


@router.post(
    "/candidates",
    response_model=CandidateListResponse,
    response_model_exclude_none=True,
    summary="List ATS Candidates",
    description="Returns paginated list of candidates from ATS with optional search.",
    operation_id="list_ats_candidates",
)
async def list_candidates(
    request: CandidateListRequest,
    ats: AtsService = Depends(get_ats_service),
) -> CandidateListResponse:
    from app.domain.models import AtsSearchParams

    params = AtsSearchParams(
        page=request.page,
        page_size=request.page_size,
        search=request.search,
        status=request.status,
        sort_by=request.sort_by,
        sort_order=request.sort_order,
    )
    result = await retry_async(
        lambda: ats.list_candidates(params),
        max_retries=2,
        name="list_candidates",
    )
    if isinstance(result, dict) and "error" in result:
        raise HTTPException(status_code=502, detail=result["error"])
    return CandidateListResponse(total=result.total, data=result.data)


@router.post(
    "/candidate",
    response_model=CandidateDetailResponse,
    response_model_exclude_none=True,
    summary="Get Candidate Details",
    description="Returns full candidate details from ATS by candidate ID.",
    operation_id="get_ats_candidate",
)
async def get_candidate(
    request: CandidateDetailRequest,
    ats: AtsService = Depends(get_ats_service),
) -> CandidateDetailResponse:
    result = await retry_async(
        lambda: ats.fetch_candidate(request.candidate_id),
        max_retries=2,
        name="get_candidate",
    )
    if isinstance(result, dict) and "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return CandidateDetailResponse(**result.model_dump())


@router.post(
    "/search",
    response_model=CandidateSearchResponse,
    response_model_exclude_none=True,
    summary="Search Candidates",
    description="Search candidates by candidate_id, name, email, phone, or company. Returns matching ATS records.",
    operation_id="search_ats_candidates",
)
async def search_candidates(
    request: CandidateSearchRequest,
    ats: AtsService = Depends(get_ats_service),
) -> CandidateSearchResponse:
    from app.domain.models import AtsSearchParams

    results: list[AtsCandidate] = []

    if request.candidate_id:
        result = await retry_async(
            lambda: ats.fetch_candidate(request.candidate_id),
            max_retries=2,
            name="search_by_id",
        )
        if not (isinstance(result, dict) and "error" in result):
            results.append(result)
        return CandidateSearchResponse(total=len(results), data=results)

    listed = await ats.list_candidates(
        AtsSearchParams(page=1, page_size=max(request.page_size, 100))
    )
    for item in listed.data:
        if request.name and request.name.lower() not in (f"{item.first_name or ''} {item.last_name or ''}").lower():
            continue
        if request.email and request.email.lower() not in (item.email or "").lower():
            continue
        if request.phone and request.phone not in (item.phone or ""):
            continue
        if request.company and request.company.lower() not in (item.current_employer or "").lower():
            continue
        full = await ats.fetch_candidate(item.candidate_id)
        if not (isinstance(full, dict) and "error" in full):
            results.append(full)

    start = (request.page - 1) * request.page_size
    end = start + request.page_size
    page = results[start:end]
    return CandidateSearchResponse(total=len(results), data=page)
