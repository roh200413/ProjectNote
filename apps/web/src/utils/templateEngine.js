import { templateSources, includeSources } from '../templates/templateSources';

function replaceIncludes(html) {
  let output = html;
  let previous = '';
  while (output !== previous) {
    previous = output;
    output = output.replace(/{%\s*include\s+["']([^"']+)["']\s*%}/g, (_, includePath) => includeSources[includePath] || '');
  }
  return output;
}

function extractBlocks(html) {
  const blocks = {};
  html.replace(/{%\s*block\s+(\w+)\s*%}([\s\S]*?){%\s*endblock\s*%}/g, (_, name, content) => {
    blocks[name] = content;
    return '';
  });
  return blocks;
}

function mergeWithBase(baseHtml, childBlocks) {
  return baseHtml.replace(/{%\s*block\s+(\w+)\s*%}([\s\S]*?){%\s*endblock\s*%}/g, (_, name, fallback) => {
    return childBlocks[name] ?? fallback;
  });
}

function collapseControlTags(html) {
  let output = html;

  output = output.replace(
    /{%\s*for\b[^%]*%}([\s\S]*?)(?:{%\s*empty\s*%}([\s\S]*?))?{%\s*endfor\s*%}/g,
    (_, loopBody) => `${loopBody}${loopBody}`
  );

  output = output.replace(
    /{%\s*if\b[^%]*%}([\s\S]*?)(?:{%\s*else\s*%}([\s\S]*?))?{%\s*endif\s*%}/g,
    (_, ifBody) => ifBody
  );

  output = output.replace(/{%\s*(elif|empty|else|endif|endfor)\b[^%]*%}/g, '');
  return output;
}

function replaceVariables(html) {
  const mapping = [
    ['current_user.name', '홍길동'],
    ['current_user.role', '관리자'],
    ['summary.teams', '12'],
    ['summary.researchers', '48'],
    ['summary.notes', '230'],
    ['p.name', '샘플 프로젝트'],
    ['p.status', 'active'],
    ['p.manager', '홍길동'],
    ['p.organization', '딥아이'],
    ['p.id', 'a1b2c3d4-e5f6-7890-abcd-1234567890ef'],
    ['error', '']
  ];

  return html.replace(/{{\s*([^}]+)\s*}}/g, (_, exprRaw) => {
    const expr = exprRaw.trim();
    const found = mapping.find(([key]) => expr.includes(key));
    if (found) return found[1];
    if (expr.includes('default')) return '미지정';
    return '샘플';
  });
}

function stripRemainingTags(html) {
  return html
    .replace(/{%\s*csrf_token\s*%}/g, '')
    .replace(/{%\s*url\s+[^%]*%}/g, '#')
    .replace(/{%\s*[^%]*%}/g, '');
}

function composeTemplate(rawHtml) {
  const child = replaceIncludes(rawHtml);
  const extendMatch = child.match(/{%\s*extends\s+["']([^"']+)["']\s*%}/);
  if (!extendMatch) return child;

  const extendsPath = extendMatch[1];
  const baseKey = `client/${extendsPath}`;
  const baseRaw = templateSources[baseKey] || '';
  const base = replaceIncludes(baseRaw);
  const blocks = extractBlocks(child);
  return mergeWithBase(base, blocks);
}

export function renderLegacyHtml(rawHtml) {
  const composed = composeTemplate(rawHtml);
  const withIncludes = replaceIncludes(composed);
  const collapsed = collapseControlTags(withIncludes);
  const replaced = replaceVariables(collapsed);
  return stripRemainingTags(replaced);
}
