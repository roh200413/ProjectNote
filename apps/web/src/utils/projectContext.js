const STORAGE_KEY = 'pnSelectedProject';

export function saveSelectedProject(project) {
  if (!project || !project.id) return;
  const payload = {
    id: String(project.id),
    name: project.name || `프로젝트 #${project.id}`,
    code: project.code || '-'
  };
  globalThis.sessionStorage?.setItem(STORAGE_KEY, JSON.stringify(payload));
}

export function readSelectedProject() {
  const raw = globalThis.sessionStorage?.getItem(STORAGE_KEY);
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
  globalThis.sessionStorage?.removeItem(STORAGE_KEY);
}
