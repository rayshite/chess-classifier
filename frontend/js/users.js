// Текущая страница и фильтр
let currentPage = 1;
let currentRole = 'all';

// Загрузка пользователей с сервера
async function loadUsers(page = 1, role = 'all') {
    const data = await loadListData({
        apiUrl: '/api/users',
        filterParam: 'role',
        filterValue: role,
        page: page,
        tableId: 'usersTable',
        dataKey: 'users',
        renderFn: renderUsers,
        onPageChange: changePage,
        errorMessage: 'Не удалось загрузить пользователей.'
    });
    if (data) {
        currentPage = data.pagination.currentPage;
    }
}

// Классы для ролей
const roleClasses = {
    'student': 'bg-light text-dark',
    'teacher': 'bg-secondary',
    'admin': 'bg-primary'
};

// Кэш пользователей для редактирования
let usersCache = {};

// Рендеринг списка пользователей
function renderUsers(users) {
    // Сохраняем данные в кэш
    usersCache = {};
    users.forEach(user => {
        usersCache[user.id] = user;
    });

    const tbody = document.getElementById('usersList');
    tbody.innerHTML = users.map(user => {
        const roleText = roleLabels[user.role] || user.role;
        const roleClass = roleClasses[user.role] || 'bg-secondary';
        const statusText = user.isActive ? 'Активен' : 'Неактивен';
        const statusClass = user.isActive ? 'bg-primary' : 'bg-light text-dark';

        return `
            <tr>
                <td>${escapeHtml(user.name)}</td>
                <td>${escapeHtml(user.email)}</td>
                <td><span class="badge ${roleClass}">${roleText}</span></td>
                <td><span class="badge ${statusClass}">${statusText}</span></td>
                <td>${formatDate(user.createdAt)}</td>
                <td>
                    <button class="btn btn-sm btn-primary edit-user-btn" data-user-id="${user.id}">
                        <i class="bi bi-pencil"></i>
                    </button>
                </td>
            </tr>
        `;
    }).join('');
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

// Модальные окна
let addUserModal;
let editUserModal;
let tempPasswordModal;

// Открытие формы добавления пользователя
function openAddUserModal() {
    // Очищаем форму
    document.getElementById('addUserForm').reset();
    document.getElementById('addUserError').style.display = 'none';

    // Открываем модальное окно
    addUserModal.show();
}

// Отправка формы регистрации
async function submitUser() {
    const name = document.getElementById('newUserName').value.trim();
    const email = document.getElementById('newUserEmail').value.trim();
    const role = document.getElementById('newUserRole').value;

    const errorEl = document.getElementById('addUserError');
    errorEl.style.display = 'none';

    // Валидация на клиенте
    if (!name || !email) {
        errorEl.textContent = 'Заполните все обязательные поля';
        errorEl.style.display = 'block';
        return;
    }

    // Блокируем кнопку на время запроса
    const submitBtn = document.getElementById('submitUserBtn');
    submitBtn.disabled = true;
    submitBtn.textContent = 'Регистрация...';

    try {
        const response = await api.post('/api/users', { name, email, role });

        if (!response || !response.ok) {
            const data = response ? await response.json() : {};
            let errorMessage = 'Ошибка при создании пользователя';
            if (Array.isArray(data.detail)) {
                const emailError = data.detail.find(e => e.loc && e.loc.includes('email'));
                if (emailError) {
                    errorMessage = 'Введите корректный email адрес';
                } else {
                    errorMessage = 'Проверьте правильность заполнения полей';
                }
            } else if (typeof data.detail === 'string') {
                errorMessage = data.detail;
            }
            throw new Error(errorMessage);
        }

        const data = await response.json();

        // Закрываем модальное окно и показываем временный пароль
        addUserModal.hide();
        document.getElementById('tempPasswordValue').textContent = data.temporaryPassword;
        tempPasswordModal.show();

        loadUsers(1, currentRole);

    } catch (error) {
        errorEl.textContent = error.message;
        errorEl.style.display = 'block';
    } finally {
        submitBtn.disabled = false;
        submitBtn.textContent = 'Зарегистрировать';
    }
}

// Открытие модального окна редактирования
function openEditUserModal(userId) {
    const user = usersCache[userId];
    if (!user) return;

    document.getElementById('editUserId').value = user.id;
    document.getElementById('editUserName').value = user.name;
    document.getElementById('editUserEmail').value = user.email;
    document.getElementById('editUserRole').value = user.role;
    document.getElementById('editUserActive').checked = user.isActive;
    document.getElementById('editUserError').style.display = 'none';

    editUserModal.show();
}

// Сохранение изменений пользователя
async function saveUser() {
    const userId = document.getElementById('editUserId').value;
    const name = document.getElementById('editUserName').value.trim();
    const email = document.getElementById('editUserEmail').value.trim();
    const role = document.getElementById('editUserRole').value;
    const isActive = document.getElementById('editUserActive').checked;

    const errorEl = document.getElementById('editUserError');
    const saveBtn = document.getElementById('saveUserBtn');

    errorEl.style.display = 'none';
    saveBtn.disabled = true;
    saveBtn.textContent = 'Сохранение...';

    try {
        const response = await api.patch(`/api/users/${userId}`, { name, email, role, isActive });

        if (!response || !response.ok) {
            const data = response ? await response.json() : {};
            let errorMessage = 'Ошибка сохранения';
            if (Array.isArray(data.detail)) {
                const emailError = data.detail.find(e => e.loc && e.loc.includes('email'));
                if (emailError) {
                    errorMessage = 'Введите корректный email адрес';
                } else {
                    errorMessage = 'Проверьте правильность заполнения полей';
                }
            } else if (typeof data.detail === 'string') {
                errorMessage = data.detail;
            }
            throw new Error(errorMessage);
        }

        editUserModal.hide();
        loadUsers(currentPage, currentRole);

    } catch (error) {
        errorEl.textContent = error.message;
        errorEl.style.display = 'block';
    } finally {
        saveBtn.disabled = false;
        saveBtn.textContent = 'Сохранить';
    }
}

// Сброс пароля пользователя
async function resetPassword() {
    const userId = document.getElementById('editUserId').value;
    const resetBtn = document.getElementById('resetPasswordBtn');

    resetBtn.disabled = true;
    resetBtn.innerHTML = '<span class="spinner-border spinner-border-sm"></span>';

    try {
        const response = await api.request(`/api/users/${userId}/reset-password`, { method: 'POST' });

        if (!response || !response.ok) {
            const data = response ? await response.json() : {};
            throw new Error(data.detail || 'Ошибка сброса пароля');
        }

        const data = await response.json();

        // Показываем временный пароль
        document.getElementById('tempPasswordValue').textContent = data.temporaryPassword;
        editUserModal.hide();
        tempPasswordModal.show();

    } catch (error) {
        document.getElementById('editUserError').textContent = error.message;
        document.getElementById('editUserError').style.display = 'block';
    } finally {
        resetBtn.disabled = false;
        resetBtn.innerHTML = '<i class="bi bi-key"></i> Сбросить пароль';
    }
}

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', () => {
    // Инициализируем модальные окна
    addUserModal = new bootstrap.Modal(document.getElementById('addUserModal'));
    editUserModal = new bootstrap.Modal(document.getElementById('editUserModal'));
    tempPasswordModal = new bootstrap.Modal(document.getElementById('tempPasswordModal'));

    // Загружаем пользователей
    loadUsers(1);

    // Обработчик кнопки добавления пользователя
    document.getElementById('addUserBtn').addEventListener('click', openAddUserModal);

    // Обработчик кнопки отправки формы
    document.getElementById('submitUserBtn').addEventListener('click', submitUser);

    // Обработчик фильтра по роли
    document.getElementById('roleFilter').addEventListener('change', filterUsers);

    // Обработчики редактирования
    document.getElementById('saveUserBtn').addEventListener('click', saveUser);
    document.getElementById('resetPasswordBtn').addEventListener('click', resetPassword);

    // Делегирование событий для кнопок редактирования пользователей
    document.getElementById('usersList').addEventListener('click', (e) => {
        const btn = e.target.closest('.edit-user-btn');
        if (btn) {
            const userId = parseInt(btn.dataset.userId);
            openEditUserModal(userId);
        }
    });
});
