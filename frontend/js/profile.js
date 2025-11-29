// Маппинг ролей
const roleLabels = {
    'student': 'Ученик',
    'teacher': 'Учитель',
    'admin': 'Администратор'
};

// Текущий email пользователя
let currentEmail = '';

// Загрузка профиля
async function loadProfile() {
    try {
        const response = await fetch('/api/current_user');
        if (!response.ok) {
            throw new Error('Ошибка загрузки профиля');
        }

        const user = await response.json();
        currentEmail = user.email;

        // Заполняем данные
        document.getElementById('profileName').textContent = user.name;
        document.getElementById('profileEmail').textContent = user.email;
        document.getElementById('profileRole').textContent = roleLabels[user.role] || user.role;

        // Показываем профиль
        document.getElementById('loading').style.display = 'none';
        document.getElementById('profileInfo').style.display = 'block';

    } catch (error) {
        console.error('Ошибка:', error);
        document.getElementById('loading').innerHTML = '<p class="text-danger">Ошибка загрузки профиля</p>';
    }
}

// Открытие модального окна редактирования
function openEditModal() {
    document.getElementById('editEmail').value = currentEmail;
    document.getElementById('editPassword').value = '';
    document.getElementById('editError').style.display = 'none';
}

// Сохранение профиля
async function saveProfile() {
    const email = document.getElementById('editEmail').value.trim();
    const password = document.getElementById('editPassword').value;
    const errorEl = document.getElementById('editError');
    const saveBtn = document.getElementById('saveProfileBtn');

    errorEl.style.display = 'none';

    // Формируем данные для обновления
    const data = {};
    if (email !== currentEmail) {
        data.email = email;
    }
    if (password) {
        if (password.length < 6) {
            errorEl.textContent = 'Пароль должен быть не менее 6 символов';
            errorEl.style.display = 'block';
            return;
        }
        data.password = password;
    }

    if (Object.keys(data).length === 0) {
        bootstrap.Modal.getInstance(document.getElementById('editProfileModal')).hide();
        return;
    }

    saveBtn.disabled = true;
    saveBtn.textContent = 'Сохранение...';

    try {
        const response = await fetch('/api/users/me', {
            method: 'PATCH',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });

        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.detail || 'Ошибка сохранения');
        }

        // Обновляем данные на странице
        if (data.email) {
            currentEmail = data.email;
            document.getElementById('profileEmail').textContent = data.email;
        }

        // Закрываем модальное окно
        bootstrap.Modal.getInstance(document.getElementById('editProfileModal')).hide();

    } catch (error) {
        errorEl.textContent = error.message;
        errorEl.style.display = 'block';
    } finally {
        saveBtn.disabled = false;
        saveBtn.textContent = 'Сохранить';
    }
}

// Инициализация
document.addEventListener('DOMContentLoaded', () => {
    loadProfile();

    // Обработчик открытия модального окна
    document.getElementById('editProfileModal').addEventListener('show.bs.modal', openEditModal);

    // Обработчик сохранения
    document.getElementById('saveProfileBtn').addEventListener('click', saveProfile);
});
