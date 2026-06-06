/**
 * SubHub.store Admin — Gift Redemptions Moderation Module
 */

let currentStatusFilter = '';
let currentOffset = 0;
const currentLimit = 15;

async function initRedemptions() {
    await loadRedemptions();
    // Refresh pending badges in sidebar
    await refreshBadges();
}

async function loadRedemptions(offset = 0) {
    currentOffset = offset;
    const tableBody = document.getElementById('redemptions-table-body');
    showLoading(tableBody);

    let path = `/redemptions?limit=${currentLimit}&offset=${currentOffset}`;
    if (currentStatusFilter) path += `&status=${currentStatusFilter}`;

    try {
        const data = await api.get(path);
        const redemptions = data.redemptions || [];

        if (redemptions.length === 0) {
            tableBody.innerHTML = '<tr><td colspan="7" class="text-center text-muted" style="padding: 40px;">Заявки на подарки не найдены.</td></tr>';
            document.getElementById('pagination-container').innerHTML = '';
            return;
        }

        let html = '';
        redemptions.forEach(r => {
            const userStr = r.telegram_username ? `@${r.telegram_username}` : `ID: ${r.telegram_id}`;
            const userLabel = `${escapeHtml(r.user_first_name || 'User')} (${escapeHtml(userStr)})`;
            
            // Determine action buttons based on status
            let actionsHtml = '';
            if (r.status === 'pending') {
                actionsHtml = `
                    <button class="btn btn-success btn-sm" onclick="processRedemption(${r.id}, 'approved')">Одобрить</button>
                    <button class="btn btn-danger btn-sm" onclick="openRejectModal(${r.id})">Отклонить</button>
                `;
            } else if (r.status === 'approved') {
                actionsHtml = `
                    <button class="btn btn-primary btn-sm" onclick="processRedemption(${r.id}, 'completed')">Выдать/Выполнить</button>
                    <button class="btn btn-danger btn-sm" onclick="openRejectModal(${r.id})">Отклонить</button>
                `;
            } else if (r.status === 'rejected' && r.rejection_note) {
                actionsHtml = `<span class="text-muted" style="font-size:11px;" title="${escapeHtml(r.rejection_note)}">Причина: ${escapeHtml(r.rejection_note.substring(0, 25))}...</span>`;
            } else {
                actionsHtml = '<span class="text-muted">—</span>';
            }

            let credentialsLabel = '';
            if (r.status === 'completed' && r.account_login) {
                credentialsLabel = `<div style="font-size: 11px; color: var(--accent-purple-light); margin-top: 4px;">👤 <code>${escapeHtml(r.account_login)}</code> : <code>${escapeHtml(r.account_password)}</code></div>`;
            }

            html += `
                <tr>
                    <td><strong>#${escapeHtml(r.public_redemption_id)}</strong></td>
                    <td>
                        <div style="font-weight: 500;">${escapeHtml(r.user_first_name || 'User')}</div>
                        <div class="text-muted" style="font-size: 11px;">${escapeHtml(userStr)}</div>
                    </td>
                    <td>
                        🎁 <strong>${escapeHtml(r.reward_name)}</strong>
                        ${credentialsLabel}
                    </td>
                    <td><strong>${formatNumber(r.points_spent)}</strong> баллов</td>
                    <td>${statusBadge(r.status)}</td>
                    <td>${formatDateShort(r.created_at)}</td>
                    <td class="text-right">${actionsHtml}</td>
                </tr>
            `;
        });
        tableBody.innerHTML = html;

        renderPagination(
            document.getElementById('pagination-container'),
            data.total,
            currentLimit,
            currentOffset,
            loadRedemptions
        );
    } catch (err) {
        tableBody.innerHTML = `<tr><td colspan="7" class="text-center text-danger" style="padding: 40px;">Ошибка загрузки: ${escapeHtml(err.message)}</td></tr>`;
    }
}

function filterRedemptions(status) {
    currentStatusFilter = status;
    document.querySelectorAll('.page-tab-btn').forEach(btn => {
        btn.classList.toggle('active', btn.id === `filter-${status || 'all'}`);
    });
    loadRedemptions(0);
}

async function processRedemption(redemptionId, status) {
    const actions = {
        approved: { title: 'Одобрить заявку', msg: 'Одобрить эту заявку? Пользователь получит сообщение в Telegram.', icon: '✅' },
        completed: { title: 'Выполнить заявку', msg: 'Пометить подарок как выданный? Процесс будет успешно завершен.', icon: '📦' }
    };
    
    const act = actions[status];
    if (!act) return;

    showConfirm(
        act.title,
        act.msg,
        act.icon,
        async () => {
            try {
                await api.post(`/redemptions/${redemptionId}/process`, { status: status });
                showToast('Статус заявки успешно изменен!', 'success');
                loadRedemptions(currentOffset);
                refreshBadges();
            } catch (err) {
                showToast('Не удалось обновить статус: ' + err.message, 'error');
            }
        }
    );
}

function openRejectModal(redemptionId) {
    document.getElementById('reject-redemption-id').value = redemptionId;
    document.getElementById('reject-note').value = '';
    openModal('rejection-modal');
}

async function submitRejection() {
    const id = document.getElementById('reject-redemption-id').value;
    const note = document.getElementById('reject-note').value.trim();

    if (!note) {
        alert('Пожалуйста, укажите причину отклонения.');
        return;
    }

    try {
        await api.post(`/redemptions/${id}/process`, {
            status: 'rejected',
            rejection_note: note
        });
        showToast('Заявка отклонена. Баллы возвращены пользователю.', 'success');
        closeModal('rejection-modal');
        loadRedemptions(currentOffset);
        refreshBadges();
    } catch (err) {
        showToast('Ошибка: ' + err.message, 'error');
    }
}

async function refreshBadges() {
    try {
        const data = await api.get('/dashboard/summary');
        
        // Update pending redemptions badge count
        const redBadgeEl = document.getElementById('nav-redemptions-badge');
        if (redBadgeEl) {
            const count = data.pending_redemptions_count || 0;
            if (count > 0) {
                redBadgeEl.textContent = count;
                redBadgeEl.style.display = 'inline-block';
            } else {
                redBadgeEl.style.display = 'none';
            }
        }
        
        // Also update legacy orders badge if present
        const orderBadgeEl = document.getElementById('nav-pending-badge');
        if (orderBadgeEl) {
            const count = data.pending_orders || 0;
            if (count > 0) {
                orderBadgeEl.textContent = count;
                orderBadgeEl.style.display = 'inline-block';
            } else {
                orderBadgeEl.style.display = 'none';
            }
        }
    } catch (err) {
        console.error('Failed to load badges:', err);
    }
}
