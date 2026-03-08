import { Navigate, Route, Routes } from 'react-router-dom';
import AdminDashboardPage from './pages/AdminDashboardPage';
import AdminLoginPage from './pages/AdminLoginPage';
import AdminTablesPage from './pages/AdminTablesPage';
import AdminTeamsPage from './pages/AdminTeamsPage';
import AdminUsersPage from './pages/AdminUsersPage';
import LegacyTemplatePage from './pages/LegacyTemplatePage';
import NotImplementedPage from './pages/NotImplementedPage';
import { LoginPage, SignupPage } from './pages/UserAuthPages';
import {
  DataUpdatesPage,
  FinalDownloadPage,
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
  ResearchNotesListPage,
  ResearchNoteViewerPage,
  ResearchersPage,
  SignaturesPage
} from './pages/UserGenericPages';
import { routeCatalog } from './pages/routeCatalog';

const legacyEnabled = import.meta.env.VITE_ENABLE_LEGACY_PAGES === 'true';
const implementedRoutes = new Set([
  '/',
  '/auth/login',
  '/auth/signup',
  '/projects',
  '/projects/create',
  '/projects/:id',
  '/projects/:id/research-notes',
  '/projects/:id/research-notes/print',
  '/researchers',
  '/projects/:id/researchers',
  '/research-notes',
  '/research-notes/:id',
  '/research-notes/:id/viewer',
  '/research-notes/:id/cover',
  '/research-notes/:id/printable',
  '/my-page',
  '/data-updates',
  '/integrations/github',
  '/signatures',
  '/final-download',
  '/auth/admin-login',
  '/admin/dashboard',
  '/admin/users',
  '/admin/teams',
  '/admin/tables',
  '/admin'
]);

export default function App() {
  return (
    <Routes>
      <Route element={<HomePage />} path="/" />
      <Route element={<LoginPage />} path="/auth/login" />
      <Route element={<SignupPage />} path="/auth/signup" />
      <Route element={<ProjectsPage />} path="/projects" />
      <Route element={<ProjectCreatePage />} path="/projects/create" />
      <Route element={<ProjectDetailPage />} path="/projects/:id" />
      <Route element={<ProjectResearchNotesPage />} path="/projects/:id/research-notes" />
      <Route element={<ProjectResearchNotesPrintPage />} path="/projects/:id/research-notes/print" />
      <Route element={<ResearchersPage />} path="/researchers" />
      <Route element={<ProjectResearchersPage />} path="/projects/:id/researchers" />
      <Route element={<ResearchNotesListPage />} path="/research-notes" />
      <Route element={<ResearchNoteDetailPage />} path="/research-notes/:id" />
      <Route element={<ResearchNoteViewerPage />} path="/research-notes/:id/viewer" />
      <Route element={<ResearchNoteCoverPage />} path="/research-notes/:id/cover" />
      <Route element={<ResearchNotePrintablePage />} path="/research-notes/:id/printable" />
      <Route element={<MyPage />} path="/my-page" />
      <Route element={<DataUpdatesPage />} path="/data-updates" />
      <Route element={<GithubIntegrationsPage />} path="/integrations/github" />
      <Route element={<SignaturesPage />} path="/signatures" />
      <Route element={<FinalDownloadPage />} path="/final-download" />

      <Route element={<AdminLoginPage />} path="/auth/admin-login" />
      <Route element={<AdminDashboardPage />} path="/admin/dashboard" />
      <Route element={<AdminUsersPage />} path="/admin/users" />
      <Route element={<AdminTeamsPage />} path="/admin/teams" />
      <Route element={<AdminTablesPage />} path="/admin/tables" />
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

      <Route element={<Navigate replace to="/" />} path="*" />
    </Routes>
  );
}
