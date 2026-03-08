import { useMemo } from 'react';
import { renderLegacyHtml } from '../utils/templateEngine';
import { templateSources } from '../templates/templateSources';

export default function LegacyTemplatePage({ source }) {
  const srcDoc = useMemo(() => renderLegacyHtml(templateSources[source] || ''), [source]);

  return (
    <iframe
      sandbox="allow-forms allow-modals allow-popups allow-same-origin allow-scripts"
      srcDoc={srcDoc}
      style={{ border: 'none', display: 'block', minHeight: '100vh', width: '100%' }}
      title={source}
    />
  );
}
