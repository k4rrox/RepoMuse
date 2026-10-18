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

export async function sendVote(repo, selected) {
  const response = await fetch('/api/feedback', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ repo, vote: selected || null }),
  });
  if (!response.ok) throw new Error(String(response.status));
}
