import logging
import re

import phonenumbers

from app.domain.models import COUNTRY_CODES, EmailDomainVerification, ResumeData, ValidationEvidence, ValidationStatus
from app.infrastructure.email_verifier import RESERVED_EXAMPLE_DOMAINS, EmailDomainVerifier

logger = logging.getLogger(__name__)

DISPOSABLE_DOMAINS = {"tempmail.com", "mailinator.com", "guerrillamail.com", "10minutemail.com", "throwaway.com", "yopmail.com", "sharklasers.com", "trashmail.com", "mailnesia.com", "getairmail.com", "temp-mail.org", "fakeinbox.com"}
COMMON_PROVIDERS = {"gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "aol.com", "protonmail.com", "icloud.com", "mail.com", "zoho.com", "yandex.com", "gmx.com"}

PHONE_TYPE_NAMES = {
    phonenumbers.PhoneNumberType.FIXED_LINE: "FIXED_LINE",
    phonenumbers.PhoneNumberType.MOBILE: "MOBILE",
    phonenumbers.PhoneNumberType.FIXED_LINE_OR_MOBILE: "FIXED_LINE_OR_MOBILE",
    phonenumbers.PhoneNumberType.TOLL_FREE: "TOLL_FREE",
    phonenumbers.PhoneNumberType.PREMIUM_RATE: "PREMIUM_RATE",
    phonenumbers.PhoneNumberType.SHARED_COST: "SHARED_COST",
    phonenumbers.PhoneNumberType.VOIP: "VOIP",
    phonenumbers.PhoneNumberType.PERSONAL_NUMBER: "PERSONAL_NUMBER",
    phonenumbers.PhoneNumberType.PAGER: "PAGER",
    phonenumbers.PhoneNumberType.UAN: "UAN",
    phonenumbers.PhoneNumberType.VOICEMAIL: "VOICEMAIL",
    phonenumbers.PhoneNumberType.UNKNOWN: "UNKNOWN",
}


class ContactValidator:
    def __init__(self):
        self.email_verifier = EmailDomainVerifier()

    async def validate(self, resume: ResumeData) -> ValidationEvidence:
        logger.info("ContactValidator input: email=%s, phone=%s", resume.email, resume.phone)
        evidence = []
        details = {"email": {}, "phone": {}}

        dns_result: EmailDomainVerification | None = None

        if resume.email:
            details["email"]["email"] = resume.email
            evidence.append(f"Email: {resume.email}")
            pattern = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
            if not pattern.match(resume.email):
                evidence.append("  Format: INVALID")
                details["email"]["format_valid"] = False
            else:
                evidence.append("  Format: VALID")
                details["email"]["format_valid"] = True

            domain = resume.email.split("@")[-1] if "@" in resume.email else ""
            details["email"]["domain"] = domain
            evidence.append(f"  Domain: {domain}")

            details["email"]["is_disposable"] = domain.lower() in DISPOSABLE_DOMAINS
            if details["email"]["is_disposable"]:
                evidence.append("  Provider: DISPOSABLE")
            else:
                evidence.append(f"  Provider: {'CORPORATE' if domain.lower() not in COMMON_PROVIDERS else 'PUBLIC'}")

            details["email"]["is_reserved"] = domain.lower() in RESERVED_EXAMPLE_DOMAINS
            if details["email"]["is_reserved"]:
                evidence.append("  Domain type: RESERVED/EXAMPLE")

            if domain.lower() in DISPOSABLE_DOMAINS:
                dns_result = EmailDomainVerification(domain=domain, is_disposable=True)
            else:
                dns_result = await self.email_verifier.verify(resume.email)
            details["email"]["dns"] = dns_result.model_dump() if dns_result else None
            if dns_result and dns_result.domain:
                if dns_result.has_dns:
                    evidence.append("  DNS: FOUND")
                else:
                    evidence.append("  DNS: NOT FOUND")
                if dns_result.has_mx:
                    evidence.append("  MX: FOUND")
                else:
                    evidence.append("  MX: NOT FOUND")
            evidence.append("")
        else:
            evidence.append("Email: MISSING")
            details["email"]["missing"] = True
            evidence.append("")

        if resume.phone:
            raw = resume.phone.strip()
            details["phone"]["phone"] = raw
            evidence.append(f"Phone: {raw}")
            details["phone"]["format_valid"] = False
            details["phone"]["country_code"] = None
            details["phone"]["national_number"] = None
            details["phone"]["country"] = None
            details["phone"]["region"] = None
            details["phone"]["number_type"] = None
            details["phone"]["international_format"] = None
            details["phone"]["e164"] = None

            try:
                parsed = phonenumbers.parse(raw, None)
                cc = parsed.country_code
                nn = str(parsed.national_number)
                is_valid = phonenumbers.is_valid_number(parsed)
                region = phonenumbers.region_code_for_number(parsed)
                ntype = phonenumbers.number_type(parsed)
                country = COUNTRY_CODES.get(cc, "Unknown")
                intl_format = phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.INTERNATIONAL)
                e164_format = phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)

                details["phone"]["country_code"] = str(cc)
                details["phone"]["national_number"] = nn
                details["phone"]["country"] = country
                details["phone"]["region"] = region
                details["phone"]["number_type"] = PHONE_TYPE_NAMES.get(ntype, "UNKNOWN")
                details["phone"]["format_valid"] = is_valid
                details["phone"]["international_format"] = intl_format
                details["phone"]["e164"] = e164_format

                if is_valid:
                    evidence.append(f"  Country: +{cc} ({country})")
                    evidence.append(f"  National: {nn}")
                    evidence.append(f"  Type: {PHONE_TYPE_NAMES.get(ntype, 'UNKNOWN')}")
                    evidence.append(f"  Region: {region}")
                    evidence.append(f"  International: {intl_format}")
                    evidence.append(f"  E164: {e164_format}")
                    evidence.append("  Valid: YES")
                else:
                    evidence.append("  Valid: NO — failed libphonenumber validation")
                    details["phone"]["validation_error"] = "Number failed libphonenumber validation"
            except phonenumbers.NumberParseException as e:
                evidence.append("  Valid: NO — could not be parsed")
                details["phone"]["validation_error"] = str(e)
            evidence.append("")
        else:
            evidence.append("Phone: MISSING")
            details["phone"]["missing"] = True
            evidence.append("")

        duplicates = self._detect_duplicate_contacts(resume)
        if duplicates:
            evidence.extend(duplicates)
            details["duplicate_contacts"] = duplicates

        # Correct classification:
        # IF invalid / critical error -> FAILED
        # IF partially valid / non-critical warning -> WARNING
        # IF fully valid -> PASSED
        has_critical_error = bool(
            details["email"].get("missing") and details["phone"].get("missing")
        )
        has_warning = bool(
            details["email"].get("missing")
            or details["phone"].get("missing")
            or details["email"].get("format_valid") is False
            or details["phone"].get("format_valid") is False
            or details["email"].get("is_disposable")
            or details["email"].get("is_reserved")
            or duplicates
            or (dns_result and not dns_result.has_dns and not details["email"].get("is_disposable"))
        )

        if has_critical_error:
            status = ValidationStatus.FAILED
        elif has_warning:
            status = ValidationStatus.WARNING
        else:
            status = ValidationStatus.PASSED

        if status == ValidationStatus.PASSED:
            evidence.append("Contact validation passed. Email format valid, phone number valid, and all checks consistent.")

        logger.info("ContactValidator decision: status=%s", status)
        return ValidationEvidence(status=status, evidence=evidence, details=details)

    def _detect_duplicate_contacts(self, resume: ResumeData) -> list[str]:
        warnings = []
        seen = set()
        if resume.email:
            seen.add(resume.email.lower())
        if resume.phone:
            digits_only = re.sub(r"[^\d]", "", resume.phone)
            seen.add(digits_only)

        for exp in resume.experience or []:
            company = exp.company or "unknown"
            if exp.description and resume.email:
                if resume.email.lower() in exp.description.lower():
                    warnings.append(f"Email '{resume.email}' appears in experience description for '{company}'")

        return warnings
