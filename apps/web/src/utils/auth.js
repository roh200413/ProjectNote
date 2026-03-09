const ROLE_KEY = 'pnRole';
let memoryRole = '';

function readRoleFromStorage() {
  try {
    return globalThis.localStorage?.getItem(ROLE_KEY) || '';
  } catch (_error) {
    return '';
  }
}

export function getRole() {
  return readRoleFromStorage() || memoryRole;
}

export function setRole(role) {
  if (!role) return;
  memoryRole = role;
  try {
    globalThis.localStorage?.setItem(ROLE_KEY, role);
  } catch (_error) {
    // ignore storage failures (private mode / blocked storage)
  }
}

export function clearRole() {
  memoryRole = '';
  try {
    globalThis.localStorage?.removeItem(ROLE_KEY);
  } catch (_error) {
    // ignore storage failures
  }
}
