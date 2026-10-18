import { lintSource } from '../scanner.js';
import { mkdtempSync, writeFileSync, rmSync } from 'node:fs';
import { execFileSync } from 'node:child_process';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import assert from 'node:assert/strict';
const here = dirname(fileURLToPath(import.meta.url));
const dir = mkdtempSync(join(here, 'verify-'));
try {
  for (let mask=0; mask<16; mask++) {
    const colour = mask&4 ? '#17675e' : '#6366f1';
    const source = `<style>\n.card {\n background: ${mask&1 ? colour : `linear-gradient(125deg, ${colour}, white)`};\n${mask&2 ? '' : ' box-shadow: 0 14px 26px #3d3c8950;\n'}}\n</style>\n<h1>${mask&8 ? 'Searchable meeting notes' : 'Unleash the future of notes.'}</h1>\n<button>${mask&8 ? 'Open notes' : 'Get started'}</button>`;
    const fixture = join(dir, 'sample.html');
    writeFileSync(fixture, source);
    let output;
    try { output=execFileSync(process.execPath,[join(here,'upstream/lint.mjs'),fixture,'--json'],{encoding:'utf8',stdio:['ignore','pipe','pipe']}); }
    catch(error) { if(error.status!==1)throw error; output=error.stdout; }
    const original=JSON.parse(output);
    const adapted=lintSource(source);
    const clean = report=>report.findings.map(f=>({...f,file:'sample.html'}));
    assert.deepEqual(clean(adapted),clean(original));
  }
  console.log('PASS: all 16 sample states match unmodified upstream CLI findings.');
} finally { rmSync(dir,{recursive:true,force:true}); }
