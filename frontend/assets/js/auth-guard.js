import { getStoredUser, request, setSession } from './api.js';

function defaultRedirect() {
  return location.pathname.includes('/pages/') ? '../index.html' : 'index.html';
}

function clearSession() {
  try {
    localStorage.removeItem('LEVA_LEVE_USER');
  } catch {}
}

async function refreshSession() {
  try {
    const currentUser = await request('/me');
    setSession({ user: currentUser });
    return currentUser;
  } catch {
    clearSession();
    return null;
  }
}

function redirectTo(target) {
  window.location.replace(target || defaultRedirect());
}

async function enforceAuth() {
  const config = window.LL_GUARD || {};
  const redirect = config.redirect || defaultRedirect();
  const allowedRoles = Array.isArray(config.roles) ? config.roles : [];

  const storedUser = getStoredUser();
  if (!storedUser) {
    redirectTo(redirect);
    return;
  }

  if (allowedRoles.length && !allowedRoles.includes(storedUser.role)) {
    redirectTo(config.fallback || redirect);
    return;
  }

  const user = await refreshSession();
  if (!user) {
    redirectTo(redirect);
    return;
  }

  if (allowedRoles.length && !allowedRoles.includes(user.role)) {
    clearSession();
    redirectTo(config.fallback || redirect);
    return;
  }
}

void enforceAuth();
