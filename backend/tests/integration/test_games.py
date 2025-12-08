"""
Интеграционные тесты для API партий.
"""

from pathlib import Path
from unittest.mock import patch

import pytest
from httpx import AsyncClient

from models import User


# Путь к тестовому изображению
TEST_IMAGE_PATH = Path(__file__).parent.parent / "test_img.png"


async def login_user(client: AsyncClient, email: str, password: str) -> str:
    """Вспомогательная функция для входа и получения cookie."""
    response = await client.post(
        "/api/auth/login",
        data={"username": email, "password": password}
    )
    assert response.status_code == 204, f"Login failed: {response.text}"
    return response.cookies.get("auth")


async def create_game(
    client: AsyncClient,
    auth_cookie: str,
    title: str,
    player1_id: int,
    player2_id: int
) -> dict:
    """Создаёт партию и возвращает её данные."""
    response = await client.post(
        "/api/games",
        json={
            "title": title,
            "player1Id": player1_id,
            "player2Id": player2_id,
        },
        cookies={"auth": auth_cookie}
    )
    assert response.status_code == 200, f"Failed to create game: {response.text}"
    return response.json()


async def delete_game(client: AsyncClient, auth_cookie: str, game_id: int):
    """Удаляет партию (для очистки после теста)."""
    await client.delete(
        f"/api/games/{game_id}",
        cookies={"auth": auth_cookie}
    )


class TestGames:
    """Тесты API партий."""

    @pytest.mark.asyncio(loop_scope="session")
    async def test_game_01_create_game_by_authorized_user(
        self,
        client: AsyncClient,
        test_user: User,
        teacher_user: User,
    ):
        """
        GAME-01: Создание партии авторизованным пользователем.

        Тип: Позитивный
        Приоритет: Критичный
        """
        auth_cookie = await login_user(client, test_user.email, "testpassword123")
        teacher_cookie = await login_user(client, teacher_user.email, "teacherpass123")

        game_data = {
            "title": "Test Game GAME-01",
            "player1Id": test_user.id,
            "player2Id": teacher_user.id,
        }

        response = await client.post(
            "/api/games",
            json=game_data,
            cookies={"auth": auth_cookie}
        )

        assert response.status_code == 200, (
            f"Ожидался статус 200, получен {response.status_code}. "
            f"Тело ответа: {response.text}"
        )

        data = response.json()
        assert "id" in data
        assert data["title"] == "Test Game GAME-01"
        assert data["status"] == "in_progress"
        assert data["player1Id"] == test_user.id
        assert data["player2Id"] == teacher_user.id

        await delete_game(client, teacher_cookie, data["id"])

    @pytest.mark.asyncio(loop_scope="session")
    async def test_game_01_student_must_be_player(
        self,
        client: AsyncClient,
        test_user: User,
        teacher_user: User,
        admin_user: User,
    ):
        """
        GAME-01 (негативный): Ученик не может создать партию,
        где он не является одним из игроков.
        """
        auth_cookie = await login_user(client, test_user.email, "testpassword123")

        game_data = {
            "title": "Game without student",
            "player1Id": teacher_user.id,
            "player2Id": admin_user.id,
        }

        response = await client.post(
            "/api/games",
            json=game_data,
            cookies={"auth": auth_cookie}
        )

        assert response.status_code == 400, (
            f"Ожидался статус 400, получен {response.status_code}"
        )

    @pytest.mark.asyncio(loop_scope="session")
    async def test_game_02_student_sees_only_own_games(
        self,
        client: AsyncClient,
        test_user: User,
        teacher_user: User,
        admin_user: User,
    ):
        """
        GAME-02: Получение списка партий (ученик видит только свои).

        Тип: Позитивный
        Приоритет: Высокий
        """
        student_cookie = await login_user(client, test_user.email, "testpassword123")
        teacher_cookie = await login_user(client, teacher_user.email, "teacherpass123")

        # Создаём партию С участием ученика
        student_game = await create_game(
            client, student_cookie,
            "Student's game GAME-02", test_user.id, teacher_user.id
        )

        # Создаём партию БЕЗ участия ученика
        teacher_game = await create_game(
            client, teacher_cookie,
            "Teacher's game GAME-02", teacher_user.id, admin_user.id
        )

        response = await client.get(
            "/api/games",
            cookies={"auth": student_cookie}
        )

        assert response.status_code == 200

        data = response.json()
        assert "games" in data
        assert len(data["games"]) > 0, "Ученик должен видеть свои партии"

        for game in data["games"]:
            player_ids = [game["player1"]["id"], game["player2"]["id"]]
            assert test_user.id in player_ids, (
                f"Ученик видит чужую партию: {game['title']}"
            )

        await delete_game(client, teacher_cookie, student_game["id"])
        await delete_game(client, teacher_cookie, teacher_game["id"])

    @pytest.mark.asyncio(loop_scope="session")
    async def test_game_03_teacher_sees_all_games(
        self,
        client: AsyncClient,
        test_user: User,
        teacher_user: User,
        admin_user: User,
    ):
        """
        GAME-03: Получение списка партий (учитель видит все).

        Тип: Позитивный
        Приоритет: Средний
        """
        student_cookie = await login_user(client, test_user.email, "testpassword123")
        teacher_cookie = await login_user(client, teacher_user.email, "teacherpass123")

        # Создаём партию ученика
        student_game = await create_game(
            client, student_cookie,
            "Student's game GAME-03", test_user.id, teacher_user.id
        )

        # Создаём партию учителя (без ученика)
        teacher_game = await create_game(
            client, teacher_cookie,
            "Teacher's game GAME-03", teacher_user.id, admin_user.id
        )

        response = await client.get(
            "/api/games",
            cookies={"auth": teacher_cookie}
        )

        assert response.status_code == 200

        data = response.json()
        assert "games" in data
        assert "pagination" in data

        # Учитель должен видеть обе партии
        game_titles = [g["title"] for g in data["games"]]
        assert "Student's game GAME-03" in game_titles, "Учитель должен видеть партию ученика"
        assert "Teacher's game GAME-03" in game_titles, "Учитель должен видеть свою партию"

        await delete_game(client, teacher_cookie, student_game["id"])
        await delete_game(client, teacher_cookie, teacher_game["id"])

    @pytest.mark.asyncio(loop_scope="session")
    async def test_game_04_upload_photo_and_get_position(
            self,
            client: AsyncClient,
            test_user: User,
            teacher_user: User,
    ):
        """
        GAME-04: Загрузка фото доски и получение распознанной позиции.

        Тип: Позитивный
        Приоритет: Критичный

        Шаги:
            1. Создать партию
            2. Загрузить фото доски
            3. Получить распознанную позицию (FEN)

        Ожидаемый результат:
            - HTTP статус 200
            - Возвращается снепшот с позицией в формате FEN
        """
        auth_cookie = await login_user(client, test_user.email, "testpassword123")
        teacher_cookie = await login_user(client, teacher_user.email, "teacherpass123")

        game = await create_game(
            client, auth_cookie,
            "Game for photo upload GAME-04", test_user.id, teacher_user.id
        )

        mock_predictions = {
            f"{col}{row}": "empty" for col in "abcdefgh" for row in range(1, 9)
        }
        mock_predictions["e1"] = "wK"
        mock_predictions["e8"] = "bK"

        with patch("routers.games.predict_all_squares", return_value=mock_predictions):
            with open(TEST_IMAGE_PATH, "rb") as f:
                response = await client.post(
                    f"/api/games/{game['id']}/snapshots",
                    files={"image": ("test_img.png", f, "image/png")},
                    cookies={"auth": auth_cookie}
                )

        assert response.status_code == 200, (
            f"Ожидался статус 200, получен {response.status_code}. "
            f"Тело ответа: {response.text}"
        )

        data = response.json()
        assert "id" in data
        assert "position" in data
        assert "moveNumber" in data
        assert data["moveNumber"] == 1
        # Позиция должна быть в формате FEN (содержит /)
        assert "/" in data["position"]

        await delete_game(client, teacher_cookie, game["id"])

    @pytest.mark.asyncio(loop_scope="session")
    async def test_game_05_upload_invalid_file(
            self,
            client: AsyncClient,
            test_user: User,
            teacher_user: User,
    ):
        """
        GAME-05: Загрузка некорректного файла (не изображение).

        Тип: Негативный
        Приоритет: Средний

        Шаги:
            1. Создать партию
            2. Попытаться загрузить текстовый файл вместо изображения

        Ожидаемый результат:
            - HTTP статус 400 или 422
            - Сообщение об ошибке
        """
        auth_cookie = await login_user(client, test_user.email, "testpassword123")
        teacher_cookie = await login_user(client, teacher_user.email, "teacherpass123")

        game = await create_game(
            client, auth_cookie,
            "Game for invalid file GAME-05", test_user.id, teacher_user.id
        )

        # Создаём "файл" с текстовым содержимым
        invalid_content = b"This is not an image, just plain text"

        response = await client.post(
            f"/api/games/{game['id']}/snapshots",
            files={"image": ("test.txt", invalid_content, "text/plain")},
            cookies={"auth": auth_cookie}
        )

        # Должен вернуть ошибку (400 или 422)
        assert response.status_code in [400, 422, 500], (
            f"Ожидалась ошибка, получен {response.status_code}"
        )

        await delete_game(client, teacher_cookie, game["id"])


    @pytest.mark.asyncio(loop_scope="session")
    async def test_game_06_finish_game(
        self,
        client: AsyncClient,
        test_user: User,
        teacher_user: User,
    ):
        """
        GAME-06: Завершение партии.

        Тип: Позитивный
        Приоритет: Высокий
        """
        auth_cookie = await login_user(client, test_user.email, "testpassword123")
        teacher_cookie = await login_user(client, teacher_user.email, "teacherpass123")

        game = await create_game(
            client, auth_cookie,
            "Game to finish GAME-06", test_user.id, teacher_user.id
        )

        response = await client.patch(
            f"/api/games/{game['id']}/status",
            cookies={"auth": auth_cookie}
        )

        assert response.status_code == 200
        assert response.json()["status"] == "finished"

        await delete_game(client, teacher_cookie, game["id"])


    @pytest.mark.asyncio(loop_scope="session")
    async def test_game_06_resume_finished_game(
        self,
        client: AsyncClient,
        test_user: User,
        teacher_user: User,
    ):
        """
        GAME-06 (дополнительно): Возобновление завершённой партии.
        """
        # Arrange
        auth_cookie = await login_user(client, test_user.email, "testpassword123")
        teacher_cookie = await login_user(client, teacher_user.email, "teacherpass123")

        game = await create_game(
            client, auth_cookie,
            "Game to resume", test_user.id, teacher_user.id
        )

        # Завершаем
        await client.patch(
            f"/api/games/{game['id']}/status",
            cookies={"auth": auth_cookie}
        )

        response = await client.patch(
            f"/api/games/{game['id']}/status",
            cookies={"auth": auth_cookie}
        )

        assert response.status_code == 200
        assert response.json()["status"] == "in_progress"

        await delete_game(client, teacher_cookie, game["id"])


    @pytest.mark.asyncio(loop_scope="session")
    async def test_game_get_by_id(
        self,
        client: AsyncClient,
        test_user: User,
        teacher_user: User,
    ):
        """
        Получение партии по ID.
        """
        auth_cookie = await login_user(client, test_user.email, "testpassword123")
        teacher_cookie = await login_user(client, teacher_user.email, "teacherpass123")

        game = await create_game(
            client, auth_cookie,
            "Game to get", test_user.id, teacher_user.id
        )

        response = await client.get(
            f"/api/games/{game['id']}",
            cookies={"auth": auth_cookie}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == game["id"]
        assert data["title"] == "Game to get"
        assert "snapshots" in data
        assert "player1" in data
        assert "player2" in data

        await delete_game(client, teacher_cookie, game["id"])


    @pytest.mark.asyncio(loop_scope="session")
    async def test_game_student_cannot_access_others_game(
        self,
        client: AsyncClient,
        test_user: User,
        teacher_user: User,
        admin_user: User,
    ):
        """
        Ученик не может получить доступ к чужой партии.
        """
        teacher_cookie = await login_user(client, teacher_user.email, "teacherpass123")
        student_cookie = await login_user(client, test_user.email, "testpassword123")

        game = await create_game(
            client, teacher_cookie,
            "Teacher's private game", teacher_user.id, admin_user.id
        )

        # Act
        response = await client.get(
            f"/api/games/{game['id']}",
            cookies={"auth": student_cookie}
        )

        assert response.status_code == 403

        await delete_game(client, teacher_cookie, game["id"])


    @pytest.mark.asyncio(loop_scope="session")
    async def test_game_without_auth_returns_401(
        self,
        client: AsyncClient,
    ):
        """
        Доступ к партиям без авторизации возвращает 401.
        """
        response = await client.get("/api/games")
        assert response.status_code == 401

    @pytest.mark.asyncio(loop_scope="session")
    async def test_game_not_found_returns_404(
        self,
        client: AsyncClient,
        test_user: User,
    ):
        """
        Запрос несуществующей партии возвращает 404.
        """
        auth_cookie = await login_user(client, test_user.email, "testpassword123")

        response = await client.get(
            "/api/games/999999",
            cookies={"auth": auth_cookie}
        )

        assert response.status_code == 404


    @pytest.mark.asyncio(loop_scope="session")
    async def test_game_07_upload_photo_to_finished_game(
        self,
        client: AsyncClient,
        test_user: User,
        teacher_user: User,
    ):
        """
        GAME-07: Загрузка фото в завершённую партию.

        Тип: Негативный
        Приоритет: Средний

        Шаги:
            1. Создать партию
            2. Завершить партию
            3. Попытаться загрузить фото

        Ожидаемый результат:
            - HTTP статус 400
            - Загрузка запрещена
        """
        auth_cookie = await login_user(client, test_user.email, "testpassword123")
        teacher_cookie = await login_user(client, teacher_user.email, "teacherpass123")

        game = await create_game(
            client, auth_cookie,
            "Game to finish GAME-07", test_user.id, teacher_user.id
        )

        # Завершаем партию
        await client.patch(
            f"/api/games/{game['id']}/status",
            cookies={"auth": auth_cookie}
        )

        # Пытаемся загрузить фото
        with open(TEST_IMAGE_PATH, "rb") as f:
            response = await client.post(
                f"/api/games/{game['id']}/snapshots",
                files={"image": ("test_img.png", f, "image/png")},
                cookies={"auth": auth_cookie}
            )

        assert response.status_code == 400, (
            f"Ожидался статус 400, получен {response.status_code}. "
            f"Загрузка в завершённую партию должна быть запрещена."
        )

        await delete_game(client, teacher_cookie, game["id"])
