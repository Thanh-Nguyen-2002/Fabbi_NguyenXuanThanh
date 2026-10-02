import pytest
from httpx import AsyncClient


async def register_and_get_token(client: AsyncClient, email: str, password: str) -> str:
    """Register a new user and return the access token."""
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password},
    )
    assert response.status_code == 201
    return response.json()["access_token"]


async def create_todo(client: AsyncClient, token: str, title: str, description: str = "") -> dict:
    """Helper to create a todo item and return its JSON payload."""
    payload: dict = {"title": title}
    if description:
        payload["description"] = description
    response = await client.post(
        "/api/v1/todos",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201
    return response.json()


@pytest.mark.asyncio
async def test_user_cannot_read_other_users_todo(client: AsyncClient):
    """User B should receive 403 when trying to GET a todo owned by User A."""
    token_a = await register_and_get_token(client, "user_a_read@example.com", "PasswordA1!")
    token_b = await register_and_get_token(client, "user_b_read@example.com", "PasswordB1!")

    todo_a = await create_todo(client, token_a, "User A's secret todo")
    todo_id = todo_a["id"]

    response = await client.get(
        f"/api/v1/todos/{todo_id}",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_user_cannot_update_other_users_todo(client: AsyncClient):
    """User B should receive 403 when trying to PUT a todo owned by User A."""
    token_a = await register_and_get_token(client, "user_a_update@example.com", "PasswordA1!")
    token_b = await register_and_get_token(client, "user_b_update@example.com", "PasswordB1!")

    todo_a = await create_todo(client, token_a, "User A's todo to update")
    todo_id = todo_a["id"]

    response = await client.put(
        f"/api/v1/todos/{todo_id}",
        json={"title": "Hijacked title"},
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_user_cannot_delete_other_users_todo(client: AsyncClient):
    """User B should receive 403 when trying to DELETE a todo owned by User A."""
    token_a = await register_and_get_token(client, "user_a_delete@example.com", "PasswordA1!")
    token_b = await register_and_get_token(client, "user_b_delete@example.com", "PasswordB1!")

    todo_a = await create_todo(client, token_a, "User A's todo to delete")
    todo_id = todo_a["id"]

    response = await client.delete(
        f"/api/v1/todos/{todo_id}",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_user_can_only_see_own_todos(client: AsyncClient):
    """User A's todo list should contain exactly their own todos, not User B's."""
    token_a = await register_and_get_token(client, "user_a_list@example.com", "PasswordA1!")
    token_b = await register_and_get_token(client, "user_b_list@example.com", "PasswordB1!")

    await create_todo(client, token_a, "User A todo 1")
    await create_todo(client, token_a, "User A todo 2")
    await create_todo(client, token_b, "User B todo 1")

    response = await client.get(
        "/api/v1/todos",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert len(data["items"]) == 2


@pytest.mark.asyncio
async def test_toggle_completed_back_to_false(client: AsyncClient):
    """Updating completed=True then completed=False should result in completed == False."""
    token = await register_and_get_token(client, "toggle_user@example.com", "Password1!")
    todo = await create_todo(client, token, "Toggle me")
    todo_id = todo["id"]

    # Set completed to True
    response = await client.put(
        f"/api/v1/todos/{todo_id}",
        json={"completed": True},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["completed"] is True

    # Set completed back to False
    response = await client.put(
        f"/api/v1/todos/{todo_id}",
        json={"completed": False},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["completed"] is False


@pytest.mark.asyncio
async def test_partial_update_does_not_erase_description(client: AsyncClient):
    """Updating only the title should leave the description unchanged."""
    token = await register_and_get_token(client, "partial_update_user@example.com", "Password1!")
    original_description = "This description must survive"
    todo = await create_todo(client, token, "Original title", description=original_description)
    todo_id = todo["id"]

    # Update only the title, omitting description
    response = await client.put(
        f"/api/v1/todos/{todo_id}",
        json={"title": "Updated title"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    updated = response.json()
    assert updated["title"] == "Updated title"
    assert updated["description"] == original_description
