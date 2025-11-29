// Обработка формы входа
document.getElementById('loginForm').addEventListener('submit', async (e) => {
    e.preventDefault();

    const email = document.getElementById('email').value.trim();
    const password = document.getElementById('password').value;
    const errorEl = document.getElementById('loginError');
    const loginBtn = document.getElementById('loginBtn');

    errorEl.style.display = 'none';

    if (!email || !password) {
        errorEl.textContent = 'Заполните все поля';
        errorEl.style.display = 'block';
        return;
    }

    // Блокируем кнопку
    loginBtn.disabled = true;
    loginBtn.textContent = 'Вход...';

    try {
        const response = await fetch('/api/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ email, password })
        });

        if (!response.ok) {
            const data = await response.json();
            throw new Error(data.detail || 'Ошибка входа');
        }

        // Успешный вход - перенаправляем на главную
        window.location.href = '/';

    } catch (error) {
        errorEl.textContent = error.message;
        errorEl.style.display = 'block';
    } finally {
        loginBtn.disabled = false;
        loginBtn.textContent = 'Войти';
    }
});
