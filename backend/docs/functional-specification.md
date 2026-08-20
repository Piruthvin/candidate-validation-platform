# Candidate Validation Platform
## Functional Specification Document

**Document Type:** Business Requirements Document / Functional Specification Document

**Audience:** Recruiters, Business Analysts, QA Engineers, Product Owners

**Version:** 2.0

---

# Table of Contents

1. [Resume Completeness Validation](#1-resume-completeness-validation)
2. [Candidate Information Validation](#2-candidate-information-validation)
3. [Email Verification](#3-email-verification)
4. [Phone Number Verification](#4-phone-number-verification)
5. [LinkedIn Verification](#5-linkedin-verification)
6. [Education Validation](#6-education-validation)
7. [Employment Validation](#7-employment-validation)
8. [Experience Validation](#8-experience-validation)
9. [Skills Validation](#9-skills-validation)
10. [Certification Validation](#10-certification-validation)
11. [Company Verification](#11-company-verification)
12. [ATS Candidate Verification](#12-ats-candidate-verification)
13. [Identity Consistency Validation](#13-identity-consistency-validation)
14. [Duplicate Candidate Check](#14-duplicate-candidate-check)
15. [Employment Timeline Validation](#15-employment-timeline-validation)
16. [Fraud Detection](#16-fraud-detection)
17. [Resume Genuineness Check](#17-resume-genuineness-check)
18. [Project Validation](#18-project-validation)
19. [Location Validation](#19-location-validation)
20. [Contact Consistency Validation](#20-contact-consistency-validation)
21. [Report Generation](#21-report-generation)
22. [Overall Candidate Scoring](#22-overall-candidate-scoring)
23. [Recommendation Generation](#23-recommendation-generation)
24. [Blob Report Storage](#24-blob-report-storage)
25. [Recruiter Report Retrieval](#25-recruiter-report-retrieval)

---

# 1. Resume Completeness Validation

## Purpose

To ensure the resume contains all the essential sections and critical fields required for any meaningful candidate evaluation. A recruiter cannot assess a candidate if the resume is missing foundational information like name, email, or work history.

## Input

- Normalized resume data (extracted from uploaded resume file or pasted text)

## Validation Flow

System receives normalized resume
↓
System checks whether candidate name is present
↓
System checks whether email address is present
↓
System checks whether phone number is present
↓
System checks whether professional summary is present
↓
System checks whether work experience section exists
↓
System checks whether education section exists
↓
System checks whether skills section exists
↓
System checks for empty experience entries (no company name and no job title)
↓
System checks for empty education entries (no institution name)
↓
System assigns a validation status
↓
Result is added to the final recruiter report

## Possible Outcomes

**Verified** — All critical fields (name, email, phone) and most optional sections are present.

**Warning** — One or more optional sections are missing (e.g., summary, projects, certifications). The resume is usable but incomplete.

**Failed** — One or more critical fields (name, email, phone) are missing. The resume cannot be processed for further validation.

## Business Rules

- If name OR email OR phone is missing → **Fail**
- If any optional section is missing (summary, skills, experience, education) → **Warning**
- If experience entries exist but have no company or title → Count as missing information
- If education entries exist but have no institution → Count as missing information
- If all critical fields are present and most optional sections exist → **Verified**

## Information Stored

- List of sections found on the resume
- List of sections missing from the resume
- Which critical fields are missing (if any)
- Number of empty experience entries
- Number of empty education entries
- Confidence percentage in the completeness of the resume

## Contribution to Final Report

This validation establishes whether the resume has sufficient data for all downstream validations. If it fails, the recruiter sees a clear instruction to request the missing critical fields from the candidate. It also feeds into the overall confidence score — an incomplete resume lowers confidence in every subsequent validation.

## Real-World Example

**Candidate resume contains:**
- Name: "Sarah Chen"
- Email: (present)
- Phone: (present)
- Summary: (present)
- Experience: 3 entries, all with company and title
- Education: 1 entry with institution
- Skills: (present)
- Projects: (not present)

↓

System confirms all critical fields present
↓
System notes projects section is missing
↓
Status = Warning
↓
Recruiter sees: "Resume is complete enough to proceed. Consider asking about projects during interview."

---

# 2. Candidate Information Validation

## Purpose

To confirm that the basic identifying information of the candidate has been successfully extracted from the raw resume and is correctly structured. This ensures that the system knows exactly who the candidate is before running any checks.

## Input

- Raw resume text (uploaded file or pasted content)

## Validation Flow

Raw resume text is received
↓
System extracts the candidate's full name
↓
System extracts the candidate's email address
↓
System extracts the candidate's phone number
↓
System extracts the candidate's professional summary
↓
System extracts the candidate's location
↓
System extracts the candidate's LinkedIn profile URL
↓
System extracts the candidate's skills list
↓
System extracts work experience entries with company names, job titles, and dates
↓
System extracts education entries with institution names and degrees
↓
System extracts certifications
↓
System extracts projects
↓
All extracted information is structured into a standardized candidate profile
↓
Result is passed to all validators

## Possible Outcomes

**Verified** — All major identifying fields were extracted successfully.

**Warning** — Some optional fields (summary, location, LinkedIn URL, certifications, projects) could not be extracted.

**Failed** — The system could not extract name or email or phone from the resume.

## Business Rules

- If the resume text is empty or unparseable → **Fail**
- If name cannot be determined → **Fail** (candidate cannot be identified)
- If email cannot be extracted → **Warning** (candidate may still be identifiable by name and phone)
- If phone cannot be extracted → **Warning** (candidate may still be reachable by email)
- Missing summary, location, LinkedIn URL, certifications, or projects are acceptable but noted

## Information Stored

- Candidate full name
- Candidate email address
- Candidate phone number
- Candidate professional summary
- Candidate location
- Candidate LinkedIn profile URL
- List of skills
- List of work experience entries with company, title, and dates
- List of education entries with institution, degree, and field of study
- List of certifications with name, issuer, and date
- List of projects with name, description, and technologies
- Total years of experience (if stated)

## Contribution to Final Report

This is the foundation of the entire report. The candidate information section at the top of the recruiter report is populated entirely from this step. If extraction fails, no further validations can run.

## Real-World Example

**Raw resume text contains:**

Sarah Chen
sarah.chen@email.com
+1 555 234 5678

Senior Software Engineer with 7 years of experience...

↓

System extracts:
- Name: "Sarah Chen"
- Email: "sarah.chen@email.com"
- Phone: "+1 555 234 5678"
- Summary: "Senior Software Engineer with 7 years of experience..."
- Skills: ["Python", "Java", "AWS", ...]
- Experience: [3 entries parsed with company, title, dates]
- Education: [1 entry: MIT, BS Computer Science]
↓
Status = Verified
↓
Candidate profile is ready for validation

---

# 3. Email Verification

## Purpose

To verify that the candidate's email address is real, properly formatted, belongs to a valid domain, and is not a disposable or temporary address. This prevents candidates from using throwaway email accounts and ensures the recruiter can reliably contact the candidate.

## Input

- Candidate email address extracted from the resume

## Validation Flow

Candidate email address is extracted
↓
System checks email format (basic structure: username@domain.extension)
↓
System identifies the email domain
↓
System checks whether the domain belongs to a disposable email provider
↓
System checks whether the domain is a reserved example domain
↓
System checks whether the domain is a corporate or public provider
↓
System performs a DNS lookup to see if the domain has DNS records
↓
System performs an MX record lookup to see if the domain accepts mail
↓
System assigns a validation status
↓
Result is added to the final recruiter report

## Possible Outcomes

**Verified** — Email format is valid, domain has DNS and MX records, and it is not disposable or reserved.

**Warning** — Email format is valid but the domain has no DNS or MX records, or the domain is a public provider (e.g., gmail.com, yahoo.com).

**Failed** — Email uses a disposable domain, a reserved example domain, or the email format is invalid.

**Unable to Verify** — No email address was provided on the resume.

## Business Rules

- If the email does not match basic email format → **Fail**
- If the email domain is a disposable provider → **Fail** (e.g., tempmail.com, mailinator.com)
- If the email domain is a reserved example domain → **Fail** (e.g., example.com, test.com)
- If the domain has no DNS records → **Warning**
- If the domain has no MX records (cannot receive mail) → **Warning**
- If everything is valid → **Verified**

## Information Stored

- The email address
- Whether the format is valid
- The domain name
- Whether the domain is disposable
- Whether the domain is a reserved example domain
- Whether the domain is corporate or a public provider
- DNS record presence
- MX record presence

## Contribution to Final Report

The email verification result directly affects the recruiter's ability to contact the candidate. A disposable or invalid email is a significant red flag. The report tells the recruiter whether the contact information is trustworthy.

## Real-World Example

**Candidate email:** john@gmail.com

↓

System checks format → Valid
↓
System checks domain → gmail.com
↓
System classifies → Public provider (not disposable, not reserved)
↓
System performs DNS lookup → DNS records found
↓
System performs MX lookup → MX records found
↓
Status = Verified

**Candidate email:** jane@tempmail.com

↓

System checks format → Valid
↓
System checks domain → tempmail.com
↓
System classifies → Disposable domain
↓
Status = Failed
↓
Recruiter sees: "Email uses a disposable domain. Request a permanent email address."

---

# 4. Phone Number Verification

## Purpose

To verify that the candidate's phone number is real, properly formatted, and belongs to a valid country and number type. This ensures the recruiter can reliably contact the candidate by phone.

## Input

- Candidate phone number extracted from the resume

## Validation Flow

Candidate phone number is extracted
↓
System parses the phone number to extract country code and national number
↓
System identifies the country based on the country code
↓
System identifies the number type (mobile, landline, VoIP, etc.)
↓
System validates the number against international phone number standards
↓
System formats the number in international format
↓
System assigns a validation status
↓
Result is added to the final recruiter report

## Possible Outcomes

**Verified** — Phone number is valid, properly formatted, and the country is identified.

**Warning** — Phone number format could not be fully verified or the number type is unusual (e.g., premium rate, pager).

**Failed** — Phone number could not be parsed or is invalid.

**Unable to Verify** — No phone number was provided on the resume.

## Business Rules

- If the phone number fails international validation → **Fail**
- If the phone number cannot be parsed at all → **Fail**
- If the phone number is valid and the country is identified → **Verified**
- If the phone number is valid but the number type is unusual → **Warning** (e.g., VoIP, toll-free)

## Information Stored

- The phone number
- Country code
- National number
- Country name
- Region code
- Number type (MOBILE, FIXED_LINE, VOIP, etc.)
- International format
- E.164 format (standardized international format)
- Whether the number passed validation

## Contribution to Final Report

The phone verification result appears in the contact section of the recruiter report. A valid phone number increases confidence that the candidate can be reached. An invalid number requires the recruiter to request corrected contact information.

## Real-World Example

**Candidate phone:** +1 555 234 5678

↓

System parses → Country code +1, national number 5552345678
↓
System identifies country → US
↓
System identifies type → MOBILE
↓
System validates → Valid
↓
Status = Verified

**Candidate phone:** 12345

↓

System attempts to parse → Could not be parsed
↓
Status = Failed
↓
Recruiter sees: "Phone number could not be validated. Request correct phone number from candidate."

---

# 5. LinkedIn Verification

## Purpose

To corroborate the information on the candidate's resume with their LinkedIn profile. This provides independent verification of the candidate's claimed experience, education, and skills.

## Input

- Candidate LinkedIn profile URL (extracted from resume or provided separately)
- Normalized resume data

## Validation Flow

LinkedIn URL is provided
↓
System validates the LinkedIn URL format
↓
System fetches the LinkedIn profile data
↓
System checks whether the profile exists and is accessible
↓
System extracts profile name and headline
↓
System extracts experience entries from LinkedIn
↓
System extracts education entries from LinkedIn
↓
System extracts skills from LinkedIn
↓
System compares LinkedIn name with resume name
↓
System compares LinkedIn employer with resume employer
↓
System compares skill sets between resume and LinkedIn
↓
System assigns a validation status
↓
Result is added to the final recruiter report

## Possible Outcomes

**Verified** — LinkedIn profile exists, name matches, employer matches, and skills overlap is acceptable.

**Warning** — LinkedIn profile exists but there are mismatches in name, employer, or skills.

**Skipped** — No LinkedIn URL was provided or the profile could not be fetched.

## Business Rules

- If no LinkedIn URL is provided → **Skipped**
- If the LinkedIn URL format is invalid → **Skipped**
- If the profile cannot be fetched → **Skipped** (profile may exist but scraping failed)
- If LinkedIn name does not match resume name → **Warning**
- If current employer on LinkedIn does not match resume → **Warning**
- If skill overlap between resume and LinkedIn is below 30% → **Warning**
- If profile exists and all checks pass → **Verified**

## Information Stored

- LinkedIn profile URL
- Profile headline
- Whether name matches between resume and LinkedIn
- Whether employer matches between resume and LinkedIn
- Number of skills on LinkedIn
- Number of experience entries on LinkedIn
- Whether location matches between resume and LinkedIn

## Contribution to Final Report

LinkedIn verification provides an independent data source to validate the candidate's resume. Mismatches are flagged for the recruiter to investigate. A matching profile increases trust in the candidate's claims.

## Real-World Example

**Resume:** Sarah Chen, Senior Engineer at Google
**LinkedIn URL:** linkedin.com/in/sarahchen

↓

System fetches profile → Profile found
↓
LinkedIn name: "Sarah Chen" → matches resume
↓
LinkedIn employer: "Google" → matches resume
↓
Skills overlap: 12 of 15 skills match → acceptable
↓
Status = Verified
↓
Recruiter sees: "LinkedIn profile corroborates resume claims."

---

# 6. Education Validation

## Purpose

To verify the completeness and consistency of the candidate's education history. This helps identify missing information, impossible dates, or suspicious entries in the academic background.

## Input

- Education entries extracted from the resume

## Validation Flow

Education entries are extracted
↓
System checks whether an institution name is present for each entry
↓
System checks whether a degree is present for each entry
↓
System checks whether start and end dates are present
↓
System verifies that the start date is before the end date
↓
System checks whether graduation dates are in the future
↓
System detects duplicate institution entries
↓
System assigns a validation status
↓
Result is added to the final recruiter report

## Possible Outcomes

**Verified** — All education entries have institution names, degrees, and valid dates.

**Warning** — Some entries are missing fields or duplicate institutions were found.

**Failed** — Invalid timelines (start after end) or future graduation dates detected.

**Skipped** — No education entries exist on the resume.

## Business Rules

- If no education entries exist → **Skipped**
- If start date is after end date for any entry → **Fail**
- If graduation date is in the future → **Fail**
- If institution name is missing → **Warning**
- If degree is missing → **Warning**
- If duplicate institutions are found → **Warning**
- If all entries are complete with valid dates → **Verified**

## Information Stored

- Number of education entries
- Number of entries with invalid timelines
- Number of entries with future dates
- Number of entries with missing fields
- List of duplicate institutions found

## Contribution to Final Report

Education validation helps the recruiter assess the candidate's academic background. Invalid dates or missing information may indicate errors on the resume or deliberate exaggeration. The report flags these issues for recruiter follow-up.

## Real-World Example

**Candidate education:**
1. MIT, BS Computer Science, 2014–2018
2. Stanford, MS Computer Science, 2019–2021

↓

System checks dates → All start before end
↓
System checks future dates → None
↓
System checks duplicates → None
↓
System checks missing fields → None
↓
Status = Verified

**Candidate education:**
1. University of XYZ, BS Physics, 2025–2024

↓

System checks dates → Start date is after end date
↓
Status = Failed
↓
Recruiter sees: "Education entry has start date after end date. Verify dates with candidate."

---

# 7. Employment Validation

## Purpose

To verify that each work experience entry contains the essential information needed to assess the candidate's professional background. This ensures every job entry has a company name, job title, and reasonable dates.

## Input

- Work experience entries extracted from the resume

## Validation Flow

Work experience entries are extracted
↓
System checks whether a company name is present for each entry
↓
System checks whether a job title is present for each entry
↓
System checks whether start and end dates are present
↓
System verifies that the start date is before the end date
↓
System detects duplicate employer entries
↓
System counts the total number of employers
↓
System assigns a validation status
↓
Result is added to the final recruiter report

## Possible Outcomes

**Verified** — All experience entries have company names, job titles, and valid dates.

**Warning** — Some entries are missing company names or job titles, or duplicate employers were found.

**Failed** — Invalid date ranges detected (start date after end date).

**Skipped** — No work experience entries exist on the resume.

## Business Rules

- If no experience entries exist → **Skipped**
- If any entry has a start date after the end date → **Fail**
- If any entry is missing a company name → **Warning**
- If any entry is missing a job title → **Warning**
- If duplicate employers are found → **Warning**
- If the candidate has 6 or more employers → **Warning** (may indicate frequent job changes)
- If all entries are complete with valid dates → **Verified**

## Information Stored

- Number of experience entries
- Number of entries missing a company name
- Number of entries missing a job title
- Number of entries with invalid date ranges
- List of duplicate employer names
- Whether the number of employers is unusually high

## Contribution to Final Report

Employment validation is one of the most important checks for a recruiter. Missing or invalid employment information directly impacts the ability to assess candidate fit. The report clearly shows which entries need clarification.

## Real-World Example

**Candidate experience:**
1. Google, Senior Engineer, 2019–2023
2. Amazon, Software Engineer, 2016–2019
3. Microsoft, Intern, 2015

↓

System checks company → All present
↓
System checks title → All present
↓
System checks dates → All valid
↓
System checks duplicates → None
↓
System checks count → 3 (normal)
↓
Status = Verified

---

# 8. Experience Validation

## Purpose

To validate the candidate's overall experience level including total years of experience, role progression, and the breadth of their professional history. This helps the recruiter understand the candidate's career trajectory.

## Input

- All work experience entries
- Total years of experience (if stated on resume)
- Skills list

## Validation Flow

Work experience entries are collected
↓
System calculates total years of experience from dates
↓
System compares stated years of experience with calculated years
↓
System analyzes job title progression over time
↓
System evaluates the breadth of roles and industries
↓
System compares experience level against skills listed
↓
System assigns a validation status
↓
Result is added to the final recruiter report

## Possible Outcomes

**Verified** — Experience level is consistent with the roles and skills listed.

**Warning** — Experience level seems inconsistent or there are gaps in the career history.

**Failed** — Major inconsistencies detected between stated experience and actual resume content.

**Skipped** — No experience entries to validate.

## Business Rules

- This validation is performed as part of multiple validators (experience, timeline, employment pattern)
- Each validator contributes evidence about the candidate's experience quality
- The LLM (AI analysis engine) makes the final determination of experience validity based on all evidence

## Information Stored

- Total years of experience (calculated vs. stated)
- Number of distinct employers
- Job title progression across roles
- Duration of each role

## Contribution to Final Report

The experience validation provides the recruiter with a clear picture of the candidate's career. It highlights whether the candidate has the depth and breadth of experience required for the role.

## Real-World Example

**Candidate has:**
- 3 jobs over 7 years
- Progression: Junior Engineer → Engineer → Senior Engineer
- Total stated: 7 years

↓

System confirms progression is logical
↓
Years match stated experience
↓
Breadth is reasonable for a senior role
↓
Status = Verified

---

# 9. Skills Validation

## Purpose

To evaluate the candidate's listed skills for relevance, density, and alignment with the technologies actually used in their projects. This helps detect skill inflation or mismatches between claimed skills and demonstrated work.

## Input

- Skills list from the resume
- Project entries with technologies used
- Total years of experience

## Validation Flow

System receives the candidate's skills list
↓
System counts the total number of skills listed
↓
System compares skills against technologies used in projects
↓
System calculates skill density (ratio of skills to years of experience)
↓
System identifies technologies used in projects but not listed as skills
↓
System assigns a validation status
↓
Result is added to the final recruiter report

## Possible Outcomes

**Verified** — Skills are consistent with project technologies and the skill count is reasonable.

**Warning** — Issues detected such as excessive skills, missing project technologies, or high skill density.

**Skipped** — No skills listed on the resume.

## Business Rules

- If no skills are listed → **Skipped**
- If more than 30 skills are listed → **Warning** (potentially inflated)
- If project technologies are not reflected in the skills list → **Warning**
- If skill density exceeds 5 skills per year of experience → **Warning** (e.g., 50 skills with 5 years experience)
- If none of the above conditions apply → **Verified**

## Information Stored

- Number of skills listed
- List of skills (up to 30)
- Technologies used in projects
- Technologies used in projects but not listed in skills
- Skill density ratio

## Contribution to Final Report

Skills validation helps the recruiter determine if the candidate's claimed expertise is backed by actual project work. A candidate who lists 40 skills but only used 5 technologies in their projects may be overstating their abilities. The report flags these discrepancies.

## Real-World Example

**Candidate skills:** Python, Java, AWS, Docker, Kubernetes, React, Angular, SQL, MongoDB, Redis (10 skills)

**Project technologies used:** Python, Java, AWS, Docker, SQL

↓

System counts skills → 10 (reasonable)
↓
System checks skill density → 10 skills / 5 years = 2.0 (reasonable)
↓
System checks project alignment → All project technologies are in skills list
↓
Status = Verified

**Candidate skills:** Python, Java, C++, JavaScript, React, Angular, Vue, Node, AWS, Azure, GCP, Docker, Kubernetes, Jenkins, Terraform, Ansible, MySQL, PostgreSQL, MongoDB, Redis, Kafka, RabbitMQ, GraphQL, REST, HTML, CSS, TypeScript, Swift, Kotlin, Flutter (30 skills)

**Project technologies used:** Python, HTML, CSS (from 2 small projects)

↓

System counts skills → 30 (at threshold)
↓
System checks alignment → 27 project technologies not listed as skills — Wait, actually 3 skills match, many project techs missing
↓
System checks density → 30 skills / 3 years = 10 skills/year (high)
↓
Status = Warning
↓
Recruiter sees: "Skill set appears inflated relative to project work. Probe for depth in key skills during interview."

---

# 10. Certification Validation

## Purpose

To verify the completeness and reasonableness of the candidate's certifications. This helps identify outdated credentials, suspicious future dates, or incomplete certification information.

## Input

- Certification entries extracted from the resume

## Validation Flow

Certification entries are extracted
↓
System checks whether a certification name is present for each entry
↓
System checks whether an issuer/vendor is present for each entry
↓
System checks whether a certification date is present
↓
System flags certifications with dates before the year 2000
↓
System flags certifications with future dates
↓
System assigns a validation status
↓
Result is added to the final recruiter report

## Possible Outcomes

**Verified** — All certifications have names, issuers, and reasonable dates.

**Warning** — Some certifications are missing names or issuers.

**Failed** — Certifications have dates before the year 2000 or future dates.

**Skipped** — No certifications listed on the resume.

## Business Rules

- If no certifications exist → **Skipped**
- If any certification date is before the year 2000 → **Fail**
- If any certification date is in the future → **Fail**
- If a certification name is missing → **Warning**
- If an issuer/vendor is missing → **Warning**
- If all certifications are complete with reasonable dates → **Verified**

## Information Stored

- Number of certifications listed
- Number of certifications missing names
- Number of certifications missing issuers
- Number of certifications with old dates
- Number of certifications with future dates

## Contribution to Final Report

Certifications indicate specialized knowledge and ongoing professional development. Outdated certifications may no longer be relevant, and future dates suggest the candidate may be estimating or guessing. The report helps the recruiter assess the value of the candidate's credentials.

## Real-World Example

**Candidate certifications:**
1. AWS Solutions Architect, Amazon, 2021
2. Certified Kubernetes Administrator, CNCF, 2022

↓

System checks names → Present
↓
System checks issuers → Present
↓
System checks dates → Both within reasonable range (after 2000, not in future)
↓
Status = Verified

**Candidate certification:**
1. , , 1995

↓

System checks name → Missing
↓
System checks issuer → Missing
↓
System checks date → Before year 2000
↓
Status = Failed
↓
Recruiter sees: "Certification entry is incomplete and the date is unusually old. Request clarification."

---

# 11. Company Verification

## Purpose

To verify that the candidate's current or most recent employer is a legitimate operating business. This prevents candidates from claiming employment at non-existent or shell companies.

## Input

- Company name from the candidate's most recent work experience entry

## Validation Flow

Company name is extracted from the most recent experience entry
↓
System attempts to find the company website
↓
System generates probable website URLs based on company name
↓
System checks whether the website is reachable (HTTP status)
↓
System checks whether the website has a valid SSL certificate
↓
System checks whether the company domain has DNS records
↓
System checks whether the company domain has MX records (email)
↓
System calculates a confidence score based on verification evidence
↓
System assigns a validation status
↓
Result is added to the final recruiter report

## Possible Outcomes

**Verified** — Company website is reachable, has DNS records, and has an SSL certificate.

**Warning** — Company website could not be reached or verified.

**Skipped** — No company name available to verify.

## Business Rules

- If no company name is available → **Skipped**
- If the company website is reachable (HTTP status under 500) → **Verified**
- If the website is not reachable → **Warning**
- If no website can be found for the company name → **Warning**
- Results are cached for 24 hours so the same company is not re-verified repeatedly

## Information Stored

- Company name
- Website URL found
- Whether the website is reachable
- Whether SSL is present
- Whether DNS records exist
- Whether MX records exist
- Confidence score (0–100)
- Trust evidence (list of positive verifications)

## Contribution to Final Report

Company verification provides a critical trust signal. A verified company increases confidence in the candidate's employment claims. An unverifiable company is a red flag that the recruiter should investigate further, possibly requesting offer letters or pay stubs.

## Real-World Example

**Candidate's most recent employer:** Google

↓

System searches for website → google.com found
↓
System checks reachability → Google.com is reachable (HTTP 200)
↓
System checks SSL → Valid SSL certificate
↓
System checks DNS → DNS records exist
↓
System checks MX → MX records exist
↓
Confidence score: 100/100
↓
Status = Verified
↓
Recruiter sees: "Company 'Google' has been verified as a legitimate operating business."

---

# 12. ATS Candidate Verification

## Purpose

To cross-reference the candidate against the organization's Applicant Tracking System (ATS) to see if there is an existing record. This helps identify whether the candidate has applied before, has been previously evaluated, or has existing data in the system.

## Input

- Candidate ID (provided by the recruiter)
- Candidate email address (from resume)
- Candidate phone number (from resume)

## Validation Flow

System receives the candidate ID
↓
System attempts to find the candidate in the ATS by their ID
↓
If not found by ID, system searches by email address
↓
If not found by email, system searches by phone number
↓
If found, system retrieves the candidate's existing ATS record
↓
System extracts ATS data: name, email, phone, skills, employer, location
↓
System checks whether a previous validation report exists
↓
If a previous report exists, system downloads it for comparison
↓
Result is passed to the cross-field validation
↓
Result is added to the final recruiter report

## Possible Outcomes

**Found** — Candidate exists in the ATS system with an existing record.

**Previous Report Available** — Candidate has been validated before and a previous report exists for comparison.

**Not Found** — Candidate does not have an existing ATS record.

## Business Rules

- If the candidate ID is numeric, it is treated as the ATS record ID directly
- If not found by ID, the system searches by email
- If not found by email, the system searches by phone
- If not found by any method → the candidate is new to the system
- If a previous report exists, it is retrieved for trend comparison

## Information Stored

- ATS candidate ID
- First and last name from ATS
- Email from ATS
- Phone from ATS
- Skills from ATS
- Current employer from ATS
- Location from ATS
- Whether a previous validation report exists
- Previous report URL and blob ID

## Contribution to Final Report

ATS verification provides the historical context for the candidate. If a previous report exists, the system can show a trend analysis (is the candidate improving or declining?). The ATS data also serves as a cross-reference for the identity consistency and cross-field validations.

## Real-World Example

**Candidate ID:** CUST-001

↓

System searches ATS by ID → Not found
↓
System searches by email → sarah.chen@email.com
↓
Match found in ATS → Record retrieved
↓
ATS record shows: Sarah Chen, sarah.chen@email.com, +1 555 234 5678
↓
Previous report exists → Downloaded for comparison
↓
Recruiter sees: "Candidate has a previous validation report from 3 months ago. Trend comparison available."

---

# 13. Identity Consistency Validation

## Purpose

To ensure the candidate's identity is consistent across all available data sources: the resume, the ATS record, LinkedIn, and company verification. This is the most powerful check for detecting misrepresentation or identity fraud.

## Input

- Normalized resume data
- ATS candidate record (if available)
- LinkedIn profile data (if available)
- Company verification data (if available)

## Validation Flow

System collects data from all available sources
↓
System compares the name on the resume with the name in the ATS
↓
System compares the name on the resume with the name on LinkedIn
↓
System compares the email on the resume with the email in the ATS
↓
System compares the phone on the resume with the phone in the ATS
↓
System checks whether the resume employer matches the verified company
↓
System checks whether work experience started before graduation
↓
System compares skills between resume and ATS record
↓
System counts the total number of discrepancies
↓
System assigns a validation status
↓
Result is added to the final recruiter report

## Possible Outcomes

**Verified** — No discrepancies found across any data source.

**Warning** — 1–2 discrepancies were found between data sources.

**Failed** — 3 or more discrepancies were found across data sources.

## Business Rules

- Each discrepancy is counted separately
- If email differs between resume and ATS → 1 discrepancy
- If name differs between resume and ATS → 1 discrepancy
- If name differs between resume and LinkedIn → 1 discrepancy
- If phone differs between resume and ATS → 1 discrepancy
- If a job started before the candidate graduated (not an internship) → 1 discrepancy
- If the most recent employer on the resume does not match the verified company → 1 discrepancy
- If 3 or more total discrepancies → **Fail**
- If 1–2 total discrepancies → **Warning**
- If 0 discrepancies → **Verified**

## Information Stored

- Total number of discrepancies found
- Specific details of each discrepancy
- Which data sources were available for comparison
- Which data sources were missing (e.g., ATS not available, LinkedIn not available)

## Contribution to Final Report

Identity consistency validation is a critical trust signal. If the candidate's name is different on their resume vs. LinkedIn, or their email differs from the ATS record, this must be investigated. The report clearly lists every discrepancy for recruiter action.

## Real-World Example

**Resume:** Sarah Chen, sarah.chen@email.com, +1 555 234 5678
**ATS:** Sarah Chen, sarah.chen@email.com, +1 555 234 5678
**LinkedIn:** Sarah Chen, Google

↓

Name: Resume = "Sarah Chen", ATS = "Sarah Chen" → Match
Name: Resume = "Sarah Chen", LinkedIn = "Sarah Chen" → Match
Email: Resume = "sarah.chen@email.com", ATS = "sarah.chen@email.com" → Match
Phone: Resume = "+1 555 234 5678", ATS = "+1 555 234 5678" → Match
Employer: Resume = "Google", Company verified = "Google" → Match
↓
0 discrepancies
↓
Status = Verified

---

# 14. Duplicate Candidate Check

## Purpose

To detect whether the same candidate already exists in the system under a different ID, email, or phone number. This prevents duplicate records and ensures the recruiter sees the complete history of the candidate.

## Input

- Candidate email address
- Candidate phone number
- ATS records

## Validation Flow

System receives candidate contact information
↓
System searches the ATS for an existing record with the same email
↓
System searches the ATS for an existing record with the same phone
↓
System checks whether the resume email appears in the experience descriptions (potential data scraping)
↓
If a duplicate is found, the existing candidate ID is noted
↓
Result is added to the final recruiter report

## Possible Outcomes

**No Duplicate Found** — The candidate does not exist in the ATS or other data sources.

**Duplicate Found** — An existing record with the same email or phone was found in the ATS.

**Potential Duplicate** — The candidate's email appears in unexpected places (e.g., inside job descriptions), which may indicate data scraping.

## Business Rules

- If the same email exists in the ATS → **Duplicate Found**
- If the same phone number exists in the ATS → **Duplicate Found**
- If the candidate's email appears in their own experience descriptions → Flagged (may indicate resume scraping or fabrication)
- The ATS resolution logic also prevents creating a new validation for an existing candidate

## Information Stored

- Whether an existing ATS record was found
- The existing candidate ID
- Previous report details if a prior validation exists
- Whether email was found in experience descriptions

## Contribution to Final Report

Duplicate detection prevents wasted effort on re-validating a candidate who has already been processed. If a duplicate is found, the recruiter can view the previous report and assess whether a new validation is needed.

## Real-World Example

**Candidate email:** sarah.chen@email.com

↓

System searches ATS by email → Found: Candidate ID "CUST-001"
↓

System notes: "Candidate CUST-001 already exists with this email. Previous validation report available."
↓

Recruiter sees option to view previous report or run a new validation.

---

# 15. Employment Timeline Validation

## Purpose

To analyze the candidate's employment timeline for gaps, overlaps, and date anomalies. This helps identify unexplained career gaps, potential dual employment, or inaccurate date reporting.

## Input

- Work experience entries with start and end dates

## Validation Flow

Work experience entries with dates are collected
↓
System sorts entries by start date (oldest to newest)
↓
System identifies gaps between consecutive employments
↓
System flags gaps of 6 months or more
↓
System specifically reports gaps of 12 months or more
↓
System detects overlapping employment periods (working at two jobs simultaneously)
↓
System flags any future end dates
↓
System calculates total gap duration
↓
System assigns a validation status
↓
Result is added to the final recruiter report

## Possible Outcomes

**Verified** — No significant gaps, no overlaps, and no future dates.

**Warning** — One or more employment gaps of 6+ months were detected.

**Failed** — Overlapping employment periods or future end dates detected.

**Skipped** — No experience entries with sufficient date information.

## Business Rules

- If no experience entries exist → **Skipped**
- If any overlapping employment is detected → **Fail**
- If any future end date is detected → **Fail**
- If gaps of 6 months or more exist → **Warning**
- Gaps of 12 months or more are specifically highlighted
- The total gap period across the entire career is calculated

## Information Stored

- Number of gaps found
- Total gap period in months
- Whether overlaps were detected
- Number of overlaps
- Number of future end dates
- Number of entries with valid date information

## Contribution to Final Report

Employment timeline validation gives the recruiter critical insight into the candidate's career stability. Unexplained gaps may indicate sabbaticals, layoffs, or other issues. Overlapping employment may indicate dual employment or inaccurate dates. The report provides specific questions the recruiter should ask.

## Real-World Example

**Candidate experience:**
1. Google, 2019-01 to 2021-06
2. Amazon, 2022-01 to 2023-12

↓

System sorts → Google (2019-01-01 to 2021-06-01), Amazon (2022-01-01 to 2023-12-01)
↓
System calculates gap → 2021-06 to 2022-01 = 7 months
↓
Gap of 7 months → Flagged (over 6 months)
↓
System checks overlaps → None
↓
System checks future dates → None
↓
Status = Warning
↓
Recruiter sees: "7-month employment gap between Google and Amazon. Discuss with candidate."

---

# 16. Fraud Detection

## Purpose

To detect signs of fraudulent, artificially generated, or template-based resume content. This protects recruiters from candidates who use AI-generated resumes, keyword stuffing, or generic templates that do not reflect genuine experience.

## Input

- Raw resume text

## Validation Flow

System receives the full raw text of the resume
↓
System scans for keyword stuffing (excessive use of buzzwords)
↓
System scans for AI generation markers (phrases like "as an AI", "as a language model")
↓
System scans for template indicators (placeholder text like "[insert]", "lorem ipsum")
↓
System scans for repeated sentences or phrases
↓
System scans for placeholder patterns (brackets, "xxxx", "click here")
↓
System counts the total number of fraud signals detected
↓
System assigns a validation status
↓
Result is added to the final recruiter report

## Possible Outcomes

**Verified** — No fraud signals detected. Resume content appears genuine.

**Warning** — 1–2 fraud signals detected. Some content may need review.

**Failed** — 3 or more fraud signals detected. Resume content is highly suspicious.

## Business Rules

- If the raw resume text is empty → No analysis performed
- Keyword stuffing is detected when buzzwords appear more than 3 times each
- AI generation is detected by specific phrases that indicate AI-generated text
- Template abuse is detected by placeholder markers in the text
- 3 or more fraud signal types → **Fail**
- 1–2 fraud signal types → **Warning**
- 0 fraud signal types → **Verified**

Buzzwords monitored: "team player", "hardworking", "motivated", "results-driven", "detail-oriented", "proven track record", "think outside the box", "synergy", "self-starter", "go-getter", "strategic thinker", "cutting edge", "world class"

AI markers monitored: "as an AI", "I don't have personal", "I cannot", "I am an AI", "as a language model", "I don't have access to", "I cannot provide"

Template markers: "[insert", "[your name]", "[company name]", "[job title]", "lorem ipsum", "xxxx", "click here", "replace with"

## Information Stored

- List of keyword stuffing indicators found
- List of AI generation indicators found
- List of template indicators found
- List of repeated phrases detected
- Total number of fraud signals

## Contribution to Final Report

Fraud detection is one of the most critical validations. If the resume appears to be AI-generated or heavily templated, the candidate's claimed experience cannot be trusted. The report provides the specific flagged content so the recruiter can ask targeted questions.

## Real-World Example

**Resume text contains:** "I am a team player who is results-driven and detail-oriented. I think outside the box and have a proven track record of success. I am a self-starter with excellent communication skills..."

↓

System detects keyword stuffing → "team player" × 4, "results-driven" × 5, "detail-oriented" × 6
↓
System detects no AI markers → Clean
↓
System detects no template markers → Clean
↓
System detects no repeated phrases → Clean
↓
Signal count: 1 (keyword stuffing)
↓
Status = Warning
↓
Recruiter sees: "Resume contains excessive buzzwords. Probe for specific examples during interview."

---

# 17. Resume Genuineness Check

## Purpose

To assess whether the resume appears to be a genuine, human-written document versus an artificially generated or heavily manipulated one. This is a broader assessment that combines fraud detection signals with overall content quality analysis.

## Input

- Raw resume text
- Fraud detection results

## Validation Flow

System receives the fraud detection results
↓
System evaluates the overall authenticity signals
↓
System checks for consistency in writing style
↓
System checks for unrealistic or exaggerated claims
↓
System checks for content that appears to be copied from job descriptions
↓
System assigns a genuineness assessment
↓
Result is added to the final recruiter report

## Possible Outcomes

**Genuine** — Resume appears to be authentic human-written content.

**Needs Review** — Some sections may be AI-generated or copied. Further investigation recommended.

**Suspicious** — Strong indicators that the resume is not a genuine representation of the candidate.

## Business Rules

- This validation builds on the Fraud Detection results
- Additional analysis is performed by the LLM (AI analysis engine) which reviews the fraud evidence in context
- The LLM considers the type and severity of each fraud signal
- The LLM makes a final determination about resume genuineness

## Information Stored

- Overall authenticity assessment
- Referenced fraud detection signals
- Specific sections of concern

## Contribution to Final Report

This validation gives the recruiter a high-level trust indicator for the resume. A "Suspicious" rating means the recruiter should approach the entire resume with skepticism and verify claims through other channels.

## Real-World Example

**Fraud detection results:** No signals detected

↓

System reviews content quality and consistency
↓
Writing style is natural and varied
↓
Claims are specific and verifiable
↓
Assessment: Genuine
↓
Recruiter sees: "Resume content appears genuine."

---

# 18. Project Validation

## Purpose

To evaluate the quality and substance of the candidate's project entries. This helps identify padded, generic, or boilerplate project descriptions that lack genuine content.

## Input

- Project entries extracted from the resume

## Validation Flow

Project entries are extracted
↓
System checks for generic or empty project descriptions
↓
System checks whether technologies are listed for each project
↓
System detects duplicate project names
↓
System assigns a validation status
↓
Result is added to the final recruiter report

## Possible Outcomes

**Verified** — All projects have meaningful descriptions and technologies listed.

**Warning** — Some projects have generic descriptions or are missing technologies.

**Failed** — Multiple generic or empty project entries found.

**Skipped** — No project entries exist on the resume.

## Business Rules

- If no projects exist → **Skipped**
- A project is considered generic if its name is fewer than 3 characters AND its description is fewer than 10 characters
- If 2 or more generic projects are found → **Fail**
- If any project has no technologies listed → **Warning**
- If duplicate project names are found → **Warning**
- If one project is generic but others are substantive → **Warning**

## Information Stored

- Number of projects
- Number of generic entries found
- Number of projects missing technology information
- List of duplicate project names

## Contribution to Final Report

Projects demonstrate practical application of skills. Generic or empty project entries reduce confidence in the candidate's actual experience. The report tells the recruiter which projects need elaboration.

## Real-World Example

**Candidate projects:**
1. "E-commerce Platform" — "Built a full-stack e-commerce platform using React, Node.js, MongoDB"
2. "Task Manager" — "Developed a task management application with real-time updates"

↓

System checks descriptions → Both meaningful (more than 10 characters)
↓
System checks technologies → Both have technologies listed
↓
System checks duplicates → None
↓
Status = Verified

**Candidate projects:**
1. "Project" — "Desc"
2. "Project" — "Desc"

↓

System checks descriptions → Both generic (name < 3 chars AND description < 10 chars)
↓
System checks duplicates → Duplicate names found
↓
2+ generic entries → Status = Failed
↓
Recruiter sees: "Project entries appear to be placeholders. Request detailed project information."

---

# 19. Location Validation

## Purpose

To verify the candidate's location information and ensure consistency between the location stated on the resume and the location from other sources (ATS, LinkedIn). This helps determine whether the candidate is in the right geographic region for the role.

## Input

- Location from the resume
- Location from LinkedIn (if available)
- Location from ATS (if available)

## Validation Flow

System extracts location from the resume
↓
System extracts location from LinkedIn (if available)
↓
System extracts location from ATS (if available)
↓
System compares location between available sources
↓
System assigns a validation status
↓
Result is added to the final recruiter report

## Possible Outcomes

**Verified** — Location is consistent across all available data sources.

**Warning** — Location could not be verified across sources, or no location was provided.

**Failed** — Location from the resume contradicts location from other sources.

**Skipped** — No location information available from any source.

## Business Rules

- If no location is provided anywhere → **Skipped**
- If resume location matches LinkedIn location → Consistent
- If resume location matches ATS location → Consistent
- If LinkedIn location matches ATS location → Consistent
- Inconsistencies between sources → Flagged
- The location is also used for determining role suitability (onsite vs. remote)

## Information Stored

- Location from resume
- Location from LinkedIn (if available)
- Location from ATS (if available)
- Whether locations match

## Contribution to Final Report

Location consistency helps the recruiter determine if the candidate is in the expected geographic area. A candidate who claims to be in New York on their resume but has a San Francisco location on LinkedIn may need clarification.

## Real-World Example

**Resume location:** San Francisco, CA
**LinkedIn location:** San Francisco Bay Area

↓

System compares → Locations match (same region)
↓
Status = Verified
↓
Recruiter sees: "Candidate location is consistent. Located in San Francisco Bay Area."

---

# 20. Contact Consistency Validation

## Purpose

To ensure the candidate's contact details are consistent across all sources and that there are no anomalies in how contact information is presented. This also checks for contact information appearing in unusual places.

## Input

- Email and phone from resume
- Email and phone from ATS (if available)
- Experience descriptions

## Validation Flow

System collects email from resume and ATS
↓
System collects phone from resume and ATS
↓
System compares email from resume with email from ATS
↓
System compares phone from resume with phone from ATS
↓
System checks whether the candidate's email appears inside their own experience descriptions
↓
System checks whether the candidate's phone appears inside their own experience descriptions
↓
System assigns a validation status
↓
Result is added to the final recruiter report

## Possible Outcomes

**Verified** — Contact information is consistent across all sources and no anomalies detected.

**Warning** — Contact information differs between sources, or email/phone appears in unusual places.

**Failed** — Significant contact inconsistencies detected.

**Skipped** — Insufficient data to compare.

## Business Rules

- If email differs between resume and ATS → Discrepancy flagged
- If phone differs between resume and ATS → Discrepancy flagged
- If the candidate's email appears in their employment descriptions → Flagged (may indicate the resume was scraped from another source)
- Each discrepancy is counted toward the cross-field validation score

## Information Stored

- Whether email is consistent between resume and ATS
- Whether phone is consistent between resume and ATS
- Whether the candidate's email was found in experience descriptions
- Whether the candidate's phone was found in experience descriptions

## Contribution to Final Report

Contact consistency is part of the broader identity verification. If a candidate's email appears inside a job description, it may suggest the resume was generated by scraping job postings rather than reflecting genuine experience. The report flags this for recruiter review.

## Real-World Example

**Resume email:** sarah.chen@email.com
**ATS email:** sarah.chen@email.com
**Resume phone:** +1 555 234 5678
**ATS phone:** +1 555 234 5678

↓

Email matches → Consistent
Phone matches → Consistent
Email not found in experience descriptions → Clean
↓
Status = Verified

---

# 21. Report Generation

## Purpose

To produce a comprehensive, branded HTML report that presents all validation evidence, scores, and recruiter recommendations in a clear, professional format. This is the final deliverable that the recruiter uses to make hiring decisions.

## Input

- All validation results from every validator
- LLM analysis (scores, recommendation, interview questions)
- Candidate information (name, email, phone, position)
- HTML report template

## Validation Flow

System receives all validation data and LLM analysis
↓
System loads the HTML report template
↓
System injects candidate information into the report
↓
System injects validation scores and risk level
↓
System injects each validation section with status and evidence
↓
System injects recruiter recommendations per validation
↓
System injects fraud detection evidence
↓
System injects company verification details
↓
System injects LinkedIn verification details
↓
System injects ATS verification details
↓
System injects cross-validation results
↓
System injects technical interview questions
↓
System renders the complete HTML report
↓
Report is uploaded to Azure Blob Storage
↓
A secure SAS URL is generated for the report
↓
The ATS record is updated with the report URL and validation status
↓
Result (blob ID and report URL) is returned

## Possible Outcomes

**Report Generated** — The HTML report was successfully created, uploaded to blob storage, and the ATS was updated.

**Report Generation Failed** — The report could not be generated due to an error in rendering, upload, or ATS update.

## Business Rules

- The report template always includes every validation, even if skipped
- Report is always uploaded as HTML to Azure Blob Storage
- A SAS (Shared Access Signature) URL is generated for secure time-limited access
- The ATS candidate record is updated with the report URL, validation status, and recommendation
- If the ATS update fails, the report is still generated and stored; the recruiter can access it via the blob URL

## Information Stored

- Complete HTML report in Azure Blob Storage
- Report metadata in ATS: report URL, blob ID, validation status, recommendation, timestamp
- SAS URL for recruiter access (time-limited)

## Contribution to Final Report

This is the final output of the entire validation pipeline. The report is the single source of truth for the recruiter, containing all validation evidence, scores, and recommendations in a professional format.

## Real-World Example

Validation Agent receives all evidence and LLM analysis
↓
Report Generator loads the template
↓
HTML is rendered with all data
↓
Report is uploaded to Azure Blob Storage
↓
SAS URL is generated: https://storage.blob.core.windows.net/reports/report-CUST-001-20260729.html?sv=...
↓
ATS is updated with report URL and status
↓
Recruiter can now access the report

---

# 22. Overall Candidate Scoring

## Purpose

To calculate a single, meaningful overall score that represents the candidate's validation quality. This score helps recruiters quickly compare candidates and prioritize their review pipeline.

## Input

- All individual validation results
- Fraud detection results
- Company verification results
- LinkedIn verification results

## Validation Flow

System collects all validation results
↓
System counts how many validations passed (Verified)
↓
System counts how many validations have warnings
↓
System counts how many validations failed
↓
System counts how many validations were skipped
↓
System calculates a validation score based on pass/fail rates
↓
System calculates a confidence score based on data quality
↓
System calculates a fraud score based on fraud signals detected
↓
System calculates a company score based on company verification
↓
System combines all scores into an overall score (0–100)
↓
System determines risk level based on the scores
↓
Result is added to the final recruiter report

## Possible Outcomes

**Score Range 80–100:** Strong candidate with minimal issues.

**Score Range 50–79:** Moderate issues found. Requires recruiter review.

**Score Range 0–49:** Significant issues found. Candidate may not be suitable.

## Business Rules

- Scores are calculated dynamically by the LLM based on the specific evidence
- Higher weight is placed on critical validations (employment, education, fraud)
- The fraud score is inverted: higher fraud signals = lower fraud score
- The overall score is a composite of all individual scores
- The LLM determines the weighting of each component based on the specific case

## Information Stored

- Overall score (0–100)
- Validation score (0–100)
- Confidence score (0–100)
- Fraud score (0–100)
- Company score (0–100)
- LinkedIn score (0–100)
- Risk level
- Count of passed, warning, failed, and skipped validations

## Contribution to Final Report

The overall score is prominently displayed at the top of the recruiter report. It serves as a quick-reference indicator of candidate quality. Recruiters can use this score to filter and prioritize candidates.

## Real-World Example

All validation results collected
↓
Validations: 12 passed, 2 warnings, 0 failed, 3 skipped
↓
Validation score: 85
↓
Confidence score: 90
↓
Fraud score: 95 (no fraud detected)
↓
Company score: 100 (company verified)
↓
Overall score: 88
↓
Risk level: Low
↓
Recruiter sees: "Overall Score: 88/100 — Low Risk"

---

# 23. Recommendation Generation

## Purpose

To provide a clear, actionable recommendation to the recruiter about whether the candidate should proceed in the hiring process. This distills all validation evidence into a single decision.

## Input

- Overall score
- All validation results
- Fraud detection results
- Executive summary

## Validation Flow

System collects all validation evidence and scores
↓
System evaluates the severity of any failures or warnings
↓
System considers fraud detection results
↓
System considers company verification results
↓
System considers cross-validation discrepancies
↓
System generates a recommendation
↓
System generates reasoning for the recommendation
↓
System generates suggested next steps for the recruiter
↓
Result is added to the final recruiter report

## Possible Outcomes

**CLEAR** — Strong candidate. No significant issues found. Candidate is recommended to proceed.

**REVIEW** — Some issues found that require recruiter judgment. Candidate may proceed with caution.

**REJECT** — Critical issues found. Candidate should not proceed in the hiring process.

## Business Rules

- If no validations failed and no significant warnings → **CLEAR**
- If some validations failed or there are significant warnings → **REVIEW**
- If critical validations failed (fraud, identity, cross-validation) → **REJECT**
- The LLM determines the final recommendation based on all evidence
- Every recommendation includes reasoning explaining why it was made
- Suggested next steps are provided for the recruiter

## Information Stored

- Recommendation (CLEAR, REVIEW, or REJECT)
- Recommendation reasoning
- Executive summary
- Candidate strengths
- Candidate weaknesses
- Suggested next steps
- Risk analysis

## Contribution to Final Report

The recommendation appears at the top of the report alongside the overall score. It gives the recruiter immediate guidance on how to proceed with the candidate.

## Real-World Example

Scores and evidence evaluated
↓
Results: All validations passed, no fraud detected, company verified
↓
Recommendation: CLEAR
↓
Reasoning: "Candidate has a consistent profile across all sources. No discrepancies or fraud indicators found. Employment history is verifiable."
↓
Recruiter sees: "Recommendation: CLEAR — Proceed with interview."

---

# 24. Blob Report Storage

## Purpose

To securely store the generated HTML report in Azure Blob Storage so it can be accessed by recruiters at any time and shared with stakeholders.

## Input

- Generated HTML report
- Candidate ID
- Generation timestamp

## Validation Flow

HTML report is generated
↓
System creates a unique blob ID: report-{candidate_id}-{timestamp}.html
↓
System uploads the HTML to Azure Blob Storage
↓
System sets content type to text/html
↓
System stores metadata: candidate_id, generated_at
↓
System verifies the upload was successful
↓
System generates a SAS (Shared Access Signature) URL for secure access
↓
System returns the blob URL
↓
Result is passed back to the report generation process

## Possible Outcomes

**Stored Successfully** — Report was uploaded and verified in blob storage. SAS URL generated.

**Storage Failed** — Report could not be uploaded due to connectivity or authentication issues.

## Business Rules

- The blob ID is unique per report (includes candidate ID and timestamp)
- Reports are stored as HTML files with text/html content type
- The upload is verified by checking blob properties after upload
- SAS URLs expire after a configurable number of hours (default: 24 hours)
- If upload fails, the report generation process returns an error

## Information Stored

- HTML report file in Azure Blob Storage
- Blob metadata: candidate_id, generated_at
- SAS URL for time-limited access

## Contribution to Final Report

Blob storage makes the report persistently available. The SAS URL ensures secure access without making the report publicly accessible. Recruiters can share the SAS URL with stakeholders.

## Real-World Example

Report generated (HTML, 45KB)
↓
Blob ID: report-CUST-001-20260729143022.html
↓
Uploading to Azure Blob Storage...
↓
Upload verified → Success
↓
SAS URL generated with 24-hour expiry
↓
Recruiter can access report via the secure link

---

# 25. Recruiter Report Retrieval

## Purpose

To allow recruiters to retrieve validation reports for review, comparison, and sharing. Multiple retrieval methods are available to support different workflows.

## Input

- Candidate ID (to get the latest report)
- Blob ID (to get a specific report)
- Search criteria (to find reports by name, status, recommendation, date range)

## Validation Flow

Recruiter requests a report
↓
System accepts the retrieval request
↓

**Option A: Get Latest Report by Candidate ID**
↓
System looks up the candidate in the ATS
↓
System retrieves the stored report URL or blob ID
↓
System generates a fresh SAS URL (if needed)
↓
System returns the report URL

**Option B: Get Report by Blob ID**
↓
System uses the blob ID to generate a SAS URL
↓
System returns the report URL

**Option C: Search Reports**
↓
System lists all candidates from the ATS
↓
System filters by search criteria (name, status, recommendation, etc.)
↓
System returns matching reports with their URLs

↓
Recruiter receives the report URL(s)

## Possible Outcomes

**Report Found** — The requested report exists and a URL is returned.

**Report Not Found** — No report exists for the given candidate ID or blob ID.

**Search Results Returned** — Matching reports are listed with their URLs.

## Business Rules

- If a candidate has a stored report URL, it is returned directly
- If only a blob ID is stored, a fresh SAS URL is generated
- SAS URLs are time-limited (default 24-hour expiry)
- Search supports filtering by candidate ID, name, recommendation, validation status, and date range
- Results are paginated

## Information Stored

- Report URL (SAS URL or permanent blob URL)
- Blob ID
- Generation timestamp
- Candidate ID
- Validation status (from ATS)
- Recommendation (from ATS)

## Contribution to Final Report

Report retrieval is the mechanism by which recruiters access the validation results. Without this, the report would be trapped in storage. Multiple retrieval methods ensure the report is accessible regardless of how the recruiter searches for it.

## Real-World Example

Recruiter searches for "Sarah Chen"
↓
System finds candidate CUST-001
↓
Latest report retrieved
↓
Report URL returned: https://storage.blob.core.windows.net/reports/report-CUST-001-20260729.html?sv=...
↓
Recruiter clicks the link and views the full validation report

---

# Complete End-to-End Functional Workflow

```
Resume Uploaded (by recruiter or candidate)
    ↓
Resume Text Extracted (from PDF, DOCX, or pasted text)
    ↓
Resume Normalized (structured candidate profile created)
    ↓
Candidate Information Identified (name, email, phone, skills, experience, etc.)
    ↓
    ├── Resume Completeness Validation
    ├── Email Validation (format, domain, DNS, disposable check)
    ├── Phone Validation (format, country, number type)
    ├── Education Validation (dates, completeness, duplicates)
    ├── Employment Validation (company, title, dates, duplicates)
    ├── Experience Validation (total years, progression, breadth)
    ├── Employment Timeline Validation (gaps, overlaps, future dates)
    ├── Employment Pattern Validation (tenure, job-hopping, stability)
    ├── Skills Validation (count, density, project alignment)
    ├── Certification Validation (name, issuer, date reasonableness)
    ├── Project Validation (description quality, technologies, duplicates)
    ├── Company Verification (website, DNS, SSL, reachability)
    ├── LinkedIn Verification (profile, name match, employer match)
    ├── ATS Candidate Verification (existing record, previous report)
    ├── Identity Consistency Validation (cross-source name/email/phone)
    ├── Contact Consistency Validation (email/phone across sources)
    ├── Location Validation (resume vs LinkedIn vs ATS)
    ├── Duplicate Candidate Check (existing email/phone in system)
    ├── Resume Genuineness Check (fraud signals, authenticity)
    └── Fraud Detection (keyword stuffing, AI generation, templates)
            ↓
    All validation evidence collected
            ↓
    LLM Analysis of Validation Evidence
            ↓
    Overall Score Calculation (0–100)
            ↓
    Recruiter Recommendation (CLEAR / REVIEW / REJECT)
            ↓
    Executive Summary & Interview Questions Generated
            ↓
    Recruiter Report Generated (HTML format)
            ↓
    HTML Report Stored in Azure Blob Storage
            ↓
    Secure SAS URL Generated
            ↓
    ATS Record Updated with Report URL and Validation Status
            ↓
    Report Available to Recruiter
            ↓
    Recruiter Reviews Report and Takes Action
```

---

*End of Functional Specification Document*
