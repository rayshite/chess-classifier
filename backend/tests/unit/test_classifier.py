"""
Юнит-тесты для classifier.py (ML инференс).
"""
import numpy as np

from services.ml import CLASS_NAMES, preprocess_square


class TestClassifier:

    def test_class_names_count(self):
        """Должно быть 13 классов."""
        assert len(CLASS_NAMES) == 13


    def test_class_names_contains_all_pieces(self):
        """Должны быть все фигуры + empty."""
        assert "empty" in CLASS_NAMES
        for piece in ["B", "K", "N", "P", "Q", "R"]:
            assert f"w{piece}" in CLASS_NAMES
            assert f"b{piece}" in CLASS_NAMES


    def test_preprocess_output_shape(self):
        """Выходная форма должна быть (1, 180, 180, 3)."""
        image = np.random.randint(0, 256, (100, 100, 3), dtype=np.uint8)
        result = preprocess_square(image)
        assert result.shape == (1, 180, 180, 3)


    def test_preprocess_resizes_any_image(self):
        """Любое изображение приводится к 180x180."""
        for size in [50, 100, 500]:
            image = np.random.randint(0, 256, (size, size, 3), dtype=np.uint8)
            result = preprocess_square(image)
            assert result.shape[1:3] == (180, 180)


