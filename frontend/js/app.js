
const API = '/api';

async function apiFetch(path, options = {}) {
  const response = await fetch(API + path, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Error desconocido' }));
    throw new Error(error.detail || 'Error en el servidor');
  }

  return response.json();
}

function apiGet(path)               { return apiFetch(path); }
function apiPost(path, body)        { return apiFetch(path, { method: 'POST',   body: JSON.stringify(body) }); }
function apiPut(path, body)         { return apiFetch(path, { method: 'PUT',    body: JSON.stringify(body) }); }
function apiDelete(path)            { return apiFetch(path, { method: 'DELETE' }); }


function formatMoney(amount) {
  return 'Q ' + parseFloat(amount).toLocaleString('es-GT', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
}

function formatDate(isoString) {
  return new Date(isoString).toLocaleDateString('es-GT');
}

function setLoading(visible) {
  const el = document.getElementById('msg-loading');
  if (el) el.style.display = visible ? 'block' : 'none';
}

function showError(message) {
  const el = document.getElementById('msg-error');
  if (el) {
    el.textContent = '⚠️ ' + message;
    el.style.display = 'block';
  }
}

function showToast(message, type = 'success') {
  let container = document.getElementById('toast-container');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toast-container';
    container.style.cssText = 'position:fixed;bottom:1rem;right:1rem;z-index:9999;display:flex;flex-direction:column;gap:0.5rem;';
    document.body.appendChild(container);
  }

  const colors = { success: '#198754', danger: '#dc3545', warning: '#856404' };
  const icons  = { success: '✓', danger: '✕', warning: '⚠' };

  const toast = document.createElement('div');
  toast.style.cssText = `
    background: #fff;
    border-left: 4px solid ${colors[type] || colors.success};
    padding: 0.75rem 1rem;
    border-radius: 6px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.15);
    font-size: 0.9rem;
    min-width: 220px;
  `;
  toast.textContent = (icons[type] || '✓') + ' ' + message;
  container.appendChild(toast);

  setTimeout(() => toast.remove(), 3000);
}