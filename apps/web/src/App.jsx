import { Navigate, Route, Routes } from 'react-router-dom';
import AdminDashboardPage from './pages/AdminDashboardPage';
import AdminLoginPage from './pages/AdminLoginPage';
import AdminTablesPage from './pages/AdminTablesPage';
import AdminTeamsPage from './pages/AdminTeamsPage';
import AdminUsersPage from './pages/AdminUsersPage';
import LegacyTemplatePage from './pages/LegacyTemplatePage';
import { routeCatalog } from './pages/routeCatalog';

const reactNativePaths = new Set(['/auth/admin-login', '/admin/dashboard', '/admin/teams', '/admin/users', '/admin/tables']);

export default function App() {
  return (
    <Routes>
      <Route element={<AdminLoginPage />} path="/auth/admin-login" />
      <Route element={<AdminDashboardPage />} path="/admin/dashboard" />
      <Route element={<AdminTeamsPage />} path="/admin/teams" />
      <Route element={<AdminUsersPage />} path="/admin/users" />
      <Route element={<AdminTablesPage />} path="/admin/tables" />

      {routeCatalog
        .filter((item) => !reactNativePaths.has(item.path))
        .map((item) => (
          <Route key={item.path} element={<LegacyTemplatePage backendPath={item.backendPath} />} path={item.path} />
        ))}

      <Route element={<Navigate replace to="/" />} path="*" />
    </Routes>
  );
}
