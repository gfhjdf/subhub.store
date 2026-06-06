/**
 * SubHub.store Admin — Wallet Top-ups Controller
 */

let currentStatusFilter = '';
let currentLimit = 20;
let currentOffset = 0;
let topupsList = [];

async function initWalletTopups() {
    await loadTopups();
}

async function loadTopups() {
    const tableBody = document.getElementById('topups-table-body');
    if (!tableBody) return;

    showLoading(tableBody);

    try {
        let path = `/wallet/topups?limit=${currentLimit}&offset=${currentOffset}`;
        if (currentStatusFilter) {
            path += `&status=${currentStatusFilter}`;
        }

        const res = await api.get(path);
        topupsList = res.topups;
        const total = res.pending_count + res.topups.length; // Approximate total or use length if no count returned

        renderTopupsTable(topupsList);
        
        const paginationContainer = document.getElementById('pagination-container');
        if (paginationContainer) {
            // Note: Since we don't have absolute counts easily, we paginate by presence of data
            renderPagination(paginationContainer, res.topups.length === currentLimit ? currentOffset + currentLimit + 1 : currentOffset + res.topups.length, currentLimit, currentOffset, (newOffset) => {
                currentOffset = newOffset;
                loadTopups();
            });
        }
    } catch (err) {
        showToast('Не удалось загрузить запросы: ' + err.message, 'error');
        tableBody.innerHTML = `<tr><td colspan="8" class="text-center text-danger">Ошибка загрузки: ${escapeHtml(err.message)}</td></tr>`;
    }
}

function renderTopupsTable(topups) {
    const tableBody = document.getElementById('topups-table-body');
    if (!tableBody) return;

    if (topups.length === 0) {
        tableBody.innerHTML = `<tr><td colspan="8" class="text-center text-muted" style="padding: 40px;">Нет запросов на пополнение</td></tr>`;
        return;
    }

    let html = '';
    topups.forEach(t => {
        const usernameLabel = t.telegram_username ? `@${t.telegram_username}` : '';
        const userDisplayName = `${escapeHtml(t.first_name || '')} ${escapeHtml(t.last_name || '')} ${escapeHtml(usernameLabel)}`.trim();
        const dateStr = formatDate(t.created_at);
        const statusBadgeHtml = statusBadge(t.status);

        // Screenshot thumbnail
        let screenshotHtml = '<span class="text-muted">—</span>';
        if (t.screenshot_path) {
            // Serve the image. In FastAPI, the file path is returned relative or static. Let's make it loadable.
            // In typical setup, the uploads/ dir is mounted as static /uploads or similar.
            const src = t.screenshot_path.startsWith('/') ? t.screenshot_path : '/' + t.screenshot_path;
            screenshotHtml = `<img src="${src}" class="screenshot-thumbnail" onclick="viewScreenshot('${src}')" alt="Чек">`;
        }

        const reqAmount = formatCurrency(t.amount_requested);
        const appAmount = t.amount_approved ? formatCurrency(t.amount_approved) : '<span class="text-muted">—</span>';

        let actionsHtml = '';
        if (t.status === 'pending') {
            actionsHtml = `
                <button class="btn btn-sm btn-success" style="margin-right: 6px;" onclick="openApproveModal(${t.id}, ${t.amount_requested})">Одобрить</button>
                <button class="btn btn-sm btn-danger" onclick="openRejectModal(${t.id})">Отклонить</button>
            `;
        } else if (t.status === 'rejected' && t.rejection_note) {
            actionsHtml = `<span class="text-muted" title="${escapeHtml(t.rejection_note)}">Отклонен: ${escapeHtml(t.rejection_note.substring(0, 15))}...</span>`;
        } else if (t.status === 'approved') {
            actionsHtml = `<span class="text-muted">Завершено</span>`;
        }

        html += `
            <tr>
                <td><strong>${escapeHtml(t.public_topup_id)}</strong></td>
                <td>
                    <div>${userDisplayName}</div>
                    <small class="text-muted">ID: ${t.telegram_id}</small>
                </td>
                <td>${screenshotHtml}</td>
                <td>${reqAmount}</td>
                <td>${appAmount}</td>
                <td>${statusBadgeHtml}</td>
                <td>${dateStr}</td>
                <td class="text-right">${actionsHtml}</td>
            </tr>
        `;
    });

    tableBody.innerHTML = html;
}

function filterTopups(status) {
    currentStatusFilter = status;
    currentOffset = 0;

    // Update active tab styling
    document.querySelectorAll('.page-tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });

    if (status === '') {
        document.getElementById('filter-all').classList.add('active');
    } else {
        document.getElementById(`filter-${status}`).classList.add('active');
    }

    loadTopups();
}

function viewScreenshot(src) {
    const modalImg = document.getElementById('modal-screenshot-img');
    if (modalImg) {
        modalImg.src = src;
        openModal('screenshot-modal');
    }
}

function openApproveModal(topupId, requestedAmount) {
    document.getElementById('approve-topup-id').value = topupId;
    document.getElementById('approve-amount').value = requestedAmount;
    openModal('approve-modal');
}

async function submitApproval() {
    const topupId = document.getElementById('approve-topup-id').value;
    const amount = parseInt(document.getElementById('approve-amount').value);

    if (!amount || amount <= 0) {
        showToast('Пожалуйста, введите корректную сумму пополнения', 'error');
        return;
    }

    try {
        await api.post(`/wallet/topups/${topupId}/process`, {
            status: 'approved',
            amount_approved: amount
        });

        showToast('Запрос на пополнение успешно одобрен!', 'success');
        closeModal('approve-modal');
        loadTopups();
        
        // Refresh sidebar badges
        initSidebar();
    } catch (err) {
        showToast('Не удалось одобрить: ' + err.message, 'error');
    }
}

function openRejectModal(topupId) {
    document.getElementById('reject-topup-id').value = topupId;
    document.getElementById('reject-note').value = '';
    openModal('rejection-modal');
}

async function submitRejection() {
    const topupId = document.getElementById('reject-topup-id').value;
    const note = document.getElementById('reject-note').value.trim();

    if (!note) {
        showToast('Пожалуйста, укажите причину отклонения', 'error');
        return;
    }

    try {
        await api.post(`/wallet/topups/${topupId}/process`, {
            status: 'rejected',
            rejection_note: note
        });

        showToast('Запрос на пополнение отклонен', 'info');
        closeModal('rejection-modal');
        loadTopups();
        
        // Refresh sidebar badges
        initSidebar();
    } catch (err) {
        showToast('Не удалось отклонить: ' + err.message, 'error');
    }
}
