/**
 * Headless check of the public page camera flow with a FAKE camera stream (Chromium flags
 * --use-fake-device-for-media-stream and --use-fake-ui-for-media-stream), against a running server.
 *
 *   PLAYWRIGHT_DIR=<dir with node_modules/playwright> BASE=http://127.0.0.1:8000 node ui/tools/camera_check.cjs
 *
 * Checks (each prints PASS or FAIL, exit code 1 on any FAIL):
 *  1. Take a photo opens a live preview, Capture shows the frame, Retake returns to the preview, Use this photo
 *     sends a JPEG no larger than 1600 px on its long side to POST /public/scans, and the server answers 202 with a
 *     job of kind public_scan (the scan job starts).
 *  2. Camera permission denied: a clear message, and Upload a photo still works.
 *  3. No camera: a clear message.
 *  4. Phone path: with a coarse pointer and a mobile user agent, Take a photo opens the capture input
 *     (capture="environment") and sends the chosen file.
 */
const path = require('path');
const fs = require('fs');
const os = require('os');
const { createRequire } = require('module');
const req = createRequire(path.join(process.env.PLAYWRIGHT_DIR || process.cwd(), 'x.js'));
const { chromium } = req('playwright');
const BASE = process.env.BASE || 'http://127.0.0.1:8000';
const URL_P1 = `${BASE}/ui/public/index.html?dev=1&devopen=1&mode=api`;

const zlib = require('zlib');
function crc32(buf) {
  let c, crc = 0xffffffff;
  for (let n = 0; n < buf.length; n++) { c = (crc ^ buf[n]) & 0xff; for (let k = 0; k < 8; k++) c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1; crc = (crc >>> 8) ^ c; }
  return (crc ^ 0xffffffff) >>> 0;
}
/** A valid grey PNG of the given size (the check needs a file the browser can decode). */
function writePng(file, w, h) {
  const chunk = (type, data) => { const t = Buffer.from(type); const len = Buffer.alloc(4); len.writeUInt32BE(data.length); const crc = Buffer.alloc(4); crc.writeUInt32BE(crc32(Buffer.concat([t, data]))); return Buffer.concat([len, t, data, crc]); };
  const ihdr = Buffer.alloc(13); ihdr.writeUInt32BE(w, 0); ihdr.writeUInt32BE(h, 4); ihdr[8] = 8; ihdr[9] = 2;
  const row = Buffer.concat([Buffer.from([0]), Buffer.alloc(w * 3, 170)]);
  const raw = Buffer.concat(Array.from({ length: h }, () => row));
  fs.writeFileSync(file, Buffer.concat([Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]), chunk('IHDR', ihdr), chunk('IDAT', zlib.deflateSync(raw)), chunk('IEND', Buffer.alloc(0))]));
}

let failed = 0;
const log = (name, ok, note) => { if (!ok) failed += 1; console.log(`${ok ? 'PASS' : 'FAIL'}  ${name} ${note || ''}`); };

async function openP1(browser, opts = {}, init) {
  const ctx = await browser.newContext({ viewport: { width: 1100, height: 900 }, ...opts });
  if (init) await ctx.addInitScript(init);
  const page = await ctx.newPage();
  const errors = [];
  page.on('pageerror', (e) => errors.push(e.message));
  await page.goto(URL_P1);
  await page.waitForSelector('#devStateButtons .btn-state');
  await page.evaluate(() => window.LabelLensStateSwitcher.setScreen('P1 Scan and Understand', 'empty (idle)'));
  await page.waitForSelector('[data-testid="take-photo"]');
  return { ctx, page, errors };
}

function unusedJpegDims(buf) {
  // read the size from the JPEG start-of-frame marker
  let i = 2;
  while (i < buf.length) {
    if (buf[i] !== 0xff) { i += 1; continue; }
    const marker = buf[i + 1];
    const len = buf.readUInt16BE(i + 2);
    if (marker >= 0xc0 && marker <= 0xcf && marker !== 0xc4 && marker !== 0xc8 && marker !== 0xcc) {
      return { h: buf.readUInt16BE(i + 5), w: buf.readUInt16BE(i + 7) };
    }
    i += 2 + len;
  }
  return null;
}

(async () => {
  const browser = await chromium.launch({ args: ['--use-fake-device-for-media-stream', '--use-fake-ui-for-media-stream'] });

  // 1. fake camera: preview, capture, retake, capture again, use, job starts
  try {
    const spy = `const f = window.fetch; window.fetch = function (u, o) { try { if (o && o.body instanceof FormData && String(u).endsWith('/public/scans')) { window.__sent = o.body.get('file'); } } catch (e) {} return f.apply(this, arguments); };`;
    const { ctx, page, errors } = await openP1(browser, {}, spy);
    const label = await page.$eval('[data-testid="take-photo"]', (b) => b.textContent.trim());
    const labelUp = await page.$eval('[data-testid="upload-photo"]', (b) => b.textContent.trim());
    log('buttons are named Take a photo and Upload a photo', label === 'Take a photo' && labelUp === 'Upload a photo', `(${label} | ${labelUp})`);
    await page.click('[data-testid="take-photo"]');
    await page.waitForSelector('[data-testid="camera-video"]');
    await page.waitForFunction(() => { const v = document.querySelector('[data-testid="camera-video"]'); return v && v.videoWidth > 0; }, null, { timeout: 15000 });
    log('live preview starts', true);
    await page.click('[data-testid="camera-capture"]');
    await page.waitForSelector('[data-testid="capture-review"]');
    log('capture shows the frame with Retake and Use this photo', !!(await page.$('[data-testid="capture-retake"]')) && !!(await page.$('[data-testid="capture-use"]')));
    await page.click('[data-testid="capture-retake"]');
    await page.waitForSelector('[data-testid="camera-video"]');
    await page.waitForFunction(() => document.querySelector('[data-testid="camera-video"]').videoWidth > 0, null, { timeout: 15000 });
    log('Retake returns to the live preview', true);
    await page.click('[data-testid="camera-capture"]');
    await page.waitForSelector('[data-testid="capture-use"]');
    const [request] = await Promise.all([
      page.waitForRequest((r) => r.url().endsWith('/public/scans') && r.method() === 'POST'),
      page.click('[data-testid="capture-use"]'),
    ]);
    const response = await request.response();
    const body = await response.json();
    log('upload starts a scan job (202, kind public_scan)', response.status() === 202 && body.kind === 'public_scan', `(HTTP ${response.status()}, kind ${body.kind}, job ${body.job_id})`);
    const sent = await page.evaluate(async () => {
      const f = window.__sent;
      if (!f) return null;
      const bmp = await createImageBitmap(f);
      return { type: f.type, size: f.size, w: bmp.width, h: bmp.height };
    });
    log('sent file is a JPEG with long side at most 1600 px', !!sent && sent.type === 'image/jpeg' && Math.max(sent.w, sent.h) <= 1600,
      sent ? `(${sent.type}, ${sent.w}x${sent.h}, ${sent.size} bytes)` : '(nothing captured)');
    await page.waitForSelector('[data-testid="scan-failed"], [data-testid="scan-extra"], [data-testid="not-identified"], [data-testid="scan-evidence"]', { timeout: 120000 });
    const gone = !(await page.$('[data-testid="scan-progress"]'));
    const shown = await page.$eval('#publicDynamicContent', (e) => e.innerText.replace(/\s+/g, ' ').slice(0, 200));
    log('the job ends in a visible outcome (retake, not identified, review or match), no hang', gone, `(${shown})`);
    log('no page errors', errors.length === 0, errors.join('; '));
    await ctx.close();
  } catch (e) { log('fake camera flow', false, e.message.split('\n')[0]); }

  // 2. permission denied, 3. no camera: clear message, upload still works
  for (const [name, errName, expect] of [['permission denied', 'NotAllowedError', /permission was denied/i], ['no camera', 'NotFoundError', /No camera was found/i]]) {
    try {
      const init = `navigator.mediaDevices.getUserMedia = () => Promise.reject(new DOMException('x', '${errName}'));`;
      const { ctx, page } = await openP1(browser, {}, init);
      await page.click('[data-testid="take-photo"]');
      await page.waitForFunction(() => /camera/i.test(document.getElementById('p1Note').textContent), null, { timeout: 5000 });
      const msg = await page.$eval('#p1Note', (e) => e.textContent);
      log(`${name}: clear message`, expect.test(msg), `(${msg})`);
      if (errName === 'NotAllowedError') {
        const png = path.join(os.tmpdir(), 'cam_check.png');
        writePng(png, 200, 150);
        const [chooser] = await Promise.all([page.waitForEvent('filechooser'), page.click('[data-testid="upload-photo"]')]);
        const [request] = await Promise.all([page.waitForRequest((r) => r.url().endsWith('/public/scans')), chooser.setFiles(png)]);
        log('upload path still works after a denied camera', request.method() === 'POST');
      }
      await ctx.close();
    } catch (e) { log(`${name} flow`, false, e.message.split('\n')[0]); }
  }

  // 4. phone: coarse pointer + mobile user agent -> capture input
  try {
    const { ctx, page } = await openP1(browser, {
      userAgent: 'Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Mobile Safari/537.36',
      hasTouch: true, isMobile: true, viewport: { width: 412, height: 860 },
    });
    const png = path.join(os.tmpdir(), 'cam_check_phone.png');
    writePng(png, 200, 150);
    const [chooser] = await Promise.all([page.waitForEvent('filechooser'), page.click('[data-testid="take-photo"]')]);
    const attr = await page.$eval('[data-testid="p1-camera-input"]', (i) => i.getAttribute('capture'));
    log('phone: Take a photo opens the capture input', attr === 'environment', `(capture=${attr})`);
    const [request] = await Promise.all([page.waitForRequest((r) => r.url().endsWith('/public/scans')), chooser.setFiles(png)]);
    log('phone: the chosen photo is sent', request.method() === 'POST');
    await ctx.close();
  } catch (e) { log('phone path', false, e.message.split('\n')[0]); }

  await browser.close();
  console.log(failed ? `${failed} FAILED` : 'ALL PASSED');
  process.exit(failed ? 1 : 0);
})();
