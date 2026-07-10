(function () {
  const guard = window.LL_GUARD || {};
  const allowedRoles = Array.isArray(guard.roles) ? guard.roles : [];
  const redirect = guard.redirect || (location.pathname.includes('/pages/') ? '../index.html' : 'index.html');
  const fallback = guard.fallback || redirect;

  let storedUser = null;
  try {
    const raw = localStorage.getItem('LEVA_LEVE_USER');
    storedUser = raw ? JSON.parse(raw) : null;
  } catch {
    storedUser = null;
  }

  if (!storedUser) {
    window.location.replace(redirect);
    return;
  }

  if (allowedRoles.length && !allowedRoles.includes(storedUser.role)) {
    window.location.replace(fallback);
  }
}());