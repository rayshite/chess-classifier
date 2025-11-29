// Получение ID партии из URL
function getGameIdFromUrl() {
    const pathParts = window.location.pathname.split('/');
    return parseInt(pathParts[pathParts.length - 1]);
}

// Текущая партия (загружается из API)
let currentGame = null;

// Моковые данные снепшотов (пока не реализовано получение из БД)
const mockSnapshots = [
    {
        id: 1,
        moveNumber: 1,
        position: "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR",
        createdAt: "2025-01-23T10:31:00"
    },
    {
        id: 2,
        moveNumber: 2,
        position: "rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR",
        createdAt: "2025-01-23T10:32:00"
    },
    {
        id: 3,
        moveNumber: 3,
        position: "rnbqkbnr/pppp1ppp/8/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R",
        createdAt: "2025-01-23T10:33:00"
    },
    {
        id: 4,
        moveNumber: 4,
        position: "rnbqkb1r/pppp1ppp/5n2/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R",
        createdAt: "2025-01-23T10:34:00"
    },
    {
        id: 5,
        moveNumber: 5,
        position: "rnbqkb1r/pppp1ppp/5n2/4p3/3PP3/5N2/PPP2PPP/RNBQKB1R",
        createdAt: "2025-01-23T10:35:00"
    }
];

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
    const snapshot = mockSnapshots.find(s => s.id === snapshotId);
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

// Добавление снепшота
function addSnapshot() {
    alert('Функция добавления снепшота будет реализована позже');
}

// Удаление последнего снепшота
function deleteLastSnapshot() {
    if (mockSnapshots.length === 0) return;

    if (confirm('Вы уверены, что хотите удалить последний снепшот?')) {
        mockSnapshots.pop();
        renderSnapshots(mockSnapshots);
        if (currentGame) {
            currentGame.snapshotCount = mockSnapshots.length;
            renderGameInfo(currentGame);
            updateControlPanel(currentGame, mockSnapshots);
        }
    }
}

// Завершение партии
function finishGame() {
    if (!currentGame || currentGame.status === 'finished') return;

    if (confirm('Вы уверены, что хотите завершить партию?')) {
        currentGame.status = 'finished';
        renderGameInfo(currentGame);
        updateControlPanel(currentGame, mockSnapshots);
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
        renderSnapshots(mockSnapshots); // Пока используем моковые снепшоты
        updateControlPanel(currentGame, mockSnapshots);
    } catch (error) {
        document.getElementById('gameTitle').textContent = 'Ошибка загрузки';
        console.error('Failed to load game:', error);
    }

    // Обработчики кнопок управления
    document.getElementById('addSnapshotBtn').addEventListener('click', addSnapshot);
    document.getElementById('deleteLastSnapshotBtn').addEventListener('click', deleteLastSnapshot);
    document.getElementById('finishGameBtn').addEventListener('click', finishGame);

    // Обработчик кнопки выхода
    document.getElementById('logoutBtn').addEventListener('click', (e) => {
        e.preventDefault();
        logout();
    });
});