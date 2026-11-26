import test, { before, after } from 'node:test';
import assert from 'node:assert/strict';
import { createServer } from 'node:http';
import { readFile, mkdir } from 'node:fs/promises';
import { resolve, extname, join } from 'node:path';
import { pathToFileURL } from 'node:url';
import { chromium } from 'playwright';
import { previewFixture } from '../tools/cat-preview-fixture.mjs';

const root = resolve('public');
const contentTypes = { '.html': 'text/html; charset=utf-8', '.css': 'text/css', '.js': 'text/javascript',
  '.webp': 'image/webp', '.mp4': 'video/mp4', '.mp3': 'audio/mpeg', '.svg': 'image/svg+xml' };
let browser;
before(async () => {
  browser = await chromium.launch(process.env.CAT_BROWSER_EXECUTABLE
    ? { executablePath: process.env.CAT_BROWSER_EXECUTABLE }
    : { channel: 'chrome' });
});
after(() => browser?.close());

async function setup(t, options = {}) {
  const fixture = previewFixture(options);
  let releaseFeed, markFeedStarted, didDefer = false;
  const feedStarted = new Promise(resolve => { markFeedStarted = resolve; });
  const feedGate = new Promise(resolve => { releaseFeed = resolve; });
  const server = createServer(async (req, res) => {
    const path = new URL(req.url, 'http://127.0.0.1').pathname;
    if (path.startsWith('/api/')) {
      let input = '';
      for await (const chunk of req) input += chunk;
      const { status, data } = fixture.handle(path.slice(5), input ? JSON.parse(input) : {});
      if(options.deferSuccessfulFeed && path === '/api/feed' && status === 200 && !didDefer){
        didDefer = true;
        markFeedStarted();
        await feedGate;
      }
      res.writeHead(status, { 'content-type': 'application/json' });
      res.end(JSON.stringify(data));
      return;
    }
    const file = resolve(root, '.' + (path === '/' ? '/index.html' : path));
    if (!file.startsWith(root)) { res.writeHead(404).end(); return; }
    try { const contents = await readFile(file); res.writeHead(200, { 'content-type': contentTypes[extname(file)] || 'application/octet-stream' }); res.end(contents); }
    catch { res.writeHead(404).end(); }
  });
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  const page = await browser.newPage({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 1,
    isMobile: true, hasTouch: true, reducedMotion: options.reduced ? 'reduce' : 'no-preference' });
  t.after(async () => { releaseFeed(); await page.close(); await new Promise(resolve => server.close(resolve)); });
  page.setDefaultTimeout(60000);
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));
  // The real site uses Google Fonts; make the preview hermetic.
  await page.route('https://**/*', route => route.abort());
  await page.route('**/assets/welcome-intro.mp4', route => route.abort());
  await page.goto(`http://127.0.0.1:${server.address().port}/?noIntro#cat`, { waitUntil: 'domcontentloaded' });
  await page.waitForFunction(n => document.querySelector('#fishCount')?.textContent === String(n), fixture.state.fish);
  const screenshot = async (name) => {
    if (!process.env.CAT_PREVIEW_DIR) return;
    await mkdir(process.env.CAT_PREVIEW_DIR, { recursive: true });
    await page.waitForFunction(() => getComputedStyle(document.querySelector('.page')).opacity === '1');
    await page.screenshot({ path: join(process.env.CAT_PREVIEW_DIR, name), fullPage: true, animations: 'allow' });
  };
  return { page, fixture, errors, screenshot, feedStarted, releaseFeed };
}

test('cat page: five touches, one task reward, one fish, all fish and visible variants', { timeout: 300000 }, async t => {
  const { page, fixture, errors, screenshot } = await setup(t);
  await page.locator('#soundBtn').click();
  await screenshot('cat-house-mobile.png');
  const cat = page.locator('#petCat');
  for (let i = 0; i < 5; i++) await cat.click();
  console.log('Browser: five touches registered');
  assert.equal(await page.locator('#petCount').textContent(), '5');
  assert.match(await page.locator('#petRemaining').textContent(), /任務達成/);
  await page.locator('.nav button[data-go="tasks"]').click();
  console.log('Browser: task page opened');
  await page.locator('[data-claim="pet"]').click();
  await page.waitForFunction(() => !document.querySelector('[data-claim="pet"]'));
  assert.equal(fixture.calls.filter(c => c.path === 'claim').length, 1);
  console.log('Browser: task reward claimed');
  await page.locator('.nav button[data-go="cat"]').click();
  const watchPoses = () => page.evaluate(() => {
    const stage = document.querySelector('#petCat');
    window.catTestPoses = [];
    new MutationObserver(() => window.catTestPoses.push(stage.dataset.pose))
      .observe(stage, { attributes: true, attributeFilter: ['data-pose'] });
  });
  await watchPoses();
  const locked = await page.locator('#feedOne').evaluate(button => {
    button.click();
    // Simulate a second handler invocation before the first request has resolved.
    const other = document.querySelector('#feedAll');
    other.onclick();
    return button.disabled && other.disabled;
  });
  assert.equal(locked, true);
  await page.waitForFunction(() => document.querySelector('#fishCount')?.textContent === '4');
  await page.waitForFunction(() => !document.querySelector('#feedOne').disabled);
  assert.ok((await page.evaluate(() => window.catTestPoses)).includes('nibble'));
  assert.deepEqual(fixture.calls.filter(c => c.path === 'feed').map(c => c.body.n), [1]);
  assert.equal(await page.locator('#chipCoin').textContent(), '0.1');
  await watchPoses();
  await page.locator('#feedAll').click();
  await page.waitForFunction(() => document.querySelector('#fishCount')?.textContent === '0');
  await page.waitForFunction(() => window.catTestPoses.includes('celebrate'));
  const poses = await page.evaluate(() => window.catTestPoses);
  assert.ok(poses.includes('feast') && poses.includes('celebrate'));
  assert.deepEqual(fixture.calls.filter(c => c.path === 'feed').map(c => c.body.n), [1, 4]);
  assert.equal(await page.locator('#chipCoin').textContent(), '0.5');
  assert.equal(await page.locator('#feedOne').isDisabled(), true);
  assert.deepEqual(errors, []);
});

test('standalone preview opens offline and shows all new watercolor assets', { timeout: 300000, skip: !process.env.CAT_PREVIEW_DIR }, async t => {
  const page = await browser.newPage({ viewport: { width: 390, height: 940 }, deviceScaleFactor: 1 });
  t.after(() => page.close());
  page.setDefaultTimeout(60000);
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));
  await page.route('http://**/*', route => route.abort());
  await page.route('https://**/*', route => route.abort());
  await page.goto(pathToFileURL(join(process.env.CAT_PREVIEW_DIR, 'cat-house-preview.html')).href);
  await page.waitForFunction(() => document.querySelector('#fishCount')?.textContent === '4');
  assert.equal(await page.locator('.cat-pose img').evaluateAll(imgs => imgs.every(img => img.complete && img.naturalWidth > 0)), true);
  // Hold poses solely for reproducible visual inspection, independent of machine speed.
  for (const [pose, visual, label, message, filename] of [
    ['curious', 'curious', '好奇地看看', '喵～妳來啦！', 'cat-house-curious.png'],
    ['nibble', 'eat', '小口嚼嚼', '好香的小魚乾！', 'cat-house-feeding.png'],
    ['celebrate', 'happy', '吃得好滿足', '吃飽了，謝謝妳～', 'cat-house-happy.png']
  ]) {
    await page.evaluate(({pose, visual, label, message}) => {
      activeCatMotion.destroy();
      const stage = document.querySelector('#petCat');
      stage.dataset.pose = pose;
      stage.dataset.visual = visual;
      stage.removeAttribute('data-video');
      document.querySelector('#catMood').textContent = label;
      document.querySelector('#houseTalk').textContent = message;
    }, {pose, visual, label, message});
    await page.waitForFunction(v => getComputedStyle(document.querySelector('.cat-pose--' + v)).opacity === '1', visual);
    await page.screenshot({ path: join(process.env.CAT_PREVIEW_DIR, filename), fullPage: true });
  }
  assert.deepEqual(errors, []);
});

test('cat page: errors keep rewards unchanged; reduced motion and route changes are safe', { timeout: 300000 }, async t => {
  const { page, fixture, errors, feedStarted, releaseFeed } = await setup(t, { failFeed: true, reduced: true, deferSuccessfulFeed: true });
  await page.locator('#soundBtn').click();
  await page.locator('#petCat').focus();
  await page.keyboard.press('Enter');
  assert.equal(await page.locator('#petCount').textContent(), '1');
  assert.equal(await page.locator('.cat-video--pet').evaluate(v => v.paused), true);
  await page.locator('#feedOne').click();
  await page.waitForFunction(() => !document.querySelector('#feedOne').disabled);
  assert.equal(await page.locator('#fishCount').textContent(), '4');
  assert.equal(fixture.state.coins, 0);
  await page.locator('#feedOne').click();
  await feedStarted;
  await page.locator('.nav button[data-go="tasks"]').click();
  await page.locator('[data-breath]').click();
  await page.locator('#breathBox').waitFor({ state: 'visible' });
  releaseFeed();
  await page.waitForFunction(() => document.querySelector('#chipCoin')?.textContent === '0.1');
  assert.equal(await page.locator('#breathBox').isVisible(), true, 'a delayed feed must not reset another task');
  await page.locator('.nav button[data-go="cat"]').click();
  await page.waitForFunction(() => document.querySelector('#fishCount')?.textContent === '3' && !document.querySelector('#feedOne').disabled);
  await page.emulateMedia({ reducedMotion: 'no-preference' });
  await page.evaluate(() => {
    const stage = document.querySelector('#petCat');
    const observer = new MutationObserver(() => {
      if (stage.dataset.pose !== 'anticipate') return;
      observer.disconnect();
      document.querySelector('.nav button[data-go="home"]').click();
    });
    observer.observe(stage, { attributes: true, attributeFilter: ['data-pose'] });
    document.querySelector('#feedOne').click();
  });
  await page.locator('.nav button[data-go="home"][aria-current="page"]').waitFor();
  await page.waitForFunction(() => document.querySelectorAll('.fly').length === 0);
  assert.equal(await page.locator('#chipCoin').textContent(), '0.2');
  await page.locator('.nav button[data-go="home"]').click();
  await page.locator('.nav button[data-go="cat"]').click();
  await page.waitForFunction(() => document.querySelector('#fishCount')?.textContent === '2' && !document.querySelector('#feedOne').disabled);
  assert.equal(await page.locator('#chipCoin').textContent(), '0.2');
  assert.deepEqual(errors, []);
});

test('cat page: a deferred feed refreshes the open wallet', { timeout: 300000 }, async t => {
  const { page, errors, feedStarted, releaseFeed } = await setup(t, { deferSuccessfulFeed: true });
  await page.locator('#feedOne').click();
  await feedStarted;
  await page.locator('.nav button[data-go="coins"]').click();
  assert.match(await page.locator('.purse .bal').textContent(), /0\.0/);
  releaseFeed();
  await page.waitForFunction(() => document.querySelector('.purse .bal')?.textContent.startsWith('0.1'));
  assert.equal(await page.locator('#chipFish').textContent(), '3');
  assert.match(await page.locator('.hist').textContent(), /餵貓咪累積/);
  assert.deepEqual(errors, []);
});

test('confirmed feeding updates the bowl during the animation and keeps the cat mounted', { timeout: 300000 }, async t => {
  const { page } = await setup(t);
  const stage = await page.locator('#petCat').elementHandle();
  const firstReaction = await page.evaluate(() => new Promise(resolve => {
    const stage = document.querySelector('#petCat');
    const observer = new MutationObserver(() => {
      if (stage.dataset.pose !== 'anticipate') return;
      observer.disconnect();
      resolve({ fish: document.querySelector('#fishCount').textContent, coins: document.querySelector('#chipCoin').textContent });
    });
    observer.observe(stage, { attributes: true, attributeFilter: ['data-pose'] });
    document.querySelector('#feedOne').click();
  }));
  assert.deepEqual(firstReaction, { fish: '3', coins: '0.1' });
  await page.waitForFunction(() => !document.querySelector('#feedOne').disabled);
  assert.equal(await stage.evaluate(el => el === document.querySelector('#petCat')), true);
});
