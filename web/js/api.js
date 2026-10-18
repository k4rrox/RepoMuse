// Talking to the local server.
import { t } from './strings.js';

// Tell "the server is gone" apart from "the data is wrong", so a stopped ./run.sh never looks like a frozen page.
export async function getJson(url) {
  let response;
  try {
    response = await fetch(url, { cache: 'no-store' });
  } catch {
    throw new Error(t('error.offline'));
  }
  if (response.status === 422) {
    const detail = await response.json().then(body => body.error || '').catch(() => '');
    throw new Error(t('error.data', { detail }));
  }
  if (!response.ok) throw new Error(t('error.load'));
  return response.json();
}

// `extra` is { reasons, note } for a "not for me"; reasons are codes from reasons.js.
export async function sendVote(repo, selected, extra = {}) {
  const body = { repo, vote: selected || null };
  if (selected === 'dislike' && extra.reasons?.length) body.reasons = extra.reasons;
  if (selected === 'dislike' && extra.note) body.note = extra.note;
  const response = await fetch('/api/feedback', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!response.ok) throw new Error(String(response.status));
}
