// "Useful" / "Not for me": saved to the local server for the agent, cached in the browser while it is unreachable.
// "Not for me" is saved at once and then asks why (reasons.js); closing that panel keeps the vote.
import { getJson, sendVote } from './api.js';
import { element, icon, link, status } from './dom.js';
import { closeReasonPanel, openReasonPanel } from './reasons.js';
import { isSample, keepVisible, state, vote } from './state.js';
import { storageGet, storageSet } from './storage.js';
import { t } from './strings.js';

const SAMPLE_VOTES = 'repomuse-sample-feedback-v1';
const SAMPLE_REASONS = 'repomuse-sample-reasons-v1';
const PENDING_VOTES = 'repomuse-pending-feedback-v1';
const NO_DETAILS = { reasons: [], note: '' };

const details = repo => state.reasons[repo.toLowerCase()] || NO_DETAILS;

// Queued entries are { vote, reasons, note }; older queues stored just the vote string.
function queued(entry) {
  return typeof entry === 'string' ? { vote: entry, reasons: [], note: '' } : entry;
}

async function flushPending() {
  const pending = storageGet(PENDING_VOTES);
  for (const [repo, entry] of Object.entries(pending)) {
    const { vote: selected, reasons, note } = queued(entry);
    try {
      await sendVote(repo, selected, { reasons, note });
      delete pending[repo];
    } catch {
      break;
    }
  }
  storageSet(PENDING_VOTES, pending);
  return pending;
}

// Sample picks keep votes in this browser only; real picks sync anything queued offline, then read the server.
export async function loadVotes(data) {
  if (data.sample) {
    state.votes = storageGet(SAMPLE_VOTES);
    state.reasons = storageGet(SAMPLE_REASONS);
    return;
  }
  const pending = await flushPending();
  const saved = await getJson('/api/feedback').catch(() => ({ votes: {} }));
  const entries = Object.entries(saved.votes || {});
  state.votes = Object.fromEntries(entries.map(([repo, entry]) => [repo, entry.vote]));
  state.reasons = Object.fromEntries(entries.map(([repo, entry]) => [repo, { reasons: entry.reasons || [], note: entry.note || '' }]));
  for (const [repo, entry] of Object.entries(pending)) {
    const { vote: selected, reasons, note } = queued(entry);
    if (selected) state.votes[repo] = selected;
    else delete state.votes[repo];
    state.reasons[repo] = { reasons: reasons || [], note: note || '' };
  }
}

// Returns [message, isError] for the status line.
async function saveVote(project, selected, extra = NO_DETAILS, savedMessage = 'feedback.saved') {
  const key = project.repo.toLowerCase();
  keepVisible(key);
  if (selected) state.votes[key] = selected;
  else delete state.votes[key];
  state.reasons[key] = selected === 'dislike' ? extra : NO_DETAILS;
  if (isSample()) {
    storageSet(SAMPLE_VOTES, state.votes);
    storageSet(SAMPLE_REASONS, state.reasons);
    return [t('feedback.sample'), false];
  }
  try {
    await sendVote(key, selected, extra);
    return [t(savedMessage), false];
  } catch {
    const pending = storageGet(PENDING_VOTES);
    pending[key] = { vote: selected || '', reasons: extra.reasons, note: extra.note };
    storageSet(PENDING_VOTES, pending);
    return [t('feedback.failed'), true];
  }
}

function findButton(project, key) {
  return [...document.querySelectorAll('[data-repo]')].find(node => node.dataset.repo === project.repo)
    ?.querySelector(`[data-feedback="${key}"]`);
}

// After a re-render the card is new; put focus back on the same button.
async function apply(project, key, selected, extra, rerender, savedMessage) {
  const result = await saveVote(project, selected, extra, savedMessage);
  rerender();
  status(...result);
  findButton(project, key)?.focus({ preventScroll: true });
}

function askWhy(project, rerender) {
  const anchor = findButton(project, 'dislike');
  if (!anchor) return;
  openReasonPanel(anchor, details(project.repo), {
    name: project.name,
    onSave: extra => apply(project, 'dislike', 'dislike', extra, rerender, 'reasons.saved'),
    onUndo: () => apply(project, 'dislike', '', NO_DETAILS, rerender),
  });
}

function voteButton(project, key, rerender) {
  const label = t(`feedback.${key}`);
  const active = vote(project) === key;
  const button = element('button', `feedback-button${active ? ' active' : ''}`, label);
  button.type = 'button';
  button.dataset.feedback = key;
  button.setAttribute('aria-pressed', String(active));
  button.setAttribute('aria-label', `${project.name}: ${label}`);
  if (key === 'dislike') button.setAttribute('aria-haspopup', 'dialog');
  button.addEventListener('click', async () => {
    closeReasonPanel({ restoreFocus: false });
    if (key === 'like') {
      await apply(project, key, vote(project) === 'like' ? '' : 'like', NO_DETAILS, rerender);
    } else if (vote(project) === 'dislike') {
      askWhy(project, rerender);  // already "not for me": edit the reasons
    } else {
      await apply(project, key, 'dislike', NO_DETAILS, rerender);
      askWhy(project, rerender);
    }
  });
  return button;
}

// "Too heavy to try · Other: needs a GPU" under the buttons once reasons are saved.
function reasonSummary(project) {
  if (vote(project) !== 'dislike') return null;
  const { reasons, note } = details(project.repo);
  const parts = [...reasons.map(code => t(`reason.${code}`)), ...(note ? [t('reasons.other', { text: note })] : [])];
  return parts.length ? element('span', 'feedback-reasons', parts.join(' · ')) : null;
}

function copyButton(project) {
  const copy = element('button', 'copy-button', t('copy'));
  copy.type = 'button';
  copy.setAttribute('aria-label', t('copy.aria', { name: project.name }));
  copy.addEventListener('click', async () => {
    try {
      await navigator.clipboard.writeText(`https://github.com/${project.repo}`);
      copy.textContent = t('copied');
      status(t('copy.done', { name: project.name }));
      setTimeout(() => { copy.textContent = t('copy'); }, 1800);
    } catch {
      status(t('copy.failed'), true);
    }
  });
  return copy;
}

export function feedbackFooter(project, rerender) {
  const footer = element('footer', 'project-footer');
  const feedback = element('div', 'feedback-buttons');
  feedback.append(voteButton(project, 'like', rerender), voteButton(project, 'dislike', rerender));
  const summary = reasonSummary(project);
  if (summary) feedback.append(summary);
  const actions = element('div', 'card-actions');
  const repoLink = link('GitHub', `https://github.com/${project.repo}`, 'repo-link');
  repoLink.append(icon('external'));
  actions.append(copyButton(project), repoLink);
  footer.append(feedback, actions);
  return footer;
}
