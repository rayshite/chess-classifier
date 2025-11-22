"""
Модуль классификации шахматных фигур.

Использует предобученную нейросеть для определения фигуры
на изображении клетки шахматной доски.
"""

import os
import cv2
import numpy as np
from tensorflow import keras


# Путь к файлу модели
MODEL_PATH = os.path.join(os.path.dirname(__file__), "model.keras")

# Названия классов в алфавитном порядке (так их видит модель)
# b = black (чёрные), w = white (белые)
# B = Bishop (слон), K = King (король), N = Knight (конь)
# P = Pawn (пешка), Q = Queen (ферзь), R = Rook (ладья)
CLASS_NAMES = ["bB", "bK", "bN", "bP", "bQ", "bR", "empty", "wB", "wK", "wN", "wP", "wQ", "wR"]

# Глобальная переменная для хранения загруженной модели
# None означает, что модель ещё не загружена
model = None


def load_model():
    """
    Загружает модель Keras из файла.

    Использует паттерн "ленивая загрузка" (lazy loading):
    модель загружается только при первом вызове.

    Returns:
        keras.Model: Загруженная модель
    """
    global model

    # Загружаем только если ещё не загружена
    if model is None:
        model = keras.models.load_model(MODEL_PATH)

    return model


def preprocess_square(image: np.ndarray) -> np.ndarray:
    """
    Подготавливает изображение клетки для подачи в модель.

    Модель обучена на изображениях размером 180x180 пикселей.
    Также нужно добавить batch dimension, потому что модель
    ожидает массив изображений, даже если оно одно.

    Args:
        image: Изображение клетки (numpy array любого размера)

    Returns:
        np.ndarray: Массив формы (1, 180, 180, 3) для подачи в модель
    """
    # Приводим к размеру, на котором обучалась модель
    resized = cv2.resize(image, (180, 180))

    # Модель ожидает batch изображений: (batch_size, height, width, channels)
    # Добавляем размерность batch_size=1: (180, 180, 3) -> (1, 180, 180, 3)
    batch = np.expand_dims(resized, axis=0)

    return batch


def predict_square(image: np.ndarray) -> tuple[str, float]:
    """
    Предсказывает фигуру на одной клетке.

    Подаёт изображение в нейросеть и возвращает класс
    с наибольшей вероятностью.

    Args:
        image: Изображение клетки (numpy array)

    Returns:
        tuple: (название_класса, уверенность)
               Например: ("wK", 0.95) - белый король с уверенностью 95%
    """
    # Получаем модель (загружаем при первом вызове)
    model = load_model()

    # Подготавливаем изображение
    preprocessed = preprocess_square(image)

    # Получаем предсказания модели
    # verbose=0 отключает вывод прогресса в консоль
    # predictions - массив вероятностей для каждого класса
    predictions = model.predict(preprocessed, verbose=0)

    # Находим индекс класса с максимальной вероятностью
    class_idx = np.argmax(predictions[0])

    # Извлекаем уверенность (вероятность) для этого класса
    confidence = float(predictions[0][class_idx])

    # Получаем название класса по индексу
    class_name = CLASS_NAMES[class_idx]

    return class_name, confidence


def predict_all_squares(squares: dict) -> dict:
    """
    Предсказывает фигуры на всех 64 клетках доски.

    Использует batch inference. Подаёт все 64 изображения в модель.

    Args:
        squares: Словарь {название_клетки: изображение}
                 Например: {"a8": np.array, "b8": np.array, ...}

    Returns:
        dict: Словарь {название_клетки: фигура}
              Например: {"a8": "bR", "b8": "bN", "c8": "empty", ...}
    """
    model = load_model()

    # Сохраняем порядок клеток для сопоставления с результатами
    square_names = list(squares.keys())

    # Собираем все изображения в один batch
    # Форма: (64, 180, 180, 3)
    batch = np.array([
        cv2.resize(squares[name], (180, 180))
        for name in square_names
    ])

    # Вызов модели для всех 64 клеток
    predictions = model.predict(batch, verbose=0)

    # Разбираем результаты
    results = {}
    for i, square_name in enumerate(square_names):
        class_idx = np.argmax(predictions[i])
        results[square_name] = CLASS_NAMES[class_idx]

    return results
