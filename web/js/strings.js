// Interface copy, in English. When repomuse.json sets another language, the agent translates this object into
// strings.json (same keys) in the checkout root; /api/config serves it and setStrings() applies it.
// repomuse/digest.py reuses some of these keys for the chat digest, and a test keeps both in step.
export const STRINGS = {
  'nav.picks': 'Picks', 'nav.demos': 'Demos', 'local': 'Runs on this machine only',
  'skip.picks': 'Skip to picks', 'skip.demos': 'Skip to demos',
  'side.edition': 'Edition', 'side.topic': 'Topic', 'side.verdict': 'Verdict', 'side.feedback': 'My feedback',
  'side.note': 'Picked for your profile, not ranked by stars. Times are shown in {tz}.',
  'previous': 'Previous edition', 'next': 'Next edition',
  'heading.picks': 'Picks', 'heading.edition': 'Picks for {day}', 'heading.demos': 'Demos', 'refresh': 'Refresh',
  'intro.default': 'GitHub projects your agent picked for you. Try the ones that catch your eye.',
  'banner.title': 'Sample picks',
  'banner.text': 'These ship with RepoMuse and were not picked for you. Your first edition from repomuse-run replaces them.',
  'search.label': 'Search', 'search.picks': 'Search projects, uses or tech', 'search.demos': 'Search projects, demos or tech',
  'sort.label': 'Sort', 'sort.editorial': "Editor's order", 'sort.easy': 'Easiest first', 'sort.name': 'Name',
  'reset': 'Clear filters', 'meta.loading': 'Loading picks…',
  'empty.nomatch': 'No matching picks', 'empty.nomatch.demos': 'No matching demos',
  'empty.none': 'No picks in this edition', 'empty.none.demos': 'No demos yet',
  'empty.msg.nomatch': 'Try another topic, or clear the search.',
  'empty.msg.none': 'Only worthwhile projects get picked, and this edition had none. Try another edition.',
  'empty.msg.demos': 'Demos appear here once your agent has built and verified them.',
  'footer': 'Picks are never padded to hit a number. Heat figures hold only for their stated source and time.',
  'noscript': 'Turn on JavaScript to load the picks and use the filters.',
  'topic.all': 'All topics', 'verdict.all': 'All verdicts',
  'verdict.try': 'Worth trying', 'verdict.watch': 'Watch closely', 'verdict.observe': 'Keep an eye on',
  'effort.low': 'Low, try it right away', 'effort.medium': 'Medium, needs setup', 'effort.high': 'High, needs a lab setup',
  'event.new': 'New', 'event.update': 'Major update', 'event.demo': 'Demo added',
  'feedback.all': 'All', 'feedback.like': 'Useful', 'feedback.dislike': 'Not for me', 'feedback.unread': 'Not rated',
  'demo.ready': 'Verified demo', 'demo.blocked': 'Demo not ready', 'demo.failed': 'Demo failed verification',
  'group.ready': 'Ready to open', 'group.blocked': 'Not ready', 'group.failed': 'Failed verification',
  'stack.missing': 'Not verified yet', 'stack.verified': 'Verified {time}',
  'stack.project': 'Core stack', 'stack.projectFull': 'Project stack', 'stack.demo': 'Demo stack',
  'demo.open': 'Open demo', 'demo.openAria': '{text}: {title} (new tab)', 'demo.reason': 'Reason: {text}',
  'demo.testedReady': 'Verified {time}', 'demo.testedOther': 'Recorded {time}', 'demo.detail': 'What was and was not verified',
  'caution': 'Heads-up: {text}',
  'row.useCase': 'Use case', 'row.requirements': 'Requirements', 'row.assessment': 'Assessment',
  'row.projectSources': 'Stack sources', 'row.demoSources': 'Demo stack sources', 'row.demoEvidence': 'Demo evidence',
  'row.demoLimits': 'Demo limits', 'row.tested': 'Tested', 'row.heat': 'Heat observed', 'row.sources': 'Sources',
  'row.verified': 'Verified', 'row.limits': 'Limits', 'row.stackSources': 'Stack sources', 'row.project': 'Project',
  'heat.totalOnly': '; cumulative snapshot, not a growth rate',
  'license.text': 'License text', 'license.unverifiedSource': 'License not verified (source)',
  'detail.toggle': 'Use case, requirements and sources',
  'stars.count': '{approx}{n} stars', 'stars.approx': '~', 'stars.none': 'Stars not recorded',
  'stars.title': 'Total stars when collected at {time}; not a daily or weekly gain.', 'stars.noSnapshot': 'No snapshot saved',
  'feedback.saved': 'Saved. Your agent will take it into account next run.',
  'feedback.sample': 'Feedback on sample picks stays in this browser.',
  'feedback.failed': 'Could not reach the local server. Kept in this browser and synced next time.',
  'copy': 'Copy link', 'copied': 'Copied', 'copy.aria': 'Copy the {name} repository link', 'copy.done': '{name} link copied.',
  'copy.failed': 'Copy failed. Right-click the GitHub link instead.',
  'why': 'Why now', 'fit': 'Why for you', 'explore': 'Outside your profile',
  'fact.heat': 'Heat', 'heat.none': 'No verified growth data', 'heat.windowNone': 'Growth is never inferred from total stars',
  'fact.license': 'License', 'license.open-source': 'Open source; the license text governs',
  'license.source-available': 'Source available, with restrictions', 'license.unverified': 'Not verified; not treated as open source',
  'fact.effort': 'Effort',
  'shown': 'Showing {n} of {total}',
  'demos.intro': '{n} small experiments that run real upstream code. Each one says what was and was not verified.',
  'demos.intro.one': 'One small experiment that runs real upstream code. It says what was and was not verified.',
  'demos.label': 'Across all editions, latest verification per project', 'demos.count': '{n} projects', 'demos.count.one': '1 project',
  'edition.intro': '{n} picks{withDemo}.', 'edition.intro.one': 'One pick{withDemo}.', 'edition.withDemo': ', {n} with a demo you can open',
  'edition.empty': 'Nothing in this edition was worth picking.',
  'edition.label': '{day} · {kind} {time} ({tz})', 'edition.sample': 'Sample, recorded', 'edition.live': 'Updated',
  'meta.editorial': "In editor's order", 'meta.filtered': 'Filtered', 'meta.none': 'No picks yet',
  'editions.none': 'No editions',
  'error.load': 'Could not load the picks. Check the local server and data, then refresh.', 'error.shape': 'The data has no editions field.',
  'error.offline': 'The local RepoMuse server is not running. Start it with ./run.sh, then press Refresh.',
  'error.data': 'The picks data did not validate: {detail}',
  'meta.unavailable': 'Data unavailable', 'empty.error': 'Cannot load the picks', 'empty.msg.error': 'Make sure the local server is running, then press Refresh.',
  'time.missing': 'No time given',
  'title.picks': 'Picks · {title}', 'title.demos': 'Demos · {title}',
};

let overrides = {};

export function setStrings(translated) {
  overrides = translated || {};
}

export function t(key, vars = {}) {
  const template = overrides[key] ?? STRINGS[key] ?? key;
  return template.replace(/\{(\w+)\}/g, (_, name) => (name in vars ? String(vars[name]) : `{${name}}`));
}

// Singular wording when a `<key>.one` string exists; translations may define it or not.
export function tn(key, n, vars = {}) {
  const one = `${key}.one`;
  return t(n === 1 && (one in overrides || one in STRINGS) ? one : key, { ...vars, n });
}
