// Drawing the page from the state. render() is the only entry point; everything else here is a piece of it.
import { card } from './cards.js';
import { demoEntry } from './demos.js';
import { $, element } from './dom.js';
import { dayLabel, shortDay, timeLabel, topicLabel } from './format.js';
import {
  FEEDBACK_KEYS, VERDICT_KEYS, demoLibrary, editions, feedbackMatches, hasFilters, isSample, projects, selectedEdition,
  selection, state, urlFor,
} from './state.js';
import { t, tn } from './strings.js';

const DEMO_GROUPS = ['ready', 'blocked', 'failed'];

function filterButtons(id, options, selected, count, onSelect) {
  $(id).replaceChildren(...options.map(([key, label]) => {
    const total = count(key);
    const button = element('button', `filter-button${key === selected ? ' selected' : ''}${total ? '' : ' empty'}`);
    button.type = 'button';
    button.setAttribute('aria-pressed', String(key === selected));
    button.append(element('span', '', label), element('span', 'filter-count', String(total)));
    button.addEventListener('click', () => {
      onSelect(key);
      render();
    });
    return button;
  }));
}

function renderFilters(all, { topicIds, inTopic, inVerdict }) {
  filterButtons('topics', [['all', t('topic.all')], ...topicIds.map(id => [id, topicLabel(id)])], state.topic,
    key => all.filter(project => key === 'all' || project.topic === key).length, key => { state.topic = key; });
  filterButtons('verdicts', [['all', t('verdict.all')], ...VERDICT_KEYS.map(key => [key, t(`verdict.${key}`)])], state.verdict,
    key => inTopic.filter(project => key === 'all' || project.verdict === key).length, key => { state.verdict = key; });
  filterButtons('feedbacks', FEEDBACK_KEYS.map(key => [key, t(`feedback.${key}`)]), state.feedback,
    key => inVerdict.filter(project => feedbackMatches(project, key)).length, key => { state.feedback = key; });
}

function renderResults(visible) {
  if (state.view !== 'demos') {
    $('results').replaceChildren(...visible.map(project => card(project, render)));
    return;
  }
  const nodes = [];
  for (const key of DEMO_GROUPS) {
    const group = visible.filter(project => project.demo.status === key);
    if (group.length) nodes.push(element('h2', 'demo-group-heading', `${t(`group.${key}`)}  ${group.length}`), ...group.map(demoEntry));
  }
  $('results').replaceChildren(...nodes);
}

function renderEmpty(all, visible, filtered) {
  const demos = state.view === 'demos';
  $('empty').hidden = visible.length > 0;
  $('reset-filters').hidden = !filtered;
  $('empty-reset').hidden = !filtered;
  $('empty-title').textContent = all.length ? t(demos ? 'empty.nomatch.demos' : 'empty.nomatch') : t(demos ? 'empty.none.demos' : 'empty.none');
  $('empty-message').textContent = all.length ? t('empty.msg.nomatch') : t(demos ? 'empty.msg.demos' : 'empty.msg.none');
}

function renderSummary(all, readyCount, filtered) {
  const edition = selectedEdition();
  if (state.view === 'demos') {
    $('intro').textContent = all.length ? tn('demos.intro', readyCount) : t('empty.msg.demos');
    $('edition-label').textContent = t('demos.label');
    $('feed-meta').textContent = tn('demos.count', all.length);
  } else if (edition) {
    const withDemo = all.filter(project => project.demo?.status === 'ready').length;
    $('page-heading').textContent = t('heading.edition', { day: shortDay(edition.day) });
    $('intro').textContent = all.length
      ? tn('edition.intro', all.length, { withDemo: withDemo ? t('edition.withDemo', { n: withDemo }) : '' })
      : t('edition.empty');
    $('edition-label').textContent = t('edition.label', {
      day: dayLabel(edition.day), kind: t(isSample() ? 'edition.sample' : 'edition.live'),
      time: timeLabel(edition.updated_at), tz: state.config.timezone,
    });
    $('feed-meta').textContent = t(filtered ? 'meta.filtered' : 'meta.editorial');
  } else {
    $('feed-meta').textContent = t('meta.none');
  }
}

function renderPaging() {
  const index = editions().findIndex(item => item.day === state.day);
  $('previous-day').disabled = index < 0 || index === editions().length - 1;
  $('next-day').disabled = index <= 0;
}

export function render() {
  const all = projects();
  const picked = selection(all);
  const filtered = hasFilters();
  const readyCount = demoLibrary().filter(project => project.demo.status === 'ready').length;
  renderFilters(all, picked);
  $('result-count').textContent = picked.visible.length;
  $('shown-count').textContent = picked.visible.length === all.length ? '' : t('shown', { n: picked.visible.length, total: all.length });
  $('nav-demo-count').textContent = readyCount ? String(readyCount) : '';
  renderResults(picked.visible);
  renderEmpty(all, picked.visible, filtered);
  renderSummary(all, readyCount, filtered);
  renderPaging();
  $('demo-banner').hidden = !isSample();
  history.replaceState(null, '', urlFor());
}

// Static text, title and navigation; runs once the settings and translations are known.
export function renderChrome() {
  const demos = state.view === 'demos';
  document.documentElement.lang = state.config.language;
  for (const node of document.querySelectorAll('[data-text]')) node.textContent = t(node.dataset.text);
  for (const node of document.querySelectorAll('[data-text-aria]')) node.setAttribute('aria-label', t(node.dataset.textAria));
  $('site-title').textContent = state.config.title;
  $('side-note').textContent = t('side.note', { tz: state.config.timezone });
  document.title = t(demos ? 'title.demos' : 'title.picks', { title: state.config.title });
  $('search').placeholder = t(demos ? 'search.demos' : 'search.picks');
  $('search').setAttribute('aria-label', t('search.label'));
  document.querySelector('.skip-link').textContent = t(demos ? 'skip.demos' : 'skip.picks');
  if (demos) {
    $('date-panel').hidden = true;
    $('page-heading').textContent = t('heading.demos');
    $('nav-daily').removeAttribute('aria-current');
    $('nav-demos').setAttribute('aria-current', 'page');
  }
}

export function renderEditionPicker() {
  const list = editions();
  const options = list.map(item => {
    const option = element('option', '', shortDay(item.day));
    option.value = item.day;
    return option;
  });
  if (!list.length) {
    const option = element('option', '', t('editions.none'));
    option.value = '';
    options.push(option);
  }
  $('edition').replaceChildren(...options);
  $('edition').disabled = state.view === 'demos' || !list.length;
  $('edition').value = state.day || '';
}
