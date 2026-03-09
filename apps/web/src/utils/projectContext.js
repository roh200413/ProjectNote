const STORAGE_KEY = 'pnSelectedProject';

export function saveSelectedProject(project) {
  if (!project || !project.id) return;
  const payload = {
    id: String(project.id),
    name: project.name || `프로젝트 #${project.id}`,
    code: project.code || '-'
  };
  try {
    globalThis.sessionStorage?.setItem(STORAGE_KEY, JSON.stringify(payload));
  } catch (_error) {
    // ignore storage failures (private mode / blocked storage)
  }
}

export function readSelectedProject() {
  let raw = null;
  try {
    raw = globalThis.sessionStorage?.getItem(STORAGE_KEY);
  } catch (_error) {
    return null;
  }
  if (!raw) return null;
  try {
    const parsed = JSON.parse(raw);
    if (!parsed?.id) return null;
    return parsed;
  } catch (_error) {
    return null;
  }
}

export function clearSelectedProject() {
  try {
    globalThis.sessionStorage?.removeItem(STORAGE_KEY);
  } catch (_error) {
    // ignore storage failures
  }
}
