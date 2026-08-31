import pytest

from app.services.company_discovery import (
    BLOCKLIST,
    discover_and_verify_company,
    domain_matches_company,
    extract_domain,
    is_valid_candidate,
    normalize_company_name,
)


def test_normalize_company_name():
    assert normalize_company_name("IGOLD Technologies Pvt Ltd") == "igold"
    assert normalize_company_name("Tech Mahindra Limited") == "tech mahindra"
    assert normalize_company_name("Google Inc.") == "google"
    assert normalize_company_name("Concentrix Catalyst") == "concentrix catalyst"


def test_extract_domain():
    assert extract_domain("https://www.techmahindra.com/en-in/") == "techmahindra.com"
    assert extract_domain("http://google.com/search") == "google.com"
    assert extract_domain("https://sub.example.co.in/path") == "sub.example.co.in"
    assert extract_domain("") is None


def test_is_valid_candidate():
    assert is_valid_candidate("techmahindra.com") is True
    assert is_valid_candidate("google.com") is False
    assert is_valid_candidate("in.linkedin.com") is False
    assert is_valid_candidate("glassdoor.com") is False
    assert is_valid_candidate("www.wikipedia.org") is False


def test_domain_matches_company():
    assert domain_matches_company("techmahindra.com", "Tech Mahindra") is True
    assert domain_matches_company("concentrix.com", "Concentrix Catalyst") is True
    assert domain_matches_company("igoldtech.com", "IGOLD Technologies Pvt Ltd") is True
    assert domain_matches_company("randomsite.org", "Tech Mahindra") is False


@pytest.mark.asyncio
async def test_discover_known_company():
    result = await discover_and_verify_company("Tech Mahindra")
    assert result["status"] in ("VERIFIED", "PARTIALLY_VERIFIED")
    assert result["website"] is not None
    assert "techmahindra" in result["website"]
    assert result["confidence"] >= 0.3
    assert result["source"] == "search"
    assert "checks" in result


@pytest.mark.asyncio
async def test_discover_concentrix():
    result = await discover_and_verify_company("Concentrix Catalyst")
    assert result["status"] in ("VERIFIED", "PARTIALLY_VERIFIED")
    assert result["website"] is not None
    assert "concentrix" in result["website"]


@pytest.mark.asyncio
async def test_discover_empty_company():
    result = await discover_and_verify_company("")
    assert result["status"] == "UNVERIFIED"
    assert result["website"] is None
    assert result["confidence"] == 0.0


@pytest.mark.asyncio
async def test_discover_fake_company():
    result = await discover_and_verify_company("FakeCoNonExistentXYZ987654321")
    assert result["status"] == "UNVERIFIED"
    assert result["website"] is None
