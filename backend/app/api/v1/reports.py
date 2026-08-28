import logging
import re
from fastapi import APIRouter, Depends, HTTPException

from app.core.dependencies import get_azure_blob_service, get_report_generator, get_sas_generator
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
from app.infrastructure.azure_blob import AzureBlobService
from app.infrastructure.sas_generator import SASGenerator
from app.services.report_generator import ReportGenerator

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/reports", tags=["Reports"])


@router.post(
    "/generate",
    response_model=ReportGenerationResponse,
    response_model_exclude_none=True,
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
    response_model_exclude_none=True,
    summary="Get Latest Report by Candidate",
    description="Returns the latest validation report URL for a candidate.",
    operation_id="get_report_by_candidate",
)
async def get_report_by_candidate(
    request: LatestReportRequest,
    azure_blob: AzureBlobService = Depends(get_azure_blob_service),
    sas_generator: SASGenerator = Depends(get_sas_generator),
) -> LatestReportResponse:
    blobs = await azure_blob.list_blobs(prefix=f"report-{request.candidate_id}-")
    if not blobs:
        raise HTTPException(status_code=404, detail=f"No report found for candidate {request.candidate_id}")

    latest_blob = sorted(blobs, reverse=True)[0]
    report_url = sas_generator.generate_sas_url(blob_path=latest_blob)
    return LatestReportResponse(
        blob_id=latest_blob,
        report_url=report_url,
        created_time="",
        candidate_id=request.candidate_id,
    )


@router.post(
    "/blob",
    response_model=BlobReportResponse,
    response_model_exclude_none=True,
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
    response_model_exclude_none=True,
    summary="Search Reports",
    description="Search validation reports by candidate_id.",
    operation_id="search_reports",
)
async def search_reports(
    request: ReportSearchRequest,
    azure_blob: AzureBlobService = Depends(get_azure_blob_service),
    sas_generator: SASGenerator = Depends(get_sas_generator),
) -> ReportSearchResponse:
    prefix = f"report-{request.candidate_id}-" if request.candidate_id else "report-"
    blobs = await azure_blob.list_blobs(prefix=prefix)

    results: list[ReportResult] = []
    for blob_id in sorted(blobs, reverse=True):
        m = re.match(r"report-([^-]+)-(\d+)\.html", blob_id)
        cid = m.group(1) if m else ""
        report_url = sas_generator.generate_sas_url(blob_path=blob_id)
        results.append(ReportResult(
            blob_id=blob_id,
            report_url=report_url,
            candidate_id=cid,
        ))

    start = (request.page - 1) * request.page_size
    end = start + request.page_size
    page = results[start:end]
    return ReportSearchResponse(total=len(results), data=page)
