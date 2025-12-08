"""
ML-модуль для классификации шахматных фигур.
"""

from .classifier import CLASS_NAMES, predict_square, predict_all_squares, preprocess_square

__all__ = [
    "CLASS_NAMES",
    "predict_square",
    "predict_all_squares",
    "preprocess_square",
]
