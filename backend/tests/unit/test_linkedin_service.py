import pytest
import respx
import httpx
from app.core.config import Settings
from app.domain.models import ResumeData, LinkedInData, ValidationStatus
from app.services.linkedin_service import LinkedInService, BROWSER_HEADERS
from app.services.validators.linkedin_validator import LinkedInValidator


@pytest.fixture
def settings():
    return Settings(linkedin_timeout=2)


@pytest.fixture
def linkedin_service(settings):
    return LinkedInService(settings)


@pytest.mark.asyncio
async def test_empty_url(linkedin_service):
    res = await linkedin_service.verify_profile(None)
    assert res.profile_url is None
    assert res.username is None
    assert res.profile_exists is False
    assert res.valid is False
    assert res.status_code == 0

    res_empty = await linkedin_service.verify_profile("   ")
    assert res_empty.profile_exists is False
    assert res_empty.valid is False
    assert res_empty.status_code == 0


@pytest.mark.asyncio
@respx.mock
async def test_head_success_200(linkedin_service):
    url = "https://www.linkedin.com/in/johndoe"
    head_route = respx.head(url).mock(return_value=httpx.Response(200))
    get_route = respx.get(url).mock(return_value=httpx.Response(200))

    res = await linkedin_service.verify_profile(url)

    assert head_route.called
    assert not get_route.called  # HEAD succeeded with 200, so GET is NOT needed
    assert res.profile_url == url
    assert res.username == "johndoe"
    assert res.profile_exists is True
    assert res.valid is True
    assert res.status_code == 200


@pytest.mark.asyncio
@respx.mock
async def test_redirect_301(linkedin_service):
    url = "https://www.linkedin.com/in/johndoe"
    respx.head(url).mock(return_value=httpx.Response(301))

    res = await linkedin_service.verify_profile(url)

    assert res.profile_exists is True
    assert res.valid is True
    assert res.status_code == 301


@pytest.mark.asyncio
@respx.mock
async def test_head_999_fallback_to_get_200(linkedin_service):
    url = "https://www.linkedin.com/in/johndoe"
    head_route = respx.head(url).mock(return_value=httpx.Response(999))
    get_route = respx.get(url).mock(return_value=httpx.Response(200))

    res = await linkedin_service.verify_profile(url)

    assert head_route.called
    assert get_route.called  # Fallback to GET occurred
    assert res.profile_exists is True
    assert res.valid is True
    assert res.status_code == 200


@pytest.mark.asyncio
@respx.mock
async def test_head_999_fallback_to_get_still_999(linkedin_service):
    url = "https://www.linkedin.com/in/johndoe"
    head_route = respx.head(url).mock(return_value=httpx.Response(999))
    get_route = respx.get(url).mock(return_value=httpx.Response(999))

    res = await linkedin_service.verify_profile(url)

    assert head_route.called
    assert get_route.called  # Fallback to GET occurred
    # When still 999: treat as "reachable but blocked", profile_exists=True, valid=True, status_code=999
    assert res.profile_exists is True
    assert res.valid is True
    assert res.status_code == 999


@pytest.mark.asyncio
@respx.mock
async def test_head_404_not_found(linkedin_service):
    url = "https://www.linkedin.com/in/nonexistentuser"
    head_route = respx.head(url).mock(return_value=httpx.Response(404))
    get_route = respx.get(url).mock(return_value=httpx.Response(404))

    res = await linkedin_service.verify_profile(url)

    assert head_route.called
    assert not get_route.called  # 404 from HEAD is definitive
    assert res.profile_exists is False
    assert res.valid is False
    assert res.status_code == 404


@pytest.mark.asyncio
@respx.mock
async def test_head_error_fallback_to_get(linkedin_service):
    url = "https://www.linkedin.com/in/johndoe"
    head_route = respx.head(url).mock(return_value=httpx.Response(405))
    get_route = respx.get(url).mock(return_value=httpx.Response(200))

    res = await linkedin_service.verify_profile(url)

    assert head_route.called
    assert get_route.called
    assert res.profile_exists is True
    assert res.valid is True
    assert res.status_code == 200


@pytest.mark.asyncio
async def test_linkedin_validator():
    validator = LinkedInValidator()
    resume = ResumeData(name="Jane Doe")

    # 1. Skipped when no url
    evidence_none = await validator.validate(resume, LinkedInData())
    assert evidence_none.status == ValidationStatus.SKIPPED

    # 2. Passed for 200
    evidence_200 = await validator.validate(
        resume,
        LinkedInData(profile_url="https://linkedin.com/in/jane", username="jane", profile_exists=True, valid=True, status_code=200)
    )
    assert evidence_200.status == ValidationStatus.PASSED

    # 3. Passed for 999 reachable
    evidence_999 = await validator.validate(
        resume,
        LinkedInData(profile_url="https://linkedin.com/in/jane", username="jane", profile_exists=True, valid=True, status_code=999)
    )
    assert evidence_999.status == ValidationStatus.PASSED

    # 4. Failed for 404
    evidence_404 = await validator.validate(
        resume,
        LinkedInData(profile_url="https://linkedin.com/in/jane", username="jane", profile_exists=False, valid=False, status_code=404)
    )
    assert evidence_404.status == ValidationStatus.FAILED
