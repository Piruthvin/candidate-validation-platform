import logging
from fastapi import APIRouter, Depends, HTTPException

from app.core.dependencies import get_report_generator, get_sas_generator
from app.core.exceptions import AzureStorageException
from app.domain.models import (
    BlobReportRequest,
    BlobReportResponse,
    ReportGenerationRequest,
    ReportGenerationResponse,
)
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
        target_id = request.record_id or request.candidate_id
        result = await generator.generate(
            candidate_id=target_id,
            candidate_info=request.candidate_info,
            validation_result=request.validation_result,
            llm_analysis=request.llm_analysis,
        )
        res_dto = ReportGenerationResponse(**result.model_dump())
        res_dto.record_id = target_id
        return res_dto
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
    try:
        report_url = sas_generator.generate_sas_url(blob_path=request.blob_id)
        return BlobReportResponse(
            blob_id=request.blob_id,
            report_url=report_url,
            candidate_id="",
        )
    except AzureStorageException as e:
        logger.error("SAS generation failed: %s", e)
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "message": f"SAS generation failed: {e}",
            },
        )
    except Exception as e:
        logger.error("SAS generation failed: %s", e)
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "message": f"SAS generation failed: {e}",
            },
        )
