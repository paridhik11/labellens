/**
 * Live DailyMed lookup in the public page (CR-28), against a running server in API mode (uses the real network).
 *
 *   PLAYWRIGHT_DIR=<dir with node_modules/playwright> BASE=http://127.0.0.1:8011 node ui/tools/live_check.cjs [name]
 *
 * Flow 1: a typed name not matched locally -> "Search DailyMed" -> candidate list (nothing picked) -> Select ->
 *         spinner text -> product page with the live label line, set id and fetch date -> P3 answers with citations.
 * Flow 2: the search answers `unavailable` (route stubbed) -> plain message, curated name still matches.
 * Flow 3: the fetch job fails (route stubbed) -> failed message, list stays usable.
 */
const path = require('path');
const { createRequire } = require('module');
const req = createRequire(path.join(process.env.PLAYWRIGHT_DIR || process.cwd(), 'x.js'));
const { chromium } = req('playwright');

const BASE = process.env.BASE || 'http://127.0.0.1:8011';
const NAME = process.argv[2] || 'cetirizine';
const URL_P = `${BASE}/ui/public/index.html?mode=api`;
let fails = 0;
const ok = (c, m) => { console.log(`${c ? 'PASS' : 'FAIL'}     ${m}`); if (!c) fails += 1; };

async function typedEmpty(page) {
  await page.goto(URL_P);
  await page.waitForFunction(() => window.LabelLensLive && window.LabelLensRenderers);
  await page.waitForSelector('[data-testid="take-photo"]'); // the page opens on the scan tab; wait for it before showing a match
  await page.evaluate((name) => {
    window.LabelLensLive.setLastName(name);
    window.LabelLensPublicScan.showMatch({ banner: 'Authenticity not verified. Based on a reference label match.', outcome: 'no_reference_match', candidates: [], message: 'No reference match.' });
  }, NAME);
  await page.waitForSelector('[data-testid="live-search-go"]');
}

(async () => {
  const browser = await chromium.launch();
  const errors = [];

  // Flow 1: the real thing
  let page = await browser.newPage();
  page.on('pageerror', (e) => errors.push(e.message));
  await typedEmpty(page);
  await page.click('[data-testid="live-search-go"]');
  await page.waitForSelector('[data-testid="live-candidate"]', { timeout: 30000 });
  const n = await page.locator('[data-testid="live-candidate"]').count();
  ok(n >= 1 && n <= 10, `candidate list shown (${n}), nothing selected yet`);
  ok(await page.locator('[data-testid="live-label"]').count() === 0, 'no product page before a pick');
  await page.locator('[data-testid="live-select"]').first().click();
  await page.waitForSelector('[data-testid="live-fetching"]', { timeout: 5000 });
  const spinner = await page.locator('[data-testid="live-fetching"]').innerText();
  ok(/little while/.test(spinner), 'fetching state says this can take a little while');
  await page.waitForSelector('[data-testid="live-label"]', { timeout: 150000 });
  const label = await page.locator('[data-testid="live-label"]').innerText();
  ok(/Fetched live from DailyMed, not in the curated set/.test(label) && /set id/.test(label) && /Fetched on 20/.test(label),
    'live label line with set id and fetch date');
  ok(!/Confidence/.test(await page.locator('body').innerText()), 'no match confidence shown for a live label');
  await page.getByRole('button', { name: /Ask questions about this medicine/ }).click();
  await page.waitForSelector('#p3QuestionInput');
  await page.fill('#p3QuestionInput', `What are the warnings for ${NAME}?`);
  await page.click('#btnP3AskSubmit');
  await page.waitForSelector('[data-testid="citation"], [data-testid="abstained"]', { timeout: 60000 });
  ok(await page.locator('[data-testid="citation"]').count() >= 1, 'P3 shows at least one citation from the fetched label');
  await page.close();

  // Flow 2: offline
  page = await browser.newPage();
  page.on('pageerror', (e) => errors.push(e.message));
  await page.route('**/public/live/search', (route) => route.fulfill({
    status: 200, contentType: 'application/json',
    body: JSON.stringify({ outcome: 'unavailable', query: NAME, source: 'DailyMed', reason: 'offline', candidates: [], message: 'DailyMed cannot be reached from this computer. The 30 curated medicines still work: type one of their names or scan its pack.' }),
  }));
  await typedEmpty(page);
  await page.click('[data-testid="live-search-go"]');
  await page.waitForSelector('[data-testid="live-offline"]');
  ok(/curated medicines still work/.test(await page.locator('[data-testid="live-offline"]').innerText()), 'offline: plain message, curated fallback named');
  await page.close();

  // Flow 3: fetch fails
  page = await browser.newPage();
  page.on('pageerror', (e) => errors.push(e.message));
  await page.route('**/public/live/fetch', (route) => route.fulfill({
    status: 202, contentType: 'application/json', body: JSON.stringify({ job_id: 'job_stub_fail', kind: 'live_fetch', state: 'queued', progress: 0 }),
  }));
  await page.route('**/jobs/job_stub_fail', (route) => route.fulfill({
    status: 200, contentType: 'application/json',
    body: JSON.stringify({ job_id: 'job_stub_fail', kind: 'live_fetch', state: 'failed', progress: 1, error: { error: 'live_fetch_failed', message: 'DailyMed did not answer in time. The curated medicines still work.', details: { reason: 'timeout' } } }),
  }));
  await typedEmpty(page);
  await page.click('[data-testid="live-search-go"]');
  await page.waitForSelector('[data-testid="live-candidate"]', { timeout: 30000 });
  await page.locator('[data-testid="live-select"]').first().click();
  await page.waitForSelector('[data-testid="live-failed"]');
  ok(await page.locator('[data-testid="live-select"]').first().isEnabled(), 'failed fetch: list stays usable');
  await page.close();

  ok(errors.length === 0, `page errors ${errors.length}${errors.length ? ': ' + errors[0] : ''}`);
  await browser.close();
  console.log(`${fails} FAIL`);
  process.exit(fails ? 1 : 0);
})();
