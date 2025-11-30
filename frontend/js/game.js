// Получение ID партии из URL
function getGameIdFromUrl() {
    const pathParts = window.location.pathname.split('/');
    return parseInt(pathParts[pathParts.length - 1]);
}

// Текущая партия (загружается из API)
let currentGame = null;

// Загрузка информации о партии из API
async function loadGameInfo(gameId) {
    try {
        const response = await fetch(`/api/games/${gameId}`);
        if (!response.ok) {
            if (response.status === 404) {
                throw new Error('Партия не найдена');
            }
            throw new Error('Ошибка загрузки партии');
        }
        return await response.json();
    } catch (error) {
        console.error('Error loading game:', error);
        throw error;
    }
}

// Отображение информации о партии
function renderGameInfo(game) {
    document.getElementById('gameTitle').textContent = game.title;
    document.getElementById('player1Name').textContent = game.player1.name;
    document.getElementById('player2Name').textContent = game.player2.name;
    document.getElementById('createdAt').textContent = formatDateTime(game.createdAt);
    document.getElementById('snapshotCount').textContent = game.snapshotCount;

    const statusBadge = document.getElementById('gameStatus');
    if (game.status === 'in_progress') {
        statusBadge.textContent = 'В процессе';
        statusBadge.className = 'badge bg-primary';
    } else {
        statusBadge.textContent = 'Завершена';
        statusBadge.className = 'badge bg-secondary';
    }
}

// Создание карточки снепшота
function createSnapshotCard(snapshot) {
    return `
        <div class="col-12 col-sm-6 col-md-4 col-lg-3 d-flex">
            <div class="card snapshot-card h-100 w-100" style="cursor: pointer;" onclick="openSnapshotModal(${snapshot.id})">
                <div id="board-${snapshot.id}" style="width: 100%"></div>
                <div class="card-body">
                    <h6 class="card-title">Ход ${snapshot.moveNumber}</h6>
                    <p class="card-text text-muted small">${formatDateTime(snapshot.createdAt)}</p>
                </div>
            </div>
        </div>
    `;
}

// Инициализация досок для снепшотов
function initializeBoards(snapshots) {
    snapshots.forEach(snapshot => {
        Chessboard(`board-${snapshot.id}`, {
            position: snapshot.position,
            draggable: false,
            dropOffBoard: 'snapback',
            sparePieces: false,
            pieceTheme: '/static/images/pieces/{piece}.png'
        });
    });
}

// Отображение снепшотов
function renderSnapshots(snapshots) {
    const snapshotsList = document.getElementById('snapshotsList');
    const emptyState = document.getElementById('emptyState');

    if (snapshots.length === 0) {
        snapshotsList.style.display = 'none';
        emptyState.style.display = 'block';
    } else {
        snapshotsList.style.display = 'flex';
        emptyState.style.display = 'none';
        snapshotsList.innerHTML = snapshots.map(snapshot => createSnapshotCard(snapshot)).join('');

        // Инициализируем доски после рендера
        setTimeout(() => initializeBoards(snapshots), 0);
    }
}

// Глобальные переменные для карусели
let snapshotCarousel = null;
let carouselBoards = [];

// Создание слайдов карусели
function buildCarouselSlides() {
    if (!currentGame || !currentGame.snapshots) return;

    const carouselInner = document.getElementById('carouselInner');
    carouselInner.innerHTML = currentGame.snapshots.map((snapshot, index) => `
        <div class="carousel-item ${index === 0 ? 'active' : ''}" data-move="${snapshot.moveNumber}">
            <div class="d-flex justify-content-center">
                <div id="carouselBoard-${index}" style="width: 400px"></div>
            </div>
        </div>
    `).join('');

    // Инициализируем доски после рендера
    setTimeout(() => {
        carouselBoards = currentGame.snapshots.map((snapshot, index) => {
            return Chessboard(`carouselBoard-${index}`, {
                position: snapshot.position,
                draggable: false,
                pieceTheme: '/static/images/pieces/{piece}.png'
            });
        });
    }, 100);
}

// Обновление заголовка и состояния стрелок при смене слайда
function updateMoveNumber() {
    const activeSlide = document.querySelector('#snapshotCarousel .carousel-item.active');
    if (activeSlide) {
        document.getElementById('modalMoveNumber').textContent = activeSlide.dataset.move;
    }

    // Обновляем состояние стрелок
    const items = document.querySelectorAll('#snapshotCarousel .carousel-item');
    const activeIndex = Array.from(items).findIndex(item => item.classList.contains('active'));
    const prevBtn = document.querySelector('#snapshotCarousel .carousel-control-prev');
    const nextBtn = document.querySelector('#snapshotCarousel .carousel-control-next');

    if (activeIndex === 0) {
        prevBtn.classList.add('disabled');
    } else {
        prevBtn.classList.remove('disabled');
    }

    if (activeIndex === items.length - 1) {
        nextBtn.classList.add('disabled');
    } else {
        nextBtn.classList.remove('disabled');
    }
}

// Открытие модального окна снепшота
function openSnapshotModal(snapshotId) {
    if (!currentGame || !currentGame.snapshots) return;
    const index = currentGame.snapshots.findIndex(s => s.id === snapshotId);
    if (index === -1) return;

    // Строим слайды если ещё не построены
    buildCarouselSlides();

    // Получаем или создаём карусель
    const carouselEl = document.getElementById('snapshotCarousel');
    snapshotCarousel = bootstrap.Carousel.getOrCreateInstance(carouselEl);

    // Переходим к нужному слайду
    setTimeout(() => {
        snapshotCarousel.to(index);
        updateMoveNumber();
    }, 150);

    const modal = new bootstrap.Modal(document.getElementById('snapshotModal'));
    modal.show();
}

// Управление партией
function updateControlPanel(game, snapshots) {
    const addBtn = document.getElementById('addSnapshotBtn');
    const deleteBtn = document.getElementById('deleteLastSnapshotBtn');
    const statusBtn = document.getElementById('finishGameBtn');

    const isInProgress = game.status === 'in_progress';

    // Кнопки добавления и удаления доступны только в статусе "в процессе"
    addBtn.disabled = !isInProgress;
    deleteBtn.disabled = !isInProgress || snapshots.length === 0;

    // Обновляем кнопку статуса в зависимости от текущего состояния
    if (isInProgress) {
        statusBtn.innerHTML = '<i class="bi bi-check-circle"></i> Завершить партию';
    } else {
        statusBtn.innerHTML = '<i class="bi bi-play-circle"></i> Возобновить партию';
    }
}

// Модальное окно добавления снепшота
let addSnapshotModal = null;

// Открытие модального окна добавления снепшота
function openAddSnapshotModal() {
    if (!addSnapshotModal) {
        addSnapshotModal = new bootstrap.Modal(document.getElementById('addSnapshotModal'));
    }

    // Сбрасываем форму
    document.getElementById('addSnapshotForm').reset();
    document.getElementById('imagePreview').style.display = 'none';
    document.getElementById('uploadError').style.display = 'none';
    document.getElementById('uploadProgress').style.display = 'none';
    document.getElementById('submitSnapshotBtn').disabled = false;

    addSnapshotModal.show();
}

// Превью изображения
function handleImagePreview(event) {
    const file = event.target.files[0];
    if (file) {
        const reader = new FileReader();
        reader.onload = function(e) {
            document.getElementById('previewImg').src = e.target.result;
            document.getElementById('imagePreview').style.display = 'block';
        };
        reader.readAsDataURL(file);
    } else {
        document.getElementById('imagePreview').style.display = 'none';
    }
}

// Отправка снепшота на сервер
async function submitSnapshot() {
    const fileInput = document.getElementById('snapshotImage');
    const file = fileInput.files[0];

    if (!file) {
        showUploadError('Выберите изображение');
        return;
    }

    const gameId = getGameIdFromUrl();
    const formData = new FormData();
    formData.append('image', file);

    // Показываем прогресс
    document.getElementById('uploadProgress').style.display = 'block';
    document.getElementById('uploadError').style.display = 'none';
    document.getElementById('submitSnapshotBtn').disabled = true;

    try {
        const response = await fetch(`/api/games/${gameId}/snapshots`, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Ошибка при добавлении снепшота');
        }

        const snapshot = await response.json();

        // Добавляем снепшот в текущую партию
        currentGame.snapshots.push(snapshot);
        currentGame.snapshotCount = currentGame.snapshots.length;

        // Обновляем отображение
        renderSnapshots(currentGame.snapshots);
        renderGameInfo(currentGame);
        updateControlPanel(currentGame, currentGame.snapshots);

        // Закрываем модальное окно
        addSnapshotModal.hide();

    } catch (error) {
        showUploadError(error.message);
    } finally {
        document.getElementById('uploadProgress').style.display = 'none';
        document.getElementById('submitSnapshotBtn').disabled = false;
    }
}

// Показать ошибку загрузки
function showUploadError(message) {
    const errorDiv = document.getElementById('uploadError');
    errorDiv.textContent = message;
    errorDiv.style.display = 'block';
}

// Модальное окно подтверждения удаления
let deleteConfirmModal = null;

// Открытие модального окна подтверждения удаления
function openDeleteConfirmModal() {
    if (!currentGame || !currentGame.snapshots || currentGame.snapshots.length === 0) return;

    if (!deleteConfirmModal) {
        deleteConfirmModal = new bootstrap.Modal(document.getElementById('deleteConfirmModal'));
    }

    deleteConfirmModal.show();
}

// Удаление последнего снепшота
async function deleteLastSnapshot() {
    const gameId = getGameIdFromUrl();
    const confirmBtn = document.getElementById('confirmDeleteBtn');

    // Блокируем кнопку на время запроса
    confirmBtn.disabled = true;
    confirmBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Удаление...';

    try {
        const response = await fetch(`/api/games/${gameId}/snapshots/last`, {
            method: 'DELETE'
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Ошибка при удалении снепшота');
        }

        // Удаляем снепшот из локального состояния
        currentGame.snapshots.pop();
        currentGame.snapshotCount = currentGame.snapshots.length;

        // Обновляем отображение
        renderSnapshots(currentGame.snapshots);
        renderGameInfo(currentGame);
        updateControlPanel(currentGame, currentGame.snapshots);

        // Закрываем модальное окно
        deleteConfirmModal.hide();

    } catch (error) {
        showError(error.message);
        console.error('Failed to delete snapshot:', error);
    } finally {
        // Восстанавливаем кнопку
        confirmBtn.disabled = false;
        confirmBtn.innerHTML = '<i class="bi bi-trash"></i> Удалить';
    }
}

// Переключение статуса партии
async function toggleGameStatus() {
    if (!currentGame) return;

    const gameId = getGameIdFromUrl();
    const statusBtn = document.getElementById('finishGameBtn');
    const isFinishing = currentGame.status === 'in_progress';

    // Блокируем кнопку на время запроса
    statusBtn.disabled = true;

    try {
        const response = await fetch(`/api/games/${gameId}/status`, {
            method: 'PATCH'
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Ошибка при смене статуса');
        }

        const data = await response.json();

        // Обновляем локальное состояние
        currentGame.status = data.status;

        // Обновляем отображение
        renderGameInfo(currentGame);
        updateControlPanel(currentGame, currentGame.snapshots);

    } catch (error) {
        showError(error.message);
        console.error('Failed to toggle game status:', error);
    } finally {
        statusBtn.disabled = false;
    }
}

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', async () => {
    const gameId = getGameIdFromUrl();
    console.log('Loading game:', gameId);

    try {
        // Загружаем информацию о партии из API
        currentGame = await loadGameInfo(gameId);

        // Отображаем информацию о партии
        renderGameInfo(currentGame);
        renderSnapshots(currentGame.snapshots);
        updateControlPanel(currentGame, currentGame.snapshots);
    } catch (error) {
        document.getElementById('gameTitle').textContent = 'Ошибка загрузки';
        console.error('Failed to load game:', error);
    }

    // Обработчики кнопок управления
    document.getElementById('addSnapshotBtn').addEventListener('click', openAddSnapshotModal);
    document.getElementById('deleteLastSnapshotBtn').addEventListener('click', openDeleteConfirmModal);
    document.getElementById('finishGameBtn').addEventListener('click', toggleGameStatus);

    // Обработчики модального окна добавления снепшота
    document.getElementById('snapshotImage').addEventListener('change', handleImagePreview);
    document.getElementById('submitSnapshotBtn').addEventListener('click', submitSnapshot);

    // Обработчик подтверждения удаления
    document.getElementById('confirmDeleteBtn').addEventListener('click', deleteLastSnapshot);

    // Обработчик смены слайда в карусели
    document.getElementById('snapshotCarousel').addEventListener('slid.bs.carousel', updateMoveNumber);
});