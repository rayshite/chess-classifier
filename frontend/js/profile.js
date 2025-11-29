// Маппинг ролей
const roleLabels = {
    'student': 'Ученик',
    'teacher': 'Учитель',
    'admin': 'Администратор'
};

// Загрузка профиля
async function loadProfile() {
    try {
        const response = await fetch('/api/current_user');
        if (!response.ok) {
            throw new Error('Ошибка загрузки профиля');
        }

        const user = await response.json();

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

// Инициализация
document.addEventListener('DOMContentLoaded', loadProfile);
