/**
 * SubHub.store Admin — Users & Referrals Module
 */

let activePageTab = 'users';
let activeModalTab = 'info';

let currentUsersOffset = 0;
let currentReferralsOffset = 0;
const currentLimit = 15;
let activeModalUserId = null;

function switchPageTab(tab) {
    activePageTab = tab;
    document.querySelectorAll('.page-tab-btn').forEach(btn => {
        btn.classList.toggle('active', btn.id === `tab-btn-${tab}`);
    });

    document.getElementById('section-users').style.display = tab === 'users' ? 'block' : 'none';
    document.getElementById('section-referrals').style.display = tab === 'referrals' ? 'block' : 'none';
    document.getElementById('section-alerts').style.display = tab === 'alerts' ? 'block' : 'none';

    if (tab === 'users') loadUsers(0);
    if (tab === 'referrals') loadReferrals(0);
    if (tab === 'alerts') loadAlerts();
}

function switchModalTab(tab) {
    activeModalTab = tab;
    document.querySelectorAll('.modal-tab').forEach(btn => {
        btn.classList.toggle('active', btn.id === `m-tab-${tab}`);
    });

    document.getElementById('m-content-info').style.display = tab === 'info' ? 'block' : 'none';
    document.getElementById('m-content-orders').style.display = tab === 'orders' ? 'block' : 'none';
    document.getElementById('m-content-txs').style.display = tab === 'txs' ? 'block' : 'none';
    document.getElementById('m-content-points').style.display = tab === 'points' ? 'block' : 'none';
    document.getElementById('m-content-refs').style.display = tab === 'refs' ? 'block' : 'none';
}

async function initUsers() {
    // Search listener
    const searchInput = document.getElementById('search-users');
    searchInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            loadUsers(0);
        }
    });

    // Check query params to switch tabs or open users
    const params = new URLSearchParams(window.location.search);
    const tabParam = params.get('tab');
    if (tabParam === 'alerts') {
        switchPageTab('alerts');
    } else {
        switchPageTab('users');
    }
}

// ─── LOAD USERS LIST ────────────────────────────────────────

async function loadUsers(offset = 0) {
    currentUsersOffset = offset;
    const tableBody = document.getElementById('users-table-body');
    showLoading(tableBody);

    const search = document.getElementById('search-users').value.trim();
    let path = `/users?limit=${currentLimit}&offset=${currentUsersOffset}`;
    if (search) path += `&search=${encodeURIComponent(search)}`;

    try {
        const data = await api.get(path);
        const users = data.users || [];

        if (users.length === 0) {
            tableBody.innerHTML = '<tr><td colspan="8" class="text-center text-muted" style="padding: 40px;">Пользователи не найдены.</td></tr>';
            document.getElementById('users-pagination-container').innerHTML = '';
            return;
        }

        let html = '';
        users.forEach(u => {
            const userStr = u.telegram_username ? `@${u.telegram_username}` : '—';
            html += `
                <tr style="cursor: pointer;" onclick="openUserModal(${u.id})">
                    <td><code>${u.telegram_id}</code></td>
                    <td>
                        <div style="font-weight: 500;">${escapeHtml(u.first_name || 'User')} ${escapeHtml(u.last_name || '')}</div>
                        <div class="text-muted" style="font-size: 11px;">${escapeHtml(userStr)}</div>
                    </td>
                    <td><span style="font-size: 11px; font-weight: 600; text-transform: uppercase;">${escapeHtml(u.language_code || 'ru')}</span></td>
                    <td>
                        <span style="font-weight: 600; color: var(--accent-cyan);">${formatCurrency(u.balance_uzs)}</span>
                        <button class="btn btn-outline btn-sm" onclick="event.stopPropagation(); promptAdjustBalance(${u.id}, ${u.balance_uzs})" style="padding: 1px 6px; font-size: 11px; margin-left: 8px; border-radius: 4px; display: inline-flex; align-items: center; justify-content: center; height: 20px; line-height: 1;" title="Изменить баланс кошелька">+</button>
                    </td>
                    <td>
                        <span style="font-weight: 600; color: var(--accent-purple-light);">${formatNumber(u.points_balance)}</span>
                        <button class="btn btn-outline btn-sm" onclick="event.stopPropagation(); promptAdjustPoints(${u.id}, ${u.points_balance})" style="padding: 1px 6px; font-size: 11px; margin-left: 8px; border-radius: 4px; display: inline-flex; align-items: center; justify-content: center; height: 20px; line-height: 1;" title="Изменить баланс баллов">+</button>
                    </td>
                    <td><code>${escapeHtml(u.referral_code)}</code></td>
                    <td>${formatDateShort(u.created_at)}</td>
                    <td class="text-right">
                        <button class="btn btn-outline btn-sm" onclick="event.stopPropagation(); openUserModal(${u.id})">Профиль</button>
                    </td>
                </tr>
            `;
        });
        tableBody.innerHTML = html;

        renderPagination(
            document.getElementById('users-pagination-container'),
            data.total,
            currentLimit,
            currentUsersOffset,
            loadUsers
        );

    } catch (err) {
        tableBody.innerHTML = `<tr><td colspan="8" class="text-center text-danger" style="padding: 40px;">Ошибка: ${escapeHtml(err.message)}</td></tr>`;
    }
}

// ─── LOAD REFERRAL HISTORY ──────────────────────────────────

async function loadReferrals(offset = 0) {
    currentReferralsOffset = offset;
    const tableBody = document.getElementById('referrals-table-body');
    showLoading(tableBody);

    try {
        const data = await api.get(`/referrals?limit=${currentLimit}&offset=${currentReferralsOffset}`);
        const referrals = data.referrals || [];

        if (referrals.length === 0) {
            tableBody.innerHTML = '<tr><td colspan="7" class="text-center text-muted" style="padding: 40px;">Реферальные связи не зарегистрированы.</td></tr>';
            document.getElementById('referrals-pagination-container').innerHTML = '';
            return;
        }

        let html = '';
        referrals.forEach(r => {
            const inviterUser = r.inviter_username ? `@${r.inviter_username}` : 'User';
            const invitedUser = r.invited_username ? `@${r.invited_username}` : 'User';
            const rowClass = r.status === 'flagged' ? 'style="background: rgba(239, 68, 68, 0.03);"' : '';

            html += `
                <tr ${rowClass}>
                    <td>
                        <div style="font-weight: 500;">${escapeHtml(inviterUser)}</div>
                    </td>
                    <td><code>${r.inviter_telegram_id}</code></td>
                    <td>
                        <div style="font-weight: 500;">${escapeHtml(invitedUser)}</div>
                    </td>
                    <td><code>${r.invited_telegram_id}</code></td>
                    <td>${formatCurrency(r.reward_uzs)}</td>
                    <td>${statusBadge(r.status)}</td>
                    <td>${formatDate(r.created_at)}</td>
                </tr>
            `;
        });
        tableBody.innerHTML = html;

        renderFakePagination(
            document.getElementById('referrals-pagination-container'),
            referrals.length,
            currentLimit,
            currentReferralsOffset,
            loadReferrals
        );

    } catch (err) {
        tableBody.innerHTML = `<tr><td colspan="7" class="text-center text-danger" style="padding: 40px;">Ошибка: ${escapeHtml(err.message)}</td></tr>`;
    }
}

// ─── LOAD SECURITY ALERTS ───────────────────────────────────

async function loadAlerts() {
    const tableBody = document.getElementById('alerts-table-body');
    showLoading(tableBody);

    try {
        const data = await api.get('/alerts');
        const alerts = data.alerts || [];

        if (alerts.length === 0) {
            tableBody.innerHTML = '<tr><td colspan="6" class="text-center text-muted" style="padding: 40px;">Нет предупреждений. Реферальная система в безопасности.</td></tr>';
            return;
        }

        let html = '';
        alerts.forEach(a => {
            const username = a.telegram_username ? `@${a.telegram_username}` : 'User';
            const statusStyle = a.status === 'new' ? 'color: var(--danger); font-weight: 600;' : 'color: var(--text-muted);';
            html += `
                <tr>
                    <td><strong>${escapeHtml(username)}</strong></td>
                    <td><code>${a.alert_user_telegram_id}</code></td>
                    <td><span class="badge badge-danger">${escapeHtml(a.type)}</span></td>
                    <td>${escapeHtml(a.details || a.description || '')}</td>
                    <td><span style="${statusStyle}">${escapeHtml(a.status).toUpperCase()}</span></td>
                    <td>${formatDate(a.created_at)}</td>
                </tr>
            `;
        });
        tableBody.innerHTML = html;
    } catch (err) {
        tableBody.innerHTML = `<tr><td colspan="6" class="text-center text-danger" style="padding: 40px;">Ошибка: ${escapeHtml(err.message)}</td></tr>`;
    }
}

// ─── USER DETAIL MODAL ──────────────────────────────────────

async function openUserModal(userId) {
    activeModalUserId = userId;
    switchModalTab('info');
    openModal('user-detail-modal');

    const infoGrid = document.getElementById('user-info-detail');
    infoGrid.innerHTML = '<div style="grid-column: 1 / -1;" class="loading-container"><div class="spinner"></div></div>';

    document.getElementById('m-orders-count').textContent = '0';
    document.getElementById('m-orders-tbody').innerHTML = '<tr><td colspan="5" class="text-center text-muted">Загрузка...</td></tr>';
    document.getElementById('m-txs-tbody').innerHTML = '<tr><td colspan="4" class="text-center text-muted">Загрузка...</td></tr>';
    document.getElementById('m-points-tbody').innerHTML = '<tr><td colspan="4" class="text-center text-muted">Загрузка...</td></tr>';
    document.getElementById('m-refs-tbody').innerHTML = '<tr><td colspan="3" class="text-center text-muted">Загрузка...</td></tr>';

    try {
        const [userData, ordersData, txsData, pointsData] = await Promise.all([
            api.get(`/users/${userId}`),
            api.get(`/users/${userId}/orders`),
            api.get(`/users/${userId}/wallet-transactions`),
            api.get(`/users/${userId}/points-transactions`)
        ]);

        const user = userData.user;
        const refInfo = userData.referral_info;
        const orders = ordersData.orders || [];
        const txs = txsData.transactions || [];
        const points = pointsData.transactions || [];

        // 1. Info Panel
        infoGrid.innerHTML = `
            <div>
                <table class="detail-table" style="width: 100%;">
                    <tr><td style="padding: 6px 0; font-weight:600;">Username в Telegram:</td><td>${user.telegram_username ? `@${escapeHtml(user.telegram_username)}` : '—'}</td></tr>
                    <tr><td style="padding: 6px 0; font-weight:600;">Имя:</td><td>${escapeHtml(user.first_name || '—')}</td></tr>
                    <tr><td style="padding: 6px 0; font-weight:600;">Фамилия:</td><td>${escapeHtml(user.last_name || '—')}</td></tr>
                    <tr><td style="padding: 6px 0; font-weight:600;">Telegram ID:</td><td><code>${user.telegram_id}</code></td></tr>
                </table>
            </div>
            <div>
                <table class="detail-table" style="width: 100%;">
                    <tr>
                        <td style="padding: 6px 0; font-weight:600;">Баланс кошелька:</td>
                        <td>
                            <strong style="color:var(--accent-cyan); font-size:16px;">${formatCurrency(user.balance_uzs)}</strong>
                            <button type="button" class="btn btn-outline btn-sm" style="margin-left: 10px; padding: 2px 8px; font-size: 11px;" onclick="promptAdjustBalance(${user.id}, ${user.balance_uzs})">Изменить</button>
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 6px 0; font-weight:600;">Баланс баллов:</td>
                        <td>
                            <strong style="color:var(--accent-purple-light); font-size:16px;">${formatNumber(user.points_balance)}</strong>
                            <button type="button" class="btn btn-outline btn-sm" style="margin-left: 10px; padding: 2px 8px; font-size: 11px;" onclick="promptAdjustPoints(${user.id}, ${user.points_balance})">Изменить</button>
                        </td>
                    </tr>
                    <tr><td style="padding: 6px 0; font-weight:600;">Реф. код:</td><td><code>${escapeHtml(user.referral_code)}</code></td></tr>
                    <tr><td style="padding: 6px 0; font-weight:600;">Предпочитаемый язык:</td><td>${user.language_code === 'uz' ? 'Узбекский 🇺🇿' : 'Русский 🇷🇺'}</td></tr>
                    <tr><td style="padding: 6px 0; font-weight:600;">Дата регистрации:</td><td>${formatDate(user.created_at)}</td></tr>
                </table>
            </div>
        `;

        // 2. Orders Panel
        document.getElementById('m-orders-count').textContent = orders.length;
        if (orders.length === 0) {
            document.getElementById('m-orders-tbody').innerHTML = '<tr><td colspan="5" class="text-center text-muted" style="padding: 20px;">Пользователь еще не совершал заказов.</td></tr>';
        } else {
            let html = '';
            orders.forEach(o => {
                html += `
                    <tr style="cursor:pointer;" onclick="closeModal('user-detail-modal'); window.location.href='/admin/orders.html?id=${o.id}'">
                        <td><strong>#${escapeHtml(o.public_order_id)}</strong></td>
                        <td>${escapeHtml(o.platform_name)} — ${escapeHtml(o.plan_name)}</td>
                        <td>${formatCurrency(o.price_original_uzs)}</td>
                        <td>${statusBadge(o.status)}</td>
                        <td>${formatDateShort(o.created_at)}</td>
                    </tr>
                `;
            });
            document.getElementById('m-orders-tbody').innerHTML = html;
        }

        // 3. Transactions Panel (Balance)
        if (txs.length === 0) {
            document.getElementById('m-txs-tbody').innerHTML = '<tr><td colspan="4" class="text-center text-muted" style="padding: 20px;">История транзакций пуста.</td></tr>';
        } else {
            let html = '';
            txs.forEach(t => {
                const amtClass = t.amount > 0 ? 'text-success font-semibold' : 'text-danger';
                const sign = t.amount > 0 ? '+' : '';
                html += `
                    <tr>
                        <td><span style="font-size:11px; font-weight:600; text-transform:uppercase;">${escapeHtml(t.type)}</span></td>
                        <td><span class="${amtClass}">${sign}${formatCurrency(t.amount)}</span></td>
                        <td><span class="text-muted" style="font-size:12px;">${escapeHtml(t.description || '—')}</span></td>
                        <td>${formatDateShort(t.created_at)}</td>
                    </tr>
                `;
            });
            document.getElementById('m-txs-tbody').innerHTML = html;
        }

        // 3b. Points Panel
        if (points.length === 0) {
            document.getElementById('m-points-tbody').innerHTML = '<tr><td colspan="4" class="text-center text-muted" style="padding: 20px;">История баллов пуста.</td></tr>';
        } else {
            let html = '';
            points.forEach(p => {
                const amtClass = p.points > 0 ? 'text-success font-semibold' : 'text-danger';
                const sign = p.points > 0 ? '+' : '';
                html += `
                    <tr>
                        <td><span style="font-size:11px; font-weight:600; text-transform:uppercase;">${escapeHtml(p.type)}</span></td>
                        <td><span class="${amtClass}">${sign}${formatNumber(p.points)}</span></td>
                        <td><span class="text-muted" style="font-size:12px;">${escapeHtml(p.description || '—')}</span></td>
                        <td>${formatDateShort(p.created_at)}</td>
                    </tr>
                `;
            });
            document.getElementById('m-points-tbody').innerHTML = html;
        }

        // 4. Referral Panel
        const botUsername = 'subhub_store_bot';
        const refLink = `https://t.me/${botUsername}?start=ref_${user.referral_code}`;
        document.getElementById('m-ref-link').textContent = refLink;
        document.getElementById('m-ref-count').textContent = refInfo.invited_count || 0;
        document.getElementById('m-ref-earned').textContent = formatCurrency(refInfo.total_earned || 0);

        document.getElementById('m-refs-tbody').innerHTML = '<tr><td colspan="3" class="text-center text-muted" style="padding: 20px;">Используйте общую вкладку "История рефералов" для просмотра связей.</td></tr>';

    } catch (err) {
        infoGrid.innerHTML = `<div class="alert alert-danger" style="grid-column: 1 / -1;">Ошибка при загрузке профиля: ${escapeHtml(err.message)}</div>`;
    }
}

function renderFakePagination(container, currentLen, limit, offset, onPageChange) {
    const currentPage = Math.floor(offset / limit) + 1;
    let html = '';
    html += `<button class="btn btn-outline btn-sm" ${currentPage <= 1 ? 'disabled' : ''} data-page="${currentPage - 1}">‹ Назад</button>`;
    html += `<span class="pagination-info">Страница ${currentPage}</span>`;
    html += `<button class="btn btn-outline btn-sm" ${currentLen < limit ? 'disabled' : ''} data-page="${currentPage + 1}">Вперед ›</button>`;

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

async function promptAdjustBalance(userId, currentBalance) {
    const input = prompt(
        `Текущий баланс: ${formatCurrency(currentBalance)}\n` +
        `Введите сумму для изменения (например, 10000 для добавления или -5000 для списания):`,
        "0"
    );
    if (input === null) return;
    
    const amount = parseInt(input.replace(/\s/g, ''), 10);
    if (isNaN(amount) || amount === 0) {
        alert("Некорректная сумма.");
        return;
    }
    
    const comment = prompt("Введите комментарий (необязательно):", "Ручная корректировка");
    if (comment === null) return;
    
    try {
        const response = await api.post(`/users/${userId}/adjust-balance`, {
            amount: amount,
            comment: comment
        });
        alert(`Баланс успешно изменен! Новый баланс: ${formatCurrency(response.new_balance)}`);
        
        openUserModal(userId);
        loadUsers(currentUsersOffset);
    } catch (err) {
        alert("Ошибка при изменении баланса: " + err.message);
    }
}

async function promptAdjustPoints(userId, currentPoints) {
    const input = prompt(
        `Текущий баланс баллов: ${formatNumber(currentPoints)}\n` +
        `Введите количество баллов для изменения (например, 10 для добавления или -5 для списания):`,
        "0"
    );
    if (input === null) return;
    
    const amount = parseInt(input.trim(), 10);
    if (isNaN(amount) || amount === 0) {
        alert("Некорректное число.");
        return;
    }
    
    const description = prompt("Введите описание (необязательно):", "Ручная корректировка");
    if (description === null) return;
    
    try {
        const response = await api.post(`/users/${userId}/adjust-points`, {
            amount: amount,
            description: description
        });
        alert(`Баллы успешно изменены! Новый баланс: ${formatNumber(response.new_points)}`);
        
        openUserModal(userId);
        loadUsers(currentUsersOffset);
    } catch (err) {
        alert("Ошибка при изменении баллов: " + err.message);
    }
}

