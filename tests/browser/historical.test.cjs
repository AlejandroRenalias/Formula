/* node --test tests/browser/historical.test.cjs
 * Requires Playwright (NODE_PATH may point at the bundled runtime). */
const {test,before,after}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const http=require('node:http');
const {spawn,execFileSync}=require('node:child_process');
const {chromium}=require('playwright');
const ROOT=path.resolve(__dirname,'../..');
const SHOTS=path.join(ROOT,'docs/historical_ux/screenshots');
let browser,server,streamlit,origin,streamlitLog='';
const mime={'.html':'text/html','.js':'application/javascript','.css':'text/css','.json':'application/json','.ttf':'font/ttf'};
before(async()=>{
  server=http.createServer((req,res)=>{
    const target=path.resolve(ROOT,'.'+decodeURIComponent(new URL(req.url,'http://local').pathname));
    if (!target.startsWith(ROOT+path.sep)) {res.writeHead(403).end();return;}
    fs.readFile(target,(err,data)=>{if(err){res.writeHead(404).end();return;}res.writeHead(200,{'Content-Type':mime[path.extname(target)]||'application/octet-stream'});res.end(data);});
  });
  await new Promise(r=>server.listen(0,'127.0.0.1',r));origin=`http://127.0.0.1:${server.address().port}`;
  const chrome=process.env.CHROME_PATH || 'C:/Program Files/Google/Chrome/Application/chrome.exe';
  browser=await chromium.launch({headless:true,...(fs.existsSync(chrome)?{executablePath:chrome}:{})});
  fs.mkdirSync(SHOTS,{recursive:true});
});
after(async()=>{await browser?.close();await new Promise(r=>server?.close(r));if(streamlit)streamlit.kill();});
async function open(viewport={width:1440,height:1000}) {
  const page=await browser.newPage({viewport});
  const errors=[];page.on('pageerror',e=>errors.push(e.message));
  await page.goto(origin+'/design/pitwall-concept.html');
  await page.locator('#workspace:not([hidden])').waitFor();
  return {page,errors};
}
async function history(page,driver='44',lap='11') {
  await page.click('#mode-historical');await page.locator('#h-race option').first().waitFor({state:'attached'});
  await page.selectOption('#h-driver',driver);page.archiveLap=lap;
}
async function shown(page){
  if ((await page.inputValue('#h-lap'))!==page.archiveLap) await page.fill('#h-lap',page.archiveLap);
  else await page.click('#h-show');
  await page.locator('#h-call-content:not([hidden])').waitFor();
}
async function lock(page,choice='STAY'){await page.click(choice==='BOX'?'#h-box':'#h-stay');await page.click('#h-lock');}
async function reveal(page){await page.click('#h-reveal');await page.locator('#h-revealed:not([hidden])').waitFor();}
test('no outcome requests before explicit Reveal; pointwise labels; eight desktop/mobile state screenshots',async()=>{
  for(const [label,viewport] of [['desktop',{width:1440,height:1000}],['mobile',{width:390,height:844}]]) {
    const {page,errors}=await open(viewport);const requests=[];
    page.on('request',r=>requests.push(r.url()));
    await history(page);
    await page.screenshot({path:path.join(SHOTS,label+'-choosing.png'),fullPage:true});
    assert.equal(requests.filter(x=>x.includes('/outcomes/')).length,0);
    await shown(page);
    assert.equal(await page.locator('#h-call').innerText(),'BOX or STAY?');
    assert.equal(await page.locator('#h-model-details').innerHTML(),'');
    assert.equal(await page.locator('#h-model-summary').innerHTML(),'');
    assert.equal(await page.locator('#h-margin, #h-confidence, #h-best-box, #h-best-stay').count(),0);
    assert.match(await page.locator('#h-situation').innerText(),/Position 2.*VER 1.8 s ahead.*BOT 4.8 s behind/);
    await page.screenshot({path:path.join(SHOTS,label+'-call-shown.png'),fullPage:true});
    assert.equal(requests.filter(x=>x.includes('/outcomes/')).length,0);
    assert.equal(await page.locator('#h-reveal').isEnabled(),false);
    assert.equal(await page.locator('#h-revealed').innerText(),'');
    await lock(page);
    assert.equal(await page.locator('#h-call').innerText(),'STAY');
    assert.equal(await page.locator('#h-preference').innerText(),'Strong model preference');
    await page.screenshot({path:path.join(SHOTS,label+'-call-locked.png'),fullPage:true});
    assert.equal(requests.filter(x=>x.includes('/outcomes/')).length,0);
    await reveal(page);
    assert.deepEqual(await page.locator('.history-comparison tr').allTextContents(),['TeamSTAY— Reference','FormulaSTAY✓ Agree','YouSTAY✓ Agree']);
    assert.match(await page.locator('#h-revealed').innerText(),/The team boxes next lap, for hards/);
    assert.match(await page.locator('#h-next-prompt').innerText(),/The team boxes next lap. Can you call it\?/);
    assert.doesNotMatch(await page.locator('#h-revealed').innerText(),/Why Formula|Different number of stops|not enough data/);
    assert.equal(requests.filter(x=>x.includes('/outcomes/')).length,1);
    assert.equal(requests.filter(x=>x.includes('/causal/')).length,1);
    assert.deepEqual(requests.filter(x=>/manifest|jsonl/.test(x)),[]);
    assert.match(await page.locator('#h-tally').innerText(),/team 1 of 1; Formula 1 of 1/);
    await page.screenshot({path:path.join(SHOTS,label+'-revealed.png'),fullPage:true});
    assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false,'no horizontal overflow');
    assert.deepEqual(errors,[]);await page.close();
  }
});
test('selection changes clear choice, lock and reveal; next lap is a fresh attempt; repeat scoring happens once',async()=>{
  const {page}=await open();await history(page);await shown(page);await lock(page);await reveal(page);
  await page.evaluate(()=>document.getElementById('h-reveal').dispatchEvent(new MouseEvent('click')));
  assert.match(await page.locator('#h-tally').innerText(),/1 of 1; Formula 1 of 1/);
  await page.click('#h-next');await page.locator('#h-call-content:not([hidden])').waitFor();
  assert.equal(await page.inputValue('#h-lap'),'12');assert.equal(await page.locator('#h-reveal').isEnabled(),false);
  assert.equal(await page.locator('#h-revealed').innerText(),'');
  for(const change of [()=>page.fill('#h-lap','11'),()=>page.selectOption('#h-driver','33'),()=>page.selectOption('#h-race','spain_2022')]) {
    await lock(page);await change();
    assert.ok(['choosing','situation-shown'].includes(await page.locator('#historical-workspace').getAttribute('data-state')));
    assert.equal(await page.locator('#h-reveal').isEnabled(),false);
    assert.equal(await page.locator('#h-revealed').innerText(),'');await shown(page);
  }
  await page.selectOption('#h-race','bahrain_2021');await page.selectOption('#h-driver','44');await page.fill('#h-lap','11');await shown(page);await lock(page);await reveal(page);
  assert.match(await page.locator('#h-tally').innerText(),/1 of 1; Formula 1 of 1/,'same snapshot counted once per session');
  await page.click('#h-reset-tally');assert.match(await page.locator('#h-tally').innerText(),/0 of 0; Formula 0 of 0/);
  assert.equal(await page.locator('#h-reveal').isEnabled(),false);await page.close();
});
test('unavailable cutoff is generic; disabled Reveal never fetches outcomes',async()=>{
  const {page}=await open();let outcomes=0;page.on('request',r=>{if(r.url().includes('/outcomes/'))outcomes++;});
  await history(page);await page.route('**/causal/**',route=>route.fulfill({status:404,body:'unavailable'}));await page.click('#h-show');
  await page.waitForFunction(()=>document.getElementById('h-message').textContent==='No archived decision at this cutoff');
  await page.evaluate(()=>document.getElementById('h-reveal').dispatchEvent(new MouseEvent('click')));
  assert.equal(outcomes,0);assert.equal(await page.locator('#h-call-content').isVisible(),false);await page.close();
});
test('future outcome poisoning cannot change pre-reveal DOM or map',async()=>{
  const {page}=await open();await history(page);await shown(page);
  const signature=await page.locator('#h-call-content').innerHTML();
  await page.route('**/outcomes/**',route=>route.fulfill({contentType:'application/json',body:'{"future":"POISONED"}'}));
  await page.route('**/causal/**/12.json',route=>route.fulfill({status:500,body:'future row poisoned'}));
  await page.click('#h-show');await page.locator('#h-call-content:not([hidden])').waitFor();
  assert.equal(await page.locator('#h-call-content').innerHTML(),signature);await page.close();
});
test('changing selection while Reveal is pending discards stale outcome and tally',async()=>{
  const {page}=await open();await history(page);await shown(page);await lock(page);
  let release;const gate=new Promise(r=>release=r);let requested;const started=new Promise(r=>requested=r);
  await page.route('**/outcomes/**',async route=>{requested();await gate;try{await route.continue();}catch{}});
  await page.click('#h-reveal');await started;await page.fill('#h-lap','12');release();
  await page.waitForTimeout(150);
  assert.equal(await page.locator('#h-revealed').innerText(),'');assert.match(await page.locator('#h-tally').innerText(),/0 of 0/);await page.close();
});
test('synthetic renderer, styles, fixture and workspace remain unchanged through mode roundtrip',async()=>{
  for(const file of ['design/assets/pitwall.js','design/assets/pitwall.css','tests/fixtures/projection_lap18.json']) {
    assert.equal(fs.readFileSync(path.join(ROOT,file),'utf8').replaceAll('\r\n','\n'),execFileSync('git',['show','0db5d57:'+file],{cwd:ROOT,encoding:'utf8'}).replaceAll('\r\n','\n'));
  }
  const {page,errors}=await open();await page.waitForTimeout(250);
  const original=await page.locator('#workspace').innerHTML();await history(page);await shown(page);await page.click('#mode-synthetic');await page.waitForTimeout(250);
  assert.equal(await page.locator('#workspace').innerHTML(),original);
  assert.equal(await page.locator('#error').isVisible(),false);
  assert.equal(await page.locator('#historical-workspace').isVisible(),false);assert.deepEqual(errors,[]);await page.close();
});
test('Streamlit wrapper serves the identical per-record static paths and works inside its iframe',async()=>{
  const python=process.platform==='win32'?path.join(ROOT,'.venv/Scripts/python.exe'):path.join(ROOT,'.venv/bin/python');
  const temp=path.join(ROOT,'data/cache/streamlit-ui-temp');fs.mkdirSync(temp,{recursive:true});
  streamlit=spawn(python,['-m','streamlit','run','app.py','--server.port','8522','--server.address','127.0.0.1','--server.headless','true','--browser.gatherUsageStats','false'],{cwd:ROOT,windowsHide:true,env:{...process.env,TEMP:temp,TMP:temp}});
  streamlit.stdout.on('data',s=>streamlitLog+=s);streamlit.stderr.on('data',s=>streamlitLog+=s);
  let ready=false;
  for(let i=0;i<60;i++){try{if((await fetch('http://127.0.0.1:8522/_stcore/health')).ok){ready=true;break;}}catch{}await new Promise(r=>setTimeout(r,500));}
  assert.ok(ready,streamlitLog);
  const page=await browser.newPage({viewport:{width:1440,height:1000}});const requests=[];page.on('request',r=>requests.push(r.url()));
  await page.goto('http://127.0.0.1:8522');
  const frame=page.frameLocator('iframe').first();await frame.locator('#mode-historical').click();
  await frame.locator('#h-race option').first().waitFor({state:'attached'});
  await frame.locator('#h-driver').selectOption('44');await frame.locator('#h-lap').fill('11');await frame.locator('#h-show').click();
  await frame.locator('#h-call-content:not([hidden])').waitFor();
  assert.equal(requests.filter(x=>x.includes('/outcomes/')).length,0);
  assert.ok(requests.some(x=>x.includes('/app/static/historical/causal/bahrain_2021/44/11.json')));
  await frame.locator('#h-stay').click();await frame.locator('#h-lock').click();await frame.locator('#h-reveal').click();await frame.locator('#h-revealed:not([hidden])').waitFor();
  assert.match(await frame.locator('.history-comparison').innerText(),/Team\s+STAY/);
  assert.equal(requests.filter(x=>x.includes('/outcomes/')).length,1);
  await page.screenshot({path:path.join(SHOTS,'streamlit-desktop-revealed.png'),fullPage:true});await page.close();
});
test('near misses use the one-lap direction and exact action in the tally',async()=>{
  const {page}=await open();await history(page);await shown(page);
  for(const direction of ['later','earlier']) {
    const o=JSON.parse(fs.readFileSync(path.join(ROOT,'static/historical/outcomes/bahrain_2021/44/11.json'),'utf8'));
    // Isolated UI fixture: validates rendering, never alters archive predictions.
    o.team_action_this_lap='BOX';o.formula_agrees_with_team=false;o.near_miss=true;
    o.near_miss_stop={boundary_lap:direction==='later'?12:10};
    o.stop_disagreement_tags[0].tags.compound_outside_candidates=true;
    await page.route('**/outcomes/**',route=>route.fulfill({contentType:'application/json',body:JSON.stringify(o)}));
    await lock(page);await reveal(page);
    assert.match(await page.locator('#h-revealed').innerText(),new RegExp('Close: the team boxed one lap '+direction));
    assert.match(await page.locator('#h-revealed').innerText(),/The team fitted a compound Formula didn't consider/);
    assert.match(await page.locator('#h-tally').innerText(),/team 0 of 1; Formula 0 of 1/);
    await page.click('#h-reset-tally');await page.unroute('**/outcomes/**');await shown(page);
  }
  await page.close();
});
test('default call order has no Formula action in the DOM until Lock, including after a prior reveal',async()=>{
  const {page}=await open();await history(page);await shown(page);
  assert.equal(await page.locator('#h-show-first').isChecked(),false);
  assert.equal(await page.locator('#h-call').innerText(),'BOX or STAY?');
  assert.equal(await page.locator('#h-model-details').innerHTML(),'');
  assert.equal(await page.locator('#h-model-summary').innerHTML(),'');
  assert.equal(await page.locator('#h-confidence,#h-margin,#h-best-box,#h-best-stay').count(),0);
  await page.click('#h-stay');
  assert.equal(await page.locator('#h-call').innerText(),'BOX or STAY?');
  const selected=await page.locator('#h-stay').evaluate(el=>({border:getComputedStyle(el).borderColor,fill:getComputedStyle(el).backgroundColor}));
  assert.equal(selected.border,'rgb(255, 128, 0)');assert.notEqual(selected.fill,'rgba(0, 0, 0, 0)');
  await page.click('#h-lock');assert.equal(await page.locator('#h-call').innerText(),'STAY');
  await reveal(page);await page.fill('#h-lap','12');await page.locator('#h-call-content:not([hidden])').waitFor();
  assert.equal(await page.locator('#h-call').innerText(),'BOX or STAY?');
  assert.equal(await page.locator('#h-model-details').innerHTML(),'');
  assert.equal(await page.locator('#h-model-summary').innerHTML(),'');
  assert.equal(await page.locator('#h-revealed').innerText(),'');
  await page.close();
});
test('Formula-first opt-in restores the prior order and separates tallies; toggle clears the attempt',async()=>{
  for(const [label,viewport] of [['desktop',{width:1440,height:1000}],['mobile',{width:390,height:844}]]) {
    const {page}=await open(viewport);let outcomes=0;page.on('request',r=>{if(r.url().includes('/outcomes/'))outcomes++;});
    await history(page);await page.check('#h-show-first');
    await page.screenshot({path:path.join(SHOTS,label+'-formula-first-choosing.png'),fullPage:true});
    await shown(page);assert.equal(await page.locator('#h-call').innerText(),'STAY');
    await page.screenshot({path:path.join(SHOTS,label+'-formula-first-call-shown.png'),fullPage:true});
    assert.equal(outcomes,0);await lock(page);
    await page.screenshot({path:path.join(SHOTS,label+'-formula-first-call-locked.png'),fullPage:true});
    assert.equal(outcomes,0);await reveal(page);
    assert.match(await page.locator('#h-tally').innerText(),/Formula first.*team 1 of 1; Formula 1 of 1/);
    await page.screenshot({path:path.join(SHOTS,label+'-formula-first-revealed.png'),fullPage:true});
    await page.uncheck('#h-show-first');await page.locator('#h-call-content:not([hidden])').waitFor();
    assert.equal(await page.locator('#h-call').innerText(),'BOX or STAY?');
    assert.equal(await page.locator('#h-reveal').isEnabled(),false);
    assert.equal(await page.locator('#h-revealed').innerText(),'');
    assert.match(await page.locator('#h-tally').innerText(),/Your call first.*team 0 of 0; Formula 0 of 0/);
    assert.match(await page.locator('#h-other-tally').innerText(),/Formula first: You 1 of 1/);
    await lock(page,'BOX');await reveal(page);
    assert.match(await page.locator('#h-tally').innerText(),/team 0 of 1; Formula 1 of 1/);
    const stored=await page.evaluate(()=>JSON.parse(sessionStorage.getItem('formula-history-tally')));
    assert.equal(stored.schema_version,2);assert.equal(stored.modes.formula_first.total,1);assert.equal(stored.modes.user_first.total,1);
    await page.close();
  }
});
test('lap arrows and direct typing load immediately and respect scheduled range',async()=>{
  const {page}=await open();await history(page);await shown(page);
  await page.click('#h-next-lap');await page.locator('#h-call-content:not([hidden])').waitFor();
  assert.equal(await page.locator('#h-lap-current').innerText(),'12');
  await page.click('#h-prev-lap');await page.locator('#h-call-content:not([hidden])').waitFor();
  assert.equal(await page.locator('#h-lap-current').innerText(),'11');
  await page.fill('#h-lap','5');
  // HAM's boundary 5 is not archived; direct navigation must preserve the
  // generic unavailable message rather than silently choosing another lap.
  await page.waitForFunction(()=>document.getElementById('h-message').textContent==='No archived decision at this cutoff');
  assert.equal(await page.locator('#h-prev-lap').isEnabled(),false);
  await page.fill('#h-lap','51');await page.locator('#h-call-content:not([hidden])').waitFor();
  assert.equal(await page.locator('#h-next-lap').isEnabled(),false);
  assert.equal(await page.locator('#h-call').innerText(),'BOX or STAY?');await page.close();
});
test('map labels only the subject and nearest three cars on each side; all dots have tooltips',async()=>{
  const {page}=await open();await history(page);await shown(page);
  const r=JSON.parse(fs.readFileSync(path.join(ROOT,'static/historical/causal/bahrain_2021/44/11.json'),'utf8'));
  const ahead=r.field.filter(c=>c.gap_to_subject_s>0).sort((a,b)=>a.gap_to_subject_s-b.gap_to_subject_s).slice(0,3);
  const behind=r.field.filter(c=>c.gap_to_subject_s<0).sort((a,b)=>b.gap_to_subject_s-a.gap_to_subject_s).slice(0,3);
  assert.deepEqual((await page.locator('#h-map text').allTextContents()).sort(),[r.subject.driver,...ahead.map(c=>c.driver),...behind.map(c=>c.driver)].sort());
  assert.equal(await page.locator('#h-map circle title').count(),r.field_count);
  assert.equal(await page.locator('#historical-workspace h2').allTextContents().then(x=>x.join('/')),'On track/Timing');
  await page.close();
});
test('next stop wording handles this lap, several laps and no further stop; tags omitted for agreement',async()=>{
  const {page}=await open();await history(page);await shown(page);
  const original=JSON.parse(fs.readFileSync(path.join(ROOT,'static/historical/outcomes/bahrain_2021/44/11.json'),'utf8'));
  for(const [distance,expected] of [[4,'The team boxes in 4 laps, for mediums'],[0,'The team boxes this lap, for mediums'],[null,'No further stop']]) {
    const o=structuredClone(original);o.next_team_stop=distance===null?null:{...o.next_team_stop,laps_from_cutoff:distance,compound:'MEDIUM'};
    await page.route('**/outcomes/**',route=>route.fulfill({contentType:'application/json',body:JSON.stringify(o)}));
    await lock(page);await reveal(page);
    assert.ok((await page.locator('#h-revealed').innerText()).includes(expected));
    assert.doesNotMatch(await page.locator('#h-revealed').innerText(),/Why Formula|Different number of stops/);
    assert.equal(await page.locator('#h-next-prompt').innerText(),'');
    await page.click('#h-reset-tally');await page.unroute('**/outcomes/**');await shown(page);
  }
  await page.close();
});
test('legacy session tally migrates to Formula-first without contaminating blind choices',async()=>{
  const {page}=await open();
  await page.evaluate(()=>sessionStorage.setItem('formula-history-tally',JSON.stringify({you:2,formula:1,total:3,seen:{old:true}})));
  await page.reload();await history(page);await shown(page);
  assert.match(await page.locator('#h-tally').innerText(),/Your call first.*team 0 of 0/);
  assert.match(await page.locator('#h-other-tally').innerText(),/Formula first: You 2 of 3; Formula 1 of 3/);
  await page.close();
});
