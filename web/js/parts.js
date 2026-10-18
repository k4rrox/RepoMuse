// Building blocks shared by the project cards and the demo library.
import { element, link } from './dom.js';
import { timeLabel } from './format.js';
import { t } from './strings.js';

export function detailRow(label, text) {
  const row = element('div', 'detail-row');
  row.append(element('strong', '', label), element('p', '', text));
  return row;
}

export function labelled(className, label, text) {
  const node = element('p', className);
  node.append(element('strong', '', label), document.createTextNode(text));
  return node;
}

// A collapsed section with a rotating marker.
export function disclosure(label, content) {
  const details = element('details', 'project-detail');
  const summary = element('summary');
  summary.append(element('span', 'detail-toggle', '▸'), element('span', '', label));
  details.append(summary, content);
  return details;
}

export function techStack(label, stack) {
  const section = element('section', 'tech-stack');
  section.setAttribute('aria-label', label);
  section.append(element('strong', 'tech-stack-label', label));
  if (!stack?.items?.length) {
    section.append(element('span', 'tech-stack-missing', t('stack.missing')));
    return section;
  }
  const list = element('ul', 'tech-stack-items');
  for (const item of stack.items) {
    const chip = element('li', 'tech-stack-item');
    chip.append(element('span', 'tech-stack-name', item.name), element('span', 'tech-stack-role', item.role));
    list.append(chip);
  }
  section.append(list);
  return section;
}

export function techSources(label, stack) {
  if (!stack) return null;
  const row = element('div', 'detail-row');
  row.append(element('strong', '', label));
  const content = element('div');
  if (stack.note) content.append(element('p', 'tech-stack-note', stack.note));
  const list = element('ul', 'source-list');
  for (const source of stack.sources || []) {
    const item = element('li');
    item.append(link(source.label, source.url));
    list.append(item);
  }
  content.append(list, element('p', 'tech-stack-verified', t('stack.verified', { time: timeLabel(stack.verified_at) })));
  row.append(content);
  return row;
}
