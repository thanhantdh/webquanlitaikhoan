/**
 * app.js — Account Manager Frontend Logic
 * Features: page navigation, file upload, real-time timers, Telegram (direct API),
 * notifications log, settings, and localStorage persistence.
 */

// ===== State =====
let accounts = [];
let alertCount = 0;
let notifications = [];
let pendingFileData = [];  // Parsed accounts from uploaded file
let timerId = null;

// Settings (stored in localStorage)
let settings = {
    botToken: '',
    chatId: '',
    defaultHours: 8
};

// ===== DOM References =====
const form          = document.getElementById('addAccountForm');
const nameInput     = document.getElementById('accountName');
const hoursInput    = document.getElementById('maxHours');
const tbody         = document.getElementById('accountsBody');
const tbody2        = document.getElementById('accountsBody2');
const emptyState    = document.getElementById('emptyState');
const emptyState2   = document.getElementById('emptyState2');
const toastContainer= document.getElementById('toastContainer');
const elTotal       = document.getElementById('totalAccounts');
const elRunning     = document.getElementById('runningAccounts');
const elStopped     = document.getElementById('stoppedAccounts');
const elAlerts      = document.getElementById('alertCount');
const elBadge       = document.getElementById('accountBadge');
const elTime        = document.getElementById('currentTime');
const statusDot     = document.getElementById('statusDot');
const uploadZone    = document.getElementById('uploadZone');
const fileInput     = document.getElementById('fileInput');
const uploadPreview = document.getElementById('uploadPreview');
const navNotifBadge = document.getElementById('navNotifBadge');

// ===== Page Navigation =====
function switchPage(pageId, navEl) {
    // Deactivate all pages
    document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
    document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
    // Activate target
    const page = document.getElementById('page-' + pageId);
    if (page) page.classList.add('active');
    if (navEl) navEl.classList.add('active');
    // Close mobile sidebar
    document.getElementById('sidebar').classList.remove('open');
    document.getElementById('sidebarOverlay').classList.remove('active');
    // Re-render tables for Accounts page
    if (pageId === 'accounts') renderTable();
    if (pageId === 'notifications') renderNotifications();
    if (pageId === 'settings') loadSettingsUI();
}

function toggleSidebar() {
    document.getElementById('sidebar').classList.toggle('open');
    document.getElementById('sidebarOverlay').classList.toggle('active');
}

// ===== Clock =====
function updateClock() {
    const now = new Date();
    elTime.textContent = now.toLocaleString('vi-VN', {
        weekday: 'long', year: 'numeric', month: '2-digit',
        day: '2-digit', hour: '2-digit', minute: '2-digit', second: '2-digit'
    });
}
updateClock();
setInterval(updateClock, 1000);

// ===== Toast Notifications =====
function showToast(type, title, message) {
    const icons = {
        success: '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>',
        error:   '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>',
        warning: '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>',
        info:    '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>'
    };
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `
        <div class="toast-icon ${type}">${icons[type]}</div>
        <div class="toast-body">
            <div class="toast-title">${title}</div>
            <div class="toast-message">${message}</div>
        </div>
        <button class="toast-close" onclick="this.parentElement.remove()">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
        </button>`;
    toastContainer.appendChild(toast);
    setTimeout(() => {
        toast.style.animation = 'fadeOut .35s ease forwards';
        setTimeout(() => toast.remove(), 350);
    }, 4000);
}

// ===== Helpers =====
function formatTime(totalSeconds) {
    const h = Math.floor(totalSeconds / 3600);
    const m = Math.floor((totalSeconds % 3600) / 60);
    const s = totalSeconds % 60;
    return `${String(h).padStart(2,'0')}:${String(m).padStart(2,'0')}:${String(s).padStart(2,'0')}`;
}
function escapeHtml(str) {
    const d = document.createElement('div');
    d.textContent = str;
    return d.innerHTML;
}
function timeAgo(dateStr) {
    const diff = Math.floor((Date.now() - new Date(dateStr).getTime()) / 1000);
    if (diff < 60) return `${diff}s trước`;
    if (diff < 3600) return `${Math.floor(diff/60)} phút trước`;
    if (diff < 86400) return `${Math.floor(diff/3600)} giờ trước`;
    return `${Math.floor(diff/86400)} ngày trước`;
}

// ===== Update Stats =====
function updateStats() {
    const total   = accounts.length;
    const running = accounts.filter(a => a.status === 'running').length;
    const stopped = accounts.filter(a => a.status !== 'running').length;
    elTotal.textContent   = total;
    elRunning.textContent = running;
    elStopped.textContent = stopped;
    elAlerts.textContent  = alertCount;
    elBadge.textContent   = `${total} tài khoản`;
    emptyState.classList.toggle('hidden', total > 0);
    if (emptyState2) emptyState2.classList.toggle('hidden', total > 0);
    // Nav notification badge
    if (notifications.length > 0) {
        navNotifBadge.style.display = 'inline';
        navNotifBadge.textContent = notifications.length;
    } else {
        navNotifBadge.style.display = 'none';
    }
}

// ===== Build table row HTML =====
function buildRowHtml(acc, idx) {
    const maxSec = acc.maxHours * 3600;
    const pct = maxSec > 0 ? Math.min((acc.elapsed / maxSec) * 100, 100) : 0;
    const isWarning = pct >= 80;
    let statusClass, statusText;
    if (acc.status === 'running') { statusClass = 'status-running'; statusText = 'Đang chạy'; }
    else if (acc.status === 'expired') { statusClass = 'status-expired'; statusText = 'Hết giờ'; }
    else { statusClass = 'status-stopped'; statusText = 'Đã dừng'; }

    return `
        <td data-label="STT" style="color:var(--text-muted)">${idx + 1}</td>
        <td data-label="Tài khoản" class="account-name">${escapeHtml(acc.name)}</td>
        <td data-label="Trạng thái"><span class="status-badge ${statusClass}"><span class="dot"></span>${statusText}</span></td>
        <td data-label="Đã chạy" class="time-display">${formatTime(acc.elapsed)}</td>
        <td data-label="Tiến trình"><div class="progress-bar-wrapper"><div class="progress-bar-fill ${isWarning?'warning':''}" style="width:${pct}%"></div></div><div class="progress-text">${pct.toFixed(1)}%</div></td>
        <td data-label="Cho phép" class="hours-display">${acc.maxHours}h</td>
        <td data-label="" class="action-buttons">
            ${acc.status === 'running'
                ? `<button class="btn btn-sm btn-stop" onclick="toggleAccount(${idx})">⏸ Dừng</button>`
                : acc.status === 'expired'
                    ? `<button class="btn btn-sm btn-start" onclick="resetAccount(${idx})">↺ Reset</button>`
                    : `<button class="btn btn-sm btn-start" onclick="toggleAccount(${idx})">▶ Bắt đầu</button>`
            }
            <button class="btn btn-sm btn-delete" onclick="deleteAccount(${idx})" title="Xóa">🗑</button>
        </td>`;
}

// ===== Render Table =====
function renderTable() {
    tbody.innerHTML = '';
    if (tbody2) tbody2.innerHTML = '';
    accounts.forEach((acc, idx) => {
        const tr = document.createElement('tr');
        tr.innerHTML = buildRowHtml(acc, idx);
        tbody.appendChild(tr);
        // Mirror to Accounts page table
        if (tbody2) {
            const tr2 = document.createElement('tr');
            tr2.innerHTML = buildRowHtml(acc, idx);
            tbody2.appendChild(tr2);
        }
    });
    updateStats();
}

// ===== Add Account =====
form.addEventListener('submit', (e) => {
    e.preventDefault();
    const name = nameInput.value.trim();
    const hours = parseFloat(hoursInput.value);
    if (!name) { showToast('error', 'Lỗi', 'Vui lòng nhập tên tài khoản'); return; }
    if (!hours || hours <= 0) { showToast('error', 'Lỗi', 'Số giờ phải lớn hơn 0'); return; }
    if (accounts.some(a => a.name.toLowerCase() === name.toLowerCase())) {
        showToast('warning', 'Trùng tên', `Tài khoản "${name}" đã tồn tại`); return;
    }
    accounts.push({ name, maxHours: hours, elapsed: 0, status: 'stopped' });
    nameInput.value = '';
    hoursInput.value = '';
    nameInput.focus();
    renderTable();
    showToast('success', 'Thành công', `Đã thêm tài khoản "${name}"`);
    saveToLocal();
});

// ===== File Upload =====
uploadZone.addEventListener('click', () => fileInput.click());
uploadZone.addEventListener('dragover', (e) => { e.preventDefault(); uploadZone.classList.add('dragover'); });
uploadZone.addEventListener('dragleave', () => uploadZone.classList.remove('dragover'));
uploadZone.addEventListener('drop', (e) => {
    e.preventDefault();
    uploadZone.classList.remove('dragover');
    if (e.dataTransfer.files.length) handleFile(e.dataTransfer.files[0]);
});
fileInput.addEventListener('change', () => {
    if (fileInput.files.length) handleFile(fileInput.files[0]);
});

function handleFile(file) {
    const ext = file.name.split('.').pop().toLowerCase();
    if (ext !== 'txt' && ext !== 'csv') {
        showToast('error', 'File không hợp lệ', 'Chỉ hỗ trợ file .txt hoặc .csv');
        return;
    }
    const reader = new FileReader();
    reader.onload = (e) => {
        const text = e.target.result;
        pendingFileData = parseFileContent(text);
        if (pendingFileData.length === 0) {
            showToast('error', 'File trống', 'Không tìm thấy tài khoản nào trong file');
            return;
        }
        document.getElementById('uploadFileName').textContent = file.name;
        document.getElementById('uploadFileCount').textContent = `${pendingFileData.length} tài khoản`;
        uploadPreview.classList.remove('hidden');
        showToast('info', 'Đã đọc file', `Tìm thấy ${pendingFileData.length} tài khoản trong "${file.name}"`);
    };
    reader.readAsText(file, 'UTF-8');
}

function parseFileContent(text) {
    const lines = text.split(/\r?\n/).map(l => l.trim()).filter(l => l && !l.startsWith('#'));
    const result = [];
    for (const line of lines) {
        // Support formats: "name" or "name,hours" or "name;hours"
        const parts = line.split(/[,;\t]/).map(p => p.trim());
        const name = parts[0];
        const hours = parts[1] ? parseFloat(parts[1]) : null;
        if (name) result.push({ name, hours });
    }
    return result;
}

function importAccounts() {
    const defaultHours = parseFloat(document.getElementById('uploadDefaultHours').value) || settings.defaultHours;
    let added = 0, skipped = 0;
    for (const item of pendingFileData) {
        if (accounts.some(a => a.name.toLowerCase() === item.name.toLowerCase())) {
            skipped++;
            continue;
        }
        accounts.push({
            name: item.name,
            maxHours: item.hours && item.hours > 0 ? item.hours : defaultHours,
            elapsed: 0,
            status: 'stopped'
        });
        added++;
    }
    clearUpload();
    renderTable();
    saveToLocal();
    showToast('success', 'Import thành công', `Đã thêm ${added} tài khoản${skipped ? `, bỏ qua ${skipped} trùng` : ''}`);
}

function clearUpload() {
    pendingFileData = [];
    uploadPreview.classList.add('hidden');
    fileInput.value = '';
}

// ===== Account Actions =====
function toggleAccount(idx) {
    const acc = accounts[idx];
    if (acc.status === 'running') {
        acc.status = 'stopped';
        showToast('info', 'Đã dừng', `Tài khoản "${acc.name}" đã được dừng`);
    } else {
        acc.status = 'running';
        showToast('success', 'Bắt đầu', `Tài khoản "${acc.name}" đang chạy`);
    }
    renderTable(); saveToLocal();
}

function resetAccount(idx) {
    accounts[idx].elapsed = 0;
    accounts[idx].status = 'stopped';
    renderTable();
    showToast('info', 'Reset', `Đã reset tài khoản "${accounts[idx].name}"`);
    saveToLocal();
}

function deleteAccount(idx) {
    const name = accounts[idx].name;
    accounts.splice(idx, 1);
    renderTable();
    showToast('warning', 'Đã xóa', `Tài khoản "${name}" đã bị xóa`);
    saveToLocal();
}

function startAllAccounts() {
    let count = 0;
    accounts.forEach(a => { if (a.status === 'stopped') { a.status = 'running'; count++; } });
    renderTable(); saveToLocal();
    showToast('success', 'Chạy tất cả', `Đã bắt đầu ${count} tài khoản`);
}
function stopAllAccounts() {
    accounts.forEach(a => { if (a.status === 'running') a.status = 'stopped'; });
    renderTable(); saveToLocal();
    showToast('info', 'Dừng tất cả', 'Tất cả tài khoản đã dừng');
}
function deleteAllAccounts() {
    if (!confirm('Bạn có chắc muốn xóa TẤT CẢ tài khoản?')) return;
    accounts = [];
    renderTable(); saveToLocal();
    showToast('warning', 'Đã xóa', 'Đã xóa tất cả tài khoản');
}

// ===== Real-time Timer =====
function startTimer() {
    timerId = setInterval(() => {
        accounts.forEach(acc => {
            if (acc.status !== 'running') return;
            acc.elapsed += 1;
            const maxSec = acc.maxHours * 3600;
            if (acc.elapsed >= maxSec) {
                acc.elapsed = maxSec;
                acc.status = 'expired';
                sendTelegramAlert(acc.name, acc.maxHours);
                showToast('warning', 'Hết giờ!', `Tài khoản "${acc.name}" đã hoạt động đủ ${acc.maxHours} giờ`);
            }
        });
        renderTable();
        saveToLocal();
    }, 1000);
}

// ===== Telegram — Direct API call (no backend needed for GitHub Pages) =====
async function sendTelegramAlert(accountName, hours) {
    alertCount++;
    // Add to notifications log
    notifications.unshift({
        type: 'alert',
        title: `Tài khoản "${accountName}" hết giờ`,
        desc: `Đã hoạt động đủ ${hours} giờ và tự động dừng`,
        time: new Date().toISOString()
    });
    updateStats();
    saveToLocal();

    if (!settings.botToken || !settings.chatId) {
        showToast('error', 'Chưa cấu hình Telegram', 'Vào Cài đặt để nhập Bot Token và Chat ID');
        return;
    }

    const message =
        `🚨 Cảnh báo Hệ Thống\n\n` +
        `📛 Tài khoản: ${accountName}\n` +
        `⏱ Đã hoạt động đủ: ${hours} giờ\n` +
        `⛔ Trạng thái: Đã được tự động dừng!\n\n` +
        `⚠️ Tài khoản ${accountName} đã hoạt động đủ ${hours} giờ và đã được tự động dừng!`;

    const url = `https://api.telegram.org/bot${settings.botToken}/sendMessage`;

    try {
        const res = await fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                chat_id: settings.chatId,
                text: message
            })
        });
        if (res.ok) {
            showToast('success', 'Telegram', `Đã gửi cảnh báo cho "${accountName}"`);
            statusDot.className = 'status-dot online';
            // Update notif as success
            notifications[0].type = 'success';
            saveToLocal();
        } else {
            const err = await res.json();
            showToast('error', 'Telegram Error', err.description || 'Lỗi gửi tin nhắn');
        }
    } catch (e) {
        console.error('Telegram error:', e);
        showToast('error', 'Lỗi mạng', 'Không thể gọi Telegram API');
    }
}

// ===== Notifications Page =====
function renderNotifications() {
    const list = document.getElementById('notifList');
    const emptyNotif = document.getElementById('emptyNotif');
    if (notifications.length === 0) {
        list.innerHTML = '';
        list.appendChild(emptyNotif);
        emptyNotif.classList.remove('hidden');
        return;
    }
    emptyNotif.classList.add('hidden');
    list.innerHTML = notifications.map(n => `
        <div class="notif-item">
            <div class="notif-icon ${n.type}">
                ${n.type === 'alert'
                    ? '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 0 1-3.46 0"/></svg>'
                    : '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>'
                }
            </div>
            <div class="notif-body">
                <div class="notif-title">${escapeHtml(n.title)}</div>
                <div class="notif-desc">${escapeHtml(n.desc)}</div>
            </div>
            <div class="notif-time">${timeAgo(n.time)}</div>
        </div>`).join('');
}

function clearNotifications() {
    notifications = [];
    alertCount = 0;
    renderNotifications();
    updateStats();
    saveToLocal();
    showToast('info', 'Đã xóa', 'Đã xóa tất cả thông báo');
}

// ===== Settings Page =====
function loadSettingsUI() {
    document.getElementById('settingBotToken').value = settings.botToken || '';
    document.getElementById('settingChatId').value = settings.chatId || '';
    document.getElementById('settingDefaultHours').value = settings.defaultHours || 8;
}

function saveSettings() {
    settings.botToken = document.getElementById('settingBotToken').value.trim();
    settings.chatId = document.getElementById('settingChatId').value.trim();
    saveToLocal();
    showToast('success', 'Đã lưu', 'Cấu hình Telegram đã được lưu');
    // Update status dot
    if (settings.botToken && settings.chatId) {
        statusDot.className = 'status-dot online';
        document.getElementById('telegramLabel').textContent = 'Telegram ✓';
    } else {
        statusDot.className = 'status-dot offline';
        document.getElementById('telegramLabel').textContent = 'Telegram Bot';
    }
}

function saveGeneralSettings() {
    settings.defaultHours = parseFloat(document.getElementById('settingDefaultHours').value) || 8;
    saveToLocal();
    showToast('success', 'Đã lưu', 'Cài đặt chung đã được cập nhật');
}

async function testTelegram() {
    const token = document.getElementById('settingBotToken').value.trim();
    const chatId = document.getElementById('settingChatId').value.trim();
    if (!token || !chatId) {
        showToast('error', 'Thiếu thông tin', 'Vui lòng nhập Bot Token và Chat ID');
        return;
    }
    try {
        const res = await fetch(`https://api.telegram.org/bot${token}/sendMessage`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                chat_id: chatId,
                text: '✅ Test thành công! AccManager đã kết nối với Telegram Bot.',
                parse_mode: 'HTML'
            })
        });
        if (res.ok) {
            showToast('success', 'Test thành công', 'Tin nhắn đã được gửi đến Telegram');
            statusDot.className = 'status-dot online';
        } else {
            const err = await res.json();
            showToast('error', 'Test thất bại', err.description || 'Kiểm tra lại Token và Chat ID');
        }
    } catch (e) {
        showToast('error', 'Lỗi mạng', 'Không thể kết nối đến Telegram API');
    }
}

function exportData() {
    const data = JSON.stringify({ accounts, notifications, alertCount, settings }, null, 2);
    const blob = new Blob([data], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `accmanager_backup_${new Date().toISOString().slice(0,10)}.json`;
    a.click();
    URL.revokeObjectURL(url);
    showToast('success', 'Xuất dữ liệu', 'File JSON đã được tải xuống');
}

// ===== LocalStorage =====
function saveToLocal() {
    localStorage.setItem('acc_manager_v2', JSON.stringify({
        accounts, alertCount, notifications, settings
    }));
}

function loadFromLocal() {
    const saved = localStorage.getItem('acc_manager_v2');
    if (saved) {
        try {
            const d = JSON.parse(saved);
            accounts = d.accounts || [];
            alertCount = d.alertCount || 0;
            notifications = d.notifications || [];
            settings = { ...settings, ...(d.settings || {}) };
        } catch { /* ignore */ }
    }
    // Also migrate from v1
    const v1 = localStorage.getItem('acc_manager_data');
    if (v1 && !saved) {
        try {
            const d = JSON.parse(v1);
            accounts = d.accounts || [];
            alertCount = d.alertCount || 0;
        } catch { /* ignore */ }
    }
}

// ===== Init =====
loadFromLocal();
renderTable();
startTimer();

// Set initial Telegram status
if (settings.botToken && settings.chatId) {
    statusDot.className = 'status-dot online';
    document.getElementById('telegramLabel').textContent = 'Telegram ✓';
}
