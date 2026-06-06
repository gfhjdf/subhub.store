/**
 * SubHub.store Admin — API Client
 * Handles all API communication with JWT auth.
 */
const API_BASE = '/api/admin';

function getToken() {
    return localStorage.getItem('subhub_admin_token');
}

function setToken(token) {
    localStorage.setItem('subhub_admin_token', token);
}

function clearToken() {
    localStorage.removeItem('subhub_admin_token');
    localStorage.removeItem('subhub_admin_user');
}

function getAdminUser() {
    try {
        return JSON.parse(localStorage.getItem('subhub_admin_user'));
    } catch {
        return null;
    }
}

function setAdminUser(user) {
    localStorage.setItem('subhub_admin_user', JSON.stringify(user));
}

function redirectToLogin() {
    clearToken();
    window.location.href = '/admin/';
}

/**
 * Core API call function with automatic JWT handling.
 */
async function apiCall(method, path, body = null) {
    const token = getToken();
    const headers = {
        'Content-Type': 'application/json',
    };
    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }

    const opts = { method, headers };
    if (body && method !== 'GET') {
        opts.body = JSON.stringify(body);
    }

    try {
        const res = await fetch(`${API_BASE}${path}`, opts);

        if (res.status === 401) {
            redirectToLogin();
            throw new Error('Unauthorized');
        }

        if (!res.ok) {
            const err = await res.json().catch(() => ({ detail: 'Request failed' }));
            throw new Error(err.detail || `HTTP ${res.status}`);
        }

        return await res.json();
    } catch (err) {
        if (err.message === 'Unauthorized') throw err;
        console.error(`API Error [${method} ${path}]:`, err);
        throw err;
    }
}

/* ─── Convenience wrappers ─────────────────────────────────── */
const api = {
    get: (path) => apiCall('GET', path),
    post: (path, body) => apiCall('POST', path, body),
    put: (path, body) => apiCall('PUT', path, body),
    delete: (path) => apiCall('DELETE', path),
};

/* ─── Toast Notifications ──────────────────────────────────── */
function showToast(message, type = 'info') {
    let container = document.getElementById('toast-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toast-container';
        container.className = 'toast-container';
        document.body.appendChild(container);
    }

    const icons = {
        success: '✅',
        error: '❌',
        info: 'ℹ️',
    };

    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.innerHTML = `<span>${icons[type] || 'ℹ️'}</span><span>${message}</span>`;
    container.appendChild(toast);

    setTimeout(() => {
        toast.style.animation = 'toastOut 0.3s ease forwards';
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}

/* ─── Number Formatting ────────────────────────────────────── */
function formatNumber(n) {
    if (n == null) return '0';
    return Number(n).toLocaleString('en-US');
}

function formatCurrency(n) {
    if (n == null) return '0 UZS';
    return Number(n).toLocaleString('en-US') + ' UZS';
}

function formatDate(dateStr) {
    if (!dateStr) return '—';
    const d = new Date(dateStr);
    return d.toLocaleDateString('ru-RU', {
        day: '2-digit', month: 'short', year: 'numeric',
        hour: '2-digit', minute: '2-digit',
    });
}

function formatDateShort(dateStr) {
    if (!dateStr) return '—';
    const d = new Date(dateStr);
    return d.toLocaleDateString('ru-RU', { day: '2-digit', month: 'short' });
}

/* ─── Status Badge Helper ──────────────────────────────────── */
function statusBadge(status) {
    const labels = {
        created: 'Создан',
        pending_payment: 'Ожидает оплаты',
        payment_submitted: 'Чек отправлен',
        under_review: 'На проверке',
        approved: 'Одобрен',
        rejected: 'Отклонен',
        delivered: 'Доставлен',
        cancelled: 'Отменен',
        failed: 'Ошибка',
        available: 'Доступен',
        reserved: 'Зарезервирован',
        sold: 'Продан',
        disabled: 'Отключен',
        credited: 'Начислено',
        flagged: 'Подозрительный',
        revoked: 'Отозван',
        new: 'Новый',
        seen: 'Просмотрен',
        resolved: 'Решен',
    };
    return `<span class="badge badge-${status}">${labels[status] || status}</span>`;
}

/* ─── Confirm Dialog ───────────────────────────────────────── */
function showConfirm(title, message, icon, onConfirm, confirmBtnClass = 'btn-primary') {
    let overlay = document.getElementById('confirm-overlay');
    if (!overlay) {
        overlay = document.createElement('div');
        overlay.id = 'confirm-overlay';
        overlay.className = 'confirm-overlay';
        document.body.appendChild(overlay);
    }

    overlay.innerHTML = `
        <div class="confirm-dialog">
            <div class="confirm-icon">${icon}</div>
            <h3>${title}</h3>
            <p>${message}</p>
            <div class="confirm-actions">
                <button class="btn btn-outline" id="confirm-cancel">Отмена</button>
                <button class="btn ${confirmBtnClass}" id="confirm-ok">Подтвердить</button>
            </div>
        </div>
    `;
    overlay.classList.add('active');

    document.getElementById('confirm-cancel').onclick = () => overlay.classList.remove('active');
    document.getElementById('confirm-ok').onclick = () => {
        overlay.classList.remove('active');
        onConfirm();
    };
}

/* ─── Pagination Helper ────────────────────────────────────── */
function renderPagination(container, total, limit, offset, onPageChange) {
    const totalPages = Math.ceil(total / limit);
    const currentPage = Math.floor(offset / limit) + 1;

    if (totalPages <= 1) {
        container.innerHTML = '';
        return;
    }

    let html = '';
    html += `<button class="btn btn-outline btn-sm" ${currentPage <= 1 ? 'disabled' : ''} data-page="${currentPage - 1}">‹ Назад</button>`;
    html += `<span class="pagination-info">Страница ${currentPage} из ${totalPages} (всего ${formatNumber(total)})</span>`;
    html += `<button class="btn btn-outline btn-sm" ${currentPage >= totalPages ? 'disabled' : ''} data-page="${currentPage + 1}">Вперед ›</button>`;

    container.innerHTML = html;
    container.querySelectorAll('[data-page]').forEach(btn => {
        if (!btn.disabled) {
            btn.addEventListener('click', () => {
                const page = parseInt(btn.dataset.page);
                onPageChange((page - 1) * limit);
            });
        }
    });
}

/* ─── Sidebar Active State ─────────────────────────────────── */
function initSidebar() {
    const path = window.location.pathname;
    document.querySelectorAll('.nav-item').forEach(item => {
        const href = item.getAttribute('href');
        if (href && path.endsWith(href.replace('/admin/', ''))) {
            item.classList.add('active');
        }
    });

    // Mobile toggle
    const toggle = document.getElementById('menu-toggle');
    const sidebar = document.querySelector('.sidebar');
    const overlay = document.getElementById('sidebar-overlay');

    if (toggle && sidebar) {
        toggle.addEventListener('click', () => {
            sidebar.classList.toggle('open');
            if (overlay) overlay.classList.toggle('active');
        });
    }

    if (overlay) {
        overlay.addEventListener('click', () => {
            sidebar.classList.remove('open');
            overlay.classList.remove('active');
        });
    }

    // Set admin name
    const admin = getAdminUser();
    const adminNameEl = document.getElementById('admin-name');
    if (adminNameEl && admin) {
        adminNameEl.textContent = admin.username || 'Admin';
    }
    const adminAvatarEl = document.getElementById('admin-avatar');
    if (adminAvatarEl && admin) {
        adminAvatarEl.textContent = (admin.username || 'A').charAt(0).toUpperCase();
    }

    // Fetch and update badges
    api.get('/dashboard/summary')
        .then(summary => {
            const pendingBadge = document.getElementById('nav-pending-badge');
            if (pendingBadge) {
                if (summary.pending_orders > 0) {
                    pendingBadge.textContent = summary.pending_orders;
                    pendingBadge.style.display = 'inline-block';
                } else {
                    pendingBadge.style.display = 'none';
                }
            }
            const redBadgeEl = document.getElementById('nav-redemptions-badge');
            if (redBadgeEl) {
                const count = summary.pending_redemptions_count || 0;
                if (count > 0) {
                    redBadgeEl.textContent = count;
                    redBadgeEl.style.display = 'inline-block';
                } else {
                    redBadgeEl.style.display = 'none';
                }
            }
            const topupBadgeEl = document.getElementById('nav-topups-badge');
            if (topupBadgeEl) {
                const count = summary.pending_topups_count || 0;
                if (count > 0) {
                    topupBadgeEl.textContent = count;
                    topupBadgeEl.style.display = 'inline-block';
                } else {
                    topupBadgeEl.style.display = 'none';
                }
            }
        })
        .catch(err => console.error('Failed to load sidebar badges:', err));
}

/* ─── Modal Helpers ────────────────────────────────────────── */
function openModal(id) {
    const el = document.getElementById(id);
    if (el) el.classList.add('active');
}

function closeModal(id) {
    const el = document.getElementById(id);
    if (el) el.classList.remove('active');
}

/* ─── Loading State ────────────────────────────────────────── */
function showLoading(container) {
    container.innerHTML = `
        <div class="loading-container">
            <div class="spinner spinner-lg"></div>
            <span>Загрузка...</span>
        </div>
    `;
}

/* ─── Escape HTML ──────────────────────────────────────────── */
function escapeHtml(str) {
    if (!str) return '';
    const div = document.createElement('div');
    div.appendChild(document.createTextNode(str));
    return div.innerHTML;
}
