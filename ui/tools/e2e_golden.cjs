/**
 * End to end on the golden package, driven only through the UI in api mode.
 * upload -> extract -> confirm -> check -> change -> generate -> recheck -> approve -> export
 * Needs the JSON printed by ui/tools/golden_setup.py. Used by live_flows.cjs (GOLDEN_JSON=<file>).
 * Every stage prints PASS or FAIL with the real outcome; a stage that cannot work live fails, nothing is faked.
 */
const fs = require('fs');

module.exports = async function runE2E({ open, go, log, goldenJson }) {
  const g = JSON.parse(fs.readFileSync(goldenJson, 'utf8'));
  const stages = [];
  const { page, errs } = await open('professional', `&product=${g.product_id}`);
  const T = 180000;
  // The dev state panel floats over the lower right of the page, so click through the DOM, not the pixels.
  const jsClick = async (sel) => { await page.waitForSelector(sel, { timeout: 30000 }); await page.$eval(sel, (e) => e.click()); };
  const text = (sel) => page.$eval(sel, (e) => e.innerText);
  const stage = async (name, fn) => {
    try { const note = await fn(); stages.push(name); log('E2E ' + name, 'PASS', note || ''); return true; }
    catch (e) { log('E2E ' + name, 'FAIL', e.message.split('\n')[0]); return false; }
  };

  const ok =
    await stage('upload', async () => {
      await go(page, 'D3 Upload or scan', 'professional/upload/loading.json');
      await page.setInputFiles('#d3File', g.pdf);
      await jsClick('#d3Upload');
      await page.waitForFunction(() => /Scan processed|Retake the photo|Upload processing failed|Upload failed/.test(document.getElementById('d3State').innerText + document.getElementById('d3Note').innerText), null, { timeout: T });
      const t = await text('#d3State');
      if (!/Scan processed/.test(t)) throw new Error('scan did not finish: ' + t.replace(/\s+/g, ' ').slice(0, 160));
      const ids = await page.evaluate(() => window.LabelLensData.CONFIG.ids);
      return `version ${ids.version_id}`;
    }) &&
    await stage('extract', async () => {
      await jsClick('#btnGoToInspect');
      await page.waitForSelector('[data-testid="extraction-status"]', { timeout: 30000 });
      const badge = await page.$eval('#dataSourceBadge', (b) => b.dataset.kind);
      if (badge !== 'api') throw new Error('extraction not live, badge ' + badge);
      const n = await page.$$eval('input[data-field]', (i) => i.length);
      return `${await text('[data-testid="extraction-status"]')}; ${n} editable unclear field(s)`;
    }) &&
    await stage('confirm', async () => {
      const names = await page.$$eval('input[data-field]', (i) => i.map((x) => x.dataset.field));
      for (const n of names) if (g.truth[n] !== undefined) await page.fill(`input[data-field="${n}"]`, g.truth[n]);
      await jsClick('#btnConfirmExtractionAction');
      await page.waitForFunction(() => /confirmed/i.test((document.querySelector('[data-testid="extraction-status"]') || {}).innerText || '') && !/Confirm failed/.test(document.getElementById('d4Note').textContent), null, { timeout: 30000 });
      return `corrected ${names.join(', ') || 'none'}`;
    }) &&
    await stage('check', async () => {
      await jsClick('#btnRunInspectionNow');
      await page.waitForSelector('[data-testid="inspect-outcome"]', { timeout: T });
      const n = await page.$$eval('[data-testid="finding"]', (x) => x.length);
      const cit = await page.$$eval('[data-testid="citation"]', (x) => x.length);
      return `${await text('[data-testid="inspect-outcome"]')}; ${n} finding(s), ${cit} citation(s)`;
    }) &&
    await stage('change', async () => {
      await jsClick('#btnGoToChanges');
      await page.waitForSelector('#btnAssessChange', { timeout: 30000 });
      await page.fill('#changeField', 'lot');
      await page.fill('#changeNewVal', 'LOT2');
      await jsClick('#btnAssessChange');
      await page.waitForFunction(() => { const n = document.getElementById('d6AssessNote'); return !n || !/Assessing/.test(n.textContent); }, null, { timeout: 60000 });
      const noteEl = await page.$('#d6AssessNote');
      const note = noteEl ? await noteEl.innerText() : '';
      if (/failed|No live|Fill/.test(note)) throw new Error(note);
      await page.waitForSelector('#btnConfirmChecklist', { timeout: 10000 });
      await jsClick('#btnConfirmChecklist');
      await page.waitForSelector('#btnGenerateDraftArtwork', { timeout: 30000 });
      return 'assessed and confirmed';
    }) &&
    await stage('generate', async () => {
      await jsClick('#btnGenerateDraftArtwork');
      await page.waitForSelector('#btnGoToReviewFromDraft, [data-testid="generate-error"]', { timeout: T });
      const e = await page.$('[data-testid="generate-error"]');
      if (e) throw new Error('API refused: ' + (await e.innerText()).replace(/\s+/g, ' '));
      const ids = await page.evaluate(() => window.LabelLensData.CONFIG.ids);
      return `draft version ${ids.version_id}, DRAFT text ${/DRAFT/.test(await text('#professionalDynamicContent'))}`;
    }) &&
    await stage('recheck', async () => {
      await jsClick('#btnGoToReviewFromDraft');
      await page.waitForSelector('#btnLiveRecheck:not([disabled])', { timeout: 30000 });
      await jsClick('#btnLiveRecheck');
      await page.waitForFunction(() => /Check .*(passed|did not pass)|Re-check failed/.test(document.getElementById('d7LiveNote').textContent), null, { timeout: T });
      const note = await text('#d7LiveNote');
      if (/failed:/.test(note)) throw new Error(note);
      if (/did not pass/.test(note)) throw new Error('re-check ran but did not pass: ' + note);
      // The golden package re-check raises B-LOT (21 CFR 801.40); D7 must draw its citation: section, title, verbatim quote.
      const lot = await page.$('[data-testid="finding"][data-rule="B-LOT"] [data-testid="citation"]');
      if (!lot) throw new Error('D7 shows no citation under the B-LOT finding');
      const ct = await lot.innerText();
      if (!/801\.40/.test(ct) || !/"[^"]{20,}"/.test(ct)) throw new Error('B-LOT citation lacks section 801.40 or a quote: ' + ct.replace(/\s+/g, ' ').slice(0, 120));
      return note + '; B-LOT citation drawn (801.40 with quote)';
    }) &&
    await stage('approve', async () => {
      await page.selectOption('[data-testid="user-select"]', 'usr_demo_reviewer');
      await page.waitForTimeout(800);
      if (await page.$eval('#btnApprove', (b) => b.disabled)) throw new Error('approve is blocked');
      await page.fill('#reviewComment', 'ui end to end run');
      await jsClick('#btnApprove');
      await page.waitForFunction(() => /Recorded|failed/i.test(document.getElementById('reviewActionNote').textContent), null, { timeout: 30000 });
      const note = await text('#reviewActionNote');
      if (!/Recorded/.test(note)) throw new Error(note);
      return note;
    }) &&
    await stage('export', async () => {
      await jsClick('.sidebar-link[data-screen="D8 Export"]');
      await page.waitForSelector('[data-testid="export-pdf"]', { timeout: 30000 });
      const kind = await page.$eval('#dataSourceBadge', (b) => b.dataset.kind);
      if (kind !== 'api') throw new Error('export not live, badge ' + kind);
      const banner = !!(await page.$('[data-testid="draft-banner"]'));
      const [dl] = await Promise.all([page.waitForEvent('download', { timeout: 30000 }), jsClick('[data-testid="export-pdf"] .dl-btn')]);
      return `downloaded ${dl.suggestedFilename().slice(0, 16)}...; DRAFT banner ${banner}; ${await text('#downloadNote')}`;
    });
  if (errs.length) log('E2E page errors', 'FAIL', errs.slice(0, 2).join('; '));
  log('E2E summary', ok && !errs.length ? 'PASS' : 'FAIL', `${stages.length}/9 stages: ${stages.join(', ')}`);
};
