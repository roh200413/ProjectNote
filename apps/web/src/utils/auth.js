const ROLE_KEY = 'pnRole';

export function getRole() {
  return localStorage.getItem(ROLE_KEY) || '';
}

export function setRole(role) {
  if (role) localStorage.setItem(ROLE_KEY, role);
}

export function clearRole() {
  localStorage.removeItem(ROLE_KEY);
}
