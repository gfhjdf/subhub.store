/**
 * SubHub.store Admin — Accounts Module
 */

let activeAddTab = 'single';
let currentOffset = 0;
const currentLimit = 20;

function switchAddTab(tab) {
    activeAddTab = tab;
    document.querySelectorAll('.form-tab').forEach(btn => {
        btn.classList.toggle('active', btn.id === `tab-${tab}`);
    });
    document.getElementById('single-account-form').style.display = tab === 'single' ? 'block' : 'none';
    document.getElementById('bulk-account-form').style.display = tab === 'bulk' ? 'block' : 'none';
}

async function initAccounts() {
    // Populate plans selectors
    try {
        const data = await api.get('/plans');
        const addPlanSelect = document.getElementById('add-plan-id');
        const filterPlanSelect = document.getElementById('filter-plan-id');

        data.plans.forEach(plan => {
            const opt1 = document.createElement('option');
            opt1.value = plan.id;
            opt1.textContent = `${plan.platform_name} — ${plan.name}`;
            addPlanSelect.appendChild(opt1);

            const opt2 = document.createElement('option');
            opt2.value = plan.id;
            opt2.textContent = `${plan.platform_name} — ${plan.name}`;
            filterPlanSelect.appendChild(opt2);
        });

        // Set from URL if present
        const params = new URLSearchParams(window.location.search);
        const urlPlanId = params.get('plan_id');
        const urlAddPlanId = params.get('add_plan_id');

        if (urlPlanId) {
            filterPlanSelect.value = urlPlanId;
        }
        if (urlAddPlanId) {
            addPlanSelect.value = urlAddPlanId;
            switchAddTab('bulk');
        }

    } catch (err) {
        console.error('Failed to load plans selectors', err);
    }

    // Filter change listeners
    document.getElementById('filter-plan-id').onchange = () => loadInventory(0);
    document.getElementById('filter-status').onchange = () => loadInventory(0);

    // Form submissions
    document.getElementById('single-account-form').onsubmit = handleSingleSubmit;
    document.getElementById('bulk-account-form').onsubmit = handleBulkSubmit;
    document.getElementById('edit-account-form').onsubmit = handleEditSubmit;

    // Load initial data
    await loadStockSummary();
    await loadInventory(0);
}

async function loadStockSummary() {
    const container = document.getElementById('stock-summary-container');
    container.innerHTML = '<div class="loading-container"><div class="spinner"></div></div>';

    try {
        const data = await api.get('/accounts/stock-summary');
        const summary = data.summary || [];

        if (summary.length === 0) {
            container.innerHTML = '<div class="text-muted">Планы каталога не найдены.</div>';
            return;
        }

        let html = '';
        summary.forEach(item => {
            const avail = item.available || 0;
            let statusColor = 'var(--success)';
            if (avail === 0) statusColor = 'var(--danger)';
            else if (avail < 5) statusColor = 'var(--warning)';

            html += `
                <div class="stock-card" style="border-bottom: 2px solid ${statusColor};">
                    <div>
                        <div class="stock-title">${escapeHtml(item.platform_name)}</div>
                        <div class="stock-meta">${escapeHtml(item.plan_name)}</div>
                        <div class="text-muted" style="font-size:10px; margin-top:2px;">Продано: ${item.sold || 0} | Всего: ${item.total || 0}</div>
                    </div>
                    <div class="stock-badge" style="color: ${statusColor};">${avail}</div>
                </div>
            `;
        });

        container.innerHTML = html;
    } catch (err) {
        container.innerHTML = `<div class="text-danger">Не удалось загрузить остатки: ${escapeHtml(err.message)}</div>`;
    }
}

async function loadInventory(offset = 0) {
    currentOffset = offset;
    const tableBody = document.getElementById('inventory-table-body');
    showLoading(tableBody);

    const planId = document.getElementById('filter-plan-id').value;
    const status = document.getElementById('filter-status').value;

    let path = `/accounts?limit=${currentLimit}&offset=${currentOffset}`;
    if (planId) path += `&plan_id=${planId}`;
    if (status) path += `&status=${status}`;

    try {
        const data = await api.get(path);
        const accounts = data.accounts || [];

        if (accounts.length === 0) {
            tableBody.innerHTML = '<tr><td colspan="7" class="text-center text-muted" style="padding: 40px;">В инвентаре нет учетных записей.</td></tr>';
            document.getElementById('pagination-container').innerHTML = '';
            return;
        }

        let html = '';
        accounts.forEach(acc => {
            html += `
                <tr>
                    <td><code>${escapeHtml(acc.login)}</code></td>
                    <td><code>${escapeHtml(acc.password)}</code></td>
                    <td>
                        <div>${escapeHtml(acc.platform_name)}</div>
                        <div class="text-muted" style="font-size: 11px;">${escapeHtml(acc.plan_name)}</div>
                    </td>
                    <td>${statusBadge(acc.status)}</td>
                    <td><span class="text-muted" style="font-size: 12px;">${escapeHtml(acc.notes || '—')}</span></td>
                    <td>${formatDateShort(acc.created_at)}</td>
                    <td class="text-right">
                        <button class="btn btn-outline btn-sm" style="margin-right: 4px;" onclick="openEditModal(${JSON.stringify(acc).replace(/"/g, '&quot;')})">Редактировать</button>
                        <button class="btn btn-danger btn-sm" onclick="deleteAccount(${acc.id})">Удалить</button>
                    </td>
                </tr>
            `;
        });

        tableBody.innerHTML = html;

        // Populate pagination
        // Since get_accounts endpoint doesn't return total count (it returns pagination parameters),
        // we can count total elements based on accounts length or render page forward/backward buttons.
        // Wait, list_accounts route returns {"accounts": accounts, "limit": limit, "offset": offset}. It does not return total.
        // So we can estimate if we have a next page by checking if accounts.length === currentLimit.
        renderFakePagination(
            document.getElementById('pagination-container'),
            accounts.length,
            currentLimit,
            currentOffset,
            loadInventory
        );

    } catch (err) {
        tableBody.innerHTML = `<tr><td colspan="7" class="text-center text-danger" style="padding: 40px;">Ошибка: ${escapeHtml(err.message)}</td></tr>`;
    }
}

// Custom pagination helper for endpoints with no count
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

// ─── ADD ACCOUNT ────────────────────────────────────────────

async function handleSingleSubmit(e) {
    e.preventDefault();
    const planId = document.getElementById('add-plan-id').value;
    const login = document.getElementById('acc-login').value.trim();
    const password = document.getElementById('acc-pass').value.trim();
    const notes = document.getElementById('acc-notes').value.trim();

    if (!planId) {
        showToast('Пожалуйста, выберите целевой тариф', 'error');
        return;
    }

    try {
        await api.post('/accounts', {
            plan_id: parseInt(planId),
            login,
            password,
            notes: notes || undefined
        });
        showToast('Аккаунт успешно добавлен', 'success');
        document.getElementById('single-account-form').reset();
        await loadStockSummary();
        await loadInventory(0);
    } catch (err) {
        showToast(err.message || 'Не удалось добавить аккаунт', 'error');
    }
}

async function handleBulkSubmit(e) {
    e.preventDefault();
    const planId = document.getElementById('add-plan-id').value;
    const rawData = document.getElementById('bulk-data').value.trim();

    if (!planId) {
        showToast('Пожалуйста, выберите целевой тариф', 'error');
        return;
    }

    let accounts = [];

    // Parse Data
    try {
        if (rawData.startsWith('[') && rawData.endsWith(']')) {
            // JSON format
            accounts = JSON.parse(rawData);
        } else {
            // Line-by-line delimiter format
            const lines = rawData.split('\n');
            lines.forEach(line => {
                const cleanLine = line.trim();
                if (!cleanLine) return;

                // Support login,password or login,password,notes (preferred)
                // Fallback to :, | or ;
                let parts = [];
                if (cleanLine.includes(',')) {
                    parts = cleanLine.split(',');
                } else if (cleanLine.includes(':')) {
                    parts = cleanLine.split(':');
                } else if (cleanLine.includes('|')) {
                    parts = cleanLine.split('|');
                } else if (cleanLine.includes(';')) {
                    parts = cleanLine.split(';');
                }

                if (parts.length >= 2) {
                    const login = parts[0].trim();
                    const password = parts[1].trim();
                    const notes = parts.slice(2).join(',').trim();

                    accounts.push({
                        login: login,
                        password: password,
                        notes: notes ? notes : undefined
                    });
                }
            });
        }
    } catch (err) {
        showToast('Не удалось разобрать ввод: ' + err.message, 'error');
        return;
    }

    if (accounts.length === 0) {
        showToast('Не найдено корректных аккаунтов во вводе', 'error');
        return;
    }

    try {
        const res = await api.post('/accounts/bulk', {
            plan_id: parseInt(planId),
            accounts
        });
        showToast(`Успешно импортировано ${res.count} аккаунтов!`, 'success');
        document.getElementById('bulk-account-form').reset();
        await loadStockSummary();
        await loadInventory(0);
    } catch (err) {
        showToast(err.message || 'Не удалось выполнить массовый импорт аккаунтов', 'error');
    }
}

// ─── EDIT / DELETE ACCOUNT ──────────────────────────────────

function openEditModal(acc) {
    document.getElementById('edit-acc-id').value = acc.id;
    document.getElementById('edit-acc-login').value = acc.login;
    document.getElementById('edit-acc-pass').value = acc.password;
    document.getElementById('edit-acc-status').value = acc.status;
    document.getElementById('edit-acc-notes').value = acc.notes || '';
    
    openModal('edit-account-modal');
}

async function handleEditSubmit(e) {
    e.preventDefault();
    const id = document.getElementById('edit-acc-id').value;
    const login = document.getElementById('edit-acc-login').value.trim();
    const password = document.getElementById('edit-acc-pass').value.trim();
    const status = document.getElementById('edit-acc-status').value;
    const notes = document.getElementById('edit-acc-notes').value.trim();

    try {
        await api.put(`/accounts/${id}`, {
            login,
            password,
            status,
            notes: notes || undefined
        });
        showToast('Учетные данные аккаунта обновлены', 'success');
        closeModal('edit-account-modal');
        await loadStockSummary();
        await loadInventory(currentOffset);
    } catch (err) {
        showToast(err.message || 'Не удалось обновить учетные данные', 'error');
    }
}

async function deleteAccount(id) {
    // Delete endpoint is not explicitly standard CRUD but we can either write one in routes
    // or set status to 'disabled' / 'sold'. Wait, looking at the FastAPI router, is there a delete account endpoint?
    // Let's check `admin_routes.py`. It has PUT /accounts/{id} to update fields (including status). It does not have DELETE /accounts/{id}.
    // So we can "delete" by updating status to 'disabled' or we can propose writing a delete endpoint in admin_routes.py if it's there.
    // Wait, let's look at `admin_routes.py` line 485. Yes, only PUT /accounts/{id}.
    // To make delete work, let's update status to 'disabled' via the PUT endpoint, or we can add a delete endpoint to admin_routes.py.
    // Let's change the delete logic to update status to 'disabled' and explain it to the admin, or write a delete method.
    // Updating status to 'disabled' is safer so we don't break order histories for sold items!
    showConfirm(
        'Отключить аккаунт?',
        'Вы уверены, что хотите отключить этот аккаунт? Его статус изменится на "disabled" (отключен), и он не будет продаваться пользователям.',
        '🚫',
        async () => {
            try {
                await api.put(`/accounts/${id}`, { status: 'disabled' });
                showToast('Учетные данные аккаунта отключены', 'success');
                await loadStockSummary();
                await loadInventory(currentOffset);
            } catch (err) {
                showToast(err.message || 'Не удалось отключить аккаунт', 'error');
            }
        },
        'btn-danger'
    );
}
