// Текущая страница и фильтр
let currentPage = 1;
let currentStatus = 'all';
let createGameModal;
let currentUser = null;

// Загрузка партий с сервера
async function loadGames(page = 1, status = 'all') {
    try {
        // Показываем индикатор загрузки
        document.getElementById('loading').style.display = 'block';
        document.getElementById('gamesTable').style.display = 'none';
        document.getElementById('emptyState').style.display = 'none';
        document.getElementById('paginationNav').style.display = 'none';

        // Запрос к API с фильтром
        let url = `/api/games?page=${page}`;
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

// Рендеринг списка партий
function renderGames(games) {
    const tbody = document.getElementById('gamesList');
    tbody.innerHTML = games.map(game => {
        const statusText = game.status === 'in_progress' ? 'В процессе' : 'Завершена';
        const badgeClass = game.status === 'in_progress' ? 'bg-primary' : 'bg-secondary';

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

// Загрузка списка игроков для выбора
async function loadPlayers() {
    try {
        const response = await fetch('/api/users/players');
        if (!response.ok) {
            throw new Error('Ошибка загрузки игроков');
        }

        const players = await response.json();

        const player1Select = document.getElementById('player1');
        const player2Select = document.getElementById('player2');

        // Очищаем и заполняем селекты
        const defaultOption = '<option value="">Выберите игрока</option>';
        const options = players.map(p => `<option value="${p.id}">${p.name}</option>`).join('');

        player1Select.innerHTML = defaultOption + options;
        player2Select.innerHTML = defaultOption + options;

        // Для учеников: автоподстановка себя во второе поле при любом изменении первого
        if (currentUser && currentUser.role === 'student') {
            player1Select.addEventListener('change', () => {
                if (player1Select.value && currentUser) {
                    // Если выбран не текущий пользователь - подставляем себя во второе поле
                    if (player1Select.value !== currentUser.id) {
                        player2Select.value = currentUser.id;
                    }
                }
            });

            player2Select.addEventListener('change', () => {
                if (player2Select.value && currentUser) {
                    // Если выбран не текущий пользователь - подставляем себя в первое поле
                    if (player2Select.value !== currentUser.id) {
                        player1Select.value = currentUser.id;
                    }
                }
            });
        }

    } catch (error) {
        console.error('Ошибка загрузки игроков:', error);
    }
}

// Открытие модального окна создания партии
async function openCreateGameModal() {
    document.getElementById('createGameForm').reset();
    document.getElementById('createGameError').style.display = 'none';

    await loadPlayers();
    createGameModal.show();
}

// Отправка формы создания партии
async function submitGame() {
    const title = document.getElementById('gameTitle').value.trim();
    const player1Id = document.getElementById('player1').value;
    const player2Id = document.getElementById('player2').value;

    const errorEl = document.getElementById('createGameError');
    errorEl.style.display = 'none';

    // Валидация
    if (!title || !player1Id || !player2Id) {
        errorEl.textContent = 'Заполните все поля';
        errorEl.style.display = 'block';
        return;
    }

    if (player1Id === player2Id) {
        errorEl.textContent = 'Игроки должны быть разными';
        errorEl.style.display = 'block';
        return;
    }

    const submitBtn = document.getElementById('submitGameBtn');
    submitBtn.disabled = true;
    submitBtn.textContent = 'Создание...';

    try {
        const response = await fetch('/api/games', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                title: title,
                player1_id: parseInt(player1Id),
                player2_id: parseInt(player2Id)
            })
        });

        if (!response.ok) {
            const data = await response.json();
            throw new Error(data.detail || 'Ошибка создания партии');
        }

        const game = await response.json();

        createGameModal.hide();
        // Переход на страницу созданной партии
        window.location.href = `/games/${game.id}`;

    } catch (error) {
        errorEl.textContent = error.message;
        errorEl.style.display = 'block';
    } finally {
        submitBtn.disabled = false;
        submitBtn.textContent = 'Создать';
    }
}

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', async () => {
    // Инициализируем модальное окно
    createGameModal = new bootstrap.Modal(document.getElementById('createGameModal'));

    // Загружаем текущего пользователя
    currentUser = await loadCurrentUser();

    // Загружаем партии
    loadGames(1);

    // Обработчик кнопки создания партии
    document.getElementById('createGameBtn').addEventListener('click', openCreateGameModal);

    // Обработчик отправки формы создания партии
    document.getElementById('submitGameBtn').addEventListener('click', submitGame);

    // Обработчик фильтра
    document.getElementById('statusFilter').addEventListener('change', filterGames);
});