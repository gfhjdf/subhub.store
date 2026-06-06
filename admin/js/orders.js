/**
 * SubHub.store Admin — Orders Module
 */

let currentOffset = 0;
const currentLimit = 15;

async function initOrders() {
    // Load Platforms for filter dropdown
    try {
        const data = await api.get('/platforms');
        const select = document.getElementById('filter-platform');
        data.platforms.forEach(p => {
            const opt = document.createElement('option');
            opt.value = p.id;
            opt.textContent = p.name;
            select.appendChild(opt);
        });
    } catch (err) {
        console.error('Failed to load platforms for filter', err);
    }

    // Set filter values from URL if present
    const params = new URLSearchParams(window.location.search);
    const urlStatus = params.get('status');
    const urlPlatform = params.get('platform_id');
    const urlMethod = params.get('payment_method');
    const urlOrderId = params.get('id');

    if (urlStatus) document.getElementById('filter-status').value = urlStatus;
    if (urlPlatform) document.getElementById('filter-platform').value = urlPlatform;
    if (urlMethod) document.getElementById('filter-payment-method').value = urlMethod;

    // Reset button handler
    document.getElementById('btn-reset-filters').onclick = () => {
        document.getElementById('filters-form').reset();
        loadOrders(0);
    };

    // Form submit handler
    document.getElementById('filters-form').onsubmit = (e) => {
        e.preventDefault();
        loadOrders(0);
    };

    // Load initial list
    await loadOrders(0);

    // If ID is in URL, auto-open that order
    if (urlOrderId) {
        openOrderDetail(parseInt(urlOrderId));
    }
}

async function loadOrders(offset = 0) {
    currentOffset = offset;
    const tableBody = document.getElementById('orders-table-body');
    showLoading(tableBody);

    const status = document.getElementById('filter-status').value;
    const paymentMethod = document.getElementById('filter-payment-method').value;
    const platformId = document.getElementById('filter-platform').value;

    let path = `/orders?limit=${currentLimit}&offset=${currentOffset}`;
    if (status) path += `&status=${encodeURIComponent(status)}`;
    if (paymentMethod) path += `&payment_method=${encodeURIComponent(paymentMethod)}`;
    if (platformId) path += `&platform_id=${encodeURIComponent(platformId)}`;

    try {
        const data = await api.get(path);
        
        // Update sidebar pending badge while we are here
        const summary = await api.get('/dashboard/summary').catch(() => null);
        if (summary) {
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
        }

        if (!data.orders || data.orders.length === 0) {
            tableBody.innerHTML = `
                <tr>
                    <td colspan="10" class="text-center text-muted" style="padding: 40px;">
                        Заказы по выбранным фильтрам не найдены.
                    </td>
                </tr>
            `;
            document.getElementById('pagination-container').innerHTML = '';
            return;
        }

        let html = '';
        data.orders.forEach(order => {
            const dateStr = formatDateShort(order.created_at);
            const userStr = order.telegram_username ? `@${order.telegram_username}` : `ID: ${order.telegram_id}`;
            const balanceUsed = order.balance_used_uzs || 0;
            const cardDue = order.card_due_uzs || 0;

            html += `
                <tr style="cursor: pointer;" onclick="openOrderDetail(${order.id})">
                    <td><strong>#${escapeHtml(order.public_order_id)}</strong></td>
                    <td>
                        <div style="font-weight: 500;">${escapeHtml(order.user_first_name || 'User')}</div>
                        <div class="text-muted" style="font-size: 11px;">${escapeHtml(userStr)}</div>
                    </td>
                    <td>
                        <div>${escapeHtml(order.platform_name)}</div>
                        <div class="text-muted" style="font-size: 11px;">${escapeHtml(order.plan_name)}</div>
                    </td>
                    <td>${formatCurrency(order.price_original_uzs)}</td>
                    <td>${balanceUsed > 0 ? formatCurrency(balanceUsed) : '—'}</td>
                    <td>${cardDue > 0 ? formatCurrency(cardDue) : '—'}</td>
                    <td><span style="font-size: 11px; text-transform: uppercase; font-weight: 600;">${escapeHtml(order.payment_method)}</span></td>
                    <td>${statusBadge(order.status)}</td>
                    <td>${formatDate(order.created_at)}</td>
                    <td>
                        <button class="btn btn-outline btn-sm" onclick="event.stopPropagation(); openOrderDetail(${order.id})">Детали</button>
                    </td>
                </tr>
            `;
        });
        tableBody.innerHTML = html;

        // Render Pagination
        renderPagination(
            document.getElementById('pagination-container'),
            data.total,
            currentLimit,
            currentOffset,
            loadOrders
        );

    } catch (err) {
        tableBody.innerHTML = `<tr><td colspan="10" class="text-center text-danger" style="padding: 40px;">Error: ${escapeHtml(err.message)}</td></tr>`;
    }
}

async function openOrderDetail(orderId) {
    const modalBody = document.getElementById('modal-order-body');
    const modalFooter = document.getElementById('modal-order-footer');
    
    document.getElementById('modal-order-title').textContent = `Детали заказа #${orderId}`;
    modalBody.innerHTML = '<div class="loading-container"><div class="spinner"></div></div>';
    modalFooter.innerHTML = '';
    
    openModal('order-detail-modal');

    try {
        const data = await api.get(`/orders/${orderId}`);
        const order = data.order;
        const user = data.user;

        document.getElementById('modal-order-title').textContent = `Детали заказа #${order.public_order_id}`;

        // Format screenshot image source
        let screenshotHtml = '<p class="text-muted">Скриншот оплаты не загружен</p>';
        if (order.payment_screenshot_path) {
            // Check path format. In FastAPI it is mounted as /uploads which corresponds to uploads/screenshots.
            // If path contains uploads/screenshots/, we clean it up or use it as relative path.
            let src = order.payment_screenshot_path;
            if (!src.startsWith('/') && !src.startsWith('http')) {
                src = '/' + src;
            }
            screenshotHtml = `
                <div class="screenshot-preview-container" style="text-align: center; margin-top: 12px; background: rgba(0,0,0,0.2); padding: 12px; border-radius: 8px;">
                    <a href="${src}" target="_blank">
                        <img src="${src}" alt="Payment Screenshot" style="max-width: 100%; max-height: 400px; border-radius: 6px; border: 1px solid var(--border);" />
                    </a>
                    <div style="font-size: 11px; margin-top: 6px; color: var(--text-muted);">Нажмите на изображение для просмотра в полном размере</div>
                </div>
            `;
        }

        modalBody.innerHTML = `
            <div class="grid-2" style="gap: 24px;">
                <div>
                    <h4 style="margin-top: 0; color: var(--accent-cyan); border-bottom: 1px solid var(--border); padding-bottom: 8px;">🛒 Информация о заказе</h4>
                    <table class="detail-table" style="width: 100%; border-collapse: collapse;">
                        <tr><td style="padding: 6px 0; font-weight: 600;">Статус:</td><td>${statusBadge(order.status)}</td></tr>
                        <tr><td style="padding: 6px 0; font-weight: 600;">Платформа:</td><td>${escapeHtml(order.platform_name)}</td></tr>
                        <tr><td style="padding: 6px 0; font-weight: 600;">Тариф:</td><td>${escapeHtml(order.plan_name)}</td></tr>
                        <tr><td style="padding: 6px 0; font-weight: 600;">Метод оплаты:</td><td><strong style="text-transform: uppercase;">${escapeHtml(order.payment_method)}</strong></td></tr>
                        <tr><td style="padding: 6px 0; font-weight: 600;">Цена оригинала:</td><td>${formatCurrency(order.price_original_uzs)}</td></tr>
                        <tr><td style="padding: 6px 0; font-weight: 600;">Оплачено с баланса:</td><td>${order.balance_used_uzs ? formatCurrency(order.balance_used_uzs) : '—'}</td></tr>
                        <tr><td style="padding: 6px 0; font-weight: 600;">К оплате по карте:</td><td><strong>${order.card_due_uzs ? formatCurrency(order.card_due_uzs) : '—'}</strong></td></tr>
                        <tr><td style="padding: 6px 0; font-weight: 600;">Создан в:</td><td>${formatDate(order.created_at)}</td></tr>
                        ${order.approved_at ? `<tr><td style="padding: 6px 0; font-weight: 600;">Одобрен в:</td><td>${formatDate(order.approved_at)}</td></tr>` : ''}
                        ${order.rejection_reason_code ? `<tr><td style="padding: 6px 0; font-weight: 600; color: var(--danger);">Причина отказа:</td><td style="color: var(--danger); font-weight: 600;">${escapeHtml(order.rejection_reason_code)}</td></tr>` : ''}
                        ${order.rejection_note ? `<tr><td style="padding: 6px 0; font-weight: 600; color: var(--danger);">Заметка об отказе:</td><td style="color: var(--danger);">${escapeHtml(order.rejection_note)}</td></tr>` : ''}
                    </table>
                </div>

                <div>
                    <h4 style="margin-top: 0; color: var(--accent-purple-light); border-bottom: 1px solid var(--border); padding-bottom: 8px;">👤 Данные пользователя</h4>
                    <table class="detail-table" style="width: 100%; border-collapse: collapse;">
                        <tr><td style="padding: 6px 0; font-weight: 600;">Имя:</td><td>${escapeHtml(user.first_name || '')} ${escapeHtml(user.last_name || '')}</td></tr>
                        <tr><td style="padding: 6px 0; font-weight: 600;">Имя пользователя Telegram:</td><td>${user.telegram_username ? `<a href="https://t.me/${user.telegram_username}" target="_blank" style="color: var(--accent-cyan);">@${escapeHtml(user.telegram_username)}</a>` : '—'}</td></tr>
                        <tr><td style="padding: 6px 0; font-weight: 600;">ID Telegram:</td><td><code>${user.telegram_id}</code></td></tr>
                        <tr><td style="padding: 6px 0; font-weight: 600;">Язык бота:</td><td>${user.language_code === 'uz' ? 'Uzbek 🇺🇿' : 'Russian 🇷🇺'}</td></tr>
                        <tr><td style="padding: 6px 0; font-weight: 600;">Текущий баланс:</td><td><strong>${formatCurrency(user.balance_uzs)}</strong></td></tr>
                    </table>
                </div>
            </div>

            <!-- Credentials Box if delivered -->
            ${order.status === 'delivered' ? `
                <div class="card" style="margin-top: 20px; padding: 16px; background: rgba(16, 185, 129, 0.08); border: 1px solid rgba(16, 185, 129, 0.3);">
                    <h4 style="margin-top:0; color: var(--success);">🔑 Доставленные реквизиты</h4>
                    <div style="display: flex; gap: 24px; flex-wrap: wrap;">
                        <div><strong>Логин / Имя пользователя:</strong> <code style="font-size: 14px;">${escapeHtml(order.account_login)}</code></div>
                        <div><strong>Пароль:</strong> <code style="font-size: 14px;">${escapeHtml(order.account_password)}</code></div>
                    </div>
                </div>
            ` : ''}

            <!-- Screenshot Area -->
            <div style="margin-top: 20px;">
                <h4 style="margin-top: 0; color: var(--text-secondary); border-bottom: 1px solid var(--border); padding-bottom: 8px;">🖼️ Скриншот подтверждения оплаты</h4>
                ${screenshotHtml}
            </div>

            <!-- Rejection Form UI (hidden initially) -->
            <div id="rejection-form-container" style="display: none; margin-top: 20px; padding: 16px; border: 1px solid var(--danger); border-radius: 8px; background: rgba(239, 68, 68, 0.05);">
                <h4 style="margin-top:0; color: var(--danger);">Отклонить заказ #${order.public_order_id}</h4>
                <div class="form-group">
                    <label class="form-label" for="reject-reason">Код причины</label>
                    <select class="form-input" id="reject-reason">
                        <option value="invalid_screenshot">Недействительный/Фальшивый скриншот</option>
                        <option value="incorrect_amount">Неверная сумма оплаты</option>
                        <option value="missing_info">Отсутствуют детали платежа</option>
                        <option value="out_of_stock">Нет на складе (Будет возврат)</option>
                        <option value="other">Другая причина / Вручную</option>
                    </select>
                </div>
                <div class="form-group">
                    <label class="form-label" for="reject-note">Текст сообщения об отклонении, который будет отправлен пользователю</label>
                    <textarea class="form-input" id="reject-note" rows="3" placeholder="Объясните причину отклонения. Этот текст будет напрямую отправлен пользователю в Telegram."></textarea>
                </div>
                <div style="display:flex; justify-content: flex-end; gap: 8px;">
                    <button class="btn btn-outline" onclick="document.getElementById('rejection-form-container').style.display='none'">Отмена</button>
                    <button class="btn btn-danger" onclick="submitRejection(${order.id})">Подтвердить отклонение</button>
                </div>
            </div>
        `;

        // Render Action Buttons in Footer if pending review
        if (order.status === 'payment_submitted' || order.status === 'under_review') {
            modalFooter.innerHTML = `
                <button class="btn btn-outline" onclick="closeModal('order-detail-modal')" style="margin-right: auto;">Закрыть</button>
                <button class="btn btn-danger" onclick="showRejectionForm()">Отклонить заказ</button>
                <button class="btn btn-success" onclick="approveOrder(${order.id})">Одобрить и выдать</button>
            `;
        } else {
            modalFooter.innerHTML = `
                <button class="btn btn-outline" onclick="closeModal('order-detail-modal')">Закрыть</button>
            `;
        }

    } catch (err) {
        modalBody.innerHTML = `<div class="alert alert-danger">Error loading order: ${escapeHtml(err.message)}</div>`;
    }
}

function showRejectionForm() {
    document.getElementById('rejection-form-container').style.display = 'block';
    document.getElementById('rejection-form-container').scrollIntoView({ behavior: 'smooth' });
}

async function approveOrder(orderId) {
    showConfirm(
        'Одобрить заказ?',
        'Это подтвердит оплату, спишет один доступный аккаунт со склада, выдаст его пользователю и уведомит его в Telegram.',
        '🚀',
        async () => {
            try {
                const res = await api.post(`/orders/${orderId}/approve`);
                showToast(`Заказ одобрен и выполнен! Выданный аккаунт: ${res.order.account_login}`, 'success');
                closeModal('order-detail-modal');
                loadOrders(currentOffset);
            } catch (err) {
                showToast(err.message || 'Ошибка подтверждения', 'error');
            }
        },
        'btn-success'
    );
}

async function submitRejection(orderId) {
    const reasonCode = document.getElementById('reject-reason').value;
    const note = document.getElementById('reject-note').value.trim();

    try {
        await api.post(`/orders/${orderId}/reject`, {
            reason_code: reasonCode,
            note: note || undefined
        });
        showToast('Заказ отклонен, пользователь уведомлен.', 'success');
        closeModal('order-detail-modal');
        loadOrders(currentOffset);
    } catch (err) {
        showToast(err.message || 'Ошибка отклонения', 'error');
    }
}
