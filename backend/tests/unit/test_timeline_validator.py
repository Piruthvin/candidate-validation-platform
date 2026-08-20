"""Unit tests for TimelineValidator.

Covers:
  - timezone-aware dates
  - timezone-naive dates
  - mixed timezone inputs
  - invalid dates
  - future employment
  - overlapping employment
  - current employment
  - validator never raises
"""

import pytest

from app.domain.models import ResumeData, ResumeExperience
from app.services.validators.timeline_validator import TimelineValidator, _normalize_datetime


# ── _normalize_datetime unit tests ──────────────────────────────────────────


def test_normalize_yyyymmdd():
    dt = _normalize_datetime("2023-01-15")
    assert dt is not None
    assert dt.tzinfo is not None
    assert dt.year == 2023
    assert dt.month == 1
    assert dt.day == 15
    assert dt.hour == 0
    assert dt.minute == 0


def test_normalize_iso_no_tz():
    dt = _normalize_datetime("2023-01-15T10:30:00")
    assert dt is not None
    assert dt.tzinfo is not None
    assert dt.hour == 10


def test_normalize_iso_with_z():
    dt = _normalize_datetime("2023-01-15T10:30:00Z")
    assert dt is not None
    assert dt.tzinfo is not None
    assert dt.hour == 10


def test_normalize_iso_with_offset():
    dt = _normalize_datetime("2023-01-15T10:30:00+05:00")
    assert dt is not None
    assert dt.tzinfo is not None
    # offset should be preserved as +05:00, NOT re-UTC'd
    assert dt.utcoffset().total_seconds() == 5 * 3600


def test_normalize_invalid():
    assert _normalize_datetime("") is None
    assert _normalize_datetime(None) is None
    assert _normalize_datetime("not-a-date") is None
    assert _normalize_datetime("2023-13-01") is None
    assert _normalize_datetime("2023-00-01") is None


def test_normalize_whitespace():
    dt = _normalize_datetime("  2023-06-15  ")
    assert dt is not None
    assert dt.year == 2023


# ── full validator tests ────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_validator_never_raises():
    """No input should cause validate() to raise."""
    validator = TimelineValidator()
    cases = [
        ResumeData(),
        ResumeData(experience=[ResumeExperience(company="X", title="Y", start_date="invalid", end_date="also-invalid")]),
        ResumeData(experience=[ResumeExperience(company="X", title="Y", start_date=None, end_date=None)]),
        ResumeData(experience=[ResumeExperience(company="X", title="Y", start_date="2023-01-01", end_date="not-a-date")]),
        ResumeData(experience=[ResumeExperience(company="X", title="Y", start_date="", end_date="")]),
    ]
    for resume in cases:
        result = await validator.validate(resume)
        assert result is not None
        assert result.status in ("PASSED", "FAILED", "WARNING", "SKIPPED")


@pytest.mark.asyncio
async def test_empty_experience():
    validator = TimelineValidator()
    result = await validator.validate(ResumeData())
    assert result.status == "SKIPPED"


@pytest.mark.asyncio
async def test_timezone_aware_dates():
    """UTC+ and UTC- offsets should compare correctly."""
    validator = TimelineValidator()
    resume = ResumeData(experience=[
        ResumeExperience(company="A", title="Eng", start_date="2020-01-01T00:00:00+00:00", end_date="2022-06-01T00:00:00+00:00"),
        ResumeExperience(company="B", title="Eng", start_date="2022-06-15T00:00:00+00:00", end_date="2024-01-01T00:00:00+00:00"),
    ])
    result = await validator.validate(resume)
    assert result.status in ("PASSED", "WARNING")
    assert result.details["overlaps_detected"] is False


@pytest.mark.asyncio
async def test_timezone_naive_dates():
    """Plain YYYY-MM-DD strings should work."""
    validator = TimelineValidator()
    resume = ResumeData(experience=[
        ResumeExperience(company="A", title="Eng", start_date="2020-01-01", end_date="2022-06-01"),
        ResumeExperience(company="B", title="Eng", start_date="2022-06-15", end_date="2024-01-01"),
    ])
    result = await validator.validate(resume)
    assert result.status in ("PASSED", "WARNING")
    assert result.details["overlaps_detected"] is False


@pytest.mark.asyncio
async def test_mixed_timezone_inputs():
    """Mixing naive and aware dates must NOT crash."""
    validator = TimelineValidator()
    resume = ResumeData(experience=[
        ResumeExperience(company="A", title="Eng", start_date="2020-01-01", end_date="2022-06-01T00:00:00Z"),
        ResumeExperience(company="B", title="Eng", start_date="2022-06-15T00:00:00+00:00", end_date="2024-01-01"),
    ])
    result = await validator.validate(resume)
    assert result.status in ("PASSED", "WARNING", "FAILED")
    assert result.details["entries_with_dates"] == 2


@pytest.mark.asyncio
async def test_invalid_dates_skipped():
    """Bad dates should be silently skipped, not crash."""
    validator = TimelineValidator()
    resume = ResumeData(experience=[
        ResumeExperience(company="A", title="Eng", start_date="bad-date", end_date="also-bad"),
        ResumeExperience(company="B", title="Eng", start_date="2020-01-01", end_date="2022-06-01"),
    ])
    result = await validator.validate(resume)
    assert result.details["entries_with_dates"] == 1


@pytest.mark.asyncio
async def test_future_employment():
    """Future end dates should be flagged."""
    validator = TimelineValidator()
    resume = ResumeData(experience=[
        ResumeExperience(company="FutureCorp", title="Eng", start_date="2020-01-01", end_date="2099-12-31"),
    ])
    result = await validator.validate(resume)
    assert result.details["future_end_dates"] > 0
    assert result.status == "FAILED"


@pytest.mark.asyncio
async def test_overlapping_employment():
    """Overlapping dates should be detected."""
    validator = TimelineValidator()
    resume = ResumeData(experience=[
        ResumeExperience(company="A", title="Eng", start_date="2020-01-01", end_date="2023-06-01"),
        ResumeExperience(company="B", title="Eng", start_date="2022-01-01", end_date="2024-01-01"),
    ])
    result = await validator.validate(resume)
    assert result.details["overlaps_detected"] is True
    assert result.details["overlap_count"] > 0
    assert result.status == "FAILED"


@pytest.mark.asyncio
async def test_current_employment():
    """Employment with no end date (or very future date) handled gracefully."""
    validator = TimelineValidator()
    resume = ResumeData(experience=[
        ResumeExperience(company="CurrentCo", title="Eng", start_date="2020-01-01", end_date="2099-12-31"),
    ])
    result = await validator.validate(resume)
    assert result.details["future_end_dates"] > 0
    assert result.status == "FAILED"


@pytest.mark.asyncio
async def test_valid_timeline_passes():
    """Non-overlapping, non-future, no-gap timeline passes."""
    validator = TimelineValidator()
    resume = ResumeData(experience=[
        ResumeExperience(company="A", title="Eng", start_date="2020-01-01", end_date="2021-12-31"),
        ResumeExperience(company="B", title="Eng", start_date="2022-01-01", end_date="2023-06-30"),
    ])
    result = await validator.validate(resume)
    assert result.status == "PASSED"
    assert result.details["overlaps_detected"] is False
    assert result.details["future_end_dates"] == 0
    assert result.details["gaps_found"] == 0


@pytest.mark.asyncio
async def test_gap_detected():
    """Gaps > 6 months should be flagged as warning."""
    validator = TimelineValidator()
    resume = ResumeData(experience=[
        ResumeExperience(company="A", title="Eng", start_date="2020-01-01", end_date="2021-01-01"),
        ResumeExperience(company="B", title="Eng", start_date="2022-06-01", end_date="2023-01-01"),
    ])
    result = await validator.validate(resume)
    assert result.details["gaps_found"] > 0
    assert result.status == "WARNING"


@pytest.mark.asyncio
async def test_naive_with_future():
    """Naive date that is in the future (no tz) should still be caught."""
    validator = TimelineValidator()
    resume = ResumeData(experience=[
        ResumeExperience(company="FutureCo", title="Eng", start_date="2020-01-01", end_date="2099-12-31"),
    ])
    result = await validator.validate(resume)
    assert result.details["future_end_dates"] > 0
