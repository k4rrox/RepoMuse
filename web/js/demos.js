// Demo links, covers and the demo library entries.
import { element, icon, link } from './dom.js';
import { timeLabel, topicLabel } from './format.js';
import { detailRow, disclosure, labelled, techSources, techStack } from './parts.js';
import { state } from './state.js';
import { t } from './strings.js';

const DEMO_PATH = /^\/demos\/[a-z0-9]+(?:-[a-z0-9]+)*\/$/;

export function demoPath(demo) {
  if (demo?.status !== 'ready' || typeof demo.path !== 'string' || !DEMO_PATH.test(demo.path)) return null;
  return demo.path;
}

// Demos are served from their own origin (the page port + 1) so they can never touch this page.
export function demoUrl(path) {
  const port = state.config.demo_port || Number(location.port || 80) + 1;
  return `${location.protocol}//${location.hostname}:${port}${path}`;
}

export function demoLink(demo, text = t('demo.open')) {
  const path = demoPath(demo);
  if (!path) return null;
  const node = element('a', 'demo-link', text);
  node.href = demoUrl(path);
  node.target = '_blank';
  node.rel = 'noopener noreferrer';
  node.setAttribute('aria-label', t('demo.openAria', { text, title: demo.title }));
  node.append(icon('external'));
  return node;
}

// A ready demo may ship cover.jpg or cover.png (served by this page's port); the block falls back to text.
export function demoThumb(demo, container) {
  const path = demoPath(demo);
  if (!path) {
    container.classList.add('no-cover');
    return null;
  }
  const anchor = element('a', 'demo-thumb');
  anchor.href = demoUrl(path);
  anchor.target = '_blank';
  anchor.rel = 'noopener noreferrer';
  anchor.tabIndex = -1;
  anchor.setAttribute('aria-hidden', 'true');
  const image = element('img');
  image.alt = '';
  image.loading = 'lazy';
  image.decoding = 'async';
  image.src = `${path}cover.jpg`;
  image.addEventListener('error', () => {
    if (image.src.endsWith('cover.jpg')) {
      image.src = `${path}cover.png`;
      return;
    }
    anchor.remove();
    container.classList.add('no-cover');
  });
  anchor.append(image);
  return anchor;
}

export function demoEntry(project) {
  const demo = project.demo;
  const article = element('article', `demo-entry ${demo.status}`);
  article.dataset.repo = project.repo;
  const thumb = demo.status === 'ready' ? demoThumb(demo, article) : null;
  if (thumb) article.append(thumb);
  else article.classList.add('no-cover');

  const body = element('div', 'demo-entry-body');
  const owner = element('p', 'demo-entry-project');
  owner.append(link(project.name, `https://github.com/${project.repo}`), document.createTextNode(`  ·  ${topicLabel(project.topic)}`));
  body.append(owner, element('h2', '', demo.title), element('p', 'demo-entry-summary', demo.summary),
    labelled('demo-entry-why', t('row.project'), project.title),
    techStack(t('stack.projectFull'), project.tech_stack), techStack(t('stack.demo'), demo.tech_stack));

  const actions = element('div', 'demo-actions');
  const entry = demoLink(demo);
  if (entry) actions.append(entry);
  const tested = t(demo.status === 'ready' ? 'demo.testedReady' : 'demo.testedOther', { time: timeLabel(demo.tested_at) });
  actions.append(element('span', 'demo-tested', tested));
  body.append(actions);
  if (demo.status !== 'ready') body.append(element('p', 'demo-evidence', t('demo.reason', { text: demo.evidence })));

  const detail = element('div', 'detail-content');
  detail.append(detailRow(t('row.verified'), demo.evidence), detailRow(t('row.limits'), demo.limitations));
  const sources = techSources(t('row.stackSources'), demo.tech_stack);
  if (sources) detail.append(sources);
  body.append(disclosure(t('demo.detail'), detail));
  article.append(body);
  return article;
}
