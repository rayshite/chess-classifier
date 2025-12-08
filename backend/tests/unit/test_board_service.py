"""
Юнит-тесты для board_service.py (обработка изображений).
"""
from pathlib import Path

import cv2
import numpy as np

from services.board_service import process_board_image, find_board_contour, four_point_transform

# Путь к тестовому изображению
TEST_IMAGE_PATH = Path(__file__).parent.parent / "test_img.png"
TEST_IMAGE_PATH_2 = Path(__file__).parent.parent / "test_img_2.png"


class TestBoardService:
    """Тесты для board_service.py."""

    def test_board_01_find_contour_on_real_image(self):
        """
        BOARD-01: find_board_contour находит доску на реальном фото.

        Тип: Позитивный
        Приоритет: Высокий
        """
        image = cv2.imread(str(TEST_IMAGE_PATH))
        assert image is not None, f"Не удалось загрузить {TEST_IMAGE_PATH}"

        contour = find_board_contour(image)

        assert contour is not None, "Контур доски не найден"
        assert len(contour) == 4, f"Ожидалось 4 точки, получено {len(contour)}"


    def test_board_02_no_contour_on_noise(self):
        """
        BOARD-02: find_board_contour — доска не найдена

        Тип: Негативный
        Приоритет: Высокий
        """
        image = np.random.randint(0, 256, (800, 800, 3), dtype=np.uint8)

        contour = find_board_contour(image)

        assert contour is None or len(contour) >= 4


    def test_board_03_returns_64_squares(self):
        """
        BOARD-03: process_board_image возвращает 64 клетки.

        Тип: Позитивный
        Приоритет: Средний
        """
        with open(TEST_IMAGE_PATH, "rb") as f:
            image_bytes = f.read()

        squares = process_board_image(image_bytes)

        assert len(squares) == 64, f"Ожидалось 64 клетки, получено {len(squares)}"

        for col in "abcdefgh":
            for row in range(1, 9):
                assert f"{col}{row}" in squares, f"Клетка {col}{row} отсутствует"

        for name, square in squares.items():
            assert square.size > 0, f"Клетка {name} пустая"
            assert square.shape[0] > 10 and square.shape[1] > 10


    def test_board_04_transform_creates_square(self):
        """
        BOARD-04: four_point_transform создаёт квадратное изображение.

        Тип: Позитивный
        Приоритет: Средний
        """
        image = cv2.imread(str(TEST_IMAGE_PATH_2))
        contour = find_board_contour(image)
        assert contour is not None

        result = four_point_transform(image, contour)

        assert result.shape[0] == result.shape[1], "Результат не квадратный"
        assert result.shape[0] >= 200, "Результат слишком маленький"
