// Display formatting for dates, times, stars and topics, following the configured language and timezone.
import { state } from './state.js';
import { t } from './strings.js';

export function intlLocale() {
  try {
    return Intl.getCanonicalLocales(state.config.language)[0];
  } catch {
    return 'en-US';
  }
}

export function dayLabel(day) {
  const date = new Date(`${day}T12:00:00Z`);
  if (Number.isNaN(date.valueOf())) return day;
  return new Intl.DateTimeFormat(intlLocale(), { timeZone: 'UTC', year: 'numeric', month: 'long', day: 'numeric' }).format(date);
}

export function shortDay(day) {
  const date = new Date(`${day}T12:00:00Z`);
  if (!/^\d{4}-\d{2}-\d{2}$/.test(day || '') || Number.isNaN(date.valueOf())) return day;
  return new Intl.DateTimeFormat(intlLocale(), { timeZone: 'UTC', month: 'short', day: 'numeric' }).format(date);
}

export function timeLabel(value) {
  const date = new Date(value);
  if (Number.isNaN(date.valueOf())) return t('time.missing');
  const options = { timeZone: state.config.timezone, month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', hourCycle: 'h23' };
  try {
    return new Intl.DateTimeFormat(intlLocale(), options).format(date);
  } catch {
    return date.toISOString().slice(0, 16).replace('T', ' ');
  }
}

export function topicLabel(id) {
  const topic = state.config.topics.find(item => item.id === id);
  return topic ? topic.label : id;
}

// Grouped like the chat digest (1,234), whatever the language.
export function starsText(project) {
  if (!Number.isInteger(project.stars?.count)) return null;
  const n = new Intl.NumberFormat('en-US').format(project.stars.count);
  return t('stars.count', { approx: project.stars.approximate ? t('stars.approx') : '', n });
}
