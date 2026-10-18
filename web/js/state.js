// The page's single store and everything that can be computed from it without touching the DOM.

export const VERDICT_KEYS = ['try', 'watch', 'observe'];
export const FEEDBACK_KEYS = ['all', 'like', 'dislike', 'unread'];
export const SORT_KEYS = ['editorial', 'easy', 'name'];
const EFFORT_ORDER = { low: 0, medium: 1, high: 2 };

export const state = {
  config: { title: 'RepoMuse', language: 'en', timezone: 'UTC', topics: [], sample: true },
  data: null,
  votes: {},  // repo -> 'like' | 'dislike'
  reasons: {},  // repo -> { reasons: [codes], note } for a dislike
  // Picks rated since the filters last changed stay listed, so a card never vanishes under the pointer
  // (and the "Not for me" panel has a card to open on). Any filter, search, sort or edition change clears it.
  kept: new Set(),
  // Filters, mirrored in the URL so a view can be shared or reloaded.
  view: 'daily', day: null, topic: 'all', verdict: 'all', feedback: 'all', query: '', sort: 'editorial',
};

export function readUrl(search) {
  const params = new URLSearchParams(search);
  const pick = (name, allowed, fallback) => (allowed.includes(params.get(name)) ? params.get(name) : fallback);
  state.view = params.get('view') === 'demos' ? 'demos' : 'daily';
  state.day = params.get('day');
  state.topic = params.get('topic') || 'all';  // checked against the data in selection()
  state.verdict = pick('verdict', VERDICT_KEYS, 'all');
  state.feedback = pick('feedback', FEEDBACK_KEYS, 'all');
  state.query = params.get('q') || '';
  state.sort = pick('sort', SORT_KEYS, 'editorial');
}

export function urlFor() {
  const next = new URLSearchParams();
  if (state.view === 'demos') next.set('view', 'demos');
  const values = [['day', state.view === 'demos' ? null : state.day], ['topic', state.topic], ['verdict', state.verdict],
    ['feedback', state.feedback], ['q', state.query], ['sort', state.sort]];
  for (const [key, value] of values) {
    if (value && value !== 'all' && value !== 'editorial') next.set(key, value);
  }
  return `/${next.size ? `?${next}` : ''}`;
}

export const editions = () => state.data?.editions || [];
export const selectedEdition = () => editions().find(item => item.day === state.day);
export const isSample = () => Boolean(state.data?.sample);
export const vote = project => state.votes[project.repo.toLowerCase()] || '';

// Across all editions, the most recently tested demo of each repository, newest first.
export function demoLibrary() {
  const latest = new Map();
  for (const edition of editions()) {
    for (const project of edition.projects) {
      if (!project.demo) continue;
      const key = project.repo.toLowerCase();
      const previous = latest.get(key);
      if (!previous || Date.parse(project.demo.tested_at) > Date.parse(previous.demo.tested_at)) latest.set(key, project);
    }
  }
  return [...latest.values()].sort((a, b) => Date.parse(b.demo.tested_at) - Date.parse(a.demo.tested_at));
}

export function projects() {
  return state.view === 'demos' ? demoLibrary() : selectedEdition()?.projects || [];
}

export function feedbackMatches(project, key) {
  if (key === 'all') return true;
  return key === 'unread' ? !vote(project) : vote(project) === key;
}

export function keepVisible(repo) {
  state.kept.add(repo.toLowerCase());
}

export function forgetKept() {
  state.kept.clear();
}

export function hasFilters() {
  return state.topic !== 'all' || state.verdict !== 'all' || state.feedback !== 'all' || Boolean(state.query.trim());
}

// Configured topics first, then any older topic id still present in the data.
export function topicIds(all) {
  const ids = [...state.config.topics.map(topic => topic.id), ...all.map(project => project.topic)];
  return ids.filter((id, index) => ids.indexOf(id) === index);
}

function searchText(project) {
  const stacks = [...(project.tech_stack?.items || []), ...(project.demo?.tech_stack?.items || [])];
  return [project.name, project.repo, project.title, project.summary, project.reason, project.fit, project.use_case,
    project.requirements, project.demo?.title, project.demo?.summary, ...(project.tags || []),
    ...stacks.flatMap(item => [item.name, item.role])].join(' ').toLocaleLowerCase();
}

// What the feed shows after topic, verdict, feedback, search and sort, plus the intermediate sets the filter counts use.
export function selection(all) {
  const ids = topicIds(all);
  if (state.topic !== 'all' && !ids.includes(state.topic)) state.topic = 'all';
  const inTopic = all.filter(project => state.topic === 'all' || project.topic === state.topic);
  const inVerdict = inTopic.filter(project => state.verdict === 'all' || project.verdict === state.verdict);
  const needle = state.query.trim().toLocaleLowerCase();
  let visible = inVerdict.filter(project => feedbackMatches(project, state.feedback) || state.kept.has(project.repo.toLowerCase()))
    .filter(project => !needle || searchText(project).includes(needle));
  if (state.sort === 'name') visible = [...visible].sort((a, b) => a.name.localeCompare(b.name));
  if (state.sort === 'easy') visible = [...visible].sort((a, b) => EFFORT_ORDER[a.effort] - EFFORT_ORDER[b.effort]);
  return { topicIds: ids, inTopic, inVerdict, visible };
}
