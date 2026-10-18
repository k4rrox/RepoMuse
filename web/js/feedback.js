// "Useful" / "Not for me": saved to the local server for the agent, cached in the browser while it is unreachable.
import { getJson, sendVote } from './api.js';
import { element, icon, link, status } from './dom.js';
import { isSample, state, vote } from './state.js';
import { storageGet, storageSet } from './storage.js';
import { t } from './strings.js';

const SAMPLE_VOTES = 'repomuse-sample-feedback-v1';
const PENDING_VOTES = 'repomuse-pending-feedback-v1';

async function flushPending() {
  const pending = storageGet(PENDING_VOTES);
  for (const [repo, selected] of Object.entries(pending)) {
    try {
      await sendVote(repo, selected);
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
    return;
  }
  const pending = await flushPending();
  const saved = await getJson('/api/feedback').catch(() => ({ votes: {} }));
  state.votes = Object.fromEntries(Object.entries(saved.votes || {}).map(([repo, entry]) => [repo, entry.vote]));
  for (const [repo, selected] of Object.entries(pending)) {
    if (selected) state.votes[repo] = selected;
    else delete state.votes[repo];
  }
}

// Returns [message, isError] for the status line.
async function saveVote(project, selected) {
  const key = project.repo.toLowerCase();
  if (selected) state.votes[key] = selected;
  else delete state.votes[key];
  if (isSample()) {
    storageSet(SAMPLE_VOTES, state.votes);
    return [t('feedback.sample'), false];
  }
  try {
    await sendVote(key, selected);
    return [t('feedback.saved'), false];
  } catch {
    const pending = storageGet(PENDING_VOTES);
    pending[key] = selected || '';
    storageSet(PENDING_VOTES, pending);
    return [t('feedback.failed'), true];
  }
}

function voteButton(project, key, rerender) {
  const label = t(`feedback.${key}`);
  const active = vote(project) === key;
  const button = element('button', `feedback-button${active ? ' active' : ''}`, label);
  button.type = 'button';
  button.dataset.feedback = key;
  button.setAttribute('aria-pressed', String(active));
  button.setAttribute('aria-label', `${project.name}: ${label}`);
  button.addEventListener('click', async () => {
    const result = await saveVote(project, vote(project) === key ? '' : key);
    rerender();
    status(...result);
    // The card was re-rendered; put focus back on the same button.
    [...document.querySelectorAll('[data-repo]')].find(node => node.dataset.repo === project.repo)
      ?.querySelector(`[data-feedback="${key}"]`)?.focus({ preventScroll: true });
  });
  return button;
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
  const actions = element('div', 'card-actions');
  const repoLink = link('GitHub', `https://github.com/${project.repo}`, 'repo-link');
  repoLink.append(icon('external'));
  actions.append(copyButton(project), repoLink);
  footer.append(feedback, actions);
  return footer;
}
