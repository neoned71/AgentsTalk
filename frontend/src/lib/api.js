// src/lib/api.js
export const API = import.meta.env.PUBLIC_API_BASE || 'http://localhost:8000';

export function apiFetch(path, opts = {}) {
  const url = path.startsWith('http') ? path : API + path;
  return fetch(url, { credentials: 'include', ...opts });
}
