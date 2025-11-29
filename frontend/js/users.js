// Текущая страница и фильтр
let currentPage = 1;
let currentRole = 'all';

// Маппинг ролей
const roleLabels = {
    'student': 'Ученик',
    'teacher': 'Учитель',
    'admin': 'Администратор'
};

// Загрузка пользователей с сервера
async function loadUsers(page = 1, role = 'all') {
    try {
        // Показываем индикатор загрузки
        document.getElementById('loading').style.display = 'block';
        document.getElementById('usersTable').style.display = 'none';
        document.getElementById('emptyState').style.display = 'none';
        document.getElementById('paginationNav').style.display = 'none';

        // Запрос к API с фильтром
        let url = `/api/users?page=${page}&limit=10`;
        if (role && role !== 'all') {
            url += `&role=${role}`;
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
        if (data.users.length === 0) {
            document.getElementById('emptyState').style.display = 'block';
        } else {
            renderUsers(data.users);
            renderPagination(data.pagination);
            document.getElementById('usersTable').style.display = 'table';
        }
    } catch (error) {
        console.error('Ошибка:', error);
        document.getElementById('loading').style.display = 'none';
        alert('Не удалось загрузить пользователей. Проверьте подключение к серверу.');
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

// Рендеринг списка пользователей
function renderUsers(users) {
    const tbody = document.getElementById('usersList');
    tbody.innerHTML = users.map(user => {
        const roleText = roleLabels[user.role] || user.role;
        const statusText = user.isActive ? 'Активен' : 'Неактивен';
        const statusClass = user.isActive ? 'bg-success' : 'bg-secondary';

        return `
            <tr>
                <td>${user.name}</td>
                <td>${user.email}</td>
                <td>${roleText}</td>
                <td><span class="badge ${statusClass}">${statusText}</span></td>
                <td>${formatDate(user.createdAt)}</td>
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
    loadUsers(page, currentRole);
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

// Фильтрация по роли
function filterUsers() {
    currentRole = document.getElementById('roleFilter').value;
    loadUsers(1, currentRole);
}

// Открытие формы добавления пользователя
function openAddUserModal() {
    alert('Функция регистрации пользователя будет реализована позже');
}

// Выход из системы
function logout() {
    alert('Функция выхода будет реализована позже');
}

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', () => {
    // Загружаем пользователей
    loadUsers(1);

    // Обработчик кнопки добавления пользователя
    document.getElementById('addUserBtn').addEventListener('click', openAddUserModal);

    // Обработчик кнопки выхода
    document.getElementById('logoutBtn').addEventListener('click', (e) => {
        e.preventDefault();
        logout();
    });

    // Обработчик фильтра по роли
    document.getElementById('roleFilter').addEventListener('change', filterUsers);
});
