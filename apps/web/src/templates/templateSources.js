import adminLogin from '../legacy/client/auth/admin_login.html?raw';
import login from '../legacy/client/auth/login.html?raw';
import signup from '../legacy/client/auth/signup.html?raw';
import adminAdmin from '../legacy/client/admin/admin.html?raw';
import adminDashboard from '../legacy/client/admin/dashboard.html?raw';
import adminTables from '../legacy/client/admin/tables.html?raw';
import adminTeams from '../legacy/client/admin/teams.html?raw';
import adminUsers from '../legacy/client/admin/users.html?raw';
import adminNavList from '../legacy/client/admin/partials/nav_list.html?raw';
import base from '../legacy/client/base.html?raw';
import baseAdmin from '../legacy/client/base_admin.html?raw';
import wfCollab from '../legacy/client/workflow/collaboration_integrations.html?raw';
import wfFinalDownload from '../legacy/client/workflow/final_download.html?raw';
import wfGithub from '../legacy/client/workflow/github_integrations.html?raw';
import wfHome from '../legacy/client/workflow/home.html?raw';
import wfMyPage from '../legacy/client/workflow/my_page.html?raw';
import wfProjectCreate from '../legacy/client/workflow/project_create.html?raw';
import wfProjectDetail from '../legacy/client/workflow/project_detail.html?raw';
import wfProjectResearchers from '../legacy/client/workflow/project_researchers.html?raw';
import wfProjects from '../legacy/client/workflow/projects.html?raw';
import wfResearchers from '../legacy/client/workflow/researchers.html?raw';
import wfSignatures from '../legacy/client/workflow/signatures.html?raw';

export const templateSources = {
  'legacy/client/auth/admin_login.html': adminLogin,
  'legacy/client/auth/login.html': login,
  'legacy/client/auth/signup.html': signup,
  'legacy/client/admin/admin.html': adminAdmin,
  'legacy/client/admin/dashboard.html': adminDashboard,
  'legacy/client/admin/tables.html': adminTables,
  'legacy/client/admin/teams.html': adminTeams,
  'legacy/client/admin/users.html': adminUsers,
  'legacy/client/base.html': base,
  'legacy/client/base_admin.html': baseAdmin,
  'legacy/client/workflow/collaboration_integrations.html': wfCollab,
  'legacy/client/workflow/final_download.html': wfFinalDownload,
  'legacy/client/workflow/github_integrations.html': wfGithub,
  'legacy/client/workflow/home.html': wfHome,
  'legacy/client/workflow/my_page.html': wfMyPage,
  'legacy/client/workflow/project_create.html': wfProjectCreate,
  'legacy/client/workflow/project_detail.html': wfProjectDetail,
  'legacy/client/workflow/project_researchers.html': wfProjectResearchers,
  'legacy/client/workflow/projects.html': wfProjects,
  'legacy/client/workflow/researchers.html': wfResearchers,
  'legacy/client/workflow/signatures.html': wfSignatures
};

export const includeSources = {
  'admin/partials/nav_list.html': adminNavList
};
