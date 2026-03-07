import { useMemo } from 'react';
import AdminShell from '../layouts/AdminShell';
import WorkflowShell from '../layouts/WorkflowShell';
import { templateSources } from '../templates/templateSources';
import { parseTemplate } from '../utils/templateEngine';

export default function LegacyTemplatePage({ source }) {
  const parsed = useMemo(() => parseTemplate(templateSources[source] || ''), [source]);

  if (parsed.type === 'workflow') {
    return (
      <WorkflowShell
        actionsHtml={parsed.actions}
        contentHtml={parsed.content}
        pageTitle={parsed.pageTitle || parsed.title}
      />
    );
  }

  if (parsed.type === 'admin') {
    return (
      <AdminShell
        actionsHtml={parsed.actions}
        contentHtml={parsed.content}
        pageTitle={parsed.pageTitle || parsed.title}
      />
    );
  }

  return <div dangerouslySetInnerHTML={{ __html: parsed.content }} />;
}
