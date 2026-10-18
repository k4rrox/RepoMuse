// The "Not for me" panel: why a pick missed, in a few fixed reasons the agent can act on, plus free text.
// A popover under the button on desktop, a bottom sheet on phones (see app.css).
import { element } from './dom.js';
import { t } from './strings.js';

// Must match DISLIKE_REASONS in repomuse/schema.py (a test checks it).
export const DISLIKE_REASONS = ['off-topic', 'too-heavy', 'already-known', 'too-early', 'inaccurate'];
const NOTE_LIMIT = 200;

let open = null;  // { panel, backdrop, anchor, onKey, onPointer }

export function closeReasonPanel({ restoreFocus = true } = {}) {
  if (!open) return;
  const { panel, backdrop, anchor, onKey, onPointer } = open;
  open = null;
  document.removeEventListener('keydown', onKey, true);
  document.removeEventListener('pointerdown', onPointer, true);
  panel.remove();
  backdrop.remove();
  if (restoreFocus && anchor.isConnected) anchor.focus({ preventScroll: true });
}

function chip(label, pressed) {
  const button = element('button', 'reason-chip', label);
  button.type = 'button';
  button.setAttribute('aria-pressed', String(pressed));
  button.addEventListener('click', () => button.setAttribute('aria-pressed', String(button.getAttribute('aria-pressed') !== 'true')));
  return button;
}

function action(className, label, onClick) {
  const button = element('button', className, label);
  button.type = 'button';
  button.addEventListener('click', onClick);
  return button;
}

/**
 * Opens the panel next to `anchor`. `current` is { reasons: [], note: '' }.
 * onSave({ reasons, note }) and onUndo() are called once; closing any other way keeps the vote as it is.
 */
export function openReasonPanel(anchor, current, { name, onSave, onUndo }) {
  closeReasonPanel({ restoreFocus: false });
  const id = `reason-title-${Math.random().toString(36).slice(2, 8)}`;
  const panel = element('div', 'reason-panel');
  panel.setAttribute('role', 'dialog');
  panel.setAttribute('aria-labelledby', id);
  const title = element('p', 'reason-title', t('reasons.title'));
  title.id = id;
  const hint = element('p', 'reason-hint', t('reasons.hint', { name }));

  const chips = DISLIKE_REASONS.map(code => {
    const button = chip(t(`reason.${code}`), current.reasons.includes(code));
    button.dataset.reason = code;
    return button;
  });
  const other = chip(t('reason.other'), Boolean(current.note));
  const note = element('textarea', 'reason-note');
  note.maxLength = NOTE_LIMIT;
  note.rows = 2;
  note.value = current.note || '';
  note.placeholder = t('reasons.placeholder');
  note.setAttribute('aria-label', t('reasons.placeholder'));
  note.hidden = !current.note;
  other.addEventListener('click', () => {
    note.hidden = other.getAttribute('aria-pressed') !== 'true';
    if (!note.hidden) note.focus();
  });
  const list = element('div', 'reason-chips');
  list.setAttribute('role', 'group');
  list.setAttribute('aria-labelledby', id);
  list.append(...chips, other);

  const actions = element('div', 'reason-actions');
  const undo = action('text-button reason-undo', t('reasons.undo'), () => { closeReasonPanel({ restoreFocus: false }); onUndo(); });
  const skip = action('quiet-button', t('reasons.skip'), () => closeReasonPanel());
  const save = action('reason-save', t('reasons.save'), () => {
    const reasons = chips.filter(button => button.getAttribute('aria-pressed') === 'true').map(button => button.dataset.reason);
    const text = other.getAttribute('aria-pressed') === 'true' ? note.value.trim().slice(0, NOTE_LIMIT) : '';
    closeReasonPanel({ restoreFocus: false });
    onSave({ reasons, note: text });
  });
  actions.append(undo, skip, save);
  panel.append(title, hint, list, note, actions);

  // Phones show the panel as a sheet over a dimmed page; on desktop the backdrop is not displayed.
  const backdrop = element('div', 'reason-backdrop');
  backdrop.addEventListener('click', () => closeReasonPanel());
  const footer = anchor.closest('.project-footer') || anchor.parentElement;
  footer.append(panel);
  document.body.append(backdrop);

  const onKey = event => {
    if (event.key === 'Escape') {
      event.stopPropagation();
      closeReasonPanel();
    }
  };
  const onPointer = event => {
    if (!panel.contains(event.target) && !anchor.contains(event.target) && event.target !== backdrop) closeReasonPanel({ restoreFocus: false });
  };
  document.addEventListener('keydown', onKey, true);
  document.addEventListener('pointerdown', onPointer, true);
  open = { panel, backdrop, anchor, onKey, onPointer };
  panel.scrollIntoView({ block: 'nearest' });
  chips[0].focus({ preventScroll: true });
}
