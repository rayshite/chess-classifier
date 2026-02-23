import logging
import os
import cv2
import numpy as np

logger = logging.getLogger(__name__)

DEBUG_SQUARES_DIR = os.path.join(os.path.dirname(__file__), "..", "debug_squares")


def _is_square_like(approx):
    """
    Проверяет, что четырёхугольник похож на квадрат
    (с допуском на перспективные искажения).
    """
    pts = approx.reshape(4, 2).astype("float32")
    sides = [np.linalg.norm(pts[(i + 1) % 4] - pts[i]) for i in range(4)]

    # Самая короткая сторона не меньше 50% от самой длинной
    if min(sides) / max(sides) < 0.5:
        return False

    # Соотношение ширины к высоте близко к 1:1
    avg_w = (sides[0] + sides[2]) / 2
    avg_h = (sides[1] + sides[3]) / 2
    if min(avg_w, avg_h) / max(avg_w, avg_h) < 0.6:
        return False

    return True


def find_board_contour(image):
    """
    Находит контур шахматной доски на изображении.

    Ищет четырёхугольник, похожий на квадрат (с учётом перспективы),
    занимающий значительную часть изображения.

    Returns:
        np.array: 4 точки углов доски или None, если доска не найдена
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    img_area = image.shape[0] * image.shape[1]

    for thresh_val in [100, 80, 60, 40]:
        _, thresh = cv2.threshold(blurred, thresh_val, 255, cv2.THRESH_BINARY)
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if not contours:
            continue

        contours = sorted(contours, key=cv2.contourArea, reverse=True)

        for contour in contours[:5]:
            if cv2.contourArea(contour) < img_area * 0.1:
                break

            peri = cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, 0.02 * peri, True)

            if len(approx) == 4 and _is_square_like(approx):
                return approx

    return None


def _order_points(pts):
    """
    Упорядочивает 4 точки: TL, TR, BR, BL.
    """
    rect = np.zeros((4, 2), dtype="float32")
    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]
    rect[2] = pts[np.argmax(s)]
    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)]
    rect[3] = pts[np.argmax(diff)]
    return rect


def four_point_transform(image, pts):
    """
    Перспективное преобразование области из 4 точек в квадрат.
    """
    rect = _order_points(pts.reshape(4, 2).astype("float32"))
    (tl, tr, br, bl) = rect

    max_width = int(max(np.linalg.norm(br - bl), np.linalg.norm(tr - tl)))
    max_height = int(max(np.linalg.norm(tr - br), np.linalg.norm(tl - bl)))
    size = max(max_width, max_height)

    dst = np.array([
        [0, 0], [size - 1, 0],
        [size - 1, size - 1], [0, size - 1]
    ], dtype="float32")

    M = cv2.getPerspectiveTransform(rect, dst)
    return cv2.warpPerspective(image, M, (size, size))


def _find_grid_peaks(profile):
    """
    Находит 9 равноотстоящих пиков градиента — линии сетки 8x8.

    Возвращает список из 9 позиций или None, если сетка не найдена.
    """
    n = len(profile)
    window = max(3, n // 80)

    # Локальные максимумы
    peaks = []
    for i in range(window, n - window):
        if profile[i] >= np.max(profile[max(0, i - window):min(n, i + window + 1)]):
            peaks.append((i, profile[i]))

    if len(peaks) < 9:
        return None

    # Топ-30 пиков по силе
    top_peaks = sorted([p[0] for p in sorted(peaks, key=lambda x: x[1], reverse=True)[:30]])

    best_score = -float('inf')
    best_span = 0
    best_matched = None

    for i in range(len(top_peaks)):
        for j in range(i + 1, len(top_peaks)):
            span = top_peaks[j] - top_peaks[i]
            spacing = span / 8

            if span < n * 0.5:
                continue

            # Для каждой ожидаемой позиции ищем ближайший пик
            matched = []
            for k in range(9):
                expected = top_peaks[i] + k * spacing
                best_match = None
                best_dist = spacing * 0.15
                for p in top_peaks:
                    dist = abs(p - expected)
                    if dist < best_dist:
                        best_dist = dist
                        best_match = p
                if best_match is not None:
                    matched.append(best_match)

            if len(matched) < 9:
                continue

            # Проверяем равномерность расстояний между соседними пиками
            spacings = [matched[k + 1] - matched[k] for k in range(8)]
            mean_sp = np.mean(spacings)
            if mean_sp == 0:
                continue
            cv = np.std(spacings) / mean_sp
            if cv > 0.10:
                continue

            score = -cv
            if score > best_score or (np.isclose(score, best_score) and span > best_span):
                best_score = score
                best_span = span
                best_matched = matched

    return best_matched


def _find_grid_lines(image):
    """
    Находит 9 горизонтальных и 9 вертикальных линий сетки.

    Returns:
        (h_lines, v_lines) или None, если сетка не найдена.
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    h, w = gray.shape

    grad_x = np.abs(cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3))
    grad_y = np.abs(cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3))

    row_lines = _find_grid_peaks(np.sum(grad_y, axis=1))
    col_lines = _find_grid_peaks(np.sum(grad_x, axis=0))

    if row_lines is None or col_lines is None:
        return None

    row_span = row_lines[-1] - row_lines[0]
    col_span = col_lines[-1] - col_lines[0]

    # Клетки квадратные → span по обеим осям близок (±20%)
    if min(row_span, col_span) / max(row_span, col_span) < 0.8:
        return None

    return row_lines, col_lines


def find_board_grid(image):
    """
    Находит игровую зону и линии сетки на изображении доски.

    Обрезает рамку с координатами, оставляя только игровую зону.
    Возвращает обрезанное изображение и линии сетки (пересчитанные
    относительно обрезанного изображения).

    Returns:
        (board_image, h_lines, v_lines) или None, если сетка не найдена.
    """
    h, w = image.shape[:2]

    result = _find_grid_lines(image)
    if result is None:
        return None

    row_lines, col_lines = result

    cell_size = max(row_lines[-1] - row_lines[0], col_lines[-1] - col_lines[0]) / 8
    board_size = int(cell_size * 8)

    row_center = (row_lines[0] + row_lines[-1]) // 2
    col_center = (col_lines[0] + col_lines[-1]) // 2

    top = max(0, row_center - board_size // 2)
    bottom = min(h, top + board_size)
    left = max(0, col_center - board_size // 2)
    right = min(w, left + board_size)

    # Пересчитываем линии относительно обрезанного изображения
    h_lines = [y - top for y in row_lines]
    v_lines = [x - left for x in col_lines]

    logger.warning(
        "find_board_grid: image=%dx%d, crop=[top=%d, bottom=%d, left=%d, right=%d], "
        "size=%dx%d, cell=%.0f",
        w, h, top, bottom, left, right, right - left, bottom - top, cell_size,
    )

    return image[top:bottom, left:right], h_lines, v_lines


def split_board_to_squares(image, h_lines, v_lines):
    """
    Разделяет изображение доски на 64 клетки.

    Returns:
        dict: {"a8": np.array, ..., "h1": np.array}
    """
    squares = {}
    for row in range(8):
        for col in range(8):
            square_name = f"{chr(ord('a') + col)}{8 - row}"
            squares[square_name] = image[h_lines[row]:h_lines[row + 1],
                                         v_lines[col]:v_lines[col + 1]]
    return squares


def _verify_checkerboard(squares):
    """
    Проверяет шахматный паттерн: соседние клетки чередуются по яркости.
    Проверяет обе ориентации и выбирает лучшую.
    """
    vals = {}
    for row in range(8):
        for col in range(8):
            name = f"{chr(ord('a') + col)}{8 - row}"
            img = squares.get(name)
            if img is None or img.size == 0:
                return False
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if len(img.shape) == 3 else img
            vals[(row, col)] = np.mean(gray)

    best_ratio = 0
    # Проверяем обе ориентации (parity=0 и parity=1)
    for parity in (0, 1):
        group_a = [v for (r, c), v in vals.items() if (c + r) % 2 == parity]
        group_b = [v for (r, c), v in vals.items() if (c + r) % 2 != parity]

        avg_a = np.mean(group_a)
        avg_b = np.mean(group_b)

        if abs(avg_a - avg_b) < 20:
            continue

        mid = (avg_a + avg_b) / 2
        correct = sum(
            1 for (r, c), v in vals.items()
            if ((c + r) % 2 == parity) == (v > mid)
        )

        ratio = correct / 64
        best_ratio = max(best_ratio, ratio)

    logger.warning("checkerboard: best_ratio=%d/64 (%.0f%%)", int(best_ratio * 64), best_ratio * 100)
    return best_ratio >= 0.75


def process_board_image(image_bytes: bytes) -> dict:
    """
    Обрабатывает изображение шахматной доски и возвращает 64 клетки.

    Raises:
        ValueError: Если не удалось найти/распознать доску
    """
    nparr = np.frombuffer(image_bytes, np.uint8)
    image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError("Не удалось декодировать изображение")

    contour = find_board_contour(image)
    if contour is None:
        raise ValueError("Не удалось найти шахматную доску на изображении")

    aligned = four_point_transform(image, contour)

    grid = find_board_grid(aligned)
    if grid is None:
        raise ValueError("Не удалось найти шахматную доску на изображении")

    board, h_lines, v_lines = grid
    squares = split_board_to_squares(board, h_lines, v_lines)

    if not _verify_checkerboard(squares):
        raise ValueError("Не удалось найти шахматную доску на изображении")

    return squares


def predictions_to_fen(predictions: dict) -> str:
    """Преобразует словарь предсказаний в FEN-нотацию."""
    piece_map = {
        'empty': '',
        'wP': 'P', 'wN': 'N', 'wB': 'B', 'wR': 'R', 'wQ': 'Q', 'wK': 'K',
        'bP': 'p', 'bN': 'n', 'bB': 'b', 'bR': 'r', 'bQ': 'q', 'bK': 'k'
    }

    fen_rows = []
    for row_num in range(8, 0, -1):
        fen_row = ''
        empty_count = 0
        for col in 'abcdefgh':
            piece = piece_map.get(predictions.get(f"{col}{row_num}", 'empty'), '')
            if piece == '':
                empty_count += 1
            else:
                if empty_count > 0:
                    fen_row += str(empty_count)
                    empty_count = 0
                fen_row += piece
        if empty_count > 0:
            fen_row += str(empty_count)
        fen_rows.append(fen_row)

    return '/'.join(fen_rows)
