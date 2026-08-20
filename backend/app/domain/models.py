from enum import Enum
from pydantic import BaseModel, Field


class ValidationStatus(str, Enum):
    PASSED = "PASSED"
    FAILED = "FAILED"
    WARNING = "WARNING"
    SKIPPED = "SKIPPED"
    NOT_EVALUATED = "NOT_EVALUATED"


class ValidationEvidence(BaseModel):
    status: ValidationStatus = ValidationStatus.SKIPPED
    evidence: list[str] = Field(default_factory=list)
    details: dict | None = None


class ResumeExperience(BaseModel):
    company: str | None = None
    title: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    description: str | None = None


class ResumeEducation(BaseModel):
    institution: str | None = None
    degree: str | None = None
    field_of_study: str | None = None
    start_date: str | None = None
    end_date: str | None = None


class ResumeCertification(BaseModel):
    name: str | None = None
    issuer: str | None = None
    date: str | None = None


class ResumeProject(BaseModel):
    name: str | None = None
    description: str | None = None
    technologies: list[str] = Field(default_factory=list)


class ResumeData(BaseModel):
    candidate_id: str = ""
    name: str | None = Field(default=None, max_length=500)
    email: str | None = Field(default=None, max_length=320)
    phone: str | None = Field(default=None, max_length=50)
    summary: str | None = Field(default=None, max_length=5000)
    location: str | None = Field(default=None, max_length=500)
    linkedin_url: str | None = Field(default=None, max_length=500)
    skills: list[str] = Field(default_factory=list, max_length=500)
    experience: list[ResumeExperience] = Field(default_factory=list, max_length=100)
    education: list[ResumeEducation] = Field(default_factory=list, max_length=50)
    certifications: list[ResumeCertification] = Field(default_factory=list, max_length=50)
    projects: list[ResumeProject] = Field(default_factory=list, max_length=100)
    languages: list[str] = Field(default_factory=list, max_length=100)
    total_years_experience: float | None = None
    raw_text: str | None = Field(default=None, max_length=200_000)
    sections_present: list[str] = Field(default_factory=list, max_length=100)


class AtsCandidate(BaseModel):
    candidate_id: str = ""
    first_name: str | None = None
    last_name: str | None = None
    email: str | None = None
    phone: str | None = None
    skills: list[str] = Field(default_factory=list)
    total_experience_years: float | None = None
    current_employer: str | None = None
    location: str | None = None
    report_url: str | None = None
    blob_id: str | None = None
    validation_status: str | None = None
    recommendation: str | None = None
    validation_timestamp: str | None = None


class PossibleMatch(BaseModel):
    url: str
    reachable: bool
    has_ssl: bool = False
    has_dns: bool = False
    has_mx: bool = False
    confidence: float = 0.0


class CompanyData(BaseModel):
    company_name: str | None = None
    website: str | None = None
    domain: str | None = None
    is_verified: bool = False
    verification_method: str | None = None
    confidence_score: float | None = None
    website_reachable: bool | None = None
    has_ssl: bool | None = None
    has_dns: bool | None = None
    has_mx: bool | None = None
    trust_evidence: list[str] = Field(default_factory=list)
    verification_reason: str | None = None
    possible_matches: list[PossibleMatch] = Field(default_factory=list)


class LinkedInData(BaseModel):
    profile_url: str | None = None
    username: str | None = None
    profile_exists: bool = False
    profile_name: str | None = None
    profile_headline: str | None = None
    experience: list[dict] = Field(default_factory=list)
    education: list[dict] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)
    name_match: bool | None = None
    employer_match: bool | None = None
    location: str | None = None
    location_match: bool | None = None
    experience_match_count: int | None = None
    education_match_count: int | None = None
    skills_overlap_count: int | None = None


COUNTRY_CODES = {
    1: "US", 7: "RU", 20: "EG", 27: "ZA", 30: "GR", 31: "NL", 32: "BE", 33: "FR", 34: "ES",
    36: "HU", 39: "IT", 40: "RO", 41: "CH", 43: "AT", 44: "GB", 45: "DK", 46: "SE", 47: "NO",
    48: "PL", 49: "DE", 51: "PE", 52: "MX", 53: "CU", 54: "AR", 55: "BR", 56: "CL", 57: "CO",
    58: "VE", 60: "MY", 61: "AU", 62: "ID", 63: "PH", 64: "NZ", 65: "SG", 66: "TH", 81: "JP",
    82: "KR", 84: "VN", 86: "CN", 90: "TR", 91: "IN", 92: "PK", 93: "AF", 94: "LK", 95: "MM",
    98: "IR", 212: "MA", 213: "DZ", 216: "TN", 218: "LY", 220: "GM", 221: "SN", 222: "MR",
    223: "ML", 224: "GN", 225: "CI", 226: "BF", 227: "NE", 228: "TG", 229: "BJ", 230: "MU",
    231: "LR", 232: "SL", 233: "GH", 234: "NG", 235: "TD", 236: "CF", 237: "CM", 238: "CV",
    239: "ST", 240: "GQ", 241: "GA", 242: "CG", 243: "CD", 244: "AO", 245: "GW", 246: "IO",
    247: "AC", 248: "SC", 249: "SD", 250: "RW", 251: "ET", 252: "SO", 253: "DJ", 254: "KE",
    255: "TZ", 256: "UG", 257: "BI", 258: "MZ", 260: "ZM", 261: "MG", 262: "RE", 263: "ZW",
    264: "NA", 265: "MW", 266: "LS", 267: "BW", 268: "SZ", 269: "KM", 290: "SH", 291: "ER",
    297: "AW", 298: "FO", 299: "GL", 350: "GI", 351: "PT", 352: "LU", 353: "IE", 354: "IS",
    355: "AL", 356: "MT", 357: "CY", 358: "FI", 359: "BG", 370: "LT", 371: "LV", 372: "EE",
    373: "MD", 374: "AM", 375: "BY", 376: "AD", 377: "MC", 378: "SM", 379: "VA", 380: "UA",
    381: "RS", 382: "ME", 385: "HR", 386: "SI", 387: "BA", 389: "MK", 420: "CZ", 421: "SK",
    423: "LI", 501: "BZ", 502: "GT", 503: "SV", 504: "HN", 505: "NI", 506: "CR", 507: "PA",
    508: "PM", 509: "HT", 590: "GP", 591: "BO", 592: "GY", 593: "EC", 594: "GF", 595: "PY",
    596: "MQ", 597: "SR", 598: "UY", 599: "CW", 670: "TL", 672: "NF", 673: "BN", 674: "NR",
    675: "PG", 676: "TO", 677: "SB", 678: "VU", 679: "FJ", 680: "PW", 681: "WF", 682: "CK",
    683: "NU", 684: "AS", 685: "WS", 686: "KI", 687: "NC", 688: "TV", 689: "PF", 690: "TK",
    691: "FM", 692: "MH", 850: "KP", 852: "HK", 853: "MO", 855: "KH", 856: "LA", 880: "BD",
    886: "TW", 960: "MV", 961: "LB", 962: "JO", 963: "SY", 964: "IQ", 965: "KW", 966: "SA",
    967: "YE", 968: "OM", 970: "PS", 971: "AE", 972: "IL", 973: "BH", 974: "QA", 975: "BT",
    976: "MN", 977: "NP", 979: "IR", 992: "TJ", 993: "TM", 994: "AZ", 995: "GE", 996: "KG",
    998: "UZ",
}


class EmailDomainVerification(BaseModel):
    domain: str | None = None
    has_dns: bool | None = None
    has_mx: bool | None = None
    dns_records: list[str] = Field(default_factory=list)
    mx_records: list[str] = Field(default_factory=list)
    smtp_check: bool | None = None
    smtp_error: str | None = None
    is_disposable: bool = False
    is_reserved: bool = False
    is_corporate: bool = False


class PreviousValidationReport(BaseModel):
    blob_id: str | None = None
    report_url: str | None = None
    exists: bool = False
    previous_validation: dict | None = None
    differences: list[str] = Field(default_factory=list)
    trend: str | None = None


class ValidationResult(BaseModel):
    candidate_id: str = ""
    candidate_name: str | None = None
    resume: ResumeData | None = None
    ats_candidate: AtsCandidate | None = None
    linkedin: LinkedInData | None = None
    company: CompanyData | None = None
    resume_completeness: ValidationEvidence | None = None
    contact_validation: ValidationEvidence | None = None
    education_validation: ValidationEvidence | None = None
    experience_validation: ValidationEvidence | None = None
    timeline_validation: ValidationEvidence | None = None
    skills_validation: ValidationEvidence | None = None
    project_validation: ValidationEvidence | None = None
    certification_validation: ValidationEvidence | None = None
    employment_pattern: ValidationEvidence | None = None
    cross_field_validation: ValidationEvidence | None = None
    linkedin_verification: ValidationEvidence | None = None
    company_verification: ValidationEvidence | None = None
    fraud_detection: ValidationEvidence | None = None
    email_domain_verification: ValidationEvidence | None = None
    previous_report_check: PreviousValidationReport | None = None
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    completed_steps: list[str] = Field(default_factory=list)
    skipped_steps: list[str] = Field(default_factory=list)
    failed_steps: list[str] = Field(default_factory=list)


class ValidateRequest(BaseModel):
    candidate_id: str
    resume: dict
    linkedin_url: str | None = None


class CandidateInfo(BaseModel):
    name: str = ""
    email: str = ""
    phone: str = ""
    position: str = ""


class ValidationSummary(BaseModel):
    passed: int = 0
    warning: int = 0
    failed: int = 0
    skipped: int = 0


class InterviewQuestion(BaseModel):
    category: str = ""
    difficulty: str = ""
    question: str = ""
    reason: str = ""


class LLMAnalysis(BaseModel):
    overall_score: int = 0
    validation_score: int = 0
    confidence_score: int = 0
    fraud_score: int = 0
    company_score: int = 0
    linkedin_score: int = 0
    resume_completeness_score: int = 0
    contact_score: int = 0
    education_score: int = 0
    experience_score: int = 0
    timeline_score: int = 0
    skills_score: int = 0
    project_score: int = 0
    certification_score: int = 0
    employment_score: int = 0
    cross_validation_score: int = 0
    risk_level: str = ""
    recommendation: str = ""
    executive_summary: str = ""
    validation_summary: ValidationSummary = Field(default_factory=ValidationSummary)
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    recruiter_notes: list[str] = Field(default_factory=list)
    category_scores: dict[str, int] = Field(default_factory=dict)
    decision_reason: str = ""
    technical_interview_questions: list[InterviewQuestion] = Field(default_factory=list)


class ReportResult(BaseModel):
    blob_id: str = ""
    report_url: str = ""
    created_time: str = ""
    candidate_id: str = ""


class ReportGenerationRequest(BaseModel):
    candidate_id: str = ""
    candidate_info: CandidateInfo = Field(default_factory=CandidateInfo)
    validation_result: dict = Field(default_factory=dict)
    llm_analysis: LLMAnalysis = Field(default_factory=LLMAnalysis)


class ReportGenerationResponse(BaseModel):
    blob_id: str = ""
    report_url: str = ""
    created_time: str = ""
    candidate_id: str = ""


# ── ATS DTOs ──────────────────────────────────────────────────────────────────

class AtsSearchParams(BaseModel):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
    search: str | None = None
    status: str | None = None
    sort_by: str = "created_time"
    sort_order: str = "desc"
    recommendation: str | None = None
    validation_status: str | None = None


class AtsCandidateListItem(BaseModel):
    candidate_id: str = ""
    first_name: str | None = None
    last_name: str | None = None
    email: str | None = None
    phone: str | None = None
    current_employer: str | None = None
    location: str | None = None
    created_time: str | None = None
    validation_status: str | None = None
    recommendation: str | None = None
    report_url: str | None = None


class AtsCandidateList(BaseModel):
    total: int = 0
    data: list[AtsCandidateListItem] = Field(default_factory=list)


class CandidateListRequest(BaseModel):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
    search: str | None = None
    status: str | None = None
    sort_by: str = "created_time"
    sort_order: str = "desc"
    recommendation: str | None = None
    validation_status: str | None = None


class CandidateListResponse(BaseModel):
    total: int = 0
    data: list[AtsCandidateListItem] = Field(default_factory=list)


class CandidateDetailRequest(BaseModel):
    candidate_id: str


class CandidateDetailResponse(AtsCandidate):
    pass


class CandidateSearchRequest(BaseModel):
    candidate_id: str | None = None
    name: str | None = None
    email: str | None = None
    phone: str | None = None
    company: str | None = None
    recommendation: str | None = None
    validation_status: str | None = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


class CandidateSearchResponse(BaseModel):
    total: int = 0
    data: list[AtsCandidate] = Field(default_factory=list)


# ── Report DTOs ───────────────────────────────────────────────────────────────

class LatestReportRequest(BaseModel):
    candidate_id: str


class LatestReportResponse(ReportResult):
    pass


class BlobReportRequest(BaseModel):
    blob_id: str


class BlobReportResponse(ReportResult):
    pass


class ReportSearchRequest(BaseModel):
    candidate_id: str | None = None
    candidate_name: str | None = None
    recommendation: str | None = None
    validation_status: str | None = None
    date_from: str | None = None
    date_to: str | None = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


class ReportSearchResponse(BaseModel):
    total: int = 0
    data: list[ReportResult] = Field(default_factory=list)
