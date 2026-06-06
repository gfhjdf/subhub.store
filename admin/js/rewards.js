/**
 * SubHub.store Admin — Rewards Catalog Module
 */

let activeLangTab = 'uz';
let allPlans = [];

function switchLangTab(lang) {
    activeLangTab = lang;
    document.querySelectorAll('.form-tab').forEach(btn => {
        btn.classList.toggle('active', btn.id === `tab-${lang}`);
    });
    document.getElementById('desc-uz-container').style.display = lang === 'uz' ? 'block' : 'none';
    document.getElementById('desc-ru-container').style.display = lang === 'ru' ? 'block' : 'none';
}

async function initRewards() {
    document.getElementById('reward-form').onsubmit = handleRewardSubmit;
    
    // Populate plans selector
    try {
        const plansData = await api.get('/plans');
        allPlans = plansData.plans || [];
        const planSelect = document.getElementById('reward-plan-id');
        if (planSelect) {
            planSelect.innerHTML = '<option value="">-- Без тарифа (ручная выдача) --</option>';
            allPlans.forEach(plan => {
                const opt = document.createElement('option');
                opt.value = plan.id;
                opt.textContent = `${plan.platform_name} — ${plan.name}`;
                planSelect.appendChild(opt);
            });
        }
    } catch (err) {
        console.error('Failed to load plans:', err);
    }

    await loadRewards();
}

async function loadRewards() {
    const tableBody = document.getElementById('rewards-table-body');
    showLoading(tableBody);

    try {
        const data = await api.get('/rewards');
        const rewards = data.rewards || [];

        if (rewards.length === 0) {
            tableBody.innerHTML = '<tr><td colspan="6" class="text-center text-muted" style="padding: 40px;">Каталог подарков пуст. Нажмите "Добавить подарок".</td></tr>';
            return;
        }

        let html = '';
        rewards.forEach(r => {
            const descUz = r.description_uz ? (r.description_uz.length > 50 ? r.description_uz.substring(0, 47) + '...' : r.description_uz) : '—';
            const descRu = r.description_ru ? (r.description_ru.length > 50 ? r.description_ru.substring(0, 47) + '...' : r.description_ru) : '—';
            const statusText = r.is_active ? '<span class="badge badge-available">Активен</span>' : '<span class="badge badge-disabled">Отключен</span>';
            
            let tariffLabel = '';
            if (r.plan_id) {
                const plan = allPlans.find(p => p.id === r.plan_id);
                if (plan) {
                    tariffLabel = `<div style="font-size: 11px; color: var(--accent-cyan); font-weight: 600; margin-top: 4px;">⚡ Авто-выдача: ${escapeHtml(plan.platform_name)} — ${escapeHtml(plan.name)}</div>`;
                } else {
                    tariffLabel = `<div style="font-size: 11px; color: var(--accent-cyan); font-weight: 600; margin-top: 4px;">⚡ Авто-выдача: Тариф #${r.plan_id}</div>`;
                }
            }

            html += `
                <tr>
                    <td>
                        <strong>${escapeHtml(r.name)}</strong>
                        ${tariffLabel}
                    </td>
                    <td class="text-muted" style="font-size:12px;">${escapeHtml(descUz)}</td>
                    <td class="text-muted" style="font-size:12px;">${escapeHtml(descRu)}</td>
                    <td><strong>${formatNumber(r.points_required)}</strong> баллов</td>
                    <td>${statusText}</td>
                    <td class="text-right">
                        <button class="btn btn-outline btn-sm" onclick="openEditModal(${r.id})">Редактировать</button>
                        <button class="btn btn-danger btn-sm" onclick="deleteReward(${r.id})">Удалить</button>
                    </td>
                </tr>
            `;
        });
        tableBody.innerHTML = html;
    } catch (err) {
        tableBody.innerHTML = `<tr><td colspan="6" class="text-center text-danger" style="padding: 40px;">Ошибка загрузки: ${escapeHtml(err.message)}</td></tr>`;
    }
}

function openCreateModal() {
    document.getElementById('reward-id').value = '';
    document.getElementById('reward-name').value = '';
    document.getElementById('reward-points').value = '';
    if (document.getElementById('reward-plan-id')) {
        document.getElementById('reward-plan-id').value = '';
    }
    document.getElementById('reward-desc-uz').value = '';
    document.getElementById('reward-desc-ru').value = '';
    document.getElementById('reward-active').checked = true;
    
    document.getElementById('reward-modal-title').textContent = 'Добавить подарок';
    switchLangTab('uz');
    openModal('reward-modal');
}

async function openEditModal(rewardId) {
    try {
        const rewardsData = await api.get('/rewards');
        const reward = (rewardsData.rewards || []).find(r => r.id === rewardId);
        if (!reward) throw new Error('Подарок не найден в списке');

        document.getElementById('reward-id').value = reward.id;
        document.getElementById('reward-name').value = reward.name;
        document.getElementById('reward-points').value = reward.points_required;
        if (document.getElementById('reward-plan-id')) {
            document.getElementById('reward-plan-id').value = reward.plan_id || '';
        }
        document.getElementById('reward-desc-uz').value = reward.description_uz || '';
        document.getElementById('reward-desc-ru').value = reward.description_ru || '';
        document.getElementById('reward-active').checked = !!reward.is_active;

        document.getElementById('reward-modal-title').textContent = 'Редактировать подарок';
        switchLangTab('uz');
        openModal('reward-modal');
    } catch (err) {
        showToast('Не удалось загрузить данные подарка: ' + err.message, 'error');
    }
}

async function handleRewardSubmit(e) {
    e.preventDefault();

    const id = document.getElementById('reward-id').value;
    const planIdVal = document.getElementById('reward-plan-id') ? document.getElementById('reward-plan-id').value : '';
    const body = {
        name: document.getElementById('reward-name').value.trim(),
        points_required: parseInt(document.getElementById('reward-points').value, 10),
        plan_id: planIdVal ? parseInt(planIdVal, 10) : null,
        description_uz: document.getElementById('reward-desc-uz').value.trim(),
        description_ru: document.getElementById('reward-desc-ru').value.trim(),
        is_active: document.getElementById('reward-active').checked
    };

    const saveBtn = document.getElementById('reward-save-btn');
    saveBtn.disabled = true;
    saveBtn.textContent = 'Сохранение...';

    try {
        if (id) {
            await api.put(`/rewards/${id}`, body);
            showToast('Подарок успешно обновлен!', 'success');
        } else {
            await api.post('/rewards', body);
            showToast('Подарок успешно добавлен в каталог!', 'success');
        }
        closeModal('reward-modal');
        loadRewards();
    } catch (err) {
        showToast('Ошибка при сохранении: ' + err.message, 'error');
    } finally {
        saveBtn.disabled = false;
        saveBtn.textContent = 'Сохранить';
    }
}

function deleteReward(rewardId) {
    showConfirm(
        'Удалить подарок',
        'Вы уверены, что хотите окончательно удалить этот подарок из каталога?',
        '🗑️',
        async () => {
            try {
                await api.delete(`/rewards/${rewardId}`);
                showToast('Подарок удален из каталога', 'success');
                loadRewards();
            } catch (err) {
                showToast('Не удалось удалить подарок: ' + err.message, 'error');
            }
        },
        'btn-danger'
    );
}
