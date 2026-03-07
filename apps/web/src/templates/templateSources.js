import adminLogin from '../../../../client/auth/admin_login.html?raw';
import login from '../../../../client/auth/login.html?raw';
import signup from '../../../../client/auth/signup.html?raw';
import adminAdmin from '../../../../client/admin/admin.html?raw';
import adminDashboard from '../../../../client/admin/dashboard.html?raw';
import adminTables from '../../../../client/admin/tables.html?raw';
import adminTeams from '../../../../client/admin/teams.html?raw';
import adminUsers from '../../../../client/admin/users.html?raw';
import adminNavList from '../../../../client/admin/partials/nav_list.html?raw';
import base from '../../../../client/base.html?raw';
import baseAdmin from '../../../../client/base_admin.html?raw';
import rnCover from '../../../../client/research_notes/cover.html?raw';
import rnDetail from '../../../../client/research_notes/detail.html?raw';
import rnList from '../../../../client/research_notes/list.html?raw';
import rnPrintable from '../../../../client/research_notes/printable.html?raw';
import rnViewer from '../../../../client/research_notes/viewer.html?raw';
import wfCollab from '../../../../client/workflow/collaboration_integrations.html?raw';
import wfFinalDownload from '../../../../client/workflow/final_download.html?raw';
import wfGithub from '../../../../client/workflow/github_integrations.html?raw';
import wfHome from '../../../../client/workflow/home.html?raw';
import wfMyPage from '../../../../client/workflow/my_page.html?raw';
import wfProjectCreate from '../../../../client/workflow/project_create.html?raw';
import wfProjectDetail from '../../../../client/workflow/project_detail.html?raw';
import wfProjectNotes from '../../../../client/workflow/project_research_notes.html?raw';
import wfProjectNotesPrint from '../../../../client/workflow/project_research_notes_print.html?raw';
import wfProjectResearchers from '../../../../client/workflow/project_researchers.html?raw';
import wfProjects from '../../../../client/workflow/projects.html?raw';
import wfResearchers from '../../../../client/workflow/researchers.html?raw';
import wfSignatures from '../../../../client/workflow/signatures.html?raw';

export const templateSources = {
  'client/auth/admin_login.html': adminLogin,
  'client/auth/login.html': login,
  'client/auth/signup.html': signup,
  'client/admin/admin.html': adminAdmin,
  'client/admin/dashboard.html': adminDashboard,
  'client/admin/tables.html': adminTables,
  'client/admin/teams.html': adminTeams,
  'client/admin/users.html': adminUsers,
  'client/base.html': base,
  'client/base_admin.html': baseAdmin,
  'client/research_notes/cover.html': rnCover,
  'client/research_notes/detail.html': rnDetail,
  'client/research_notes/list.html': rnList,
  'client/research_notes/printable.html': rnPrintable,
  'client/research_notes/viewer.html': rnViewer,
  'client/workflow/collaboration_integrations.html': wfCollab,
  'client/workflow/final_download.html': wfFinalDownload,
  'client/workflow/github_integrations.html': wfGithub,
  'client/workflow/home.html': wfHome,
  'client/workflow/my_page.html': wfMyPage,
  'client/workflow/project_create.html': wfProjectCreate,
  'client/workflow/project_detail.html': wfProjectDetail,
  'client/workflow/project_research_notes.html': wfProjectNotes,
  'client/workflow/project_research_notes_print.html': wfProjectNotesPrint,
  'client/workflow/project_researchers.html': wfProjectResearchers,
  'client/workflow/projects.html': wfProjects,
  'client/workflow/researchers.html': wfResearchers,
  'client/workflow/signatures.html': wfSignatures
};

export const includeSources = {
  'admin/partials/nav_list.html': adminNavList
};
