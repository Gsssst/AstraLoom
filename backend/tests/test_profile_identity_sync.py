"""Regression tests for profile identity synchronization."""

from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.api.auth import get_me


@pytest.mark.asyncio
async def test_current_user_response_restores_visible_profile_identity():
    avatar = "data:image/png;base64,cHJvZmlsZQ=="
    user = SimpleNamespace(
        id=uuid4(),
        username="researcher",
        email="researcher@example.com",
        role="user",
        is_active=True,
        avatar=avatar,
        display_name="Researcher Name",
    )

    response = await get_me(current_user=user)

    assert response.avatar == avatar
    assert response.display_name == "Researcher Name"
