import uuid
from datetime import timedelta

import pytest
from httpx import AsyncClient

from app.core.security import create_access_token, create_refresh_token


async def register_and_get_token(client: AsyncClient, email: str, password: str) -> str:
    """Register a new user and return the access token."""
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password},
    )
    assert response.status_code == 201
    return response.json()["access_token"]


@pytest.mark.asyncio
async def test_expired_token_is_rejected(client: AsyncClient):
    """A token that has already expired should be rejected with 401."""
    expired_token = create_access_token(
        data={"sub": str(uuid.uuid4())},
        expires_delta=timedelta(seconds=-1),
    )
    response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {expired_token}"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_tampered_token_is_rejected(client: AsyncClient):
    """A valid token with extra characters appended should be rejected with 401."""
    email = "tampered@example.com"
    token = await register_and_get_token(client, email, "Password123!")

    tampered_token = token + "tampered"
    response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {tampered_token}"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_refresh_token_cannot_be_used_as_access_token(client: AsyncClient):
    """A refresh token must not be accepted where an access token is required."""
    user_id = str(uuid.uuid4())
    refresh_token = create_refresh_token(data={"sub": user_id})

    response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {refresh_token}"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_login_with_wrong_email_returns_401_not_404(client: AsyncClient):
    """Login with a non-existent email should return 401, not 404 (prevent user enumeration)."""
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "nonexistent@example.com", "password": "SomePassword1!"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_login_with_wrong_password_returns_same_error(client: AsyncClient):
    """Login with a correct email but wrong password should return 401 with the same message
    as a non-existent email, to prevent user enumeration attacks."""
    email = "realuser@example.com"
    password = "CorrectPassword1!"
    await register_and_get_token(client, email, password)

    wrong_email_response = await client.post(
        "/api/v1/auth/login",
        json={"email": "nonexistent@example.com", "password": "WrongPassword1!"},
    )

    wrong_password_response = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "WrongPassword1!"},
    )

    assert wrong_password_response.status_code == 401
    assert wrong_password_response.json()["detail"] == wrong_email_response.json()["detail"]
