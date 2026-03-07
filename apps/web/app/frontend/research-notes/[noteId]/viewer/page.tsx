import LegacyIframePage from '../../../_components/LegacyIframePage';

export default function ResearchNoteViewerPage({ params }: { params: { noteId: string } }) {
  return <LegacyIframePage path={`research-notes/${params.noteId}/viewer`} />;
}
