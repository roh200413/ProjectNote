/* AUTO-GENERATED FILE. DO NOT EDIT. */
/* source_hash:6133fb2dbb5f74bcd52efffa2027dac8ef8ebdcad70b06d0ebf7a9a07ee08461 */

export type HealthResponse = {
  status: string;
};

export type FrontendBootstrapResponse = {
  api_name: string;
  api_version: string;
  timestamp: string;
};

export type AuthMeResponse = {
  user?: Record<string, unknown>;
  detail?: string;
};

export type AuthLoginResponse = {
  message?: string;
  user?: Record<string, unknown>;
  detail?: string;
};

export type PostApiV1AuthSignupResponse = Record<string, unknown>;
export type PostApiV1AuthLoginResponse = AuthLoginResponse;
export type PostApiV1AuthLogoutResponse = Record<string, unknown>;
export type GetApiV1AuthMeResponse = AuthMeResponse;
export type GetApiV1HealthResponse = HealthResponse;
export type GetApiV1OpenapiJsonResponse = Record<string, unknown>;
export type PostApiV1OpenapiJsonResponse = Record<string, unknown>;
export type GetApiV1FrontendBootstrapResponse = FrontendBootstrapResponse;
export type GetApiV1DashboardSummaryResponse = Record<string, unknown>;
export type PostApiV1DashboardSummaryResponse = Record<string, unknown>;
export type GetApiV1ProjectsResponse = Record<string, unknown>;
export type PostApiV1ProjectsResponse = Record<string, unknown>;
export type GetApiV1ProjectManagementResponse = Record<string, unknown>;
export type PostApiV1ProjectManagementResponse = Record<string, unknown>;
export type GetApiV1ProjectsStrProjectIdUpdateResponse = Record<string, unknown>;
export type PostApiV1ProjectsStrProjectIdUpdateResponse = Record<string, unknown>;
export type GetApiV1ProjectsStrProjectIdCoverResponse = Record<string, unknown>;
export type PostApiV1ProjectsStrProjectIdCoverResponse = Record<string, unknown>;
export type GetApiV1ProjectsStrProjectIdCoverPrintResponse = Record<string, unknown>;
export type PostApiV1ProjectsStrProjectIdCoverPrintResponse = Record<string, unknown>;
export type GetApiV1ProjectsStrProjectIdResearchersResponse = Record<string, unknown>;
export type PostApiV1ProjectsStrProjectIdResearchersResponse = Record<string, unknown>;
export type GetApiV1ProjectsStrProjectIdResearchersRemoveResponse = Record<string, unknown>;
export type PostApiV1ProjectsStrProjectIdResearchersRemoveResponse = Record<string, unknown>;
export type GetApiV1ProjectsStrProjectIdResearchNotesUploadResponse = Record<string, unknown>;
export type PostApiV1ProjectsStrProjectIdResearchNotesUploadResponse = Record<string, unknown>;
export type GetApiV1ProjectsStrProjectIdResearchNotesExportPdfResponse = Record<string, unknown>;
export type PostApiV1ProjectsStrProjectIdResearchNotesExportPdfResponse = Record<string, unknown>;
export type GetApiV1ResearchersResponse = Record<string, unknown>;
export type PostApiV1ResearchersResponse = Record<string, unknown>;
export type GetApiV1DataUpdatesResponse = Record<string, unknown>;
export type PostApiV1DataUpdatesResponse = Record<string, unknown>;
export type GetApiV1FinalDownloadResponse = Record<string, unknown>;
export type PostApiV1FinalDownloadResponse = Record<string, unknown>;
export type GetApiV1SignaturesResponse = Record<string, unknown>;
export type PostApiV1SignaturesResponse = Record<string, unknown>;
export type GetApiV1AdminTeamsResponse = Record<string, unknown>;
export type PostApiV1AdminTeamsResponse = Record<string, unknown>;
export type GetApiV1AdminUsersResponse = Record<string, unknown>;
export type PostApiV1AdminUsersResponse = Record<string, unknown>;
export type GetApiV1AdminTablesResponse = Record<string, unknown>;
export type PostApiV1AdminTablesResponse = Record<string, unknown>;
export type GetApiV1AdminTablesStrTableNameTruncateResponse = Record<string, unknown>;
export type PostApiV1AdminTablesStrTableNameTruncateResponse = Record<string, unknown>;
export type GetApiV1ResearchNotesResponse = Record<string, unknown>;
export type PostApiV1ResearchNotesResponse = Record<string, unknown>;
export type GetApiV1ResearchNotesStrNoteIdResponse = Record<string, unknown>;
export type PostApiV1ResearchNotesStrNoteIdResponse = Record<string, unknown>;
export type GetApiV1ResearchNotesStrNoteIdUpdateResponse = Record<string, unknown>;
export type PostApiV1ResearchNotesStrNoteIdUpdateResponse = Record<string, unknown>;
export type GetApiV1ResearchNotesStrNoteIdViewerExportPdfResponse = Record<string, unknown>;
export type PostApiV1ResearchNotesStrNoteIdViewerExportPdfResponse = Record<string, unknown>;
export type GetApiV1ResearchNotesStrNoteIdFilesStrFileIdUpdateResponse = Record<string, unknown>;
export type PostApiV1ResearchNotesStrNoteIdFilesStrFileIdUpdateResponse = Record<string, unknown>;
