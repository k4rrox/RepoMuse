import { lintSource } from './scanner.js';
import { PRESETS } from './presets.js';
const ids=['gradient','shadow','purple','copy'];
const inputs=Object.fromEntries(ids.map(id=>[id,document.getElementById(id)]));
function update(){
 const fixed=Object.fromEntries(ids.map(id=>[id,inputs[id].checked]));
 const colour=fixed.purple?'#17675e':'#6366f1';
 const end=fixed.purple?'#2b8072':'#8b5cf6';
 const background=fixed.gradient?colour:`linear-gradient(125deg, ${colour}, ${end})`;
 const shadow=fixed.shadow?'none':'0 14px 26px #3d3c8950';
 const title=fixed.copy?'Turn meetings into searchable notes.':'Unleash the future of notes.';
 const text=fixed.copy?'Clean up transcripts, pull out action items and search by keyword.':'Effortlessly transform ideas into a seamless workflow.';
 const action=fixed.copy?'Open a sample note':'Get started';
 const source=`<style>\n.card {\n  background: ${background};\n${fixed.shadow?'':`  box-shadow: ${shadow};\n`}}\n</style>\n<section class="card">\n  <h1>${title}</h1>\n  <p>${text}</p>\n  <button>${action}</button>\n</section>`;
 const card=document.querySelector('.mock-card');
 card.style.background=background;card.style.boxShadow=shadow;
 document.getElementById('sample-title').textContent=title;
 document.getElementById('sample-copy').textContent=text;
 document.getElementById('sample-action').textContent=action;
 document.getElementById('sample-action').style.color=colour;
 document.getElementById('source').textContent=source;
 const report=lintSource(source);
 const failures=report.findings.filter(f=>f.level==='FAIL').length;
 document.getElementById('count').textContent=`${failures} FAIL / ${report.findings.length-failures} WARN`;
 const area=document.getElementById('findings');area.replaceChildren();
 if(!report.findings.length){const p=document.createElement('div');p.className='pass';const strong=document.createElement('strong');strong.textContent='No banned source patterns found';const span=document.createElement('span');span.textContent='A real browser check and human judgement still come next. This is not a taste score.';p.append(strong,span);area.append(p);}
 for(const finding of report.findings){const item=document.createElement('div');item.className=`finding ${finding.level==='WARN'?'warn':''}`;const meta=document.createElement('p');meta.className='meta';meta.textContent=`${finding.level} · ${finding.id} · line ${finding.line}`;const label=document.createElement('p');label.textContent=finding.message;const code=document.createElement('code');code.textContent=finding.match;item.append(meta,label,code);area.append(item);}
 const total=ids.filter(id=>fixed[id]).length;
 document.getElementById('state').textContent=total===0?'Original sample':total===4?'All rules applied':`${total} of 4 adjusted`;
 document.getElementById('reset').classList.toggle('active',total===0);
 document.getElementById('fix').classList.toggle('active',total===4);
}
for(const input of Object.values(inputs))input.addEventListener('change',update);
document.getElementById('reset').addEventListener('click',()=>{ids.forEach(id=>inputs[id].checked=false);update();});
document.getElementById('fix').addEventListener('click',()=>{ids.forEach(id=>inputs[id].checked=true);update();});
update();

// Free-form editor: the same upstream scanner on any pasted source.
const editor=document.getElementById('code-input');
const notes={landing:'A sample stitched together from typical AI landing page habits; nearly every line hits a rule.',before:'An excerpt of this page\'s styles and script before its redesign: hairlines, 1px outlined boxes, monospace labels and emoji.',after:'The matching styles after the redesign: tone and spacing instead of lines and boxes, monospace only for code. Zero hits only means no banned patterns, not that it looks good.'};
let editorTimer=0;
function lintEditor(){
 const report=lintSource(editor.value);
 const failures=report.findings.filter(f=>f.level==='FAIL').length;
 document.getElementById('editor-count').textContent=report.findings.length?`${failures} FAIL / ${report.findings.length-failures} WARN`:'0 FAIL / 0 WARN · no banned patterns';
 const list=document.getElementById('editor-findings');list.replaceChildren();
 for(const finding of report.findings){
  const item=document.createElement('li');const button=document.createElement('button');button.type='button';button.className=`hit ${finding.level==='WARN'?'warn':''}`;
  const meta=document.createElement('span');meta.className='meta';meta.textContent=`line ${finding.line} · ${finding.level} · ${finding.id}`;
  const label=document.createElement('span');label.textContent=finding.message;
  const code=document.createElement('code');code.textContent=finding.match;
  button.append(meta,label,code);button.addEventListener('click',()=>selectLine(finding.line));item.append(button);list.append(item);
 }
}
function selectLine(line){
 const lines=editor.value.split('\n');const start=lines.slice(0,line-1).reduce((n,l)=>n+l.length+1,0);
 editor.focus();editor.setSelectionRange(start,start+(lines[line-1]||'').length);
 const height=editor.scrollHeight/Math.max(lines.length,1);editor.scrollTop=Math.max(0,(line-3)*height);
}
function loadPreset(name){
 editor.value=PRESETS[name];document.getElementById('editor-note').textContent=notes[name];
 for(const button of document.querySelectorAll('[data-preset]'))button.classList.toggle('active',button.dataset.preset===name);
 editor.scrollTop=0;lintEditor();
}
editor.addEventListener('input',()=>{clearTimeout(editorTimer);editorTimer=setTimeout(lintEditor,150);for(const button of document.querySelectorAll('[data-preset]'))button.classList.remove('active');document.getElementById('editor-note').textContent='Edited: results update live from your code.';});
for(const button of document.querySelectorAll('[data-preset]'))button.addEventListener('click',()=>loadPreset(button.dataset.preset));
loadPreset('landing');
