import LegacyIframePage from '../../../_components/LegacyIframePage';

export default function ProjectResearchNotesPage({ params }: { params: { projectId: string } }) {
  return <LegacyIframePage path={`projects/${params.projectId}/research-notes`} />;
}
