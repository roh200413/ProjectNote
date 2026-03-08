import { Navigate, Route, Routes } from 'react-router-dom';
import AdminDashboardPage from './pages/AdminDashboardPage';
import AdminLoginPage from './pages/AdminLoginPage';
import AdminTablesPage from './pages/AdminTablesPage';
import AdminTeamsPage from './pages/AdminTeamsPage';
import AdminUsersPage from './pages/AdminUsersPage';
import LegacyTemplatePage from './pages/LegacyTemplatePage';
import NotImplementedPage from './pages/NotImplementedPage';
import { routeCatalog } from './pages/routeCatalog';

const legacyEnabled = import.meta.env.VITE_ENABLE_LEGACY_PAGES === 'true';
const reactRoutes = new Set(['/auth/admin-login', '/admin/dashboard', '/admin/users', '/admin/teams', '/admin/tables']);

export default function App() {
  return (
    <Routes>
      <Route element={<AdminLoginPage />} path="/auth/admin-login" />
      <Route element={<AdminDashboardPage />} path="/admin/dashboard" />
      <Route element={<AdminUsersPage />} path="/admin/users" />
      <Route element={<AdminTeamsPage />} path="/admin/teams" />
      <Route element={<AdminTablesPage />} path="/admin/tables" />

      {routeCatalog
        .filter((item) => !reactRoutes.has(item.path))
        .map((item) => (
          <Route
            key={item.path}
            element={
              legacyEnabled ? (
                <LegacyTemplatePage source={item.source} />
              ) : (
                <NotImplementedPage legacyEnabled={legacyEnabled} path={item.path} />
              )
            }
            path={item.path}
          />
        ))}

      <Route element={<Navigate replace to="/admin/dashboard" />} path="*" />
    </Routes>
  );
}
