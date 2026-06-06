/**
 * SubHub.store Admin — Platforms & Plans Module
 */

let activeLanguageTab = 'uz';

function switchLanguageTab(lang) {
    activeLanguageTab = lang;
    document.querySelectorAll('.form-tab').forEach(btn => {
        btn.classList.toggle('active', btn.id === `tab-${lang}`);
    });
    document.getElementById('fields-uz').style.display = lang === 'uz' ? 'block' : 'none';
    document.getElementById('fields-ru').style.display = lang === 'ru' ? 'block' : 'none';
}

async function initCatalog() {
    // Add Platform button handler
    document.getElementById('btn-add-platform').onclick = () => {
        openPlatformModal();
    };

    // Form submissions
    document.getElementById('platform-form').onsubmit = handlePlatformSubmit;
    document.getElementById('plan-form').onsubmit = handlePlanSubmit;

    // Load catalog
    await loadCatalog();
}

async function loadCatalog() {
    const container = document.getElementById('catalog-list');
    showLoading(container);

    try {
        const [platformsData, plansData, stockData] = await Promise.all([
            api.get('/platforms'),
            api.get('/plans'),
            api.get('/accounts/stock-summary')
        ]);

        const platforms = platformsData.platforms;
        const plans = plansData.plans;
        const stockSummary = stockData.summary || [];

        // Build stock map for quick lookup
        const stockMap = {};
        stockSummary.forEach(item => {
            stockMap[item.plan_id] = item.available || 0;
        });

        if (platforms.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <div class="empty-icon">🎮</div>
                    <div class="empty-title">Каталог пуст</div>
                    <div class="empty-subtitle">Создайте вашу первую платформу, чтобы начать</div>
                    <button class="btn btn-primary mt-16" onclick="openPlatformModal()">➕ Добавить платформу</button>
                </div>
            `;
            return;
        }

        let html = '';
        platforms.forEach(p => {
            // Filter plans for this platform
            const platformPlans = plans.filter(plan => plan.platform_id === p.id);

            let plansHtml = '';
            if (platformPlans.length === 0) {
                plansHtml = `
                    <tr>
                        <td colspan="6" class="text-center text-muted" style="padding: 16px;">
                            Для этой платформы тарифы еще не созданы.
                        </td>
                    </tr>
                `;
            } else {
                platformPlans.forEach(plan => {
                    const availableStock = stockMap[plan.id] || 0;
                    const stockClass = availableStock === 0 ? 'text-danger font-semibold' : (availableStock < 5 ? 'text-warning font-semibold' : 'text-success');
                    
                    let priceHtml = formatCurrency(plan.price_uzs);
                    if (plan.plan_type === 'contact_admin') {
                        priceHtml += ` <span class="badge badge-purple" style="font-size:10px; padding: 2px 6px; margin-left: 4px;">TG</span>`;
                    }

                    plansHtml += `
                        <tr>
                            <td><strong>${escapeHtml(plan.name)}</strong></td>
                            <td>${priceHtml}</td>
                            <td><span class="${stockClass}">${availableStock} шт.</span></td>
                            <td>${plan.is_active ? '<span class="badge badge-approved">Активен</span>' : '<span class="badge badge-cancelled">Отключен</span>'}</td>
                            <td><code>${plan.sort_order}</code></td>
                            <td class="text-right">
                                <button class="btn btn-outline btn-sm" style="margin-right: 4px;" onclick="openPlanModal(${p.id}, ${plan.id}, ${JSON.stringify(plan).replace(/"/g, '&quot;')})">Редактировать</button>
                                <button class="btn btn-danger btn-sm" onclick="deletePlan(${plan.id})">Удалить</button>
                            </td>
                        </tr>
                    `;
                });
            }

            const emojiStr = p.custom_emoji_code ? (/^\d+$/.test(p.custom_emoji_code.trim()) ? '🔹 ' : p.custom_emoji_code + ' ') : '';
            html += `
                <div class="card platform-card">
                    <div class="card-header" style="flex-wrap: wrap; gap: 12px;">
                        <div>
                            <div style="display: flex; align-items: center; gap: 8px;">
                                <h3 class="card-title">${emojiStr}${escapeHtml(p.name)}</h3>
                                ${p.is_active ? '<span class="badge badge-approved">Активен</span>' : '<span class="badge badge-cancelled">Отключен</span>'}
                            </div>
                            <div class="card-subtitle">Slug: <code>${escapeHtml(p.slug)}</code> | Сорт: <code>${p.sort_order}</code></div>
                        </div>
                        <div style="display: flex; gap: 8px;">
                            <button class="btn btn-outline btn-sm" onclick="openPlatformModal(${JSON.stringify(p).replace(/"/g, '&quot;')})">Редактировать</button>
                            <button class="btn btn-danger btn-sm" onclick="deletePlatform(${p.id})">Удалить</button>
                            <button class="btn btn-primary btn-sm" onclick="openPlanModal(${p.id})">➕ Добавить тариф</button>
                        </div>
                    </div>
                    <div class="table-container" style="border: none; padding: 0 24px 24px 24px;">
                        <table class="plans-table" style="width: 100%;">
                            <thead>
                                <tr>
                                    <th>Название тарифа</th>
                                    <th>Цена</th>
                                    <th>Запас</th>
                                    <th>Статус</th>
                                    <th>Сорт</th>
                                    <th class="text-right">Действия</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${plansHtml}
                            </tbody>
                        </table>
                    </div>
                </div>
            `;
        });

        container.innerHTML = html;

    } catch (err) {
        container.innerHTML = `<div class="alert alert-danger">Ошибка загрузки каталога: ${escapeHtml(err.message)}</div>`;
    }
}

// ─── PLATFORM CRUD ──────────────────────────────────────────

function openPlatformModal(platformObj = null) {
    if (platformObj) {
        document.getElementById('platform-id').value = platformObj.id || '';
        document.getElementById('platform-name').value = platformObj.name || '';
        document.getElementById('platform-slug').value = platformObj.slug || '';
        document.getElementById('platform-emoji').value = platformObj.custom_emoji_code || '';
        document.getElementById('platform-sort').value = platformObj.sort_order || 0;
        document.getElementById('platform-active').checked = platformObj.is_active;
        document.getElementById('platform-modal-title').textContent = 'Редактировать платформу';
    } else {
        document.getElementById('platform-form').reset();
        document.getElementById('platform-id').value = '';
        document.getElementById('platform-emoji').value = '';
        document.getElementById('platform-sort').value = 0;
        document.getElementById('platform-active').checked = true;
        document.getElementById('platform-modal-title').textContent = 'Добавить платформу';
    }
    openModal('platform-modal');
}

async function handlePlatformSubmit(e) {
    e.preventDefault();
    const id = document.getElementById('platform-id').value;
    const name = document.getElementById('platform-name').value.trim();
    const slug = document.getElementById('platform-slug').value.trim();
    const customEmojiCode = document.getElementById('platform-emoji').value.trim();
    const sortOrder = parseInt(document.getElementById('platform-sort').value) || 0;
    const isActive = document.getElementById('platform-active').checked;

    const body = {
        name,
        slug,
        custom_emoji_code: customEmojiCode || null,
        sort_order: sortOrder,
        is_active: isActive
    };

    try {
        if (id) {
            await api.put(`/platforms/${id}`, body);
            showToast('Платформа успешно обновлена', 'success');
        } else {
            await api.post('/platforms', body);
            showToast('Платформа успешно создана', 'success');
        }
        closeModal('platform-modal');
        loadCatalog();
    } catch (err) {
        showToast(err.message || 'Не удалось сохранить платформу', 'error');
    }
}

async function deletePlatform(id) {
    showConfirm(
        'Удалить платформу?',
        'Вы уверены, что хотите удалить эту платформу? Все тарифы внутри нее также будут удалены из базы данных.',
        '🗑️',
        async () => {
            try {
                await api.delete(`/platforms/${id}`);
                showToast('Платформа удалена', 'success');
                loadCatalog();
            } catch (err) {
                showToast(err.message || 'Ошибка удаления', 'error');
            }
        },
        'btn-danger'
    );
}

// ─── PLAN CRUD ──────────────────────────────────────────────

function openPlanModal(platformId, planId = null, planObj = null) {
    switchLanguageTab('uz');
    document.getElementById('plan-id').value = planId || '';
    document.getElementById('plan-platform-id').value = platformId;
    
    if (planObj) {
        document.getElementById('plan-name').value = planObj.name || '';
        document.getElementById('plan-price').value = planObj.price_uzs || '';
        document.getElementById('plan-sort').value = planObj.sort_order || 0;
        document.getElementById('plan-active').checked = planObj.is_active;
        document.getElementById('plan-type').value = planObj.plan_type || 'regular';
        document.getElementById('plan-desc-uz').value = planObj.description_uz || '';
        document.getElementById('plan-desc-ru').value = planObj.description_ru || '';
        document.getElementById('plan-faq-uz').value = planObj.faq_uz || '';
        document.getElementById('plan-faq-ru').value = planObj.faq_ru || '';
        document.getElementById('plan-modal-title').textContent = 'Редактировать тариф';
    } else {
        document.getElementById('plan-form').reset();
        document.getElementById('plan-id').value = '';
        document.getElementById('plan-platform-id').value = platformId;
        document.getElementById('plan-sort').value = 0;
        document.getElementById('plan-active').checked = true;
        document.getElementById('plan-type').value = 'regular';
        document.getElementById('plan-modal-title').textContent = 'Добавить тариф';
    }
    
    openModal('plan-modal');
}

async function handlePlanSubmit(e) {
    e.preventDefault();
    const id = document.getElementById('plan-id').value;
    const platformId = parseInt(document.getElementById('plan-platform-id').value);
    const name = document.getElementById('plan-name').value.trim();
    const price = parseInt(document.getElementById('plan-price').value);
    const sortOrder = parseInt(document.getElementById('plan-sort').value) || 0;
    const isActive = document.getElementById('plan-active').checked;
    const planType = document.getElementById('plan-type').value;
    
    const descUz = document.getElementById('plan-desc-uz').value.trim();
    const descRu = document.getElementById('plan-desc-ru').value.trim();
    const faqUz = document.getElementById('plan-faq-uz').value.trim();
    const faqRu = document.getElementById('plan-faq-ru').value.trim();

    const body = {
        platform_id: platformId,
        name,
        price_uzs: price,
        description_uz: descUz,
        description_ru: descRu,
        faq_uz: faqUz,
        faq_ru: faqRu,
        is_active: isActive,
        sort_order: sortOrder,
        plan_type: planType
    };

    try {
        if (id) {
            await api.put(`/plans/${id}`, body);
            showToast('Тариф успешно обновлен', 'success');
        } else {
            await api.post('/plans', body);
            showToast('Тариф успешно создан', 'success');
        }
        closeModal('plan-modal');
        loadCatalog();
    } catch (err) {
        showToast(err.message || 'Не удалось сохранить тариф', 'error');
    }
}

async function deletePlan(id) {
    showConfirm(
        'Удалить тариф?',
        'Вы уверены, что хотите удалить этот тариф? Все аккаунты, связанные с этим тарифом, останутся в базе данных, но связь с тарифом будет удалена.',
        '🗑️',
        async () => {
            try {
                await api.delete(`/plans/${id}`);
                showToast('Тариф удален', 'success');
                loadCatalog();
            } catch (err) {
                showToast(err.message || 'Ошибка удаления', 'error');
            }
        },
        'btn-danger'
    );
}
