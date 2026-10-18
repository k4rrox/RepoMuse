// Entry point: read the URL, wire the controls, load the data.
import { getJson } from './api.js';
import { $, status } from './dom.js';
import { loadVotes } from './feedback.js';
import { render, renderChrome, renderEditionPicker } from './render.js';
import { editions, readUrl, state } from './state.js';
import { setStrings, t } from './strings.js';

let requestId = 0;

function showLoadError(message) {
  status(message, true);
  if (state.data) return;  // keep showing what was already loaded
  $('feed-meta').textContent = t('meta.unavailable');
  $('empty').hidden = false;
  $('empty-title').textContent = t('empty.error');
  $('empty-message').textContent = t('empty.msg.error');
  $('empty-reset').hidden = true;
}

async function loadConfig() {
  try {
    const { strings, ...config } = await getJson('/api/config');
    state.config = config;
    setStrings(strings);
  } catch (error) {
    if (error.message === t('error.offline')) throw error;
    // An invalid repomuse.json still leaves a readable page with the English defaults.
  }
}

async function load() {
  const request = ++requestId;
  $('refresh').disabled = true;
  $('results').setAttribute('aria-busy', 'true');
  status('');
  try {
    await loadConfig();
    if (request !== requestId) return;
    renderChrome();
    const data = await getJson('/api/editions');
    if (request !== requestId) return;
    if (!Array.isArray(data.editions)) throw new Error(t('error.shape'));
    data.editions.sort((a, b) => b.day.localeCompare(a.day));
    state.data = data;
    await loadVotes(data);
    if (!data.editions.some(item => item.day === state.day)) state.day = data.editions[0]?.day || null;
    renderEditionPicker();
    render();
  } catch (error) {
    if (request === requestId) showLoadError(error.message);
  } finally {
    if (request === requestId) {
      $('refresh').disabled = false;
      $('results').setAttribute('aria-busy', 'false');
    }
  }
}

function selectDay(day) {
  state.day = day;
  $('edition').value = day;
  status('');
  render();
}

function resetFilters() {
  Object.assign(state, { topic: 'all', verdict: 'all', feedback: 'all', query: '' });
  $('search').value = '';
  status('');
  render();
}

function bindControls() {
  $('search').value = state.query;
  $('sort').value = state.sort;
  $('refresh').addEventListener('click', load);
  $('edition').addEventListener('change', () => selectDay($('edition').value));
  for (const [id, offset] of [['previous-day', 1], ['next-day', -1]]) {
    $(id).addEventListener('click', () => {
      const next = editions()[editions().findIndex(item => item.day === state.day) + offset];
      if (next) selectDay(next.day);
    });
  }
  $('search').addEventListener('input', () => { state.query = $('search').value; render(); });
  $('sort').addEventListener('change', () => { state.sort = $('sort').value; render(); });
  $('reset-filters').addEventListener('click', resetFilters);
  $('empty-reset').addEventListener('click', resetFilters);
}

readUrl(location.search);
bindControls();
load();
