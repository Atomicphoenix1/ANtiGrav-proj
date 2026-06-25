// ─── State ────────────────────────────────────────────────────────────────────
let efficiencyChart = null;
let savingsChart = null;
let allRequests = [];
let filterQuery = '';

// ─── Formatters ───────────────────────────────────────────────────────────────
function formatNumber(num) {
    if (num >= 1_000_000) return (num / 1_000_000).toFixed(1) + 'M';
    if (num >= 1_000)     return (num / 1_000).toFixed(1) + 'k';
    return num.toString();
}

function formatTime(unixTs) {
    return new Date(unixTs * 1000).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
}

function formatDate(unixTs) {
    return new Date(unixTs * 1000).toLocaleString();
}

// ─── JSON syntax highlighter ──────────────────────────────────────────────────
function syntaxHighlight(json) {
    if (!json) return '<span style="color:var(--text-secondary)">— no data —</span>';
    // Pretty-print if not already
    try { json = JSON.stringify(JSON.parse(json), null, 2); } catch {}
    return json.replace(/("(\\u[a-zA-Z0-9]{4}|\\[^u]|[^\\"])*"(\s*:)?|\b(true|false|null)\b|-?\d+(?:\.\d*)?(?:[eE][+\-]?\d+)?)/g, (match) => {
        let cls = 'json-number';
        if (/^"/.test(match)) {
            cls = /:$/.test(match) ? 'json-key' : 'json-string';
        } else if (/true|false/.test(match)) {
            cls = 'json-bool';
        } else if (/null/.test(match)) {
            cls = 'json-null';
        }
        return `<span class="${cls}">${match}</span>`;
    });
}

// ─── Dashboard fetch & render ─────────────────────────────────────────────────
async function updateDashboard() {
    try {
        const [statsRes, reqsRes] = await Promise.all([
            fetch('/api/stats'),
            fetch('/api/requests?limit=100')
        ]);
        const stats    = await statsRes.json();
        const requests = await reqsRes.json();

        allRequests = requests;

        // Top stat cards
        document.getElementById('stat-money-saved').textContent = `$${stats.total_saved_usd.toFixed(4)}`;

        const hitRate = stats.total_input_tokens > 0
            ? ((stats.total_cached_tokens / stats.total_input_tokens) * 100).toFixed(1)
            : '0.0';
        document.getElementById('stat-hit-rate').textContent = `${hitRate}%`;
        document.getElementById('stat-cached-tokens').textContent = formatNumber(stats.total_cached_tokens);
        document.getElementById('stat-total-tokens').textContent  = `of ${formatNumber(stats.total_input_tokens)} total input tokens`;
        document.getElementById('stat-latency').textContent = `${stats.avg_latency_ms.toFixed(0)} ms`;

        updateCharts(stats);
        renderTable(requests);

    } catch (err) {
        console.error('Dashboard update error:', err);
    }
}

// ─── Table render ──────────────────────────────────────────────────────────────
function renderTable(requests) {
    const q = filterQuery.toLowerCase();
    const filtered = q
        ? requests.filter(r =>
            r.client_app.toLowerCase().includes(q) ||
            r.provider.toLowerCase().includes(q) ||
            r.model.toLowerCase().includes(q) ||
            String(r.status_code).includes(q)
          )
        : requests;

    document.getElementById('req-count').textContent = filtered.length;
    const tbody = document.getElementById('requests-tbody');

    if (filtered.length === 0) {
        tbody.innerHTML = `<tr><td colspan="12" class="empty-state">
            <i class="fa-solid fa-satellite-dish" style="font-size:2rem;margin-bottom:0.75rem;opacity:0.4;"></i><br>
            No requests intercepted yet.<br>
            <small>Point your agent base URL to <code>http://localhost:8000</code></small>
        </td></tr>`;
        return;
    }

    tbody.innerHTML = '';
    filtered.forEach((req, idx) => {
        const tr = document.createElement('tr');
        tr.className = 'data-row';

        const providerKey = req.provider.toLowerCase();
        const badgeClass  = `badge badge-${providerKey}`;
        const statusClass = req.status_code === 200 ? 'status-success' : 'status-error';
        const savingsText = req.cost_saved_usd > 0 ? `<span class="savings-highlight">$${req.cost_saved_usd.toFixed(4)}</span>` : '<span style="color:var(--text-secondary)">—</span>';
        const cacheBar    = req.input_tokens > 0
            ? `<div style="font-size:0.7rem;color:var(--accent-emerald);">${Math.round(req.cached_input_tokens/req.input_tokens*100)}% cached</div>`
            : '';

        tr.innerHTML = `
            <td class="mono" style="color:var(--text-secondary);font-size:0.75rem;">${idx + 1}</td>
            <td class="mono" style="font-size:0.77rem;white-space:nowrap;">${formatTime(req.timestamp)}</td>
            <td><strong>${req.client_app}</strong></td>
            <td><span class="${badgeClass}">${req.provider}</span></td>
            <td class="mono" style="max-width:180px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;font-size:0.78rem;" title="${req.model}">${req.model}</td>
            <td class="mono">${req.input_tokens.toLocaleString()}</td>
            <td class="mono">${req.cached_input_tokens.toLocaleString()}${cacheBar}</td>
            <td class="mono">${req.output_tokens.toLocaleString()}</td>
            <td>${savingsText}</td>
            <td class="mono">${req.latency_ms} ms</td>
            <td class="${statusClass} mono">${req.status_code}</td>
            <td><button class="view-log-btn" data-id="${req.id}"><i class="fa-solid fa-magnifying-glass"></i> Logs</button></td>
        `;

        // Click row or button → open modal
        tr.querySelector('.view-log-btn').addEventListener('click', (e) => {
            e.stopPropagation();
            openModal(req);
        });
        tr.addEventListener('click', () => openModal(req));
        tbody.appendChild(tr);
    });
}

// ─── Charts ────────────────────────────────────────────────────────────────────
function updateCharts(stats) {
    const daily        = stats.daily || [];
    const labels       = daily.map(d => d.day);
    const inputTokens  = daily.map(d => d.input);
    const cachedTokens = daily.map(d => d.cached);
    const savings      = daily.map(d => d.saved);

    const chartDefaults = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { labels: { color: '#8c9ba5' } } },
        scales: {
            x: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#8c9ba5' } },
            y: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#8c9ba5' } }
        }
    };

    if (!efficiencyChart) {
        efficiencyChart = new Chart(
            document.getElementById('efficiencyChart').getContext('2d'),
            {
                type: 'line',
                data: {
                    labels,
                    datasets: [
                        { label: 'Total Input Tokens', data: inputTokens, borderColor: '#6366f1', backgroundColor: 'rgba(99,102,241,0.1)', fill: true, tension: 0.4 },
                        { label: 'Cached Tokens',      data: cachedTokens, borderColor: '#10b981', backgroundColor: 'rgba(16,185,129,0.1)', fill: true, tension: 0.4 }
                    ]
                },
                options: chartDefaults
            }
        );
    } else {
        efficiencyChart.data.labels = labels;
        efficiencyChart.data.datasets[0].data = inputTokens;
        efficiencyChart.data.datasets[1].data = cachedTokens;
        efficiencyChart.update();
    }

    if (!savingsChart) {
        savingsChart = new Chart(
            document.getElementById('savingsChart').getContext('2d'),
            {
                type: 'bar',
                data: {
                    labels,
                    datasets: [{ label: 'USD Saved', data: savings, backgroundColor: 'rgba(6,182,212,0.6)', borderColor: '#06b6d4', borderWidth: 1, borderRadius: 4 }]
                },
                options: chartDefaults
            }
        );
    } else {
        savingsChart.data.labels = labels;
        savingsChart.data.datasets[0].data = savings;
        savingsChart.update();
    }
}

// ─── Modal ─────────────────────────────────────────────────────────────────────
function openModal(req) {
    const overlay = document.getElementById('detail-modal');

    // Badge
    const badge = document.getElementById('modal-badge');
    badge.className = `badge badge-${req.provider.toLowerCase()}`;
    badge.textContent = req.provider;

    // Title
    document.getElementById('modal-title').textContent = req.model;

    // Meta strip
    document.getElementById('meta-app').textContent      = req.client_app;
    document.getElementById('meta-model').textContent    = req.model;
    document.getElementById('meta-endpoint').textContent = req.endpoint;
    document.getElementById('meta-status').textContent   = req.status_code;
    document.getElementById('meta-status').className     = req.status_code === 200 ? 'status-success' : 'status-error';
    document.getElementById('meta-latency').textContent  = `${req.latency_ms} ms`;
    document.getElementById('meta-input').textContent    = req.input_tokens.toLocaleString();
    document.getElementById('meta-cached').textContent   = `${req.cached_input_tokens.toLocaleString()} (${req.input_tokens > 0 ? Math.round(req.cached_input_tokens/req.input_tokens*100) : 0}%)`;
    document.getElementById('meta-output').textContent   = req.output_tokens.toLocaleString();
    document.getElementById('meta-actual').textContent   = `$${req.cost_actual_usd.toFixed(5)}`;
    document.getElementById('meta-saved').textContent    = req.cost_saved_usd > 0 ? `$${req.cost_saved_usd.toFixed(5)}` : '—';

    // Code blocks
    document.getElementById('req-code').innerHTML = syntaxHighlight(req.raw_request  || '{}');
    document.getElementById('res-code').innerHTML = syntaxHighlight(req.raw_response || '{}');

    // Reset to request tab
    switchTab('request');

    overlay.style.display = 'flex';
    document.body.style.overflow = 'hidden';
}

function closeModal() {
    document.getElementById('detail-modal').style.display = 'none';
    document.body.style.overflow = '';
}

function switchTab(tab) {
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.toggle('active', b.dataset.tab === tab));
    document.querySelectorAll('.tab-panel').forEach(p => p.classList.toggle('active', p.id === `tab-${tab}`));
}

// ─── Event listeners ───────────────────────────────────────────────────────────
document.getElementById('modal-close').addEventListener('click', closeModal);
document.getElementById('detail-modal').addEventListener('click', (e) => {
    if (e.target === e.currentTarget) closeModal();
});
document.addEventListener('keydown', (e) => { if (e.key === 'Escape') closeModal(); });

document.querySelectorAll('.tab-btn').forEach(btn =>
    btn.addEventListener('click', () => switchTab(btn.dataset.tab))
);

document.querySelectorAll('.copy-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        const target = document.getElementById(btn.dataset.target);
        navigator.clipboard.writeText(target.innerText).then(() => {
            btn.innerHTML = '<i class="fa-solid fa-check"></i> Copied!';
            btn.classList.add('copied');
            setTimeout(() => {
                btn.innerHTML = '<i class="fa-solid fa-copy"></i> Copy';
                btn.classList.remove('copied');
            }, 1800);
        });
    });
});

document.getElementById('refresh-btn').addEventListener('click', updateDashboard);

document.getElementById('filter-input').addEventListener('input', (e) => {
    filterQuery = e.target.value;
    renderTable(allRequests);
});

// ─── Boot ──────────────────────────────────────────────────────────────────────
updateDashboard();
setInterval(updateDashboard, 4000);
