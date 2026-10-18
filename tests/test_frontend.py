import json
from pathlib import Path
import re
import shutil
import subprocess
import unittest

WEB = Path(__file__).resolve().parents[1] / "web"
JS = WEB / "js"


@unittest.skipUnless(shutil.which("node"), "front-end checks need Node.js")
class FrontendTests(unittest.TestCase):
    """The page's pure modules (state, strings, format, demos) imported straight into Node; no DOM needed."""

    def run_node(self, body):
        script = f"""
import assert from 'node:assert/strict';
const load = name => import(new URL(name + '.js', {json.dumps((JS.as_uri() + '/'))}));
const {{ state, readUrl, urlFor, projects, selection, demoLibrary }} = await load('state');
const {{ t, tn, setStrings, STRINGS }} = await load('strings');
const {{ shortDay, timeLabel, topicLabel, starsText }} = await load('format');
const {{ demoPath, demoUrl }} = await load('demos');
""" + body
        result = subprocess.run([shutil.which("node"), "--input-type=module", "-e", script], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_every_module_parses(self):
        for module in sorted(JS.glob("*.js")):
            with self.subTest(module=module.name):
                result = subprocess.run([shutil.which("node"), "--check", str(module)], capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stderr)

    def test_demo_library_deduplicates_across_editions_and_url_keeps_state(self):
        self.run_node(r"""
readUrl('?view=demos&q=component&verdict=bogus&sort=name');
assert.equal(state.verdict, 'all');
assert.equal(state.sort, 'name');
state.day = '2026-10-16';
state.data = { editions: [
  { day: '2026-10-16', projects: [
    { repo: 'owner/one', demo: { status: 'ready', tested_at: '2026-10-16T09:00:00-07:00' } },
    { repo: 'owner/no-demo' } ] },
  { day: '2026-10-15', projects: [
    { repo: 'OWNER/ONE', demo: { status: 'failed', tested_at: '2026-10-15T18:00:00-07:00' } },
    { repo: 'owner/two', demo: { status: 'blocked', tested_at: '2026-10-16T17:30:00+00:00' } } ] },
] };
assert.equal(projects().length, 2);
assert.equal(projects()[0].repo, 'owner/two');
assert.equal(projects()[1].demo.status, 'ready');
assert.equal(urlFor(), '/?view=demos&q=component&sort=name');
state.view = 'daily';
assert.equal(urlFor(), '/?day=2026-10-16&q=component&sort=name');
assert.equal(projects()[1].repo, 'owner/no-demo');
assert.equal(demoLibrary().length, 2);
""")

    def test_selection_filters_searches_and_sorts(self):
        self.run_node(r"""
const pick = (name, topic, verdict, effort, extra = {}) => ({ name, repo: `o/${name}`, topic, verdict, effort, ...extra });
const all = [pick('Zed', 'ai', 'try', 'high'), pick('Alpha', 'ai', 'watch', 'low', { tags: ['Rust'] }),
  pick('Mid', 'web', 'try', 'medium', { tech_stack: { items: [{ name: 'Svelte', role: 'UI' }] } })];
state.config.topics = [{ id: 'ai', label: 'AI' }, { id: 'rust', label: 'Rust' }];
Object.assign(state, { topic: 'all', verdict: 'all', feedback: 'all', query: '', sort: 'editorial', votes: {} });
let picked = selection(all);
assert.deepEqual(picked.topicIds, ['ai', 'rust', 'web']);
assert.deepEqual(picked.visible.map(p => p.name), ['Zed', 'Alpha', 'Mid']);
state.sort = 'easy';
assert.deepEqual(selection(all).visible.map(p => p.name), ['Alpha', 'Mid', 'Zed']);
state.sort = 'name';
assert.deepEqual(selection(all).visible.map(p => p.name), ['Alpha', 'Mid', 'Zed']);
state.query = 'svelte';
assert.deepEqual(selection(all).visible.map(p => p.name), ['Mid']);
Object.assign(state, { query: '', topic: 'ai', verdict: 'try' });
picked = selection(all);
assert.deepEqual(picked.inTopic.map(p => p.name), ['Zed', 'Alpha']);  // filter sets keep editorial order
assert.deepEqual(picked.visible.map(p => p.name), ['Zed']);
Object.assign(state, { topic: 'gone', verdict: 'all', feedback: 'like', votes: { 'o/alpha': 'like' } });
assert.deepEqual(selection(all).visible.map(p => p.name), ['Alpha']);
assert.equal(state.topic, 'all');
""")

    def test_language_topics_timezone_and_agent_strings_follow_config(self):
        self.run_node(r"""
assert.equal(t('verdict.try'), 'Worth trying');
assert.equal(t('missing.key'), 'missing.key');
assert.equal(tn('demos.count', 1), '1 project');
assert.equal(tn('demos.count', 3), '3 projects');
state.config = { language: 'zh-CN', timezone: 'Asia/Shanghai', title: 'x', topics: [{ id: 'agents', label: 'Agent 框架' }] };
setStrings({ 'verdict.try': '值得试用', 'edition.withDemo': '，其中 {n} 个附带 Demo' });
assert.equal(topicLabel('agents'), 'Agent 框架');
assert.equal(topicLabel('gone'), 'gone');
assert.equal(t('verdict.try'), '值得试用');
assert.equal(t('edition.withDemo', { n: 2 }), '，其中 2 个附带 Demo');
assert.equal(t('verdict.watch'), 'Watch closely');
assert.equal(shortDay('2026-10-07'), '10月7日');
assert.equal(timeLabel('2026-10-17T00:30:00Z'), '10/17 08:30');
assert.equal(starsText({ stars: { count: 12345, approximate: true } }), '~12,345 stars');
state.config.language = 'not a tag';
assert.equal(shortDay('2026-10-07'), 'Oct 7');
""")

    def test_demo_links_point_at_the_demo_origin(self):
        self.run_node(r"""
globalThis.location = { protocol: 'http:', hostname: '127.0.0.1', port: '53265' };
assert.equal(demoPath({ status: 'ready', path: '/demos/a-b/' }), '/demos/a-b/');
for (const path of ['/demos/../', '/demos/a/index.html', ' /demos/a/', 'https://x/']) {
  assert.equal(demoPath({ status: 'ready', path }), null);
}
assert.equal(demoPath({ status: 'blocked', path: '/demos/a/' }), null);
assert.equal(demoUrl('/demos/a/'), 'http://127.0.0.1:53266/demos/a/');
state.config.demo_port = 60000;
assert.equal(demoUrl('/demos/a/'), 'http://127.0.0.1:60000/demos/a/');
""")

    def test_module_layers_only_depend_downward(self):
        # Mirrors the table in CONTRIBUTING.md: logic < I/O < widgets < page.
        layers = {"strings": 0, "state": 0, "format": 0, "api": 1, "storage": 1,
                  "dom": 2, "parts": 2, "demos": 2, "reasons": 2, "feedback": 2, "cards": 2, "render": 3, "main": 3}
        modules = {path.stem for path in JS.glob("*.js")}
        self.assertEqual(modules, set(layers), "add new modules to the layer table here and in CONTRIBUTING.md")
        for name in sorted(modules):
            imports = re.findall(r"from '\./([a-z]+)\.js'", (JS / f"{name}.js").read_text(encoding="utf-8"))
            for target in imports:
                with self.subTest(module=name, imports=target):
                    self.assertLessEqual(layers[target], layers[name])
                    self.assertFalse(layers[name] == 2 and target == "render", "widgets get a rerender callback")
            if layers[name] == 0:
                self.assertNotIn("document.", (JS / f"{name}.js").read_text(encoding="utf-8"), f"{name}.js must not touch the DOM")

    def test_dislike_reasons_match_the_server_and_have_labels(self):
        from repomuse.schema import DISLIKE_REASONS
        self.run_node("""
const { DISLIKE_REASONS } = await load('reasons');
assert.deepEqual(DISLIKE_REASONS, %s);
const keys = [...DISLIKE_REASONS.map(code => 'reason.' + code), 'reason.other', 'reasons.title', 'reasons.hint',
  'reasons.placeholder', 'reasons.other', 'reasons.save', 'reasons.skip', 'reasons.undo', 'reasons.saved'];
assert.deepEqual(keys.filter(key => !(key in STRINGS)), []);
assert.equal(t('reasons.hint', { name: 'X' }).includes('X'), true);
""" % json.dumps(list(DISLIKE_REASONS)))

    def test_every_static_text_key_exists_in_strings(self):
        html = (WEB / "index.html").read_text(encoding="utf-8")
        keys = sorted(set(re.findall(r'data-text(?:-aria)?="([^"]+)"', html)))
        self.run_node("assert.deepEqual(%s.filter(key => !(key in STRINGS)), []);" % json.dumps(keys))


if __name__ == "__main__":
    unittest.main()
