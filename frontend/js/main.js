// Текущая страница и фильтр
let currentPage = 1;
let currentStatus = 'all';

// Загрузка партий с сервера
async function loadGames(page = 1, status = 'all') {
    try {
        // Показываем индикатор загрузки
        document.getElementById('loading').style.display = 'block';
        document.getElementById('gamesTable').style.display = 'none';
        document.getElementById('emptyState').style.display = 'none';
        document.getElementById('paginationNav').style.display = 'none';

        // Запрос к API с фильтром
        let url = `/api/games?page=${page}&limit=2`;
        if (status && status !== 'all') {
            url += `&status=${status}`;
        }

        const response = await fetch(url);
        if (!response.ok) {
            throw new Error('Ошибка загрузки данных');
        }

        const data = await response.json();
        currentPage = data.pagination.currentPage;

        // Скрываем индикатор загрузки
        document.getElementById('loading').style.display = 'none';

        // Отображаем данные
        if (data.games.length === 0) {
            document.getElementById('emptyState').style.display = 'block';
        } else {
            renderGames(data.games);
            renderPagination(data.pagination);
            document.getElementById('gamesTable').style.display = 'table';
        }
    } catch (error) {
        console.error('Ошибка:', error);
        document.getElementById('loading').style.display = 'none';
        alert('Не удалось загрузить партии. Проверьте подключение к серверу.');
    }
}

// Форматирование даты
function formatDate(isoString) {
    const date = new Date(isoString);
    return date.toLocaleDateString('ru-RU', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric'
    });
}

// Рендеринг списка партий
function renderGames(games) {
    const tbody = document.getElementById('gamesList');
    tbody.innerHTML = games.map(game => {
        const statusText = game.status === 'in_progress' ? 'В процессе' : 'Завершена';
        const badgeClass = game.status === 'in_progress' ? 'bg-success' : 'bg-primary';

        return `
            <tr style="cursor: pointer;" onclick="window.location.href='/games/${game.id}'">
                <td>${game.title}</td>
                <td>${game.player1.name}</td>
                <td>${game.player2.name}</td>
                <td>${game.snapshotCount}</td>
                <td><span class="badge ${badgeClass}">${statusText}</span></td>
                <td>${formatDate(game.createdAt)}</td>
            </tr>
        `;
    }).join('');
}

// Рендеринг пагинации
function renderPagination(pagination) {
    const { currentPage, totalPages } = pagination;

    if (totalPages <= 1) {
        document.getElementById('paginationNav').style.display = 'none';
        return;
    }

    const paginationEl = document.getElementById('pagination');
    let html = '';

    // Кнопка "Назад"
    html += `
        <li class="page-item ${currentPage === 1 ? 'disabled' : ''}">
            <a class="page-link" href="#" onclick="changePage(${currentPage - 1}); return false;">Назад</a>
        </li>
    `;

    // Номера страниц
    for (let i = 1; i <= totalPages; i++) {
        html += `
            <li class="page-item ${i === currentPage ? 'active' : ''}">
                <a class="page-link" href="#" onclick="changePage(${i}); return false;">${i}</a>
            </li>
        `;
    }

    // Кнопка "Вперёд"
    html += `
        <li class="page-item ${currentPage === totalPages ? 'disabled' : ''}">
            <a class="page-link" href="#" onclick="changePage(${currentPage + 1}); return false;">Вперёд</a>
        </li>
    `;

    paginationEl.innerHTML = html;
    document.getElementById('paginationNav').style.display = 'block';
}

// Переключение страницы
function changePage(page) {
    if (page < 1) return;
    loadGames(page, currentStatus);
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

// Фильтрация по статусу
function filterGames() {
    currentStatus = document.getElementById('statusFilter').value;
    loadGames(1, currentStatus);  // Сбрасываем на первую страницу
}

// Создание новой партии
function createGame() {
    alert('Функция создания партии будет реализована позже');
}

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', () => {
    // Загружаем партии
    loadGames(1);

    // Обработчик кнопки создания партии
    document.getElementById('createGameBtn').addEventListener('click', createGame);

    // Обработчик фильтра
    document.getElementById('statusFilter').addEventListener('change', filterGames);
});