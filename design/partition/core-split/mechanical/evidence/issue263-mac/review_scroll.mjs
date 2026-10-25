// Supplemental real-input/scroll capture of the unmodified inspector.
// Usage: node review_scroll.mjs PLAYWRIGHT_MODULE CHROME_EXECUTABLE NEW_OUTPUT_DIR
import {pathToFileURL, fileURLToPath} from 'node:url';
import {mkdir, writeFile, readFile} from 'node:fs/promises';
import {resolve, dirname} from 'node:path';
import {execFileSync} from 'node:child_process';
import assert from 'node:assert/strict';
const [modulePath, executablePath, outputPath] = process.argv.slice(2);
const out = resolve(outputPath);
await mkdir(out); // Do not overwrite prior evidence.
const {chromium} = await import(pathToFileURL(resolve(modulePath)).href);
const here = dirname(fileURLToPath(import.meta.url));
const mechanical = resolve(here, '../..');
const receipt = {source_sha: execFileSync('git', ['rev-parse', 'HEAD'], {encoding:'utf8'}).trim(), commands:process.argv, errors:[], assertions:[], screenshots:[]};
let browser;
try {
  browser = await chromium.launch({executablePath, headless:true, chromiumSandbox:true, timeout:20000});
  receipt.browser_version = browser.version();
  const page = await browser.newPage({viewport:{width:1500,height:1200}});
  page.setDefaultTimeout(5000);
  page.on('pageerror', e=>receipt.errors.push(String(e)));
  page.on('console', m=>{if(m.type()==='error')receipt.errors.push(m.text());});
  page.on('requestfailed', r=>receipt.errors.push(r.url()+': '+r.failure().errorText));
  await page.goto(pathToFileURL(resolve(mechanical, 'generated/inspection.html')).href);
  const report = JSON.parse(await readFile(resolve(mechanical, 'generated/comparison.json'),'utf8'));
  let rows = 0;
  for (const a of report.alternatives) {
    await page.locator('#alternative').selectOption(a.id);
    assert.equal(await page.locator('#detail').textContent(), '');
    let count = 0;
    for (const b of a.boards) {
      await page.locator('#board').selectOption(b.id);
      assert.equal(await page.locator('#detail').textContent(), '');
      const expected = a.trimmers.filter(t=>t.board===b.id);
      assert.deepEqual(await page.locator('#trims button').allTextContents(), expected.map(t=>t.ref));
      count += expected.length;
      for (const face of ['F.Cu','B.Cu']) {
        const t = expected.find(t=>t.mounted_face===face);
        await page.getByRole('button', {name:t.ref,exact:true}).click();
        assert.deepEqual(JSON.parse(await page.locator('#detail').textContent()),t);
        assert.equal(await page.locator('#face').inputValue(),face);
        await page.locator('#face').selectOption(face==='F.Cu'?'B.Cu':'F.Cu');
        assert.equal(await page.locator('#detail').textContent(),'');
      }
      await page.getByRole('button',{name:expected[0].ref,exact:true}).click();
      receipt.assertions.push(`${a.id}/${b.id}: real select/click, both faces, exact detail, reset and inventory`);
    }
    assert.equal(count,100); rows += count;
  }
  assert.equal(rows,500);
  await page.locator('#alternative').selectOption('three-compact');
  const representative = report.alternatives.find(a=>a.id==='three-compact').trimmers.find(t=>t.board==='KA' && t.mounted_face==='F.Cu');
  await page.getByRole('button',{name:representative.ref,exact:true}).click();
  await page.evaluate(()=>window.scrollTo(0,0));
  await page.locator('#stack').evaluate(img=>img.decode());
  const shot = async name => {await page.screenshot({path:resolve(out,name)});receipt.screenshots.push(name);};
  await shot('three-compact-1500x1200.png');
  await page.locator('#trims button').last().click(); // Playwright scrolls actual control into view.
  await page.locator('#detail').evaluate(e=>{e.scrollTop=e.scrollHeight;});
  await shot('selected-last-row.png');
  await page.locator('#conflicts').scrollIntoViewIfNeeded();
  await shot('conflicts-scroll.png');
  receipt.scroll = await page.evaluate(()=>({page:scrollY,table:document.querySelector('.scroll').scrollTop,detail:document.querySelector('#detail').scrollTop}));
  assert(receipt.scroll.page>0 && receipt.scroll.table>0 && receipt.scroll.detail>0);
  assert.deepEqual(receipt.errors,[]);
  receipt.status='PASS';
} catch(error) {receipt.status='FAIL';receipt.failure=error.stack;process.exitCode=1;}
finally {if(browser)await browser.close();await writeFile(resolve(out,'receipt.json'),JSON.stringify(receipt,null,2)+'\n');}
