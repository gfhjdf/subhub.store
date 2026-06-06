/**
 * SubHub.store Admin — Settings Module
 */

function switchSettingsTab(lang) {
    document.querySelectorAll('.form-tab').forEach(btn => {
        btn.classList.toggle('active', btn.id === `tab-${lang}`);
    });
    document.getElementById('fields-uz').style.display = lang === 'uz' ? 'block' : 'none';
    document.getElementById('fields-ru').style.display = lang === 'ru' ? 'block' : 'none';
}

async function initSettings() {
    document.getElementById('settings-form').onsubmit = handleSettingsSubmit;
    const securityForm = document.getElementById('admin-security-form');
    if (securityForm) {
        securityForm.onsubmit = handleSecuritySubmit;
    }
    await loadSettings();
}

async function loadSettings() {
    try {
        const data = await api.get('/settings');
        const settings = data.settings || {};

        document.getElementById('set-card-number').value = settings.card_number || '';
        document.getElementById('set-card-holder').value = settings.card_holder || '';
        document.getElementById('set-points-referral').value = settings.points_per_referral || '1';
        document.getElementById('set-points-checkin').value = settings.points_per_daily_checkin || '1';
        document.getElementById('set-ref-reward').value = settings.referral_reward_uzs || 3000;
        document.getElementById('set-stock-threshold').value = settings.low_stock_threshold || 5;
        document.getElementById('set-support-contact').value = settings.support_contact || '';
        document.getElementById('set-wallet-enabled').value = settings.wallet_enabled || 'true';
        document.getElementById('set-wallet-min').value = settings.wallet_min_topup || '5000';
        document.getElementById('set-wallet-max').value = settings.wallet_max_topup || '1000000';
        
        document.getElementById('set-sub-enabled').value = settings.sub_check_enabled || 'false';
        document.getElementById('set-sub-channel').value = settings.sub_channel_username || '';
        document.getElementById('set-sub-msg-uz').value = settings.sub_message_uz || '';
        document.getElementById('set-sub-msg-ru').value = settings.sub_message_ru || '';
        
        document.getElementById('set-instructions-uz').value = settings.payment_instructions_uz || '';
        document.getElementById('set-instructions-ru').value = settings.payment_instructions_ru || '';
        
        document.getElementById('set-warranty-uz').value = settings.warranty_expired_uz || '';
        document.getElementById('set-warranty-ru').value = settings.warranty_expired_ru || '';
        
        document.getElementById('set-faq-uz').value = settings.faq_general_uz || '';
        document.getElementById('set-faq-ru').value = settings.faq_general_ru || '';

    } catch (err) {
        showToast('Не удалось загрузить настройки: ' + err.message, 'error');
    }
}

async function handleSettingsSubmit(e) {
    e.preventDefault();
    
    const settings = {
        card_number: document.getElementById('set-card-number').value.trim(),
        card_holder: document.getElementById('set-card-holder').value.trim(),
        points_per_referral: document.getElementById('set-points-referral').value.trim(),
        points_per_daily_checkin: document.getElementById('set-points-checkin').value.trim(),
        referral_reward_uzs: parseInt(document.getElementById('set-ref-reward').value) || 0,
        low_stock_threshold: parseInt(document.getElementById('set-stock-threshold').value) || 0,
        support_contact: document.getElementById('set-support-contact').value.trim(),
        wallet_enabled: document.getElementById('set-wallet-enabled').value,
        wallet_min_topup: document.getElementById('set-wallet-min').value.trim(),
        wallet_max_topup: document.getElementById('set-wallet-max').value.trim(),
        
        sub_check_enabled: document.getElementById('set-sub-enabled').value,
        sub_channel_username: document.getElementById('set-sub-channel').value.trim(),
        sub_message_uz: document.getElementById('set-sub-msg-uz').value.trim(),
        sub_message_ru: document.getElementById('set-sub-msg-ru').value.trim(),
        
        payment_instructions_uz: document.getElementById('set-instructions-uz').value.trim(),
        payment_instructions_ru: document.getElementById('set-instructions-ru').value.trim(),
        
        warranty_expired_uz: document.getElementById('set-warranty-uz').value.trim(),
        warranty_expired_ru: document.getElementById('set-warranty-ru').value.trim(),
        
        faq_general_uz: document.getElementById('set-faq-uz').value.trim(),
        faq_general_ru: document.getElementById('set-faq-ru').value.trim()
    };

    const submitBtn = document.querySelector('#settings-form button[type="submit"]');
    submitBtn.disabled = true;
    submitBtn.textContent = 'Сохранение...';

    try {
        await api.put('/settings', { settings });
        showToast('Настройки успешно сохранены!', 'success');
    } catch (err) {
        showToast('Не удалось сохранить настройки: ' + err.message, 'error');
    } finally {
        submitBtn.disabled = false;
        submitBtn.textContent = 'Сохранить настройки системы';
    }
}

async function handleSecuritySubmit(e) {
    e.preventDefault();

    const newUsername = document.getElementById('sec-new-username').value.trim();
    const newPassword = document.getElementById('sec-new-password').value;
    const currentPassword = document.getElementById('sec-current-password').value;

    if (!newUsername && !newPassword) {
        showToast('Пожалуйста, введите новый логин или новый пароль для изменения', 'error');
        return;
    }

    if (newPassword && newPassword.length < 6) {
        showToast('Пароль должен состоять минимум из 6 символов', 'error');
        return;
    }

    if (!currentPassword) {
        showToast('Пожалуйста, введите текущий пароль для подтверждения', 'error');
        return;
    }

    const submitBtn = document.querySelector('#admin-security-form button[type="submit"]');
    submitBtn.disabled = true;
    submitBtn.textContent = 'Обновление...';

    try {
        const body = {
            current_password: currentPassword
        };
        if (newUsername) body.new_username = newUsername;
        if (newPassword) body.new_password = newPassword;

        await api.put('/auth/me', body);
        showToast('Данные входа успешно обновлены! Выход из системы...', 'success');
        
        setTimeout(() => {
            redirectToLogin();
        }, 1500);

    } catch (err) {
        showToast('Не удалось обновить учетные данные: ' + err.message, 'error');
        submitBtn.disabled = false;
        submitBtn.textContent = 'Обновить учетные данные';
        document.getElementById('sec-current-password').value = '';
    }
}
