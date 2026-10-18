"""Bridge the unmodified upstream CLI scanner to one in-memory source file."""
from pathlib import Path
root = Path(__file__).resolve().parent.parent
source = (root / 'source/upstream/lint.mjs').read_text()
lines = source.splitlines()
assert lines[0].startswith('#!')
assert lines[5].startswith('//')
source = '\n'.join(line for line in lines[1:] if not line.startswith('import '))
bridge = r'''
export function lintSource(source) {
  let payload;
  const stopped = Symbol('CLI exit');
  const console = { log(value) { payload = JSON.parse(value); }, error(value) { throw new Error(value); } };
  const process = { argv: ['node', 'lint.mjs', '/sample.html', '--json'], cwd: () => '/', exit(code) { throw stopped; } };
  const readFileSync = () => source;
  const readdirSync = () => [];
  const statSync = () => ({ isDirectory: () => false, size: source.length });
  const join = (...parts) => parts.join('/');
  const extname = () => '.html';
  const relative = () => 'sample.html';
  const resolve = (value) => value;
  try {
'''
(root/'scanner.js').write_text('// MIT · Leonxlnx/taste-skill · f624f37a8c650b9cc550253104925efe4c8de246\n' + bridge + source + '''
  } catch (error) { if (error !== stopped) throw error; }
  if (!payload) throw new Error('Scanner returned no JSON');
  return payload;
}
''')
print('Built scanner.js from upstream lint.mjs; rule table and scanning loop unchanged.')
