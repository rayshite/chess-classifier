"""
Интеграционные тесты для API пользователей
"""

import time

import pytest
from httpx import AsyncClient

from models import User


async def login_user(client: AsyncClient, email: str, password: str) -> str:
    """Вспомогательная функция для входа и получения cookie."""
    response = await client.post(
        "/api/auth/login",
        data={"username": email, "password": password}
    )
    assert response.status_code == 204, f"Login failed: {response.text}"
    return response.cookies.get("auth")


def unique_email(prefix: str) -> str:
    """Генерирует уникальный email для теста."""
    return f"{prefix}_{int(time.time() * 1000)}@example.com"


async def create_user(
    client: AsyncClient,
    auth_cookie: str,
    name: str,
    email: str,
    role: str = "student"
) -> dict:
    """Создаёт пользователя и возвращает его данные."""
    response = await client.post(
        "/api/users",
        json={"name": name, "email": email, "role": role},
        cookies={"auth": auth_cookie}
    )
    assert response.status_code == 200, f"Failed to create user: {response.text}"
    return response.json()


async def delete_user(client: AsyncClient, auth_cookie: str, user_id: int):
    """Удаляет пользователя (деактивирует)."""
    await client.patch(
        f"/api/users/{user_id}",
        json={"isActive": False},
        cookies={"auth": auth_cookie}
    )


class TestUsers:
    """Тесты API пользователей."""

    @pytest.mark.asyncio(loop_scope="session")
    async def test_user_01_admin_creates_user(
        self,
        client: AsyncClient,
        admin_user: User,
    ):
        """
        USER-01: Админ создаёт пользователя.

        Тип: Позитивный
        Приоритет: Средний
        """
        auth_cookie = await login_user(client, admin_user.email, "adminpass123")
        email = unique_email("newstudent")

        response = await client.post(
            "/api/users",
            json={
                "name": "New Student",
                "email": email,
                "role": "student"
            },
            cookies={"auth": auth_cookie}
        )

        assert response.status_code == 200, (
            f"Ожидался статус 200, получен {response.status_code}. "
            f"Тело ответа: {response.text}"
        )

        data = response.json()
        assert "id" in data
        assert data["name"] == "New Student"
        assert data["email"] == email
        assert data["role"] == "student"
        assert "temporaryPassword" in data
        assert len(data["temporaryPassword"]) == 10

        await delete_user(client, auth_cookie, data["id"])

    @pytest.mark.asyncio(loop_scope="session")
    async def test_user_01_admin_creates_teacher(
        self,
        client: AsyncClient,
        admin_user: User,
    ):
        """
        USER-01: Админ создаёт учителя.
        """
        auth_cookie = await login_user(client, admin_user.email, "adminpass123")
        email = unique_email("newteacher")

        # Act
        response = await client.post(
            "/api/users",
            json={
                "name": "New Teacher",
                "email": email,
                "role": "teacher"
            },
            cookies={"auth": auth_cookie}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["role"] == "teacher"

        await delete_user(client, auth_cookie, data["id"])

    @pytest.mark.asyncio(loop_scope="session")
    async def test_user_01_duplicate_email_fails(
        self,
        client: AsyncClient,
        admin_user: User,
        test_user: User,
    ):
        """
        USER-01 (негативный): Нельзя создать пользователя с существующим email.
        """
        auth_cookie = await login_user(client, admin_user.email, "adminpass123")

        response = await client.post(
            "/api/users",
            json={
                "name": "Duplicate User",
                "email": test_user.email,
                "role": "student"
            },
            cookies={"auth": auth_cookie}
        )

        assert response.status_code == 400

    @pytest.mark.asyncio(loop_scope="session")
    async def test_user_02_student_cannot_access_users_list(
        self,
        client: AsyncClient,
        test_user: User,
    ):
        """
        USER-02: Ученик пытается зайти на /api/users/.

        Тип: Негативный
        Приоритет: Высокий
        """
        auth_cookie = await login_user(client, test_user.email, "testpassword123")

        response = await client.get(
            "/api/users",
            cookies={"auth": auth_cookie}
        )

        assert response.status_code == 403, (
            f"Ожидался статус 403, получен {response.status_code}. "
            f"Тело ответа: {response.text}"
        )


    @pytest.mark.asyncio(loop_scope="session")
    async def test_user_02_teacher_cannot_access_users_list(
        self,
        client: AsyncClient,
        teacher_user: User,
    ):
        """
        USER-02: Учитель тоже не имеет доступа к /api/users/.
        """
        auth_cookie = await login_user(client, teacher_user.email, "teacherpass123")

        response = await client.get(
            "/api/users",
            cookies={"auth": auth_cookie}
        )

        assert response.status_code == 403


    @pytest.mark.asyncio(loop_scope="session")
    async def test_user_03_admin_changes_user_role(
        self,
        client: AsyncClient,
        admin_user: User,
    ):
        """
        USER-03: Админ меняет роль пользователя.

        Тип: Позитивный
        Приоритет: Средний
        """
        auth_cookie = await login_user(client, admin_user.email, "adminpass123")
        email = unique_email("rolechange")

        user = await create_user(client, auth_cookie, "Role Change Test", email, "student")

        response = await client.patch(
            f"/api/users/{user['id']}",
            json={"role": "teacher"},
            cookies={"auth": auth_cookie}
        )

        assert response.status_code == 200
        assert response.json()["role"] == "teacher"

        await delete_user(client, auth_cookie, user["id"])

    @pytest.mark.asyncio(loop_scope="session")
    async def test_user_03_admin_deactivates_user(
        self,
        client: AsyncClient,
        admin_user: User,
    ):
        """
        USER-03: Админ деактивирует пользователя.
        """
        auth_cookie = await login_user(client, admin_user.email, "adminpass123")
        email = unique_email("deactivate")

        user = await create_user(client, auth_cookie, "Deactivate Test", email, "student")

        response = await client.patch(
            f"/api/users/{user['id']}",
            json={"isActive": False},
            cookies={"auth": auth_cookie}
        )

        assert response.status_code == 200
        assert response.json()["isActive"] is False

    @pytest.mark.asyncio(loop_scope="session")
    async def test_admin_gets_users_list(
        self,
        client: AsyncClient,
        admin_user: User,
    ):
        """
        Админ может получить список пользователей.
        """
        auth_cookie = await login_user(client, admin_user.email, "adminpass123")

        response = await client.get(
            "/api/users",
            cookies={"auth": auth_cookie}
        )

        assert response.status_code == 200
        data = response.json()
        assert "users" in data
        assert "pagination" in data
        assert data["pagination"]["totalCount"] >= 1

    @pytest.mark.asyncio(loop_scope="session")
    async def test_admin_gets_users_filtered_by_role(
        self,
        client: AsyncClient,
        admin_user: User,
    ):
        """
        Админ может фильтровать пользователей по роли.
        """
        auth_cookie = await login_user(client, admin_user.email, "adminpass123")

        response = await client.get(
            "/api/users?role=student",
            cookies={"auth": auth_cookie}
        )

        assert response.status_code == 200
        data = response.json()
        for user in data["users"]:
            assert user["role"] == "student"

    @pytest.mark.asyncio(loop_scope="session")
    async def test_get_current_user(
        self,
        client: AsyncClient,
        test_user: User,
    ):
        """
        Любой авторизованный пользователь может получить свои данные.
        """
        auth_cookie = await login_user(client, test_user.email, "testpassword123")

        response = await client.get(
            "/api/users/current_user",
            cookies={"auth": auth_cookie}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == test_user.email
        assert data["name"] == test_user.name
        assert data["role"] == test_user.role.value

    @pytest.mark.asyncio(loop_scope="session")
    async def test_get_players_list(
        self,
        client: AsyncClient,
        test_user: User,
    ):
        """
        Любой авторизованный пользователь может получить список игроков.
        """
        auth_cookie = await login_user(client, test_user.email, "testpassword123")

        response = await client.get(
            "/api/users/players",
            cookies={"auth": auth_cookie}
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        for player in data:
            assert "id" in player
            assert "name" in player

    @pytest.mark.asyncio(loop_scope="session")
    async def test_admin_resets_user_password(
        self,
        client: AsyncClient,
        admin_user: User,
    ):
        """
        Админ может сбросить пароль пользователя.
        """
        auth_cookie = await login_user(client, admin_user.email, "adminpass123")
        email = unique_email("passwordreset")

        user = await create_user(client, auth_cookie, "Password Reset Test", email, "student")

        response = await client.post(
            f"/api/users/{user['id']}/reset-password",
            cookies={"auth": auth_cookie}
        )

        assert response.status_code == 200
        data = response.json()
        assert "temporaryPassword" in data
        assert len(data["temporaryPassword"]) == 10

        await delete_user(client, auth_cookie, user["id"])

    @pytest.mark.asyncio(loop_scope="session")
    async def test_update_nonexistent_user_returns_404(
        self,
        client: AsyncClient,
        admin_user: User,
    ):
        """
        Обновление несуществующего пользователя возвращает 404.
        """
        auth_cookie = await login_user(client, admin_user.email, "adminpass123")

        response = await client.patch(
            "/api/users/999999",
            json={"name": "New Name"},
            cookies={"auth": auth_cookie}
        )

        assert response.status_code == 404


    @pytest.mark.asyncio(loop_scope="session")
    async def test_student_cannot_create_user(
        self,
        client: AsyncClient,
        test_user: User,
    ):
        """
        Ученик не может создавать пользователей.
        """
        auth_cookie = await login_user(client, test_user.email, "testpassword123")
        email = unique_email("unauthorized")

        response = await client.post(
            "/api/users",
            json={
                "name": "Unauthorized Create",
                "email": email,
                "role": "student"
            },
            cookies={"auth": auth_cookie}
        )

        assert response.status_code == 403


    @pytest.mark.asyncio(loop_scope="session")
    async def test_student_cannot_update_other_user(
        self,
        client: AsyncClient,
        test_user: User,
        teacher_user: User,
    ):
        """
        Ученик не может изменять других пользователей.
        """
        auth_cookie = await login_user(client, test_user.email, "testpassword123")

        response = await client.patch(
            f"/api/users/{teacher_user.id}",
            json={"name": "Hacked Name"},
            cookies={"auth": auth_cookie}
        )

        assert response.status_code == 403
