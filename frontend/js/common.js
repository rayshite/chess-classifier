// Общие функции для всех страниц

// API клиент с централизованной обработкой ошибок
const api = {
    async request(url, options = {}) {
        try {
            const response = await fetch(url, options);

            // Редирект на логин при 401
            if (response.status === 401) {
                window.location.href = '/login';
                return null;
            }

            return response;
        } catch (error) {
            console.error('API ошибка:', error);
            throw error;
        }
    },

    async get(url) {
        return this.request(url);
    },

    async post(url, data) {
        return this.request(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
    },

    async postForm(url, formData) {
        return this.request(url, {
            method: 'POST',
            body: formData
        });
    },

    async patch(url, data) {
        return this.request(url, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
    },

    async delete(url) {
        return this.request(url, { method: 'DELETE' });
    }
};

// Маппинг ролей
const roleLabels = {
    'student': 'Ученик',
    'teacher': 'Учитель',
    'admin': 'Администратор'
};

// Экранирование HTML для предотвращения XSS
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Форматирование даты (в московском часовом поясе)
function formatDate(isoString) {
    const date = new Date(isoString);
    return date.toLocaleDateString('ru-RU', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        timeZone: 'Europe/Moscow'
    });
}

// Форматирование даты и времени (в московском часовом поясе)
function formatDateTime(isoString) {
    const date = new Date(isoString);
    return date.toLocaleDateString('ru-RU', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        timeZone: 'Europe/Moscow'
    });
}

// Показать модальное окно ошибки
let errorModal = null;

function showError(message) {
    if (!errorModal) {
        errorModal = new bootstrap.Modal(document.getElementById('errorModal'));
    }
    document.getElementById('errorMessage').textContent = message;
    errorModal.show();
}

// Загрузка данных списка с пагинацией и фильтрацией
async function loadListData(options) {
    const {
        apiUrl,
        filterParam,
        filterValue,
        page,
        tableId,
        dataKey,
        renderFn,
        onPageChange,
        errorMessage
    } = options;

    try {
        // Показываем индикатор загрузки
        document.getElementById('loading').style.display = 'block';
        document.getElementById(tableId).style.display = 'none';
        document.getElementById('emptyState').style.display = 'none';
        document.getElementById('paginationNav').style.display = 'none';

        // Запрос к API с фильтром
        let url = `${apiUrl}?page=${page}`;
        if (filterValue && filterValue !== 'all') {
            url += `&${filterParam}=${filterValue}`;
        }

        const response = await api.get(url);
        if (!response || !response.ok) {
            throw new Error('Ошибка загрузки данных');
        }

        const data = await response.json();

        // Скрываем индикатор загрузки
        document.getElementById('loading').style.display = 'none';

        // Отображаем данные
        const items = data[dataKey];
        if (items.length === 0) {
            document.getElementById('emptyState').style.display = 'block';
        } else {
            renderFn(items);
            renderPagination(data.pagination, onPageChange);
            document.getElementById(tableId).style.display = 'table';
        }

        return data;
    } catch (error) {
        console.error('Ошибка:', error);
        document.getElementById('loading').style.display = 'none';
        showError(errorMessage);
        return null;
    }
}

// Рендеринг пагинации
function renderPagination(pagination, onPageChange) {
    const { currentPage, totalPages } = pagination;

    if (totalPages <= 1) {
        document.getElementById('paginationNav').style.display = 'none';
        return;
    }

    const paginationEl = document.getElementById('pagination');
    paginationEl.innerHTML = '';

    // Кнопка "Назад"
    const prevLi = document.createElement('li');
    prevLi.className = `page-item ${currentPage === 1 ? 'disabled' : ''}`;
    const prevLink = document.createElement('a');
    prevLink.className = 'page-link';
    prevLink.href = '#';
    prevLink.textContent = 'Назад';
    if (currentPage > 1) {
        prevLink.addEventListener('click', (e) => {
            e.preventDefault();
            onPageChange(currentPage - 1);
        });
    }
    prevLi.appendChild(prevLink);
    paginationEl.appendChild(prevLi);

    // Номера страниц
    for (let i = 1; i <= totalPages; i++) {
        const li = document.createElement('li');
        li.className = `page-item ${i === currentPage ? 'active' : ''}`;
        const link = document.createElement('a');
        link.className = 'page-link';
        link.href = '#';
        link.textContent = i;
        link.addEventListener('click', (e) => {
            e.preventDefault();
            onPageChange(i);
        });
        li.appendChild(link);
        paginationEl.appendChild(li);
    }

    // Кнопка "Вперёд"
    const nextLi = document.createElement('li');
    nextLi.className = `page-item ${currentPage === totalPages ? 'disabled' : ''}`;
    const nextLink = document.createElement('a');
    nextLink.className = 'page-link';
    nextLink.href = '#';
    nextLink.textContent = 'Вперёд';
    if (currentPage < totalPages) {
        nextLink.addEventListener('click', (e) => {
            e.preventDefault();
            onPageChange(currentPage + 1);
        });
    }
    nextLi.appendChild(nextLink);
    paginationEl.appendChild(nextLi);

    document.getElementById('paginationNav').style.display = 'block';
}

// Выход из системы
async function logout() {
    await api.request('/api/auth/logout', { method: 'POST' });
    window.location.href = '/login';
}

// Загрузка текущего пользователя
async function loadCurrentUser() {
    const response = await api.get('/api/current_user');
    if (!response || !response.ok) {
        return null;
    }

    const user = await response.json();

    // Обновляем имя в хедере
    const userNameEl = document.getElementById('userName');
    if (userNameEl) {
        userNameEl.textContent = user.name;
    }

    return user;
}

// Инициализация общих элементов
document.addEventListener('DOMContentLoaded', () => {
    // Загружаем текущего пользователя
    loadCurrentUser();

    // Обработчик кнопки выхода
    const logoutBtn = document.getElementById('logoutBtn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', (e) => {
            e.preventDefault();
            logout();
        });
    }
});
