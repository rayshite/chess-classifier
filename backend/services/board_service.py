import cv2
import numpy as np


def find_board_contour(image):
    """
    Находит контур шахматной доски на изображении.

    Алгоритм:
    1. Преобразуем изображение в оттенки серого
    2. Размываем для уменьшения шума
    3. Применяем пороговую бинаризацию с разными значениями порога
    4. Ищем контуры и выбираем самый большой
    5. Если контур достаточно большой (>10% площади изображения),
       аппроксимируем его до 4 точек (углы доски)

    Returns:
        np.array: 4 точки углов доски или None, если доска не найдена
    """
    # Преобразуем в оттенки серого для упрощения обработки
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Размытие по Гауссу убирает мелкий шум
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)

    # Пробуем разные пороги бинаризации (от светлого к тёмному)
    for thresh_val in [200, 180, 160, 140]:
        # Бинаризация: пиксели > thresh_val становятся белыми, остальные — чёрными
        _, thresh = cv2.threshold(blurred, thresh_val, 255, cv2.THRESH_BINARY)

        # Находим все контуры на бинарном изображении
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if contours:
            # Берём контур с максимальной площадью
            max_contour = max(contours, key=cv2.contourArea)
            area = cv2.contourArea(max_contour)

            # Проверяем, что контур занимает хотя бы 10% изображения
            if area > image.shape[0] * image.shape[1] * 0.1:
                # Вычисляем периметр контура
                peri = cv2.arcLength(max_contour, True)

                # Аппроксимируем контур многоугольником
                # epsilon = 2% от периметра определяет точность аппроксимации
                approx = cv2.approxPolyDP(max_contour, 0.02 * peri, True)

                # Если получили 4 точки — это углы доски
                if len(approx) == 4:
                    return approx

                # Иначе возвращаем ограничивающий прямоугольник
                x, y, w, h = cv2.boundingRect(max_contour)
                return np.array([[x, y], [x+w, y], [x+w, y+h], [x, y+h]])

    return None


def order_points(pts):
    """
    Упорядочивает 4 точки в порядке:
    верхний-левый, верхний-правый, нижний-правый, нижний-левый.

    Это нужно для корректного перспективного преобразования,
    чтобы углы исходного изображения правильно соответствовали
    углам результата.

    Алгоритм:
    - Верхний-левый угол имеет наименьшую сумму координат (x+y)
    - Нижний-правый угол имеет наибольшую сумму координат (x+y)
    - Верхний-правый угол имеет наименьшую разницу (y-x)
    - Нижний-левый угол имеет наибольшую разницу (y-x)
    """
    rect = np.zeros((4, 2), dtype="float32")

    # Сумма координат: x + y
    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]  # Верхний-левый: минимальная сумма
    rect[2] = pts[np.argmax(s)]  # Нижний-правый: максимальная сумма

    # Разница координат: y - x
    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)]  # Верхний-правый: минимальная разница
    rect[3] = pts[np.argmax(diff)]  # Нижний-левый: максимальная разница

    return rect


def four_point_transform(image, pts):
    """
    Выполняет перспективное преобразование изображения.

    Преобразует область, ограниченную 4 точками (например, сфотографированную
    под углом доску), в ровный квадрат. Это исправляет искажения перспективы.

    Args:
        image: Исходное изображение
        pts: 4 точки углов области для преобразования

    Returns:
        np.array: Выровненное квадратное изображение
    """
    # Упорядочиваем точки: TL, TR, BR, BL
    rect = order_points(pts.reshape(4, 2).astype("float32"))
    (tl, tr, br, bl) = rect

    # Вычисляем ширину результата как максимум из двух горизонтальных сторон
    width_a = np.linalg.norm(br - bl)  # Нижняя сторона
    width_b = np.linalg.norm(tr - tl)  # Верхняя сторона
    max_width = int(max(width_a, width_b))

    # Вычисляем высоту результата как максимум из двух вертикальных сторон
    height_a = np.linalg.norm(tr - br)  # Правая сторона
    height_b = np.linalg.norm(tl - bl)  # Левая сторона
    max_height = int(max(height_a, height_b))

    # Делаем результат квадратным (для шахматной доски)
    size = max(max_width, max_height)

    # Целевые точки - углы квадрата размером size x size
    dst = np.array([
        [0, 0],              # Верхний-левый
        [size - 1, 0],       # Верхний-правый
        [size - 1, size - 1], # Нижний-правый
        [0, size - 1]        # Нижний-левый
    ], dtype="float32")

    # Вычисляем матрицу перспективного преобразования
    M = cv2.getPerspectiveTransform(rect, dst)

    # Применяем преобразование
    warped = cv2.warpPerspective(image, M, (size, size))

    return warped


def remove_white_border(image):
    """
    Удаляет белую рамку вокруг шахматной доски.

    Многие изображения досок имеют белые поля по краям.
    Функция находит границы, где начинается "не белый" контент,
    и обрезает изображение.

    Алгоритм:
    1. Преобразуем в оттенки серого
    2. Создаём маску "не белых" пикселей (яркость < 240)
    3. Для каждой стороны находим первую строку/столбец,
       где более 50% пикселей не белые
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    h, w = gray.shape

    # Маска: True для пикселей, которые не белые (яркость < 240)
    not_white = gray < 240

    # Ищем верхнюю границу (первая строка с >50% не белых пикселей)
    top = 0
    for i in range(h):
        if np.sum(not_white[i, :]) > w * 0.5:
            top = i
            break

    # Ищем нижнюю границу (последняя строка с >50% не белых пикселей)
    bottom = h
    for i in range(h - 1, -1, -1):
        if np.sum(not_white[i, :]) > w * 0.5:
            bottom = i + 1
            break

    # Ищем левую границу
    left = 0
    for i in range(w):
        if np.sum(not_white[:, i]) > h * 0.5:
            left = i
            break

    # Ищем правую границу
    right = w
    for i in range(w - 1, -1, -1):
        if np.sum(not_white[:, i]) > h * 0.5:
            right = i + 1
            break

    # Обрезаем изображение
    return image[top:bottom, left:right]


def find_grid_lines(image):
    """
    Находит линии сетки шахматной доски по градиентам яркости.

    На границах клеток (светлая/тёмная) происходит резкое
    изменение яркости. Находим эти переходы с помощью оператора Собеля.

    Алгоритм:
    1. Вычисляем градиенты по X и Y
    2. Суммируем градиенты по строкам и столбцам
    3. Находим 9 пиков (линии между 8 рядами/колонками клеток)

    Returns:
        tuple: (h_lines, v_lines) — списки из 9 позиций горизонтальных
               и вертикальных линий
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    h, w = gray.shape

    # Оператор Собеля вычисляет градиент (изменение яркости)
    # grad_x — вертикальные границы, grad_y — горизонтальные границы
    grad_x = np.abs(cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3))
    grad_y = np.abs(cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3))

    # Суммируем градиенты: получаем профили по строкам и столбцам
    # Пики профиля - это линии сетки
    row_profile = np.sum(grad_y, axis=1)  # Профиль для горизонтальных линий
    col_profile = np.sum(grad_x, axis=0)  # Профиль для вертикальных линий

    # Сглаживаем профили для уменьшения шума
    kernel_size = max(3, h // 100)
    if kernel_size % 2 == 0:
        kernel_size += 1
    row_profile = np.convolve(row_profile, np.ones(kernel_size)/kernel_size, mode='same')
    col_profile = np.convolve(col_profile, np.ones(kernel_size)/kernel_size, mode='same')

    def find_9_peaks(profile):
        """
        Находит 9 пиков в профиле градиентов.
        9 пиков = 9 линий сетки (границы 8 клеток).
        """
        n = len(profile)
        expected_spacing = n / 8  # Ожидаемое расстояние между линиями

        # Окно для поиска локальных максимумов
        window = int(expected_spacing * 0.3)
        peaks = []

        # Находим все локальные максимумы
        for i in range(window, n - window):
            if profile[i] == np.max(profile[max(0, i-window):min(n, i+window+1)]):
                peaks.append((i, profile[i]))

        # Если пиков меньше 9, возвращаем равномерную сетку
        if len(peaks) < 9:
            return [int(i * n / 8) for i in range(9)]

        # Сортируем пики по высоте (значению градиента)
        peaks_sorted = sorted(peaks, key=lambda x: x[1], reverse=True)

        # Выбираем 9 самых высоких пиков, которые не слишком близко друг к другу
        best_peaks = []
        for pos, val in peaks_sorted:
            too_close = False
            for bp in best_peaks:
                if abs(pos - bp) < expected_spacing * 0.5:
                    too_close = True
                    break
            if not too_close:
                best_peaks.append(pos)
            if len(best_peaks) == 9:
                break

        # Если не нашли 9 пиков, возвращаем равномерную сетку
        if len(best_peaks) < 9:
            return [int(i * n / 8) for i in range(9)]

        # Сортируем по позиции
        return sorted(best_peaks)

    h_lines = find_9_peaks(row_profile)
    v_lines = find_9_peaks(col_profile)

    return h_lines, v_lines


def split_board_to_squares(image, h_lines, v_lines):
    """
    Разделяет изображение доски на 64 клетки.

    Использует найденные линии сетки для вырезания каждой клетки.
    Клетки именуются в шахматной нотации: a1-h8.

    Args:
        image: Изображение доски
        h_lines: 9 горизонтальных линий (Y-координаты)
        v_lines: 9 вертикальных линий (X-координаты)

    Returns:
        dict: {square_name: image_array}
              Например: {"a8": np.array, "b8": np.array, ...}
    """
    squares = {}

    for row in range(8):
        for col in range(8):
            # Границы клетки
            y_start = h_lines[row]
            y_end = h_lines[row + 1]
            x_start = v_lines[col]
            x_end = v_lines[col + 1]

            # Вырезаем клетку
            square = image[y_start:y_end, x_start:x_end]

            # Формируем имя клетки в шахматной нотации
            # Колонки: a-h (слева направо)
            # Ряды: 8-1 (сверху вниз на изображении)
            col_letter = chr(ord('a') + col)  # 0->a, 1->b, ..., 7->h
            row_number = 8 - row              # 0->8, 1->7, ..., 7->1
            square_name = f"{col_letter}{row_number}"

            squares[square_name] = square

    return squares


def process_board_image(image_bytes: bytes) -> dict:
    """
    Главная функция: обрабатывает изображение шахматной доски
    и возвращает 64 клетки.

    Этапы обработки:
    1. Декодирование байтов в изображение
    2. Поиск контура доски
    3. Перспективное выравнивание (если доска под углом)
    4. Удаление белой рамки
    5. Поиск линий сетки
    6. Разделение на 64 клетки

    Args:
        image_bytes: Байты изображения (например, из HTTP-запроса)

    Returns:
        dict: {square_name: image_array}

    Raises:
        ValueError: Если изображение не удалось декодировать
    """
    # Декодируем байты в numpy-массив изображения
    nparr = np.frombuffer(image_bytes, np.uint8)
    image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    if image is None:
        raise ValueError("Не удалось декодировать изображение")

    # Находим контур доски
    contour = find_board_contour(image)

    # Выравниваем перспективу (если нашли контур)
    if contour is not None:
        aligned = four_point_transform(image, contour)
    else:
        aligned = image.copy()

    # Удаляем белую рамку
    board = remove_white_border(aligned)

    # Находим линии сетки
    h_lines, v_lines = find_grid_lines(board)

    # Разделяем на 64 клетки
    squares = split_board_to_squares(board, h_lines, v_lines)

    return squares


def predictions_to_fen(predictions: dict) -> str:
    """
    Преобразует словарь предсказаний в FEN-нотацию позиции.

    Args:
        predictions: Словарь {square_name: piece}
                     Например: {"a8": "bR", "b8": "bN", ...}

    Returns:
        Строка позиции в формате FEN
    """
    # Маппинг из формата классификатора в FEN
    # Классификатор: bB, bK, bN, bP, bQ, bR, wB, wK, wN, wP, wQ, wR, empty
    # FEN: b, k, n, p, q, r (чёрные строчные), B, K, N, P, Q, R (белые заглавные)
    piece_map = {
        'empty': '',
        'wP': 'P', 'wN': 'N', 'wB': 'B', 'wR': 'R', 'wQ': 'Q', 'wK': 'K',
        'bP': 'p', 'bN': 'n', 'bB': 'b', 'bR': 'r', 'bQ': 'q', 'bK': 'k'
    }

    fen_rows = []
    # FEN начинается с 8-го ряда (верхний ряд доски)
    for row_num in range(8, 0, -1):
        fen_row = ''
        empty_count = 0
        # Колонки от a до h
        for col in 'abcdefgh':
            square_name = f"{col}{row_num}"
            piece_code = predictions.get(square_name, 'empty')
            piece = piece_map.get(piece_code, '')

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

