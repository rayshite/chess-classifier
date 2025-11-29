// Общие функции для всех страниц

// Выход из системы
async function logout() {
    try {
        await fetch('/api/logout', { method: 'POST' });
        window.location.href = '/login';
    } catch (error) {
        console.error('Ошибка выхода:', error);
        window.location.href = '/login';
    }
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
