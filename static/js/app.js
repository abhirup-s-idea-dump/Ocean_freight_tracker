/**
 * Ocean Freight Rate & Shipment Tracker Frontend Application
 * Interacts with FastAPI backend endpoints for all 4 modules.
 */

// Application State
const state = {
    currentUser: null,
    activeTab: 'overview',
    ports: { origin_ports: [], destination_ports: [], carriers: [], container_types: ['20ft', '40ft'] },
    rateSearchResults: null,
    shipments: [],
    shipmentFilter: { status: 'all', carrier: 'all', search: '' },
    chartInstance: null,
    inboxEmails: [],
    parsingResults: null,
    fxRate: 83.50
};

// Initialization
document.addEventListener('DOMContentLoaded', async () => {
    await checkAuth();
    await loadPortDropdowns();
    await loadShipments();
    await loadShipmentStats();
    await loadInbox();
    await runInvoiceAudit();
    setupEventListeners();
});

// ----------------------------------------------------------------------------
// AUTHENTICATION & ROLES
// ----------------------------------------------------------------------------

// ----------------------------------------------------------------------------
// AUTHENTICATION & CREDENTIAL STORAGE
// ----------------------------------------------------------------------------

function switchAuthMode(mode) {
    const loginForm = document.getElementById('login-form');
    const registerForm = document.getElementById('register-form');
    const tabLogin = document.getElementById('auth-tab-login');
    const tabRegister = document.getElementById('auth-tab-register');
    const loginErr = document.getElementById('login-error-msg');
    const regErr = document.getElementById('register-error-msg');

    if (loginErr) loginErr.classList.add('hidden');
    if (regErr) regErr.classList.add('hidden');

    if (mode === 'register') {
        loginForm?.classList.add('hidden');
        registerForm?.classList.remove('hidden');
        tabLogin?.classList.remove('bg-sky-500', 'text-white');
        tabLogin?.classList.add('text-slate-400');
        tabRegister?.classList.remove('text-slate-400');
        tabRegister?.classList.add('bg-emerald-500', 'text-white');
    } else {
        registerForm?.classList.add('hidden');
        loginForm?.classList.remove('hidden');
        tabRegister?.classList.remove('bg-emerald-500', 'text-white');
        tabRegister?.classList.add('text-slate-400');
        tabLogin?.classList.remove('text-slate-400');
        tabLogin?.classList.add('bg-sky-500', 'text-white');
    }
}

async function checkAuth() {
    const loginScreen = document.getElementById('login-screen');
    const appWorkspace = document.getElementById('app-workspace');

    try {
        const res = await fetch('/api/auth/me');
        const data = await res.json();
        if (data.authenticated && data.user) {
            state.currentUser = data.user;
            loginScreen?.classList.add('hidden');
            appWorkspace?.classList.remove('hidden');
            renderAuthUI();
            await loadPortDropdowns();
            await loadShipments();
            await loadShipmentStats();
            await loadInbox();
            await runInvoiceAudit();
        } else {
            state.currentUser = null;
            loginScreen?.classList.remove('hidden');
            appWorkspace?.classList.add('hidden');
            renderAuthUI();
        }
    } catch (e) {
        console.error('Auth check error:', e);
        state.currentUser = null;
        loginScreen?.classList.remove('hidden');
        appWorkspace?.classList.add('hidden');
        renderAuthUI();
    }
}

function renderAuthUI() {
    const authContainer = document.getElementById('auth-header-container');
    if (!authContainer) return;

    if (state.currentUser) {
        const isAdmin = state.currentUser.role === 'admin';
        authContainer.innerHTML = `
            <div class="flex items-center gap-3">
                <div class="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-800/80 border border-white/[0.08] text-sm">
                    <span class="w-2.5 h-2.5 rounded-full ${isAdmin ? 'bg-purple-400' : 'bg-cyan-400'} animate-pulse"></span>
                    <span class="font-medium text-slate-200">${state.currentUser.full_name}</span>
                    <span class="px-2 py-0.5 rounded text-xs font-semibold uppercase ${isAdmin ? 'bg-purple-900/60 text-purple-300 border border-purple-700' : 'bg-cyan-900/60 text-cyan-300 border border-cyan-700'}">
                        ${state.currentUser.role}
                    </span>
                </div>
                ${isAdmin ? `
                    <button onclick="resetDemoData()" class="px-3 py-1.5 rounded-lg bg-red-950/40 hover:bg-red-900/60 text-xs text-red-300 border border-red-800/60 transition" title="Reset all data to pristine sample files">
                        <i class="fa-solid fa-rotate-left mr-1"></i> Reset Data
                    </button>
                ` : ''}
                <button onclick="logout()" class="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs text-slate-300 border border-white/[0.08] transition" title="Log out from current session">
                    <i class="fa-solid fa-arrow-right-from-bracket mr-1"></i> Logout
                </button>
            </div>
        `;
    } else {
        authContainer.innerHTML = '';
    }
}

async function loginAs(username, password) {
    const errorMsgEl = document.getElementById('login-error-msg');
    const submitBtn = document.getElementById('login-submit-btn');
    const loginScreen = document.getElementById('login-screen');
    const appWorkspace = document.getElementById('app-workspace');

    if (errorMsgEl) errorMsgEl.classList.add('hidden');
    if (submitBtn) {
        submitBtn.innerHTML = `<i class="fa-solid fa-spinner fa-spin mr-2"></i> Verifying password hash...`;
        submitBtn.disabled = true;
    }

    try {
        const res = await fetch('/api/auth/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });
        const data = await res.json();
        if (res.ok) {
            state.currentUser = data.user;
            loginScreen?.classList.add('hidden');
            appWorkspace?.classList.remove('hidden');
            renderAuthUI();
            showToast(`Welcome back, ${data.user.full_name} (${data.user.role.toUpperCase()})`, 'success');
            await loadPortDropdowns();
            await loadShipments();
            await loadShipmentStats();
            await loadInbox();
            await runInvoiceAudit();
        } else {
            if (errorMsgEl) {
                errorMsgEl.innerText = data.detail || 'Invalid username or password';
                errorMsgEl.classList.remove('hidden');
            }
            showToast(data.detail || 'Authentication failed', 'error');
        }
    } catch (e) {
        if (errorMsgEl) {
            errorMsgEl.innerText = 'Unable to connect to authentication server';
            errorMsgEl.classList.remove('hidden');
        }
        showToast('Login request failed', 'error');
    } finally {
        if (submitBtn) {
            submitBtn.innerHTML = `<i class="fa-solid fa-arrow-right-to-bracket mr-2"></i> Sign In to Dashboard`;
            submitBtn.disabled = false;
        }
    }
}

async function registerAccount(fullName, username, password, role) {
    const errorMsgEl = document.getElementById('register-error-msg');
    const submitBtn = document.getElementById('register-submit-btn');
    const loginScreen = document.getElementById('login-screen');
    const appWorkspace = document.getElementById('app-workspace');

    if (errorMsgEl) errorMsgEl.classList.add('hidden');
    if (submitBtn) {
        submitBtn.innerHTML = `<i class="fa-solid fa-spinner fa-spin mr-2"></i> Storing credentials with PBKDF2 salt...`;
        submitBtn.disabled = true;
    }

    try {
        const res = await fetch('/api/auth/register', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                full_name: fullName,
                username: username,
                password: password,
                role: role
            })
        });
        const data = await res.json();
        if (res.ok) {
            state.currentUser = data.user;
            loginScreen?.classList.add('hidden');
            appWorkspace?.classList.remove('hidden');
            renderAuthUI();
            showToast(data.message || `Account created successfully!`, 'success');
            await loadPortDropdowns();
            await loadShipments();
            await loadShipmentStats();
            await loadInbox();
            await runInvoiceAudit();
        } else {
            if (errorMsgEl) {
                errorMsgEl.innerText = data.detail || 'Failed to register account';
                errorMsgEl.classList.remove('hidden');
            }
            showToast(data.detail || 'Registration failed', 'error');
        }
    } catch (e) {
        if (errorMsgEl) {
            errorMsgEl.innerText = 'Unable to connect to authentication server';
            errorMsgEl.classList.remove('hidden');
        }
        showToast('Registration request failed', 'error');
    } finally {
        if (submitBtn) {
            submitBtn.innerHTML = `<i class="fa-solid fa-floppy-disk mr-2"></i> Store Credentials & Sign In`;
            submitBtn.disabled = false;
        }
    }
}

function fillAndLogin(username, password) {
    const uField = document.getElementById('login-username');
    const pField = document.getElementById('login-password');
    if (uField) uField.value = username;
    if (pField) pField.value = password;
    loginAs(username, password);
}

async function logout() {
    const loginScreen = document.getElementById('login-screen');
    const appWorkspace = document.getElementById('app-workspace');

    try {
        await fetch('/api/auth/logout', { method: 'POST' });
    } catch (e) {
        // Continue clearing local state
    }
    state.currentUser = null;
    appWorkspace?.classList.add('hidden');
    loginScreen?.classList.remove('hidden');
    renderAuthUI();
    showToast('Logged out successfully. Please sign in to continue.', 'info');
}

async function resetDemoData() {
    if (!confirm('Reset all carrier rates, shipments, and email logs back to initial sample CSVs?')) return;
    try {
        const res = await fetch('/api/system/reset', { method: 'POST' });
        const data = await res.json();
        showToast(data.message, 'success');
        await loadShipments();
        await loadShipmentStats();
        await loadPortDropdowns();
        await runInvoiceAudit();
        if (state.rateSearchResults) searchRates();
    } catch (e) {
        showToast('Reset failed', 'error');
    }
}


// ----------------------------------------------------------------------------
// NAVIGATION TABS
// ----------------------------------------------------------------------------

function switchTab(tabName) {
    state.activeTab = tabName;
    document.querySelectorAll('.tab-content').forEach(el => el.classList.add('hidden'));
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('bg-sky-500/10', 'text-sky-400', 'border-sky-500');
        btn.classList.add('text-slate-400', 'border-transparent');
    });

    const targetContent = document.getElementById(`tab-${tabName}`);
    const targetBtn = document.getElementById(`nav-${tabName}`);
    if (targetContent) targetContent.classList.remove('hidden');
    if (targetBtn) {
        targetBtn.classList.add('bg-sky-500/10', 'text-sky-400', 'border-sky-500');
        targetBtn.classList.remove('text-slate-400', 'border-transparent');
    }

    if (tabName === 'overview') {
        loadShipmentStats();
    } else if (tabName === 'shipments') {
        loadShipments();
    } else if (tabName === 'emails') {
        loadInbox();
    } else if (tabName === 'invoices') {
        runInvoiceAudit();
    }
}


// ----------------------------------------------------------------------------
// MODULE 1: RATE SEARCH
// ----------------------------------------------------------------------------

async function loadPortDropdowns() {
    try {
        const res = await fetch('/api/rates/ports');
        const data = await res.json();
        state.ports = data;

        const originSelect = document.getElementById('search-origin');
        const destSelect = document.getElementById('search-dest');
        const modalOrigin = document.getElementById('modal-origin');
        const modalDest = document.getElementById('modal-dest');
        const modalCarrier = document.getElementById('modal-carrier');
        const carrierFilter = document.getElementById('shipment-carrier-filter');

        if (originSelect) {
            originSelect.innerHTML = data.origin_ports.map(p => `<option value="${p}">${p}</option>`).join('');
            originSelect.value = "Nhava Sheva";
            updateDestinationDropdown("Nhava Sheva");
        }

        if (modalOrigin) {
            modalOrigin.innerHTML = data.origin_ports.map(p => `<option value="${p}">${p}</option>`).join('');
            modalOrigin.value = "Nhava Sheva";
            updateModalDestinationDropdown("Nhava Sheva");
        }
        if (modalCarrier) modalCarrier.innerHTML = data.carriers.map(c => `<option value="${c}">${c}</option>`).join('');

        if (carrierFilter) {
            carrierFilter.innerHTML = `<option value="all">All Liner Carriers</option>` + 
                data.carriers.map(c => `<option value="${c}">${c}</option>`).join('');
        }

        // Trigger default search on first load
        searchRates();
    } catch (e) {
        console.error('Error loading ports:', e);
    }
}

function updateDestinationDropdown(selectedOrigin) {
    const destSelect = document.getElementById('search-dest');
    if (!destSelect || !state.ports) return;

    const routesMap = state.ports.routes_by_origin || {};
    const validDests = routesMap[selectedOrigin] || state.ports.destination_ports;

    destSelect.innerHTML = validDests.map(p => `<option value="${p}">${p}</option>`).join('');
    destSelect.value = validDests[0] || '';
}

function updateModalDestinationDropdown(selectedOrigin) {
    const modalDest = document.getElementById('modal-dest');
    if (!modalDest || !state.ports) return;

    const routesMap = state.ports.routes_by_origin || {};
    const validDests = routesMap[selectedOrigin] || state.ports.destination_ports;

    modalDest.innerHTML = validDests.map(p => `<option value="${p}">${p}</option>`).join('');
    modalDest.value = validDests[0] || '';
}

async function searchRates() {
    const origin = document.getElementById('search-origin')?.value;
    const dest = document.getElementById('search-dest')?.value;
    const containerType = document.querySelector('input[name="search-container"]:checked')?.value || '20ft';
    const sortBy = document.getElementById('search-sort')?.value || 'price';

    if (!origin || !dest) {
        showToast('Please select both Origin and Destination ports', 'warning');
        return;
    }

    const container = document.getElementById('rates-results-container');
    container.innerHTML = `<div class="p-8 text-center text-slate-400"><i class="fa-solid fa-spinner fa-spin text-2xl text-sky-400"></i><p class="mt-2">Finding best ocean rates...</p></div>`;

    try {
        const res = await fetch(`/api/rates/search?origin_port=${encodeURIComponent(origin)}&destination_port=${encodeURIComponent(dest)}&container_type=${containerType}&sort_by=${sortBy}`);
        const data = await res.json();
        state.rateSearchResults = data;
        renderRateResults(data);
    } catch (e) {
        container.innerHTML = `<div class="p-8 text-center text-red-400">Failed to load freight rates.</div>`;
    }
}

function renderRateResults(data) {
    const container = document.getElementById('rates-results-container');
    if (!container) return;

    if (!data.results || data.results.length === 0) {
        container.innerHTML = `
            <div class="glass-panel p-8 rounded-xl text-center">
                <i class="fa-solid fa-anchor text-3xl text-slate-500 mb-3"></i>
                <h4 class="text-lg font-semibold text-slate-300">No Rates Found</h4>
                <p class="text-slate-400 text-sm mt-1">No direct carrier contracts found for ${data.origin_port} to ${data.destination_port} (${data.container_type}).</p>
            </div>
        `;
        return;
    }

    const cheapest = data.cheapest_carrier;
    let html = '';

    // Highlight Banner for Cheapest Option
    if (cheapest) {
        html += `
            <div class="p-5 rounded-2xl bg-gradient-to-r from-emerald-950/40 via-sky-950/40 to-slate-900 border border-emerald-500/40 shadow-lg shadow-emerald-950/20 mb-6">
                <div class="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
                    <div class="flex items-center gap-3">
                        <div class="w-12 h-12 rounded-xl bg-emerald-500/20 border border-emerald-500/40 flex items-center justify-center text-emerald-400 text-xl font-bold">
                            <i class="fa-solid fa-award"></i>
                        </div>
                        <div>
                            <div class="flex items-center gap-2">
                                <span class="px-2.5 py-0.5 rounded-full text-xs font-bold tracking-wide uppercase bg-emerald-500 text-slate-950">
                                    ★ OPTIMAL TARIFF RECOMMENDATION
                                </span>
                                <span class="text-xs text-emerald-400/90 font-mono">Master Contract Rate</span>
                            </div>
                            <h3 class="text-xl font-bold text-white mt-1">${cheapest.carrier}</h3>
                            <p class="text-xs text-slate-300">
                                Lane: <span class="font-medium text-slate-100">${cheapest.origin_port}</span> → <span class="font-medium text-slate-100">${cheapest.destination_port}</span> 
                                • Transit Schedule: <span class="font-medium text-amber-300">${cheapest.transit_days} days</span>
                            </p>
                        </div>
                    </div>
                    <div class="flex items-center gap-6">
                        <div class="text-right">
                            <div class="text-2xl font-extrabold text-emerald-400">$${cheapest.rate_usd.toLocaleString()} <span class="text-xs text-slate-400 font-normal">USD</span></div>
                            <div class="text-xs text-slate-400 font-mono">₹${cheapest.rate_inr.toLocaleString()} INR</div>
                            ${data.max_savings_usd > 0 ? `<div class="text-xs text-emerald-300 font-semibold mt-0.5">Saves $${data.max_savings_usd.toLocaleString()} vs highest carrier tariff</div>` : ''}
                        </div>
                        <button onclick="prefillShipmentModal('${cheapest.carrier}', '${cheapest.origin_port}', '${cheapest.destination_port}', '${cheapest.container_type}')" 
                                class="px-4 py-2.5 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold text-sm transition shadow-md shadow-emerald-500/20 flex items-center gap-2">
                            <i class="fa-solid fa-plus-circle"></i> Procure & Track
                        </button>
                    </div>
                </div>
            </div>
        `;
    }

    // Rate Comparison Table
    html += `
        <div class="glass-panel rounded-2xl overflow-hidden border border-slate-800">
            <div class="px-5 py-4 border-b border-slate-800 flex justify-between items-center">
                <h4 class="font-semibold text-slate-200 text-sm flex items-center gap-2">
                    <i class="fa-solid fa-ship text-sky-400"></i> Contracted Liner Carrier Benchmark (${data.results_count})
                </h4>
                <div class="text-xs text-slate-400">
                    Maritime Lane: <span class="text-sky-300">${data.origin_port} → ${data.destination_port}</span> | Equipment: <span class="text-sky-300">${data.container_type}</span>
                </div>
            </div>
            <div class="overflow-x-auto">
                <table class="w-full text-left text-sm">
                    <thead class="bg-slate-900/80 text-xs uppercase text-slate-400 font-medium border-b border-slate-800">
                        <tr>
                            <th class="py-3 px-4">Liner Carrier</th>
                            <th class="py-3 px-4">Transit Time</th>
                            <th class="py-3 px-4">Contract Tariff (USD)</th>
                            <th class="py-3 px-4">Contract Tariff (INR)</th>
                            <th class="py-3 px-4">Margin Advantage</th>
                            <th class="py-3 px-4 text-center">Status</th>
                            <th class="py-3 px-4 text-right">Action</th>
                        </tr>
                    </thead>
                    <tbody class="divide-y divide-slate-800/60">
    `;

    data.results.forEach(r => {
        const isCheapest = r.is_cheapest;
        html += `
            <tr class="hover:bg-slate-800/40 transition ${isCheapest ? 'bg-emerald-950/20' : ''}">
                <td class="py-3.5 px-4 font-semibold ${isCheapest ? 'text-emerald-300' : 'text-slate-200'}">
                    ${r.carrier}
                    ${r.source === 'email_update' ? '<span class="ml-2 text-3xs px-1.5 py-0.5 rounded bg-sky-900/60 text-sky-300 border border-sky-700/60">Email Updated</span>' : ''}
                </td>
                <td class="py-3.5 px-4 text-slate-300">
                    <span class="inline-flex items-center gap-1.5">
                        <i class="fa-regular fa-clock text-xs text-amber-400/80"></i>
                        <span class="font-medium">${r.transit_days} days</span>
                    </span>
                </td>
                <td class="py-3.5 px-4 font-mono font-bold ${isCheapest ? 'text-emerald-400 text-base' : 'text-slate-200'}">
                    $${r.rate_usd.toLocaleString()}
                </td>
                <td class="py-3.5 px-4 font-mono text-slate-400 text-xs">
                    ₹${r.rate_inr.toLocaleString()}
                </td>
                <td class="py-3.5 px-4 font-mono text-xs">
                    ${r.potential_savings_usd > 0 ? `<span class="text-emerald-400 font-semibold">+$${r.potential_savings_usd.toLocaleString()}</span>` : '<span class="text-slate-500">—</span>'}
                </td>
                <td class="py-3.5 px-4 text-center">
                    ${isCheapest ? `
                        <span class="px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-500/20 text-emerald-300 border border-emerald-500/40">
                            Cheapest
                        </span>
                    ` : `
                        <span class="px-2 py-0.5 rounded-full text-xs text-slate-400 bg-slate-800">Standard</span>
                    `}
                </td>
                <td class="py-3.5 px-4 text-right">
                    <button onclick="prefillShipmentModal('${r.carrier}', '${r.origin_port}', '${r.destination_port}', '${r.container_type}')" 
                            class="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-sky-600 hover:text-white text-xs text-sky-400 border border-slate-700 hover:border-sky-500 transition">
                        Select
                    </button>
                </td>
            </tr>
        `;
    });

    html += `
                    </tbody>
                </table>
            </div>
        </div>
    `;

    container.innerHTML = html;
}


// ----------------------------------------------------------------------------
// MODULE 2: SHIPMENT TRACKER
// ----------------------------------------------------------------------------

async function loadShipments() {
    const status = state.shipmentFilter.status;
    const carrier = state.shipmentFilter.carrier;
    const search = state.shipmentFilter.search;

    const tableBody = document.getElementById('shipments-table-body');
    if (!tableBody) return;

    try {
        let url = `/api/shipments?`;
        if (status && status !== 'all') url += `status_filter=${encodeURIComponent(status)}&`;
        if (carrier && carrier !== 'all') url += `carrier_filter=${encodeURIComponent(carrier)}&`;
        if (search) url += `search=${encodeURIComponent(search)}&`;

        const res = await fetch(url);
        const data = await res.json();
        state.shipments = data.shipments;
        renderShipmentsTable(data.shipments);
    } catch (e) {
        console.error('Error loading shipments:', e);
    }
}

function renderShipmentsTable(shipments) {
    const tableBody = document.getElementById('shipments-table-body');
    const countBadge = document.getElementById('shipment-count-badge');
    if (countBadge) countBadge.innerText = `${shipments.length} Shipments`;
    if (!tableBody) return;

    if (shipments.length === 0) {
        tableBody.innerHTML = `
            <tr>
                <td colspan="8" class="text-center py-10 text-slate-400">
                    <i class="fa-solid fa-box-open text-3xl mb-2 text-slate-600"></i>
                    <p>No shipments match the current filters.</p>
                </td>
            </tr>
        `;
        return;
    }

    tableBody.innerHTML = shipments.map(s => {
        const status = s.computed_status;
        let badgeClass = 'badge-intransit';
        let icon = 'fa-solid fa-route';
        if (status === 'Delivered') {
            badgeClass = 'badge-delivered';
            icon = 'fa-solid fa-circle-check';
        } else if (status === 'Delayed') {
            badgeClass = 'badge-delayed';
            icon = 'fa-solid fa-triangle-exclamation';
        }

        // Invoice status badge
        let invoiceBadge = '';
        if (s.invoice_status === 'OVERCHARGED') {
            invoiceBadge = `<span class="badge-overcharged px-2 py-0.5 rounded text-xs font-semibold cursor-pointer" onclick="openInvoiceCheckFor('${s.shipment_id}', ${s.invoice_amount_usd})">Overcharged +$${s.discrepancy_usd}</span>`;
        } else if (s.invoice_status === 'CORRECT') {
            invoiceBadge = `<span class="badge-correct px-2 py-0.5 rounded text-xs font-semibold cursor-pointer" onclick="openInvoiceCheckFor('${s.shipment_id}', ${s.invoice_amount_usd})">Correct ($${s.invoice_amount_usd})</span>`;
        } else if (s.invoice_status === 'UNDERCHARGED') {
            invoiceBadge = `<span class="bg-blue-900/40 text-blue-300 border border-blue-700/60 px-2 py-0.5 rounded text-xs font-semibold cursor-pointer" onclick="openInvoiceCheckFor('${s.shipment_id}', ${s.invoice_amount_usd})">Discount -$${Math.abs(s.discrepancy_usd)}</span>`;
        } else {
            invoiceBadge = `<span class="text-slate-500 text-xs italic">Unbilled</span>`;
        }

        return `
            <tr class="hover:bg-slate-800/40 transition border-b border-slate-800/60">
                <td class="py-3.5 px-4 font-mono font-bold text-sky-400">
                    ${s.shipment_id}
                </td>
                <td class="py-3.5 px-4 font-medium text-slate-200">
                    ${s.carrier}
                    <div class="text-xs text-slate-400 font-mono">${s.container_type}</div>
                </td>
                <td class="py-3.5 px-4 text-slate-300 text-xs">
                    <span class="font-medium text-slate-100">${s.origin_port}</span>
                    <i class="fa-solid fa-arrow-right mx-1 text-slate-500 text-3xs"></i>
                    <span class="font-medium text-slate-100">${s.destination_port}</span>
                </td>
                <td class="py-3.5 px-4 text-xs font-mono text-slate-400">
                    ${s.departure_date}
                </td>
                <td class="py-3.5 px-4 text-xs font-mono ${status === 'Delayed' ? 'text-red-400 font-semibold' : 'text-slate-300'}">
                    ${s.expected_arrival}
                    ${s.delivered_date ? `<div class="text-emerald-400 font-sans">Delivered: ${s.delivered_date}</div>` : ''}
                </td>
                <td class="py-3.5 px-4">
                    <span class="px-2.5 py-1 rounded-full text-xs font-semibold inline-flex items-center gap-1.5 ${badgeClass}">
                        <i class="${icon}"></i> ${status}
                    </span>
                    ${s.status_notes ? `<div class="text-3xs text-slate-400 mt-0.5 truncate max-w-xs" title="${s.status_notes}">${s.status_notes}</div>` : ''}
                </td>
                <td class="py-3.5 px-4">
                    ${invoiceBadge}
                </td>
                <td class="py-3.5 px-4 text-right">
                    <div class="flex items-center justify-end gap-1.5">
                        ${status !== 'Delivered' ? `
                            <button onclick="markDelivered('${s.shipment_id}')" class="p-1.5 rounded bg-emerald-950/60 hover:bg-emerald-900 text-emerald-400 text-xs border border-emerald-800 transition" title="Mark as Delivered">
                                <i class="fa-solid fa-check"></i>
                            </button>
                        ` : ''}
                        <button onclick="openInvoiceCheckFor('${s.shipment_id}', ${s.invoice_amount_usd || (s.contracted_rate_usd || 2000)})" class="p-1.5 rounded bg-slate-800 hover:bg-slate-700 text-sky-400 text-xs border border-slate-700 transition" title="Verify Invoice">
                            <i class="fa-solid fa-receipt"></i>
                        </button>
                    </div>
                </td>
            </tr>
        `;
    }).join('');
}

async function markDelivered(shipmentId) {
    try {
        const res = await fetch(`/api/shipments/${shipmentId}/deliver`, { method: 'POST' });
        const data = await res.json();
        showToast(data.message, 'success');
        await loadShipments();
        await loadShipmentStats();
    } catch (e) {
        showToast('Failed to mark delivered', 'error');
    }
}

function prefillShipmentModal(carrier, origin, dest, containerType) {
    document.getElementById('modal-shipment-id').value = `SHP${Math.floor(1020 + Math.random() * 900)}`;
    document.getElementById('modal-carrier').value = carrier;
    document.getElementById('modal-origin').value = origin;
    document.getElementById('modal-dest').value = dest;
    document.getElementById('modal-container').value = containerType;
    
    const today = new Date().toISOString().split('T')[0];
    const expected = new Date(Date.now() + 28 * 24 * 60 * 60 * 1000).toISOString().split('T')[0];
    document.getElementById('modal-departure').value = today;
    document.getElementById('modal-expected').value = expected;

    openModal('add-shipment-modal');
}

async function submitAddShipment(e) {
    e.preventDefault();
    const payload = {
        shipment_id: document.getElementById('modal-shipment-id').value.trim(),
        carrier: document.getElementById('modal-carrier').value,
        origin_port: document.getElementById('modal-origin').value,
        destination_port: document.getElementById('modal-dest').value,
        container_type: document.getElementById('modal-container').value,
        departure_date: document.getElementById('modal-departure').value,
        expected_arrival: document.getElementById('modal-expected').value,
        invoice_amount_usd: parseFloat(document.getElementById('modal-invoice').value) || null
    };

    try {
        const res = await fetch('/api/shipments', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const data = await res.json();
        if (res.ok) {
            showToast(data.message, 'success');
            closeModal('add-shipment-modal');
            await loadShipments();
            await loadShipmentStats();
            switchTab('shipments');
        } else {
            showToast(data.detail || 'Failed to add shipment', 'error');
        }
    } catch (err) {
        showToast('Submission error', 'error');
    }
}

function exportShipmentsCSV() {
    window.location.href = '/api/shipments/export';
}


// ----------------------------------------------------------------------------
// MODULE 3: INVOICE CHECKER
// ----------------------------------------------------------------------------

function openInvoiceCheckFor(shipmentId, amount) {
    switchTab('invoices');
    const select = document.getElementById('invoice-shipment-select');
    if (select) {
        select.value = shipmentId;
    }
    const amtInput = document.getElementById('invoice-amount-input');
    if (amtInput && amount) {
        amtInput.value = amount;
    }
    checkSingleInvoice();
}

async function populateInvoiceShipmentDropdown() {
    const select = document.getElementById('invoice-shipment-select');
    if (!select || !state.shipments.length) return;

    select.innerHTML = `<option value="">Select Shipment...</option>` +
        state.shipments.map(s => `
            <option value="${s.shipment_id}" data-contracted="${s.contracted_rate_usd || ''}">
                ${s.shipment_id} - ${s.carrier} (${s.origin_port} → ${s.destination_port}, ${s.container_type})
            </option>
        `).join('');
}

async function checkSingleInvoice() {
    const shipmentId = document.getElementById('invoice-shipment-select')?.value;
    const amount = parseFloat(document.getElementById('invoice-amount-input')?.value);

    if (!shipmentId || isNaN(amount)) {
        showToast('Please select a shipment and enter an invoiced amount', 'warning');
        return;
    }

    const resultBox = document.getElementById('invoice-result-card');
    resultBox.classList.remove('hidden');
    resultBox.innerHTML = `<div class="p-6 text-center text-slate-400"><i class="fa-solid fa-spinner fa-spin text-xl text-sky-400"></i> Verifying against contract rate...</div>`;

    try {
        const res = await fetch('/api/invoice/check', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ shipment_id: shipmentId, invoice_amount_usd: amount })
        });
        const data = await res.json();
        if (!res.ok) {
            resultBox.innerHTML = `<div class="p-6 rounded-xl bg-red-950/40 border border-red-800 text-red-300">${data.detail}</div>`;
            return;
        }

        renderInvoiceVerdict(data);
        await runInvoiceAudit();
    } catch (e) {
        resultBox.innerHTML = `<div class="p-6 text-red-400">Network error checking invoice</div>`;
    }
}

function renderInvoiceVerdict(data) {
    const resultBox = document.getElementById('invoice-result-card');
    if (!resultBox) return;

    let bannerBg = 'bg-emerald-950/40 border-emerald-500/50 text-emerald-300';
    let icon = 'fa-solid fa-circle-check text-emerald-400';
    let headline = `Reconciliation Cleared: Matches Master Contract Tariff ($0.00 Variance)`;
    
    if (data.verdict === 'OVERCHARGED') {
        bannerBg = 'bg-rose-950/50 border-rose-500/60 text-rose-300';
        icon = 'fa-solid fa-triangle-exclamation text-rose-400 animate-pulse';
        headline = `Billing Discrepancy Flagged: Overcharged by $${data.discrepancy_usd.toLocaleString()} USD (₹${data.discrepancy_inr.toLocaleString()} INR)`;
    } else if (data.verdict === 'UNDERCHARGED') {
        bannerBg = 'bg-blue-950/50 border-blue-500/60 text-blue-300';
        icon = 'fa-solid fa-arrow-trend-down text-blue-400';
        headline = `Favorable Variance / Volume Credit: -$${Math.abs(data.discrepancy_usd).toLocaleString()} USD`;
    }

    resultBox.innerHTML = `
        <div class="p-6 rounded-2xl border ${bannerBg} shadow-lg">
            <div class="flex items-center gap-3">
                <i class="${icon} text-2xl"></i>
                <div>
                    <span class="text-xs font-bold uppercase tracking-wider px-2 py-0.5 rounded bg-black/40">Master Contract Audit</span>
                    <h3 class="text-xl font-bold text-white mt-0.5">${headline}</h3>
                </div>
            </div>

            <div class="grid grid-cols-2 sm:grid-cols-4 gap-4 mt-6 pt-5 border-t border-slate-700/50">
                <div class="bg-slate-900/60 p-3 rounded-xl border border-slate-800">
                    <div class="text-xs text-slate-400">Master Contract Tariff</div>
                    <div class="text-lg font-bold text-slate-100 font-mono mt-1">$${data.contracted_rate_usd.toLocaleString()}</div>
                    <div class="text-3xs text-slate-400 font-mono">₹${data.contracted_rate_inr.toLocaleString()}</div>
                </div>
                <div class="bg-slate-900/60 p-3 rounded-xl border border-slate-800">
                    <div class="text-xs text-slate-400">Carrier Billed Total</div>
                    <div class="text-lg font-bold text-slate-100 font-mono mt-1">$${data.invoiced_amount_usd.toLocaleString()}</div>
                    <div class="text-3xs text-slate-400 font-mono">₹${data.invoiced_amount_inr.toLocaleString()}</div>
                </div>
                <div class="bg-slate-900/60 p-3 rounded-xl border border-slate-800">
                    <div class="text-xs text-slate-400">Identified Discrepancy</div>
                    <div class="text-lg font-bold font-mono mt-1 ${data.discrepancy_usd > 0 ? 'text-rose-400' : 'text-emerald-400'}">
                        ${data.discrepancy_usd > 0 ? '+' : ''}$${data.discrepancy_usd.toLocaleString()}
                    </div>
                    <div class="text-3xs text-slate-400 font-mono">${data.discrepancy_usd > 0 ? '+' : ''}₹${data.discrepancy_inr.toLocaleString()}</div>
                </div>
                <div class="bg-slate-900/60 p-3 rounded-xl border border-slate-800">
                    <div class="text-xs text-slate-400">Contract Variance %</div>
                    <div class="text-lg font-bold font-mono mt-1 ${data.percentage_difference > 0 ? 'text-rose-400' : 'text-emerald-400'}">
                        ${data.percentage_difference > 0 ? '+' : ''}${data.percentage_difference}%
                    </div>
                    <div class="text-3xs text-slate-400 font-medium">Liner: ${data.carrier}</div>
                </div>
            </div>
        </div>
    `;
}

async function runInvoiceAudit() {
    const tableBody = document.getElementById('audit-table-body');
    const overchargeTotalEl = document.getElementById('total-overcharge-badge');
    if (!tableBody) return;

    try {
        const res = await fetch('/api/invoice/audit-all');
        const data = await res.json();

        if (overchargeTotalEl) {
            overchargeTotalEl.innerHTML = `
                <span class="text-rose-400 font-bold">$${data.total_overcharge_usd.toLocaleString()} USD</span> 
                <span class="text-slate-400 text-xs font-normal">(${data.overcharged_count} audited discrepancies)</span>
            `;
        }

        tableBody.innerHTML = data.items.map(item => {
            const isOver = item.status === 'OVERCHARGED';
            const isUnder = item.status === 'UNDERCHARGED';
            const isOk = item.status === 'CORRECT';

            let badge = `<span class="badge-correct px-2 py-0.5 rounded text-xs font-semibold">Cleared (Match)</span>`;
            if (isOver) {
                badge = `<span class="badge-overcharged px-2 py-0.5 rounded text-xs font-semibold">Overcharge +$${item.discrepancy_usd}</span>`;
            } else if (isUnder) {
                badge = `<span class="bg-blue-900/40 text-blue-300 border border-blue-700 px-2 py-0.5 rounded text-xs font-semibold">Volume Rebate -$${Math.abs(item.discrepancy_usd)}</span>`;
            }

            return `
                <tr class="hover:bg-slate-800/40 transition border-b border-slate-800/60 ${isOver ? 'bg-rose-950/15' : ''}">
                    <td class="py-3 px-4 font-mono font-bold text-sky-400">${item.shipment_id}</td>
                    <td class="py-3 px-4 text-slate-200 text-xs font-medium">${item.carrier}</td>
                    <td class="py-3 px-4 text-slate-300 text-xs">${item.route} <span class="text-slate-500 font-mono">(${item.container_type})</span></td>
                    <td class="py-3 px-4 font-mono text-slate-300 text-xs">$${item.contracted_rate_usd.toLocaleString()}</td>
                    <td class="py-3 px-4 font-mono text-slate-100 text-xs font-semibold">$${item.invoiced_amount_usd.toLocaleString()}</td>
                    <td class="py-3 px-4 font-mono text-xs ${isOver ? 'text-rose-400 font-bold' : (isUnder ? 'text-blue-400' : 'text-emerald-400')}">
                        ${item.discrepancy_usd > 0 ? '+' : ''}$${item.discrepancy_usd.toLocaleString()}
                    </td>
                    <td class="py-3 px-4">${badge}</td>
                </tr>
            `;
        }).join('');
    } catch (e) {
        console.error('Audit failed:', e);
    }
}


// ----------------------------------------------------------------------------
// CARRIER DISPATCH INGESTION
// ----------------------------------------------------------------------------

async function loadInbox() {
    const listEl = document.getElementById('inbox-list-container');
    if (!listEl) return;

    try {
        const res = await fetch('/api/emails/inbox');
        const data = await res.json();
        state.inboxEmails = data.emails;

        listEl.innerHTML = data.emails.map(email => {
            let badge = '';
            let borderGlow = 'border-slate-800';
            if (email.type === 'rate_update') {
                badge = `<span class="px-2 py-0.5 rounded text-xs font-bold uppercase bg-sky-900/60 text-sky-300 border border-sky-700">Tariff Revision</span>`;
                borderGlow = 'border-sky-800/60 hover:border-sky-500/60';
            } else if (email.type === 'shipment_update') {
                badge = `<span class="px-2 py-0.5 rounded text-xs font-bold uppercase bg-amber-900/60 text-amber-300 border border-amber-700">Voyage Advisory</span>`;
                borderGlow = 'border-amber-800/60 hover:border-amber-500/60';
            } else {
                badge = `<span class="px-2 py-0.5 rounded text-xs font-semibold uppercase bg-slate-800 text-slate-400 border border-slate-700">Non-Operational</span>`;
            }

            return `
                <div class="glass-panel p-4 rounded-xl border ${borderGlow} transition cursor-pointer hover:bg-slate-800/50" onclick="previewEmailModal(${email.email_index})">
                    <div class="flex items-start justify-between gap-3">
                        <div class="flex items-center gap-2">
                            <span class="w-6 h-6 rounded-full bg-slate-800 text-slate-300 text-xs font-bold flex items-center justify-center font-mono">
                                ${email.email_index}
                            </span>
                            <span class="text-xs font-medium text-slate-300 truncate max-w-xs">${email.headers.From || 'Unknown'}</span>
                        </div>
                        <div class="flex items-center gap-2">
                            ${badge}
                            <span class="text-3xs font-mono text-slate-400">${email.headers.Date || ''}</span>
                        </div>
                    </div>
                    <h5 class="text-sm font-semibold text-white mt-2">${email.headers.Subject || 'No Subject'}</h5>
                    <p class="text-xs text-slate-400 mt-1 line-clamp-2">${email.body}</p>
                    <div class="mt-2.5 pt-2 border-t border-slate-800/80 flex items-center justify-between text-3xs text-slate-400">
                        <span><i class="fa-solid fa-bolt text-sky-400 mr-1"></i> ${email.reason}</span>
                        <span class="text-sky-400 hover:underline">Inspect advisory parameters →</span>
                    </div>
                </div>
            `;
        }).join('');
    } catch (e) {
        console.error('Error loading inbox:', e);
    }
}

async function parseAllEmails() {
    const btn = document.getElementById('parse-all-btn');
    const originalText = btn.innerHTML;
    btn.innerHTML = `<i class="fa-solid fa-spinner fa-spin mr-2"></i> Ingesting carrier feeds...`;
    btn.disabled = true;

    try {
        const res = await fetch('/api/emails/parse-all?apply_to_db=true', { method: 'POST' });
        const data = await res.json();
        state.parsingResults = data;

        showToast(`Ingested ${data.total_emails_parsed} carrier advisories. Synchronized ${data.rates_updated_count} tariff revisions and ${data.shipments_updated_count} voyage milestones.`, 'success');

        renderParsingLog(data);
        await loadShipments();
        await loadShipmentStats();
        await loadPortDropdowns();
        await runInvoiceAudit();
        if (state.rateSearchResults) searchRates();
    } catch (e) {
        showToast('Carrier feed ingestion failed', 'error');
    } finally {
        btn.innerHTML = originalText;
        btn.disabled = false;
    }
}

function renderParsingLog(data) {
    const logContainer = document.getElementById('parsing-results-container');
    if (!logContainer) return;
    logContainer.classList.remove('hidden');

    let html = `
        <div class="glass-panel p-6 rounded-2xl border border-sky-500/40 shadow-xl mb-6">
            <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-800">
                <div>
                    <h4 class="text-lg font-bold text-white flex items-center gap-2">
                        <i class="fa-solid fa-check-double text-emerald-400"></i> Carrier Dispatch Stream Ingested & Verified
                    </h4>
                    <p class="text-xs text-slate-400 mt-0.5">Autonomous NLP entity extraction synchronized to master operational database.</p>
                </div>
                <div class="flex items-center gap-3">
                    <span class="px-3 py-1 rounded-lg bg-sky-950 text-sky-300 text-xs font-bold border border-sky-800">
                        ${data.rates_updated_count} Tariffs Committed
                    </span>
                    <span class="px-3 py-1 rounded-lg bg-amber-950 text-amber-300 text-xs font-bold border border-amber-800">
                        ${data.shipments_updated_count} Milestones Updated
                    </span>
                    <span class="px-3 py-1 rounded-lg bg-slate-800 text-slate-300 text-xs font-bold border border-slate-700">
                        ${data.skipped_emails_count} Non-Operational Filtered
                    </span>
                </div>
            </div>

            <!-- Rates updated -->
            <div class="mt-5">
                <h5 class="text-xs font-bold uppercase tracking-wider text-sky-400 mb-2">1. Master Contract Tariff Revisions Committed</h5>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-2 text-xs">
                    ${data.applied_rates.map(r => `
                        <div class="p-2.5 rounded-lg bg-slate-900/80 border border-slate-800 flex justify-between items-center">
                            <div>
                                <span class="font-bold text-slate-200">${r.carrier}</span>
                                <span class="text-slate-400 font-mono text-3xs block">${r.route} (${r.container_type})</span>
                            </div>
                            <div class="text-right font-mono">
                                <span class="text-slate-400 line-through mr-1.5">$${r.previous_rate_usd || '—'}</span>
                                <span class="text-emerald-400 font-bold">$${r.new_rate_usd.toLocaleString()}</span>
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>

            <!-- Shipments updated -->
            <div class="mt-5">
                <h5 class="text-xs font-bold uppercase tracking-wider text-amber-400 mb-2">2. Vessel Milestone Advisories Synchronized</h5>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-2 text-xs">
                    ${data.applied_shipments.map(s => `
                        <div class="p-2.5 rounded-lg bg-slate-900/80 border border-slate-800 flex justify-between items-center">
                            <div>
                                <span class="font-bold text-sky-400 font-mono">${s.shipment_id}</span>
                                <span class="text-slate-400 text-3xs block">${s.notes || 'Status changed'}</span>
                            </div>
                            <div class="text-right">
                                <span class="px-2 py-0.5 rounded text-xs font-bold ${s.new_status === 'Delivered' ? 'bg-emerald-950 text-emerald-300' : 'bg-red-950 text-red-300'}">
                                    ${s.new_status}
                                </span>
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>

            <!-- Skipped emails -->
            <div class="mt-5">
                <h5 class="text-xs font-bold uppercase tracking-wider text-slate-400 mb-2">3. Non-Operational Advisories Filtered (Zero Disruption)</h5>
                <div class="space-y-1.5 text-xs">
                    ${data.skipped_emails.map(e => `
                        <div class="p-2 rounded-lg bg-slate-900/50 border border-slate-800/80 flex items-center justify-between text-slate-400">
                            <span class="truncate max-w-md"><strong class="text-slate-300">#${e.email_index}:</strong> ${e.subject}</span>
                            <span class="text-3xs px-2 py-0.5 rounded bg-slate-800 text-slate-400 font-mono">${e.reason}</span>
                        </div>
                    `).join('')}
                </div>
            </div>
        </div>
    `;

    logContainer.innerHTML = html;
}

function previewEmailModal(emailIndex) {
    const email = state.inboxEmails.find(e => e.email_index === emailIndex);
    if (!email) return;

    document.getElementById('email-detail-title').innerText = `Email #${email.email_index}: ${email.headers.Subject || 'No Subject'}`;
    document.getElementById('email-detail-headers').innerHTML = `
        <div class="text-xs text-slate-300 space-y-1 font-mono">
            <div><strong class="text-slate-400">From:</strong> ${email.headers.From}</div>
            <div><strong class="text-slate-400">Date:</strong> ${email.headers.Date}</div>
            <div><strong class="text-slate-400">Type:</strong> <span class="uppercase font-bold text-sky-400">${email.type}</span></div>
            <div><strong class="text-slate-400">Parser Action:</strong> ${email.reason}</div>
        </div>
    `;
    document.getElementById('email-detail-body').innerText = email.body;
    document.getElementById('email-detail-json').innerText = JSON.stringify(email.extracted_data, null, 2);

    openModal('email-detail-modal');
}

async function testCustomEmail() {
    const text = document.getElementById('custom-email-input')?.value;
    if (!text || !text.trim()) {
        showToast('Please enter or paste email text', 'warning');
        return;
    }

    const applyDb = document.getElementById('custom-apply-db')?.checked || false;
    const outputBox = document.getElementById('custom-email-output');
    outputBox.classList.remove('hidden');
    outputBox.innerHTML = `<div class="p-4 text-center text-slate-400"><i class="fa-solid fa-spinner fa-spin text-sky-400"></i> Parsing entities...</div>`;

    try {
        const res = await fetch('/api/emails/parse-single', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email_text: text, apply_to_db: applyDb })
        });
        const data = await res.json();
        const parsed = data.parsed_result;

        let badge = `<span class="px-2 py-0.5 rounded text-xs font-bold uppercase bg-slate-800 text-slate-300">${parsed.type}</span>`;
        if (parsed.type === 'rate_update') badge = `<span class="px-2 py-0.5 rounded text-xs font-bold uppercase bg-sky-900/60 text-sky-300 border border-sky-700">Rate Update</span>`;
        if (parsed.type === 'shipment_update') badge = `<span class="px-2 py-0.5 rounded text-xs font-bold uppercase bg-amber-900/60 text-amber-300 border border-amber-700">Shipment Update</span>`;

        outputBox.innerHTML = `
            <div class="p-4 rounded-xl bg-slate-900 border border-slate-800 text-xs">
                <div class="flex items-center justify-between pb-2 border-b border-slate-800">
                    <div class="flex items-center gap-2">
                        ${badge}
                        <span class="text-slate-300">${parsed.reason}</span>
                    </div>
                    <span class="text-3xs text-emerald-400">${data.applied_to_db ? '✓ Applied to Database' : 'Preview Mode'}</span>
                </div>
                <div class="mt-3">
                    <div class="text-slate-400 font-semibold mb-1">Extracted Entities (JSON):</div>
                    <pre class="bg-black/60 p-3 rounded-lg font-mono text-3xs text-sky-300 overflow-x-auto">${JSON.stringify(parsed.extracted_data, null, 2)}</pre>
                </div>
            </div>
        `;

        if (data.applied_to_db) {
            await loadShipments();
            await loadShipmentStats();
            await loadPortDropdowns();
            showToast('Changes applied to database', 'success');
        }
    } catch (e) {
        outputBox.innerHTML = `<div class="p-4 text-red-400">Parsing failed</div>`;
    }
}


// ----------------------------------------------------------------------------
// BONUS FEATURE: VISUAL DASHBOARD STATS & CHART.JS
// ----------------------------------------------------------------------------

async function loadShipmentStats() {
    try {
        const res = await fetch('/api/shipments/stats');
        const stats = await res.json();

        // Update KPI counter cards
        const totalShipmentsEl = document.getElementById('stat-total-shipments');
        const inTransitEl = document.getElementById('stat-intransit');
        const delayedEl = document.getElementById('stat-delayed');
        const deliveredEl = document.getElementById('stat-delivered');
        const overchargesEl = document.getElementById('stat-overcharges');

        if (totalShipmentsEl) totalShipmentsEl.innerText = stats.total_shipments;
        if (inTransitEl) inTransitEl.innerText = stats.status_distribution['In Transit'] || 0;
        if (delayedEl) delayedEl.innerText = stats.status_distribution['Delayed'] || 0;
        if (deliveredEl) deliveredEl.innerText = stats.status_distribution['Delivered'] || 0;
        if (overchargesEl) overchargesEl.innerText = `$${stats.total_overcharge_usd.toLocaleString()}`;

        // Render Chart.js Donut
        renderStatusChart(stats.status_distribution);
    } catch (e) {
        console.error('Stats error:', e);
    }
}

function renderStatusChart(dist) {
    const ctx = document.getElementById('shipmentStatusChart')?.getContext('2d');
    if (!ctx) return;

    if (state.chartInstance) {
        state.chartInstance.destroy();
    }

    state.chartInstance = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['In Transit', 'Delayed', 'Delivered'],
            datasets: [{
                data: [
                    dist['In Transit'] || 0,
                    dist['Delayed'] || 0,
                    dist['Delivered'] || 0
                ],
                backgroundColor: [
                    '#f59e0b', // Amber
                    '#ef4444', // Red
                    '#10b981'  // Emerald
                ],
                borderWidth: 2,
                borderColor: '#0b1329'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        color: '#94a3b8',
                        font: { family: "'Plus Jakarta Sans', sans-serif", size: 12 },
                        padding: 15
                    }
                }
            },
            cutout: '72%'
        }
    });
}


// ----------------------------------------------------------------------------
// EVENT LISTENERS & MODAL UTILITIES
// ----------------------------------------------------------------------------

function setupEventListeners() {
    // Search form
    document.getElementById('rates-search-btn')?.addEventListener('click', searchRates);
    document.getElementById('search-sort')?.addEventListener('change', searchRates);
    document.querySelectorAll('input[name="search-container"]').forEach(r => r.addEventListener('change', searchRates));
    document.getElementById('search-origin')?.addEventListener('change', (e) => {
        updateDestinationDropdown(e.target.value);
        searchRates();
    });
    document.getElementById('search-dest')?.addEventListener('change', searchRates);
    document.getElementById('modal-origin')?.addEventListener('change', (e) => {
        updateModalDestinationDropdown(e.target.value);
    });

    // Shipment filters
    document.getElementById('shipment-status-filter')?.addEventListener('change', (e) => {
        state.shipmentFilter.status = e.target.value;
        loadShipments();
    });
    document.getElementById('shipment-carrier-filter')?.addEventListener('change', (e) => {
        state.shipmentFilter.carrier = e.target.value;
        loadShipments();
    });
    document.getElementById('shipment-search-input')?.addEventListener('input', (e) => {
        state.shipmentFilter.search = e.target.value;
        loadShipments();
    });

    // Invoice dropdown populate on open
    document.getElementById('invoice-shipment-select')?.addEventListener('change', (e) => {
        const selected = state.shipments.find(s => s.shipment_id === e.target.value);
        if (selected && selected.invoice_amount_usd) {
            document.getElementById('invoice-amount-input').value = selected.invoice_amount_usd;
        } else if (selected && selected.contracted_rate_usd) {
            document.getElementById('invoice-amount-input').value = selected.contracted_rate_usd;
        }
    });

    document.getElementById('verify-invoice-btn')?.addEventListener('click', checkSingleInvoice);
    document.getElementById('parse-all-btn')?.addEventListener('click', parseAllEmails);
    document.getElementById('test-custom-email-btn')?.addEventListener('click', testCustomEmail);
    document.getElementById('add-shipment-form')?.addEventListener('submit', submitAddShipment);

    // Login Form Submit
    document.getElementById('login-form')?.addEventListener('submit', (e) => {
        e.preventDefault();
        const username = document.getElementById('login-username').value.trim();
        const password = document.getElementById('login-password').value;
        loginAs(username, password);
    });

    // Register Form Submit (Store Credentials)
    document.getElementById('register-form')?.addEventListener('submit', (e) => {
        e.preventDefault();
        const fullName = document.getElementById('reg-fullname').value.trim();
        const username = document.getElementById('reg-username').value.trim();
        const password = document.getElementById('reg-password').value;
        const role = document.getElementById('reg-role').value;
        registerAccount(fullName, username, password, role);
    });
}

function openModal(id) {
    if (id === 'add-shipment-modal' && !state.currentUser) {
        showToast('Please sign in first to add shipments', 'warning');
        logout();
        return;
    }
    const el = document.getElementById(id);
    if (el) el.classList.remove('hidden');
    if (id === 'add-shipment-modal') {
        populateInvoiceShipmentDropdown();
    }
}

function closeModal(id) {
    const el = document.getElementById(id);
    if (el) el.classList.add('hidden');
}

function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    const colors = {
        success: 'bg-emerald-950/90 border-emerald-500 text-emerald-200',
        error: 'bg-rose-950/90 border-rose-500 text-rose-200',
        warning: 'bg-amber-950/90 border-amber-500 text-amber-200',
        info: 'bg-sky-950/90 border-sky-500 text-sky-200'
    };

    toast.className = `fixed bottom-6 right-6 z-50 px-4 py-3 rounded-xl border shadow-2xl backdrop-blur-md text-sm transition-all transform duration-300 translate-y-2 opacity-0 flex items-center gap-3 ${colors[type] || colors.info}`;
    toast.innerHTML = `
        <i class="fa-solid ${type === 'success' ? 'fa-circle-check text-emerald-400' : type === 'error' ? 'fa-circle-xmark text-rose-400' : 'fa-circle-info text-sky-400'}"></i>
        <span>${message}</span>
    `;

    document.body.appendChild(toast);
    requestAnimationFrame(() => {
        toast.classList.remove('translate-y-2', 'opacity-0');
    });

    setTimeout(() => {
        toast.classList.add('opacity-0', 'translate-y-2');
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}
