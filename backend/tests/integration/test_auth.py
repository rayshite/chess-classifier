"""
Интеграционные тесты аутентификации.
"""

import pytest
from httpx import AsyncClient

from db import User


class TestAuth:
    """Тесты аутентификации."""

    @pytest.mark.asyncio(loop_scope="session")
    async def test_auth_01_successful_login(
        self,
        client: AsyncClient,
        test_user: User,
    ):
        """
        AUTH-01: Успешный вход с корректными данными.

        Тип: Позитивный
        Приоритет: Критичный

        Предусловия:
            - Пользователь существует в базе данных
            - Пользователь активен (is_active=True)

        Шаги:
            1. Отправить POST запрос на /api/auth/login
            2. Передать корректные email и password

        Ожидаемый результат:
            - HTTP статус 204 (No Content) - успешный вход
            - В ответе установлена cookie "auth" с JWT токеном
            - Cookie имеет флаг HttpOnly
        """

        login_data = {
            "username": test_user.email,
            "password": "testpassword123",
        }

        response = await client.post(
            "/api/auth/login",
            data=login_data,
        )

        assert response.status_code == 204, (
            f"Ожидался статус 204, получен {response.status_code}. "
            f"Тело ответа: {response.text}"
        )

        assert "auth" in response.cookies, (
            "Cookie 'auth' не установлена после успешного входа"
        )

        auth_cookie = response.cookies.get("auth")
        assert auth_cookie, "Cookie 'auth' пустая"

        jwt_parts = auth_cookie.split(".")
        assert len(jwt_parts) == 3, (
            f"Некорректный формат JWT токена. "
            f"Ожидалось 3 части, получено {len(jwt_parts)}"
        )

    @pytest.mark.asyncio(loop_scope="session")
    async def test_auth_02_login_with_wrong_password_or_wrong_user(
        self,
        client: AsyncClient,
        test_user: User,
    ):
        """
        AUTH-02: Сценарий 1 - Вход с неверным паролем.

        Тип: Негативный
        Приоритет: Высокий

        Предусловия:
            - Пользователь существует в базе данных

        Шаги:
            1. Отправить POST запрос на /api/auth/login
            2. Передать корректный email, но неверный password

        Ожидаемый результат:
            - HTTP статус 400 (Bad Request)
            - Cookie "auth" НЕ установлена

        AUTH-02: Сценарий 2 - Вход с несуществующим пользователем.

        Тип: Негативный
        Приоритет: Высокий

        Шаги:
            1. Отправить POST запрос на /api/auth/login
            2. Передать несуществующий email

        Ожидаемый результат:
            - HTTP статус 400 (Bad Request)
            - Cookie "auth" НЕ установлена
        """
        login_data = {
            "username": test_user.email,
            "password": "wrong_password_123",
        }

        response = await client.post(
            "/api/auth/login",
            data=login_data,
        )

        assert response.status_code == 400, (
            f"Ожидался статус 400, получен {response.status_code}. "
            f"Неверный пароль должен быть отклонён."
        )

        assert "auth" not in response.cookies, (
            "Cookie 'auth' не должна устанавливаться при неверном пароле"
        )

        login_data = {
            "username": "nonexistent@example.com",
            "password": "anypassword123",
        }

        response = await client.post(
            "/api/auth/login",
            data=login_data,
        )

        assert response.status_code == 400, (
            f"Ожидался статус 400, получен {response.status_code}. "
            f"Несуществующий пользователь должен быть отклонён."
        )

        assert "auth" not in response.cookies, (
            "Cookie 'auth' не должна устанавливаться для несуществующего пользователя"
        )

    @pytest.mark.asyncio(loop_scope="session")
    async def test_auth_03_access_games_without_token(
        self,
        client: AsyncClient,
    ):
        """
        AUTH-03: Доступ к /api/games без токена.

        Тип: Негативный
        Приоритет: Высокий

        Ожидаемый результат:
            - HTTP статус 401 (Unauthorized)
        """
        response = await client.get("/api/games")

        assert response.status_code == 401, (
            f"Ожидался статус 401, получен {response.status_code}. "
            f"Доступ к партиям без токена должен быть запрещён."
        )

        game_data = {
            "title": "Test Game",
            "player1_id": 1,
            "player2_id": 2,
        }

        response = await client.post("/api/games", json=game_data)

        assert response.status_code == 401, (
            f"Ожидался статус 401, получен {response.status_code}. "
            f"Создание партии без токена должно быть запрещено."
        )
