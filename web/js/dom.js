// Small DOM helpers. Text always goes in through textContent, never innerHTML.

export const $ = id => document.getElementById(id);

export function element(tag, className = '', text = '') {
  const node = document.createElement(tag);
  node.className = className;
  node.textContent = text;
  return node;
}

const ICONS = { external: 'M8 2h4v4M12 2 6 8M5 2H2v10h10V9' };
const ICON_ATTRIBUTES = {
  viewBox: '0 0 14 14', fill: 'none', stroke: 'currentColor', 'stroke-width': '1.4', 'stroke-linecap': 'round',
  'stroke-linejoin': 'round', 'aria-hidden': 'true', class: 'icon',
};

export function icon(kind) {
  const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
  for (const [key, value] of Object.entries(ICON_ATTRIBUTES)) svg.setAttribute(key, value);
  const path = document.createElementNS(svg.namespaceURI, 'path');
  path.setAttribute('d', ICONS[kind]);
  svg.append(path);
  return svg;
}

// An external link, only ever to HTTPS; anything else renders as plain text.
export function link(text, url, className = '') {
  const node = element('a', className, text);
  try {
    const parsed = new URL(url);
    if (parsed.protocol !== 'https:') throw new Error('not https');
    node.href = parsed.href;
    node.target = '_blank';
    node.rel = 'noopener noreferrer';
  } catch {
    node.removeAttribute('href');
  }
  return node;
}

export function status(message, error = false) {
  const node = $('status');
  node.textContent = message;
  node.hidden = !message;
  node.classList.toggle('error', error);
}
