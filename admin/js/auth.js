/**
 * SubHub.store Admin — Auth Module
 * Login, logout, and auth check.
 */

/**
 * Initialize login form handling (for index.html only).
 */
function initLoginForm() {
    const form = document.getElementById('login-form');
    if (!form) return;

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const btn = form.querySelector('button[type="submit"]');
        const errorEl = document.getElementById('login-error');
        const username = document.getElementById('login-username').value.trim();
        const password = document.getElementById('login-password').value;

        if (!username || !password) {
            errorEl.textContent = 'Пожалуйста, введите имя пользователя и пароль';
            errorEl.classList.add('show');
            return;
        }

        btn.disabled = true;
        btn.innerHTML = '<span class="spinner"></span> Вход...';
        errorEl.classList.remove('show');

        try {
            const data = await apiCall('POST', '/auth/login', { username, password });
            setToken(data.access_token);
            setAdminUser(data.admin);
            window.location.href = '/admin/dashboard.html';
        } catch (err) {
            errorEl.textContent = err.message || 'Неверные учетные данные';
            errorEl.classList.add('show');
            btn.disabled = false;
            btn.innerHTML = 'Войти';
        }
    });
}

/**
 * Check auth for protected pages. Redirect to login if not authenticated.
 */
function requireAuth() {
    const token = getToken();
    if (!token) {
        redirectToLogin();
        return false;
    }
    return true;
}

/**
 * Logout function.
 */
async function logout() {
    try {
        await api.post('/auth/logout');
    } catch (e) {
        // ignore errors on logout
    }
    clearToken();
    window.location.href = '/admin/';
}

/**
 * Setup logout button.
 */
function initLogout() {
    const logoutBtn = document.getElementById('logout-btn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', (e) => {
            e.preventDefault();
            logout();
        });
    }
}
