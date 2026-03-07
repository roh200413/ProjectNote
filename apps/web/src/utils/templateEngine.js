import { includeSources } from '../templates/templateSources';

function extractBlock(html, blockName) {
  const re = new RegExp(`{%\\s*block\\s+${blockName}\\s*%}([\\s\\S]*?){%\\s*endblock\\s*%}`, 'm');
  const match = html.match(re);
  return match ? match[1].trim() : '';
}

function extractBody(html) {
  const match = html.match(/<body[^>]*>([\s\S]*?)<\/body>/i);
  return match ? match[1].trim() : html;
}

function replaceIncludes(html) {
  return html.replace(/{%\s*include\s+"([^"]+)"\s*%}/g, (_, includePath) => includeSources[includePath] || '');
}

function stripTemplateTokens(html) {
  return html
    .replace(/{%\s*csrf_token\s*%}/g, '')
    .replace(/{%\s*(if|elif|else|endif|for|empty|endfor)\b[^%]*%}/g, '')
    .replace(/{%\s*url\s+[^%]*%}/g, '#')
    .replace(/{{\s*[^}]+\s*}}/g, '샘플')
    .replace(/{%\s*[^%]*%}/g, '');
}

export function parseTemplate(rawHtml) {
  const replaced = replaceIncludes(rawHtml);
  const isChild = replaced.includes('{% extends "base.html" %}') || replaced.includes('{% extends "base_admin.html" %}');

  if (!isChild) {
    return {
      type: 'standalone',
      title: '',
      pageTitle: '',
      actions: '',
      content: stripTemplateTokens(extractBody(replaced))
    };
  }

  const type = replaced.includes('{% extends "base_admin.html" %}') ? 'admin' : 'workflow';
  return {
    type,
    title: stripTemplateTokens(extractBlock(replaced, 'title')),
    pageTitle: stripTemplateTokens(extractBlock(replaced, 'page_title')),
    actions: stripTemplateTokens(extractBlock(replaced, 'page_actions')),
    content: stripTemplateTokens(extractBlock(replaced, 'content'))
  };
}
