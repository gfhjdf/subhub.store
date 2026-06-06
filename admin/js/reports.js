/**
 * SubHub.store Admin — Reports Module
 */

let chartRevenue = null;
let chartPlatforms = null;
let chartPayments = null;

function initReports() {
    // Set default dates (past 30 days)
    const end = new Date();
    const start = new Date();
    start.setDate(start.getDate() - 30);

    document.getElementById('report-start-date').value = start.toISOString().split('T')[0];
    document.getElementById('report-end-date').value = end.toISOString().split('T')[0];

    document.getElementById('report-filter-form').onsubmit = (e) => {
        e.preventDefault();
        loadReportData();
    };

    loadReportData();
}

async function loadReportData() {
    const startDate = document.getElementById('report-start-date').value;
    const endDate = document.getElementById('report-end-date').value;

    try {
        const [revData, orderData, refData] = await Promise.all([
            api.get(`/reports/revenue?start_date=${startDate}&end_date=${endDate}`),
            api.get(`/reports/orders?start_date=${startDate}&end_date=${endDate}`),
            api.get(`/reports/referrals`)
        ]);

        // 1. Update KPIs
        document.getElementById('rep-revenue').textContent = formatCurrency(revData.total_revenue);
        document.getElementById('rep-orders').textContent = formatNumber(revData.delivered_count);
        document.getElementById('rep-aov').textContent = formatCurrency(revData.avg_order_value);
        document.getElementById('rep-ref-cost').textContent = formatCurrency(refData.stats.total_paid || 0);

        // 2. Render Charts
        renderRevenueChart(revData.over_time || []);
        renderPlatformsChart(revData.by_platform || []);
        renderPaymentsChart(orderData.by_payment_method || {});

        // 3. Render Leaderboard
        renderLeaderboard(refData.top_inviters || []);

    } catch (err) {
        showToast('Не удалось загрузить данные отчетов: ' + err.message, 'error');
    }
}

function renderRevenueChart(data) {
    if (chartRevenue) chartRevenue.destroy();

    const ctx = document.getElementById('chart-revenue').getContext('2d');
    const labels = data.map(d => formatDateShort(d.date));
    const values = data.map(d => d.revenue);

    chartRevenue = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Выручка (UZS)',
                data: values,
                borderColor: '#8b5cf6',
                backgroundColor: 'rgba(139, 92, 246, 0.1)',
                borderWidth: 2,
                fill: true,
                tension: 0.3
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false }
            },
            scales: {
                y: {
                    grid: { color: 'rgba(255, 255, 255, 0.05)' },
                    ticks: { color: '#94a3b8' }
                },
                x: {
                    grid: { display: false },
                    ticks: { color: '#94a3b8' }
                }
            }
        }
    });
}

function renderPlatformsChart(data) {
    if (chartPlatforms) chartPlatforms.destroy();

    const ctx = document.getElementById('chart-platforms').getContext('2d');
    const labels = data.map(d => d.platform);
    const values = data.map(d => d.revenue);

    chartPlatforms = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Выручка с продаж (UZS)',
                data: values,
                backgroundColor: '#06b6d4',
                borderRadius: 4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false }
            },
            scales: {
                y: {
                    grid: { color: 'rgba(255, 255, 255, 0.05)' },
                    ticks: { color: '#94a3b8' }
                },
                x: {
                    grid: { display: false },
                    ticks: { color: '#94a3b8' }
                }
            }
        }
    });
}

function renderPaymentsChart(data) {
    if (chartPayments) chartPayments.destroy();

    const ctx = document.getElementById('chart-payments').getContext('2d');
    
    // keys map
    const keys = Object.keys(data);
    const values = Object.values(data);
    
    const colors = {
        full_card: '#8b5cf6',
        balance: '#10b981',
        hybrid: '#f59e0b'
    };

    const paymentLabels = {
        full_card: 'Карта',
        balance: 'Баланс',
        hybrid: 'Карта + Баланс'
    };

    const backgroundColors = keys.map(k => colors[k] || '#64748b');

    chartPayments = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: keys.map(k => paymentLabels[k] || k.toUpperCase().replace('_', ' ')),
            datasets: [{
                data: values,
                backgroundColor: backgroundColors,
                borderWidth: 0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: { color: '#f1f5f9', boxWidth: 12 }
                }
            }
        }
    });
}

function renderLeaderboard(data) {
    const container = document.getElementById('leaderboard-container');
    
    if (data.length === 0) {
        container.innerHTML = '<div class="text-center text-muted" style="padding: 20px;">Нет данных о рефералах.</div>';
        return;
    }

    let html = '';
    data.forEach((inv, index) => {
        const username = inv.telegram_username ? `@${inv.telegram_username}` : `ID: ${inv.telegram_id}`;
        const medals = ['🥇', '🥈', '🥉'];
        const rank = medals[index] || `<span class="text-muted" style="font-size:12px; margin-left:4px;">#${index + 1}</span>`;

        html += `
            <div class="leaderboard-item">
                <div style="display:flex; align-items:center; gap: 12px;">
                    <div style="font-size:18px; width:24px; text-align:center;">${rank}</div>
                    <div>
                        <div style="font-weight: 600;">${escapeHtml(inv.first_name || 'User')}</div>
                        <div class="text-muted" style="font-size:11px;">${escapeHtml(username)}</div>
                    </div>
                </div>
                <div class="text-right">
                    <div style="font-weight: 700; color: var(--success);">${inv.invited_count} пригл.</div>
                    <div style="font-size:11px; color: var(--text-muted);">${formatCurrency(inv.total_earned)} получено</div>
                </div>
            </div>
        `;
    });

    container.innerHTML = html;
}
