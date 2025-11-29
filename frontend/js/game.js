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

// Форматирование даты
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('ru-RU', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

// Отображение информации о партии
function renderGameInfo(game) {
    document.getElementById('gameTitle').textContent = game.title;
    document.getElementById('player1Name').textContent = game.player1.name;
    document.getElementById('player2Name').textContent = game.player2.name;
    document.getElementById('createdAt').textContent = formatDate(game.createdAt);
    document.getElementById('snapshotCount').textContent = game.snapshotCount;

    const statusBadge = document.getElementById('gameStatus');
    if (game.status === 'in_progress') {
        statusBadge.textContent = 'В процессе';
        statusBadge.className = 'badge bg-success';
    } else {
        statusBadge.textContent = 'Завершена';
        statusBadge.className = 'badge bg-primary';
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
                    <p class="card-text text-muted small">${formatDate(snapshot.createdAt)}</p>
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
            pieceTheme: 'https://chessboardjs.com/img/chesspieces/wikipedia/{piece}.png'
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

// Глобальная переменная для доски в модальном окне
let modalBoard = null;

// Открытие модального окна снепшота
function openSnapshotModal(snapshotId) {
    if (!currentGame || !currentGame.snapshots) return;
    const snapshot = currentGame.snapshots.find(s => s.id === snapshotId);
    if (!snapshot) return;

    document.getElementById('modalSnapshotNumber').textContent = snapshot.id;
    document.getElementById('modalMoveNumber').textContent = snapshot.moveNumber;

    // Инициализируем или обновляем доску в модальном окне
    if (!modalBoard) {
        modalBoard = Chessboard('modalBoard', {
            position: snapshot.position,
            draggable: false,
            pieceTheme: 'https://chessboardjs.com/img/chesspieces/wikipedia/{piece}.png'
        });
    } else {
        modalBoard.position(snapshot.position);
    }

    const modal = new bootstrap.Modal(document.getElementById('snapshotModal'));
    modal.show();
}

// Управление партией
function updateControlPanel(game, snapshots) {
    const deleteBtn = document.getElementById('deleteLastSnapshotBtn');
    const finishBtn = document.getElementById('finishGameBtn');

    // Отключаем кнопку удаления, если нет снепшотов
    deleteBtn.disabled = snapshots.length === 0;

    // Отключаем кнопку завершения, если партия уже завершена
    finishBtn.disabled = game.status === 'finished';
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

// Удаление последнего снепшота
function deleteLastSnapshot() {
    if (!currentGame || !currentGame.snapshots || currentGame.snapshots.length === 0) return;

    if (confirm('Вы уверены, что хотите удалить последний снепшот?')) {
        currentGame.snapshots.pop();
        currentGame.snapshotCount = currentGame.snapshots.length;
        renderSnapshots(currentGame.snapshots);
        renderGameInfo(currentGame);
        updateControlPanel(currentGame, currentGame.snapshots);
    }
}

// Завершение партии
function finishGame() {
    if (!currentGame || currentGame.status === 'finished') return;

    if (confirm('Вы уверены, что хотите завершить партию?')) {
        currentGame.status = 'finished';
        renderGameInfo(currentGame);
        updateControlPanel(currentGame, currentGame.snapshots);
        alert('Партия завершена');
    }
}

// Выход из системы
function logout() {
    if (confirm('Вы уверены, что хотите выйти?')) {
        alert('Функция выхода будет реализована позже');
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
    document.getElementById('deleteLastSnapshotBtn').addEventListener('click', deleteLastSnapshot);
    document.getElementById('finishGameBtn').addEventListener('click', finishGame);

    // Обработчики модального окна добавления снепшота
    document.getElementById('snapshotImage').addEventListener('change', handleImagePreview);
    document.getElementById('submitSnapshotBtn').addEventListener('click', submitSnapshot);

    // Обработчик кнопки выхода
    document.getElementById('logoutBtn').addEventListener('click', (e) => {
        e.preventDefault();
        logout();
    });
});