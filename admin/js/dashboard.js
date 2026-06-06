/**
 * SubHub.store Admin — Dashboard Module
 */

async function loadDashboard() {
    try {
        const summary = await api.get('/dashboard/summary');
        
        // Update KPI values
        // total_orders = only completed paid sales (gifts excluded)
        // total_revenue = card_revenue + wallet_revenue (real cash in)
        // gifts_given = completed gift redemptions from the gifts/rewards system
        document.getElementById('kpi-total-orders').textContent = formatNumber(summary.total_orders);
        document.getElementById('kpi-revenue').textContent = formatCurrency(summary.total_revenue);
        document.getElementById('kpi-pending').textContent = formatNumber(summary.pending_orders);
        document.getElementById('kpi-users').textContent = formatNumber(summary.user_count);
        document.getElementById('kpi-stock').textContent = formatNumber(summary.total_available_stock);
        document.getElementById('kpi-gifts-given').textContent = formatNumber(summary.gifts_given || 0);

        // Show revenue breakdown as subtitle
        const revCard = document.getElementById('kpi-revenue').closest('.kpi-card');
        if (revCard && (summary.card_revenue || summary.wallet_revenue)) {
            let breakdown = revCard.querySelector('.kpi-breakdown');
            if (!breakdown) {
                breakdown = document.createElement('div');
                breakdown.className = 'kpi-breakdown';
                breakdown.style.cssText = 'font-size:11px; color: var(--text-muted); margin-top:4px;';
                revCard.appendChild(breakdown);
            }
            breakdown.textContent = `💳 ${formatCurrency(summary.card_revenue || 0)} карта  +  💰 ${formatCurrency(summary.wallet_revenue || 0)} кошелёк`;
        }

        // Sidebar badge update
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

        // Render system alerts (if alerts_count > 0, we can fetch alerts or show count)
        const alertsSection = document.getElementById('alerts-section');
        alertsSection.innerHTML = '';
        if (summary.alerts_count > 0) {
            const alertBox = document.createElement('div');
            alertBox.className = 'alert alert-danger mb-24';
            alertBox.innerHTML = `
                <div style="display: flex; justify-content: space-between; align-items: center; width: 100%;">
                    <div>🚨 <strong>Угроза безопасности:</strong> Есть ${summary.alerts_count} активных реферальных/системных уведомлений, требующих проверки.</div>
                    <a href="/admin/users.html?tab=alerts" class="btn btn-danger btn-sm" style="text-decoration:none; margin-left:16px;">Проверить</a>
                </div>
            `;
            alertsSection.appendChild(alertBox);
        }

        // Render Pending Orders list
        const pendingContainer = document.getElementById('pending-orders-list');
        if (summary.pending_list && summary.pending_list.length > 0) {
            let html = '<div class="list-container">';
            summary.pending_list.forEach(order => {
                html += `
                    <div class="list-item" style="cursor: pointer;" onclick="window.location.href='/admin/orders.html?id=${order.id}'">
                        <div class="list-item-left">
                            <span class="list-item-icon">⏳</span>
                            <div>
                                <div class="list-item-title">${escapeHtml(order.platform_name)} — ${escapeHtml(order.plan_name)}</div>
                                <div class="list-item-subtitle">By @${escapeHtml(order.telegram_username || 'User')} | ${formatDateShort(order.created_at)}</div>
                            </div>
                        </div>
                        <div class="list-item-right">
                            <span class="list-item-value">${formatCurrency(order.price_original_uzs)}</span>
                            ${statusBadge(order.status)}
                        </div>
                    </div>
                `;
            });
            html += '</div>';
            pendingContainer.innerHTML = html;
        } else {
            pendingContainer.innerHTML = `
                <div class="empty-state">
                    <div class="empty-icon">🎉</div>
                    <div class="empty-title">Все проверено</div>
                    <div class="empty-subtitle">Нет заказов, ожидающих проверки</div>
                </div>
            `;
        }

        // Render Low Stock Warnings
        const stockContainer = document.getElementById('low-stock-list');
        if (summary.low_stock_warnings && summary.low_stock_warnings.length > 0) {
            let html = '<div class="list-container">';
            summary.low_stock_warnings.forEach(item => {
                const avail = item.available || 0;
                const progressColor = avail <= 1 ? 'var(--danger)' : 'var(--warning)';
                html += `
                    <div class="list-item" style="cursor: pointer;" onclick="window.location.href='/admin/accounts.html?plan_id=${item.plan_id}'">
                        <div class="list-item-left">
                            <span class="list-item-icon">⚠️</span>
                            <div>
                                <div class="list-item-title">${escapeHtml(item.platform_name)} — ${escapeHtml(item.plan_name)}</div>
                                <div class="list-item-subtitle" style="color: ${progressColor}; font-weight: 600;">Осталось всего ${avail} аккаунтов!</div>
                            </div>
                        </div>
                        <div class="list-item-right">
                            <a href="/admin/accounts.html?add_plan_id=${item.plan_id}" class="btn btn-outline btn-sm" onclick="event.stopPropagation();">Пополнить</a>
                        </div>
                    </div>
                `;
            });
            html += '</div>';
            stockContainer.innerHTML = html;
        } else {
            stockContainer.innerHTML = `
                <div class="empty-state">
                    <div class="empty-icon">🛡️</div>
                    <div class="empty-title">Склад полон</div>
                    <div class="empty-subtitle">Все тарифы обеспечены аккаунтами</div>
                </div>
            `;
        }

        // Render Recent Orders Table
        const tbody = document.getElementById('recent-orders-body');
        if (summary.recent_orders && summary.recent_orders.length > 0) {
            let html = '';
            summary.recent_orders.forEach(order => {
                html += `
                    <tr style="cursor: pointer;" onclick="window.location.href='/admin/orders.html?id=${order.id}'">
                        <td><strong>#${escapeHtml(order.public_order_id)}</strong></td>
                        <td>
                            <div style="font-weight: 500;">${escapeHtml(order.user_first_name || 'User')}</div>
                            <div class="text-muted" style="font-size: 11px;">@${escapeHtml(order.telegram_username || 'N/A')}</div>
                        </td>
                        <td>
                            <div>${escapeHtml(order.platform_name)}</div>
                            <div class="text-muted" style="font-size: 11px;">${escapeHtml(order.plan_name)}</div>
                        </td>
                        <td>${formatCurrency(order.price_original_uzs)}</td>
                        <td><span style="font-size: 12px; text-transform: uppercase;">${escapeHtml(order.payment_method)}</span></td>
                        <td>${statusBadge(order.status)}</td>
                        <td>${formatDateShort(order.created_at)}</td>
                    </tr>
                `;
            });
            tbody.innerHTML = html;
        } else {
            tbody.innerHTML = '<tr><td colspan="7" class="text-center text-muted" style="padding: 40px;">Нет недавних заказов.</td></tr>';
        }

    } catch (err) {
        showToast('Ошибка загрузки сводки панели: ' + err.message, 'error');
    }
}

// Auto refresh dashboard every 30 seconds
let dashboardInterval = setInterval(loadDashboard, 30000);

// Cleanup interval if user navigates away
window.addEventListener('unload', () => {
    clearInterval(dashboardInterval);
});
