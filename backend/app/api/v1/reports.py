import logging

from fastapi import APIRouter, Depends, HTTPException

from app.core.dependencies import get_ats_service, get_report_generator, get_sas_generator
from app.core.exceptions import AzureStorageException
from app.domain.models import (
    BlobReportRequest,
    BlobReportResponse,
    LatestReportRequest,
    LatestReportResponse,
    ReportGenerationRequest,
    ReportGenerationResponse,
    ReportSearchRequest,
    ReportSearchResponse,
    ReportResult,
)
from app.infrastructure.retry import retry_async
from app.infrastructure.sas_generator import SASGenerator
from app.services.ats_service import AtsService
from app.services.report_generator import ReportGenerator

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/reports", tags=["Reports"])


@router.post(
    "/generate",
    response_model=ReportGenerationResponse,
    summary="Generate Recruiter Report",
    description="Generates an HTML report from validation data, uploads to Azure Blob, and returns a SAS URL.",
    operation_id="generate_report",
)
async def generate_report(
    request: ReportGenerationRequest,
    generator: ReportGenerator = Depends(get_report_generator),
) -> ReportGenerationResponse:
    try:
        result = await generator.generate(
            candidate_id=request.candidate_id,
            candidate_info=request.candidate_info,
            validation_result=request.validation_result,
            llm_analysis=request.llm_analysis,
        )
        return ReportGenerationResponse(**result.model_dump())
    except AzureStorageException as e:
        logger.error("Report generation failed — upload error: %s", e)
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "message": "Report upload failed. The blob was not stored in Azure Storage.",
            },
        )
    except Exception as e:
        logger.error("Report generation failed — unexpected error: %s", e)
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "message": f"Report generation failed: {e}",
            },
        )


@router.post(
    "/latest",
    response_model=LatestReportResponse,
    summary="Get Latest Report by Candidate",
    description="Returns the latest validation report URL for a candidate by looking up their ATS record.",
    operation_id="get_report_by_candidate",
)
async def get_report_by_candidate(
    request: LatestReportRequest,
    ats: AtsService = Depends(get_ats_service),
    sas_generator: SASGenerator = Depends(get_sas_generator),
) -> LatestReportResponse:
    candidate = await retry_async(
        lambda: ats.fetch_candidate(request.candidate_id),
        max_retries=2,
        name="fetch_for_report",
    )
    if isinstance(candidate, dict) and "error" in candidate:
        raise HTTPException(status_code=404, detail=f"Candidate {request.candidate_id} not found")
    if not candidate.report_url and not candidate.blob_id:
        raise HTTPException(status_code=404, detail=f"No report found for candidate {request.candidate_id}")
    report_url = candidate.report_url or ""
    blob_id = candidate.blob_id or ""
    if blob_id and not report_url:
        report_url = sas_generator.generate_sas_url(blob_path=blob_id)
    return LatestReportResponse(
        blob_id=blob_id,
        report_url=report_url,
        created_time=candidate.validation_timestamp or "",
        candidate_id=request.candidate_id,
    )


@router.post(
    "/blob",
    response_model=BlobReportResponse,
    summary="Fetch Report by Blob ID",
    description="Returns a report URL for a given Azure Blob ID.",
    operation_id="get_report_by_blob",
)
async def get_report_by_blob(
    request: BlobReportRequest,
    sas_generator: SASGenerator = Depends(get_sas_generator),
) -> BlobReportResponse:
    report_url = sas_generator.generate_sas_url(blob_path=request.blob_id)
    return BlobReportResponse(
        blob_id=request.blob_id,
        report_url=report_url,
        candidate_id="",
    )


@router.post(
    "/search",
    response_model=ReportSearchResponse,
    summary="Search Reports",
    description="Search validation reports by candidate_id, name, recommendation, or validation status.",
    operation_id="search_reports",
)
async def search_reports(
    request: ReportSearchRequest,
    ats: AtsService = Depends(get_ats_service),
) -> ReportSearchResponse:
    from app.domain.models import AtsSearchParams as AtsSearch

    listed = await retry_async(
        lambda: ats.list_candidates(AtsSearch(page=1, page_size=max(request.page_size, 200))),
        max_retries=2,
        name="search_reports_list",
    )
    if isinstance(listed, dict) and "error" in listed:
        raise HTTPException(status_code=502, detail=listed["error"])

    results: list[ReportResult] = []
    for item in listed.data:
        if request.candidate_id and request.candidate_id.lower() not in item.candidate_id.lower():
            continue
        if request.candidate_name and request.candidate_name.lower() not in f"{item.first_name or ''} {item.last_name or ''}".lower():
            continue
        if request.recommendation and (item.recommendation or "").lower() != request.recommendation.lower():
            continue
        if request.validation_status and (item.validation_status or "").lower() != request.validation_status.lower():
            continue
        if item.report_url or item.blob_id:
            results.append(ReportResult(
                blob_id=item.blob_id or "",
                report_url=item.report_url or "",
                candidate_id=item.candidate_id,
            ))

    start = (request.page - 1) * request.page_size
    end = start + request.page_size
    page = results[start:end]
    return ReportSearchResponse(total=len(results), data=page)
