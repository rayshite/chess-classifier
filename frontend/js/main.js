// Настройки пагинации
const ITEMS_PER_PAGE = 10;
let currentPage = 1;
let filteredGames = [];

// Моковые данные партий
const mockGames = [
    {
        id: 1,
        title: "Партия Иван vs Мария",
        status: "in_progress",
        player1: { name: "Иван Петров" },
        player2: { name: "Мария Сидорова" },
        snapshotCount: 5,
        createdAt: "2025-01-23T10:30:00"
    },
    {
        id: 2,
        title: "Партия Алексей vs Ольга",
        status: "finished",
        player1: { name: "Алексей Иванов" },
        player2: { name: "Ольга Смирнова" },
        snapshotCount: 12,
        createdAt: "2025-01-22T14:15:00"
    },
    {
        id: 3,
        title: "Партия Дмитрий vs Елена",
        status: "in_progress",
        player1: { name: "Дмитрий Козлов" },
        player2: { name: "Елена Новикова" },
        snapshotCount: 3,
        createdAt: "2025-01-23T16:45:00"
    },
    {
        id: 4,
        title: "Партия Сергей vs Анна",
        status: "finished",
        player1: { name: "Сергей Морозов" },
        player2: { name: "Анна Волкова" },
        snapshotCount: 18,
        createdAt: "2025-01-21T11:00:00"
    },
    {
        id: 5,
        title: "Партия Николай vs Татьяна",
        status: "in_progress",
        player1: { name: "Николай Соколов" },
        player2: { name: "Татьяна Лебедева" },
        snapshotCount: 7,
        createdAt: "2025-01-23T09:20:00"
    }
];

// Форматирование даты
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('ru-RU', { day: '2-digit', month: '2-digit', year: 'numeric' });
}

// Создание HTML строки таблицы для партии
function createGameRow(game) {
    const statusText = game.status === 'in_progress' ? 'В процессе' : 'Завершена';
    const badgeClass = game.status === 'in_progress' ? 'bg-success' : 'bg-primary';

    return `
        <tr style="cursor: pointer;" onclick="openGame(${game.id})">
            <td>${game.title}</td>
            <td>${game.player1.name}</td>
            <td>${game.player2.name}</td>
            <td>${game.snapshotCount}</td>
            <td><span class="badge ${badgeClass}">${statusText}</span></td>
            <td>${formatDate(game.createdAt)}</td>
        </tr>
    `;
}

// Рендеринг списка партий с пагинацией
function renderGames(games) {
    filteredGames = games;
    currentPage = 1;
    renderPage();
}

// Отображение текущей страницы
function renderPage() {
    const start = (currentPage - 1) * ITEMS_PER_PAGE;
    const end = start + ITEMS_PER_PAGE;
    const pageGames = filteredGames.slice(start, end);

    const gamesList = document.getElementById('gamesList');
    gamesList.innerHTML = pageGames.map(game => createGameRow(game)).join('');

    renderPagination();
}

// Рендеринг пагинации
function renderPagination() {
    const totalPages = Math.ceil(filteredGames.length / ITEMS_PER_PAGE);
    const pagination = document.getElementById('pagination');

    if (totalPages <= 1) {
        pagination.innerHTML = '';
        return;
    }

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

    pagination.innerHTML = html;
}

// Переключение страницы
function changePage(page) {
    const totalPages = Math.ceil(filteredGames.length / ITEMS_PER_PAGE);
    if (page < 1 || page > totalPages) return;

    currentPage = page;
    renderPage();
}

// Фильтрация партий
function filterGames() {
    const status = document.getElementById('statusFilter').value;

    if (status === 'all') {
        renderGames(mockGames);
    } else {
        const filtered = mockGames.filter(game => game.status === status);
        renderGames(filtered);
    }
}

// Открытие страницы партии
function openGame(gameId) {
    window.location.href = `/games/${gameId}`;
}

// Создание новой партии
function createGame() {
    alert('Функция создания партии будет реализована позже');
}

// Выход из системы
function logout() {
    alert('Функция выхода будет реализована позже');
}

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', () => {
    // Рендерим все партии
    renderGames(mockGames);

    // Обработчик фильтра
    document.getElementById('statusFilter').addEventListener('change', filterGames);

    // Обработчик кнопки создания партии
    document.getElementById('createGameBtn').addEventListener('click', createGame);

    // Обработчик кнопки выхода
    document.getElementById('logoutBtn').addEventListener('click', (e) => {
        e.preventDefault();
        logout();
    });
});