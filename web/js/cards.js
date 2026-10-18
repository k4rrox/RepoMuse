// One project card in the picks feed.
import { demoLink, demoThumb } from './demos.js';
import { element, link } from './dom.js';
import { feedbackFooter } from './feedback.js';
import { starsText, timeLabel, topicLabel } from './format.js';
import { detailRow, disclosure, labelled, techSources, techStack } from './parts.js';
import { t } from './strings.js';

const DEMO_STATES = ['ready', 'blocked', 'failed'];

function metaLine(project) {
  const meta = element('p', 'project-meta');
  meta.append(element('span', '', topicLabel(project.topic)), element('span', '', t(`event.${project.event}`)));
  for (const tag of project.tags || []) meta.append(element('span', '', tag));
  const stars = starsText(project);
  const snapshot = element('span', 'stars', stars || t('stars.none'));
  snapshot.title = stars ? t('stars.title', { time: timeLabel(project.stars.observed_at) }) : t('stars.noSnapshot');
  meta.append(snapshot);
  return meta;
}

function demoBlock(demo) {
  const preview = element('section', `project-demo ${demo.status}`);
  const thumb = demoThumb(demo, preview);
  if (thumb) preview.append(thumb);
  const description = element('div', 'demo-description');
  description.append(element('span', 'demo-status', t(`demo.${demo.status}`)), element('strong', 'demo-title', demo.title),
    element('p', 'demo-summary', demo.summary));
  const actions = element('div', 'demo-actions');
  actions.append(demoLink(demo) || element('p', 'demo-evidence', t('demo.reason', { text: demo.evidence })));
  description.append(techStack(t('stack.demo'), demo.tech_stack), actions);
  preview.append(description);
  return preview;
}

function fact(label, value, note, valueClass = '') {
  const node = element('div', 'fact');
  node.append(element('dt', '', label), element('dd', valueClass, value), element('small', '', note));
  return node;
}

function facts(project) {
  const list = element('dl', 'facts');
  list.append(
    fact(t('fact.heat'), project.heat?.label || t('heat.none'), project.heat?.window || t('heat.windowNone')),
    fact(t('fact.license'), project.license.name, t(`license.${project.license.kind}`),
      project.license.kind !== 'open-source' ? 'source-available' : ''),
    fact(t('fact.effort'), t(`effort.${project.effort}`), project.platforms.join(' / ')));
  return list;
}

function sourceList(project) {
  const row = element('div', 'detail-row');
  row.append(element('strong', '', t('row.sources')));
  const list = element('ul', 'source-list');
  for (const source of project.sources) {
    const item = element('li');
    item.append(link(source.label, source.url));
    if (source.observed_at) {
      const time = element('time', '', timeLabel(source.observed_at));
      time.dateTime = source.observed_at;
      item.append(time);
    }
    list.append(item);
  }
  const license = element('li');
  license.append(link(project.license.kind === 'unverified' ? t('license.unverifiedSource') : t('license.text'), project.license.url));
  list.append(license);
  row.append(list);
  return row;
}

function detailBody(project) {
  const demo = project.demo;
  const body = element('div', 'detail-content');
  if (project.caution) body.append(element('p', 'caution', t('caution', { text: project.caution })));
  body.append(detailRow(t('row.useCase'), project.use_case), detailRow(t('row.requirements'), project.requirements),
    detailRow(t('row.assessment'), project.assessment));
  for (const row of [techSources(t('row.projectSources'), project.tech_stack), techSources(t('row.demoSources'), demo?.tech_stack)]) {
    if (row) body.append(row);
  }
  if (demo) {
    body.append(detailRow(t('row.demoEvidence'), demo.evidence), detailRow(t('row.demoLimits'), demo.limitations),
      detailRow(t('row.tested'), timeLabel(demo.tested_at)));
  }
  if (project.heat?.observed_at) {
    const note = project.heat.total_only ? t('heat.totalOnly') : '';
    body.append(detailRow(t('row.heat'), `${timeLabel(project.heat.observed_at)}${note}`));
  }
  body.append(sourceList(project));
  return body;
}

export function card(project, rerender) {
  const article = element('article', 'project-card');
  article.dataset.repo = project.repo;
  const head = element('header', 'project-head');
  head.append(link(project.name, `https://github.com/${project.repo}`, 'project-name'), element('span', 'repo-path', project.repo));
  if (project.explore) head.append(element('span', 'explore-note', t('explore')));
  head.append(element('span', `verdict ${project.verdict}`, t(`verdict.${project.verdict}`)));

  article.append(head, metaLine(project), element('h2', 'project-title', project.title),
    element('p', 'project-summary', project.summary), labelled('selection-reason', t('why'), project.reason));
  if (project.fit) article.append(labelled('selection-reason fit', t('fit'), project.fit));
  article.append(techStack(t('stack.project'), project.tech_stack));
  if (project.demo && DEMO_STATES.includes(project.demo.status)) article.append(demoBlock(project.demo));
  article.append(facts(project), disclosure(t('detail.toggle'), detailBody(project)), feedbackFooter(project, rerender));
  return article;
}
