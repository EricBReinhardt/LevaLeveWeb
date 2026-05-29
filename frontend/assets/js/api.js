function defaultApiBase() {
  const override = localStorage.getItem('LEVA_LEVE_API_BASE');
  if (override) {
    return override.replace(/\/$/, '');
  }

  if (location.protocol === 'file:') {
    return 'http://localhost:8000';
  }

  return location.origin;
}

const API_BASE = defaultApiBase();

export function getToken() {
  return localStorage.getItem('LEVA_LEVE_TOKEN') || '';
}

export function setSession(session) {
  if (session?.token) {
    localStorage.setItem('LEVA_LEVE_TOKEN', session.token);
  }
  if (session?.user) {
    localStorage.setItem('LEVA_LEVE_USER', JSON.stringify(session.user));
  }
}

export function getStoredUser() {
  const raw = localStorage.getItem('LEVA_LEVE_USER');
  return raw ? JSON.parse(raw) : null;
}

import { money as _money } from './utils.js';

export function money(value, opts) { return _money(value, opts); }

export async function request(path, options = {}) {
  const headers = new Headers(options.headers || {});
  headers.set('Content-Type', 'application/json');

  const token = getToken();
  if (token) {
    headers.set('Authorization', `Bearer ${token}`);
  }

  let response;
  try {
    response = await fetch(`${API_BASE}${path}`, {
      ...options,
      headers,
    });
  } catch (error) {
    throw new Error(`Nao foi possivel conectar ao backend em ${API_BASE}. Verifique se o servidor esta rodando.`);
  }

  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(formatErrorDetail(payload.detail));
  }
  return payload;
}

function formatErrorDetail(detail) {
  if (!detail) {
    return 'Falha na requisicao';
  }

  if (typeof detail === 'string') {
    return detail;
  }

  if (Array.isArray(detail)) {
    return detail
      .map((item) => {
        if (typeof item === 'string') {
          return item;
        }
        if (item && typeof item === 'object') {
          const field = Array.isArray(item.loc) ? item.loc[item.loc.length - 1] : '';
          return item.msg ? `${field ? `${field}: ` : ''}${item.msg}` : JSON.stringify(item);
        }
        return String(item);
      })
      .join('\n');
  }

  if (typeof detail === 'object') {
    return detail.msg || detail.message || JSON.stringify(detail);
  }

  return String(detail);
}
