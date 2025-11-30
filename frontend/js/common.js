// Общие функции для всех страниц

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

// Выход из системы
async function logout() {
    try {
        const response = await fetch('/api/auth/logout', { method: 'POST' });
        console.log('Logout response:', response.status);
    } catch (error) {
        console.error('Ошибка выхода:', error);
    }
    // Всегда перенаправляем на логин
    window.location.href = '/login';
}

// Загрузка текущего пользователя
async function loadCurrentUser() {
    try {
        const response = await fetch('/api/current_user');
        if (!response.ok) {
            // Не авторизован - перенаправляем на логин
            window.location.href = '/login';
            return null;
        }
        const user = await response.json();

        // Обновляем имя в хедере
        const userNameEl = document.getElementById('userName');
        if (userNameEl) {
            userNameEl.textContent = user.name;
        }

        return user;
    } catch (error) {
        console.error('Ошибка загрузки пользователя:', error);
        window.location.href = '/login';
        return null;
    }
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
