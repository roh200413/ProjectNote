import { Navigate, Route, Routes } from 'react-router-dom';
import AdminDashboardPage from './pages/AdminDashboardPage';
import AdminLoginPage from './pages/AdminLoginPage';
import AdminTablesPage from './pages/AdminTablesPage';
import AdminTeamsPage from './pages/AdminTeamsPage';
import AdminUsersPage from './pages/AdminUsersPage';
import { AdminRoute, UserRoute } from './components/RouteGuards';
import LegacyTemplatePage from './pages/LegacyTemplatePage';
import LogoutPage from './pages/LogoutPage';
import NotImplementedPage from './pages/NotImplementedPage';
import { LoginPage, SignupPage } from './pages/UserAuthPages';
import {
  DataUpdatesPage,
  GithubIntegrationsPage,
  HomePage,
  MyPage,
  ProjectCreatePage,
  ProjectDetailPage,
  ProjectResearchNotesPage,
  ProjectResearchNotesPrintPage,
  ProjectResearchersPage,
  ProjectsPage,
  ResearchNoteCoverPage,
  ResearchNoteDetailPage,
  ResearchNotePrintablePage,
  ResearchNoteViewerPage,
  ResearchersPage
} from './pages/UserGenericPages';
import { routeCatalog } from './pages/routeCatalog';

const legacyEnabled = import.meta.env.VITE_ENABLE_LEGACY_PAGES === 'true';
const implementedRoutes = new Set([
  '/', '/auth/login', '/auth/signup', '/logout',
  '/projects', '/projects/create', '/projects/:id',
  '/projects/:id/research-notes', '/projects/:id/research-notes/print',
  '/researchers', '/projects/:id/researchers',
  '/research-notes', '/research-notes/:id', '/research-notes/:id/viewer', '/research-notes/:id/cover', '/research-notes/:id/printable',
  '/my-page', '/data-updates', '/integrations/github', '/signatures',
  '/auth/admin-login', '/admin/dashboard', '/admin/users', '/admin/teams', '/admin/tables', '/admin'
]);

export default function App() {
  return (
    <Routes>
      <Route element={<LoginPage />} path="/auth/login" />
      <Route element={<SignupPage />} path="/auth/signup" />
      <Route element={<AdminLoginPage />} path="/auth/admin-login" />
      <Route element={<LogoutPage />} path="/logout" />

      <Route element={<UserRoute><HomePage /></UserRoute>} path="/" />
      <Route element={<UserRoute><ProjectsPage /></UserRoute>} path="/projects" />
      <Route element={<UserRoute><ProjectCreatePage /></UserRoute>} path="/projects/create" />
      <Route element={<UserRoute><ProjectDetailPage /></UserRoute>} path="/projects/:id" />
      <Route element={<UserRoute><ProjectResearchNotesPage /></UserRoute>} path="/projects/:id/research-notes" />
      <Route element={<UserRoute><ProjectResearchNotesPrintPage /></UserRoute>} path="/projects/:id/research-notes/print" />
      <Route element={<UserRoute><ResearchersPage /></UserRoute>} path="/researchers" />
      <Route element={<UserRoute><ProjectResearchersPage /></UserRoute>} path="/projects/:id/researchers" />
      <Route element={<Navigate replace to="/projects" />} path="/research-notes" />
      <Route element={<UserRoute><ResearchNoteDetailPage /></UserRoute>} path="/research-notes/:id" />
      <Route element={<UserRoute><ResearchNoteViewerPage /></UserRoute>} path="/research-notes/:id/viewer" />
      <Route element={<UserRoute><ResearchNoteCoverPage /></UserRoute>} path="/research-notes/:id/cover" />
      <Route element={<UserRoute><ResearchNotePrintablePage /></UserRoute>} path="/research-notes/:id/printable" />
      <Route element={<UserRoute><MyPage /></UserRoute>} path="/my-page" />
      <Route element={<UserRoute><DataUpdatesPage /></UserRoute>} path="/data-updates" />
      <Route element={<UserRoute><GithubIntegrationsPage /></UserRoute>} path="/integrations/github" />
      <Route element={<Navigate replace to="/my-page" />} path="/signatures" />
      <Route element={<Navigate replace to="/my-page" />} path="/final-download" />

      <Route element={<AdminRoute><AdminDashboardPage /></AdminRoute>} path="/admin/dashboard" />
      <Route element={<AdminRoute><AdminUsersPage /></AdminRoute>} path="/admin/users" />
      <Route element={<AdminRoute><AdminTeamsPage /></AdminRoute>} path="/admin/teams" />
      <Route element={<AdminRoute><AdminTablesPage /></AdminRoute>} path="/admin/tables" />
      <Route element={<Navigate replace to="/admin/dashboard" />} path="/admin" />

      {routeCatalog
        .filter((item) => !implementedRoutes.has(item.path))
        .map((item) => (
          <Route
            key={item.path}
            element={legacyEnabled ? <LegacyTemplatePage source={item.source} /> : <NotImplementedPage legacyEnabled={legacyEnabled} path={item.path} />}
            path={item.path}
          />
        ))}

      <Route element={<Navigate replace to="/auth/login" />} path="*" />
    </Routes>
  );
}
