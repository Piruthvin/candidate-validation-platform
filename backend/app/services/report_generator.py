import logging
from datetime import datetime, timezone
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from app.core.config import Settings
from app.core.exceptions import AzureStorageException
from app.domain.models import CandidateInfo, ReportResult
from app.infrastructure.azure_blob import AzureBlobService
from app.infrastructure.sas_generator import SASGenerator

logger = logging.getLogger(__name__)

TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "templates"


class ReportGenerator:
    def __init__(
        self,
        azure_blob_service: AzureBlobService,
        sas_generator: SASGenerator,
        settings: Settings,
    ):
        self.azure_blob_service = azure_blob_service
        self.sas_generator = sas_generator
        self.settings = settings
        self.env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)))

    async def generate(
        self,
        candidate_id: str,
        candidate_info: object,
        validation_result: dict,
        llm_analysis: object,
    ) -> ReportResult:
        candidate_name = candidate_info.name if isinstance(candidate_info, CandidateInfo) else getattr(candidate_info, "name", "Unknown")
        candidate_info_dict = candidate_info.model_dump() if isinstance(candidate_info, CandidateInfo) else (candidate_info if isinstance(candidate_info, dict) else {})
        llm_analysis_dict = llm_analysis.model_dump() if not isinstance(llm_analysis, dict) else llm_analysis

        self._log_mappings(candidate_id, candidate_info_dict, validation_result, llm_analysis_dict)

        template = self.env.get_template("validation_report.html")
        now = datetime.now(timezone.utc)

        logger.info("Rendering report HTML for candidate %s", candidate_id)
        html = template.render(
            candidate_id=candidate_id,
            candidate_name=candidate_name,
            generated_at=now.isoformat(),
            candidate_info=candidate_info_dict,
            validation_result=validation_result,
            llm_analysis=llm_analysis_dict,
        )
        logger.info("Report HTML rendered: %d bytes", len(html.encode("utf-8")))

        blob_id = f"report-{candidate_id}-{now.strftime('%Y%m%d%H%M%S')}.html"
        logger.info("Blob name: %s", blob_id)

        logger.info("Uploading report to Azure Blob Storage...")
        try:
            blob_url = await self.azure_blob_service.upload_blob(
                blob_path=blob_id,
                data=html.encode("utf-8"),
                content_type="text/html",
                metadata={"candidate_id": candidate_id, "generated_at": now.isoformat()},
            )
            logger.info("Upload completed. Azure blob URL: %s", blob_url)
        except AzureStorageException as e:
            logger.error("Upload FAILED for blob %s: %s", blob_id, e)
            raise
        except Exception as e:
            logger.error("Unexpected upload error for blob %s: %s", blob_id, e)
            raise AzureStorageException("Unexpected upload error", detail=str(e))

        logger.info("Generating SAS URL for blob: %s", blob_id)
        sas_url = self.sas_generator.generate_sas_url(blob_path=blob_id)
        logger.info("SAS URL generated successfully")

        logger.info("Returning success for candidate %s, blob %s", candidate_id, blob_id)
        return ReportResult(
            blob_id=blob_id,
            report_url=sas_url,
            created_time=now.isoformat(),
            candidate_id=candidate_id,
        )

    def _log_mappings(self, candidate_id: str, candidate_info: dict, validation_result: dict, llm_analysis: dict) -> None:
        contact = validation_result.get("contact_validation", {})
        phone_obj = (contact.get("details") or {}).get("phone") or {}
        email_obj = (contact.get("details") or {}).get("email") or {}
        company = validation_result.get("company_verification", {})
        company_details = company.get("details") or {}

        logger.info("=== Report Generator Mappings ===")
        logger.info("Candidate ID: %s", candidate_id)
        logger.info("Candidate Info: name=%s, email=%s, phone=%s, position=%s",
                     candidate_info.get("name", "N/A"),
                     candidate_info.get("email", "N/A"),
                     candidate_info.get("phone", "N/A"),
                     candidate_info.get("position", "N/A"))

        logger.info("Contact Validation status=%s", contact.get("status", "N/A"))
        logger.info("Phone Object: country_code=%s, national_number=%s, country=%s, region=%s, number_type=%s, international_format=%s, e164=%s, format_valid=%s",
                     phone_obj.get("country_code", "N/A"),
                     phone_obj.get("national_number", "N/A"),
                     phone_obj.get("country", "N/A"),
                     phone_obj.get("region", "N/A"),
                     phone_obj.get("number_type", "N/A"),
                     phone_obj.get("international_format", "N/A"),
                     phone_obj.get("e164", "N/A"),
                     phone_obj.get("format_valid", "N/A"))
        logger.info("Email Object: email=%s, domain=%s, format_valid=%s, is_disposable=%s, is_reserved=%s, is_corporate=%s",
                     email_obj.get("email", "N/A"),
                     email_obj.get("domain", "N/A"),
                     email_obj.get("format_valid", "N/A"),
                     email_obj.get("is_disposable", "N/A"),
                     email_obj.get("is_reserved", "N/A"),
                     email_obj.get("is_corporate", "N/A"))

        logger.info("Company Verification: company=%s, website=%s, is_verified=%s",
                     company_details.get("company_name", company.get("company_name", "N/A")),
                     company_details.get("website", company.get("website", "N/A")),
                     company.get("is_verified", company.get("status") == "PASSED"))

        logger.info("LLM Scores: overall=%s, validation=%s, confidence=%s, fraud=%s, company=%s, linkedin=%s, risk_level=%s, recommendation=%s",
                     llm_analysis.get("overall_score", "N/A"),
                     llm_analysis.get("validation_score", "N/A"),
                     llm_analysis.get("confidence_score", "N/A"),
                     llm_analysis.get("fraud_score", "N/A"),
                     llm_analysis.get("company_score", "N/A"),
                     llm_analysis.get("linkedin_score", "N/A"),
                     llm_analysis.get("risk_level", "N/A"),
                     llm_analysis.get("recommendation", "N/A"))

        val_summary = llm_analysis.get("validation_summary", {})
        logger.info("Validation Summary: passed=%s, failed=%s, warning=%s, skipped=%s",
                     val_summary.get("passed", "N/A"),
                     val_summary.get("failed", "N/A"),
                     val_summary.get("warning", "N/A"),
                     val_summary.get("skipped", "N/A"))
        logger.info("=== End Report Generator Mappings ===")