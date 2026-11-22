/**
 * ui/pro/pro.js
 * Single-workflow Professional page: Products, Add label, Check, Change, Revise artwork, Review and approve, Export.
 *
 * Rules kept here:
 * - Every value on screen comes from an API response (window.ProApi) or from what the person typed. The only
 *   fixed text is the help text and the plain sentences that explain an API decision.
 * - No mock data, no sample results, no fallback. A failed call shows the API's message and a Retry button.
 * - Approval is decided by the API (role, hash, passed check). The page never works around a refusal.
 * - Same call sequence as scripts/demo_flow.py. Operations: docs/PRO_UI_API_MAP.md.
 * - No em dashes.
 */
(function () {
  const A = window.ProApi;
  const $ = (sel) => document.querySelector(sel);
  const esc = (v) => String(v === undefined || v === null ? '' : v)
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&#39;');

  const STAGES = [
    ['products', 'Products'], ['add', 'Add label'], ['check', 'Check'], ['change', 'Change'],
    ['artwork', 'Revise artwork'], ['review', 'Review and approve'], ['export', 'Export'],
  ];
  const NEEDS_PRODUCT = new Set(['check', 'change', 'artwork', 'review', 'export']);
  // Record fields of the add form, in the order the task lists them.
  const RECORD_FIELDS = [
    ['name', 'Product name'], ['manufacturer', 'Manufacturer'], ['manufacturer_address', 'Manufacturer address'],
    ['model', 'Model'], ['lot', 'Lot'], ['expiry', 'Expiry date (YYYY-MM-DD)'], ['udi_di', 'UDI-DI (device identifier)'],
    ['serial', 'Serial'], ['sterilization', 'Sterilization'], ['storage', 'Storage'],
  ];
  // Fields a change can edit: canonical names of docs/CHANGE_SPEC.md section 2.
  const CHANGE_FIELDS = [
    ['name', 'Name'], ['model', 'Model'], ['manufacturer', 'Manufacturer'], ['manufacturer_address', 'Manufacturer address'],
    ['storage', 'Storage'], ['sterilization', 'Sterilization'], ['lot', 'Lot'], ['expiry', 'Expiry (YYYY-MM-DD)'],
    ['serial', 'Serial'], ['udi_di', 'UDI-DI'],
  ];
  const EXTRA_KEYS = ['lot', 'expiry', 'serial'];
  // Label text field (extractor name) that carries each record field (src/checker/synthetic.py FIELD_ORDER).
  const LABEL_FIELD = { name: 'product_name', manufacturer: 'manufacturer', manufacturer_address: 'manufacturer_address', model: 'model', lot: 'lot', expiry: 'expiry' };
  const PREFIX_RE = /^\s*[A-Za-z][A-Za-z .#/]{0,15}:\s*/;
  const TEST_UDI = '00000000000000';

  function freshAdd() {
    return { file: null, source: 'upload', previewUrl: null, read: null, form: {}, notes: {}, prog: null, camMsg: '' };
  }

  const S = {
    stage: 'products', role: 'editor', me: null,
    busy: null, busyMsg: '', busyStart: 0, errors: {}, flash: '',
    products: null, filter: '',
    add: freshAdd(), cam: null,
    product: null, versions: [], labelId: null, history: [],
    checks: {},
    evidence: { open: false, query: 'format of expiration date on a device label', question: 'What must a label show for the expiration date?', search: null, answer: null },
    change: { field: 'lot', value: '', assessment: null, decisions: {}, confirmed: null },
    artwork: null, artworkL: null, previewUrl: null,
    exports: {}, reviews: {}, reviewComment: '', lastReview: null,
    download: null, print: { file: null, condition: 'clean_print_scan', result: null, list: {} },
  };

  // ---------------------------------------------------------------- small helpers

  const currentVersion = () => (S.versions.length ? S.versions[S.versions.length - 1] : null);
  const latestGenerated = () => { const v = currentVersion(); return v && v.kind === 'generated' ? v : null; };
  const isIntake = (p) => ((p.record || {}).extra || {}).intake === 'true';
  const recVal = (rec, f) => (EXTRA_KEYS.includes(f) ? ((rec.extra || {})[f] || '') : (rec[f] || ''));
  const secs = () => Math.floor((Date.now() - S.busyStart) / 1000);
  const fmtVal = (v) => (v === TEST_UDI ? `${esc(v)} <span class="badge warn">TEST</span>` : esc(v || ''));
  const when = (t) => esc(String(t || '').replace('T', ' ').replace('Z', ' UTC'));
  const isEditor = () => S.role === 'editor';

  function btn(act, label, o) {
    const opt = o || {};
    const attrs = Object.entries(opt.data || {}).map(([k, v]) => ` data-${k}="${esc(v)}"`).join('');
    return `<button type="button" class="btn${opt.primary ? ' primary' : ''}${opt.small ? ' small' : ''}" data-act="${act}"${attrs}`
      + ` data-testid="${esc(opt.testid || 'btn-' + act)}"${opt.disabled || S.busy ? ' disabled' : ''}>${label}</button>`;
  }

  function statusHtml(id) {
    if (S.busy === id) {
      return `<div class="status" data-testid="busy-${id}"><span class="spinner"></span><span data-busymsg>${esc(S.busyMsg || 'Working...')}</span><span class="muted" data-secs>${secs()} s</span></div>`;
    }
    const e = S.errors[id];
    if (e) {
      return `<div class="err" data-testid="error-${id}"><div class="msg">${esc(e.message)}</div>`
        + `<button type="button" class="btn small" data-retry="${id}" data-testid="retry-${id}"${S.busy ? ' disabled' : ''}>Retry</button></div>`;
    }
    return '';
  }

  // ---------------------------------------------------------------- running actions

  let ticker = null;
  function setMsg(text) {
    S.busyMsg = text;
    const el = document.querySelector('[data-busymsg]');
    if (el) el.textContent = text;
  }

  /** Run one action: spinner and seconds while it runs, every button disabled, error text and Retry when it fails. */
  async function act(id, fn) {
    if (S.busy) return;
    S.busy = id; S.busyMsg = ''; S.busyStart = Date.now(); delete S.errors[id];
    render();
    ticker = setInterval(() => { const el = document.querySelector('[data-secs]'); if (el) el.textContent = `${secs()} s`; }, 250);
    try {
      await fn();
    } catch (e) {
      S.errors[id] = { message: e && e.message ? e.message : String(e), retry: () => act(id, fn) };
      if (e && e.network) setLive(false);
    } finally {
      clearInterval(ticker); ticker = null;
      S.busy = null;
      render();
    }
  }

  // ---------------------------------------------------------------- server health and role

  function setLive(ok) {
    const el = $('#proLive');
    el.classList.toggle('ok', ok); el.classList.toggle('down', !ok);
    $('#proLiveText').textContent = ok ? 'LIVE API' : 'API offline';
    el.title = ok ? `LIVE API: ${A.BASE}/health answered ok` : `No answer from ${A.BASE}/health. Start scripts/run_demo.py.`;
  }
  async function healthLoop() {
    try { setLive(await A.health()); } catch (e) { setLive(false); }
  }

  function setRole(role) {
    if (S.busy) return;
    S.role = role;
    A.setUser(A.USERS[role]);
    S.me = null;
    act('role', async () => { S.me = await A.me(); });
  }

  // ---------------------------------------------------------------- navigation and loading

  function goStage(stage) {
    if (S.busy) return;
    if (NEEDS_PRODUCT.has(stage) && !S.product) return;
    S.stage = stage; S.flash = '';
    if (stage === 'products') {
      history.replaceState(null, '', '#');
      act('products', loadProducts);
      return;
    }
    if (stage === 'review' && latestGenerated()) { act('review-load', loadReview); return; }
    if (stage === 'export' && latestGenerated()) { act('export-load', loadExport); return; }
    render();
  }

  async function loadProducts() {
    setMsg('Loading products');
    S.products = await A.listProducts();
  }

  async function loadProduct(pid) {
    setMsg('Loading the product');
    const detail = await A.getProduct(pid);
    if (!S.product || S.product.product.product_id !== pid) {
      Object.assign(S, { checks: {}, artwork: null, artworkL: null, exports: {}, reviews: {}, lastReview: null, download: null });
      S.change = { field: 'lot', value: '', assessment: null, decisions: {}, confirmed: null };
      S.print = { file: null, condition: 'clean_print_scan', result: null, list: {} };
      S.evidence.search = null; S.evidence.answer = null;
      if (S.previewUrl) { URL.revokeObjectURL(S.previewUrl); S.previewUrl = null; }
    }
    S.product = detail;
    S.labelId = detail.labels.length ? detail.labels[0].label_id : null;
    setMsg('Loading label versions and history');
    S.versions = S.labelId ? await A.labelVersions(S.labelId) : [];
    S.history = await A.history(pid);
    history.replaceState(null, '', `#product=${encodeURIComponent(pid)}`);
  }

  function openProduct(pid) {
    act('open', async () => { await loadProduct(pid); S.stage = 'check'; S.flash = ''; });
  }

  async function loadReview() {
    const v = latestGenerated().version_id;
    setMsg('Loading the export hash and the review decisions');
    S.exports[v] = await A.exports(v);
    S.reviews[v] = await A.reviews(v);
  }

  async function loadExport() {
    const v = latestGenerated().version_id;
    setMsg('Loading the export package');
    S.exports[v] = await A.exports(v);
    S.print.list[v] = await A.printVerifications(v);
    S.history = await A.history(S.product.product.product_id);
  }

  // ---------------------------------------------------------------- add label: read, prefill, save

  function setFile(file, source) {
    if (S.add.previewUrl) URL.revokeObjectURL(S.add.previewUrl);
    const keep = S.add.camMsg;
    S.add = freshAdd();
    S.add.camMsg = keep;
    S.add.file = file; S.add.source = source;
    if (/^image\//.test(file.type)) S.add.previewUrl = URL.createObjectURL(file);
  }

  /** The one internal intake record that holds label reads before a product exists (uploadScan needs a product_id). */
  async function ensureIntake() {
    const items = await A.listProducts();
    const found = items.find(isIntake);
    if (found) return found.product.product_id;
    const made = await A.registerProduct({ name: 'Label intake (internal, not a product)', extra: { intake: 'true' }, intended_market: ['US'] });
    return made.product.product_id;
  }

  async function doRead() {
    if (!S.add.file) throw new Error('Choose a label file, take a photo or use the sample first.');
    setMsg('Preparing the intake record');
    const intake = await ensureIntake();
    setMsg('Uploading the label');
    const scan = await A.upload(S.add.file, S.add.source, intake, (j) => setMsg(`Reading text and barcode: ${j.message || j.state}`));
    setMsg('Loading what was read');
    const ex = await A.extraction(scan.version_id);
    S.add.read = { intake, scan, ex };
    const pre = prefill(ex);
    S.add.form = pre.values; S.add.notes = pre.notes; S.add.prog = null;
  }

  /** GS1 AI 17 is YYMMDD. The renderer and the change rules use years 2000 to 2099 (docs/CHANGE_SPEC.md). */
  function gs1Date(v) {
    const m = /^(\d{2})(\d{2})(\d{2})$/.exec(v || '');
    if (!m || m[3] === '00') return '';
    return `20${m[1]}-${m[2]}-${m[3]}`;
  }
  const strip = (v) => String(v || '').replace(PREFIX_RE, '').trim();
  const norm = (v) => String(v || '').replace(/\s+/g, '').toUpperCase();

  /** Fill the form from the extraction: label text for words, the decoded barcode for encoded values. */
  function prefill(ex) {
    const F = ex.fields || {};
    const unclear = new Set(ex.unclear_fields || []);
    const bc = (ex.barcodes || []).find((b) => b.parsed && Object.keys(b.parsed).length);
    const ai = bc ? bc.parsed : {};
    const values = {}; const notes = {};
    const textField = (rf) => {
      const lf = LABEL_FIELD[rf];
      const raw = F[lf];
      if (raw === undefined || raw === '') return { value: '', src: '', why: 'Not read from the label. Type it from the product specification.' };
      const value = ['model', 'lot', 'expiry'].includes(rf) ? strip(raw) : String(raw).trim();
      return { value, raw, src: `Printed text: "${raw}"`, why: unclear.has(lf) ? 'Reading confidence was low. Check it against the label.' : '' };
    };
    for (const rf of ['name', 'manufacturer', 'manufacturer_address', 'model']) {
      const t = textField(rf);
      values[rf] = t.value; notes[rf] = { src: t.src, why: t.why };
    }
    // Encoded values: the barcode decoder reads them exactly, so it wins over printed text; disagreement is shown.
    const encoded = [['lot', '10', (v) => v], ['expiry', '17', gs1Date], ['serial', '21', (v) => v]];
    for (const [rf, code, conv] of encoded) {
      const t = LABEL_FIELD[rf] ? textField(rf) : { value: '', src: '', why: '' };
      const fromBc = ai[code] ? conv(ai[code]) : '';
      if (fromBc) {
        values[rf] = fromBc;
        const differs = t.value && norm(t.value) !== norm(fromBc);
        notes[rf] = {
          src: `From the barcode (AI ${code}: ${ai[code]})${t.src ? '; ' + t.src : ''}`,
          why: differs ? `The barcode says ${fromBc}, but the printed text was read as "${t.raw}". Check the label.` : (t.why || ''),
        };
      } else {
        values[rf] = t.value;
        notes[rf] = { src: t.src, why: t.why || (rf === 'serial' ? 'Not read from the label. Type it from the product specification.' : '') };
      }
    }
    values.udi_di = ai['01'] || '';
    notes.udi_di = ai['01']
      ? { src: `From the barcode (AI 01)${ai['01'] === TEST_UDI ? ': the GS1 test placeholder [TEST]' : ''}`, why: '' }
      : { src: '', why: 'No barcode identifier was read. Type the allocated UDI-DI, or leave it empty. LabelLens never makes one up.' };
    for (const rf of ['sterilization', 'storage']) {
      values[rf] = '';
      notes[rf] = { src: '', why: 'Not read from the label. Type it from the product specification if it applies.' };
    }
    return { values, notes };
  }

  const trimmedForm = () => Object.fromEntries(RECORD_FIELDS.map(([f]) => [f, String(S.add.form[f] || '').trim()]));

  function recordBody(v) {
    const body = { name: v.name, intended_market: ['US'] };
    for (const f of ['model', 'manufacturer', 'manufacturer_address', 'udi_di', 'sterilization', 'storage']) if (v[f]) body[f] = v[f];
    const extra = {};
    for (const f of EXTRA_KEYS) if (v[f]) extra[f] = v[f];
    if (Object.keys(extra).length) body.extra = extra;
    return body;
  }

  /** The label text the person confirms: each value written the way the label prints it (keeps "LOT: " style prefixes). */
  function confirmFields(v, ex) {
    const read = ex.fields || {};
    const out = {};
    for (const [rf, lf] of Object.entries(LABEL_FIELD)) {
      if (!v[rf]) continue;
      const m = ['model', 'lot', 'expiry'].includes(rf) ? PREFIX_RE.exec(read[lf] || '') : null;
      out[lf] = (m ? m[0] : '') + v[rf];
    }
    return out;
  }

  async function doSave() {
    const v = trimmedForm();
    if (!v.name) throw new Error('Type the product name before saving.');
    const p = S.add.prog || (S.add.prog = {});
    if (!p.pid) {
      setMsg('Step 1 of 4: registering the product record');
      const made = await A.registerProduct(recordBody(v));
      p.pid = made.product.product_id;
    }
    if (!p.template) {
      setMsg('Step 2 of 4: registering the label template');
      const res = await fetch('/ui/pro/sample/test_device.json', { cache: 'no-store' });
      if (!res.ok) throw new Error(`Could not load the template file /ui/pro/sample/test_device.json (HTTP ${res.status}).`);
      const t = await res.json();
      const tpl = await A.registerTemplate(p.pid, { size_mm: t.size_mm, background: null, slots: t.slots });
      p.template = `${tpl.template_id} v${tpl.version}`;
    }
    if (!p.scan) {
      setMsg('Step 3 of 4: uploading the label as the first label version');
      p.scan = await A.upload(S.add.file, S.add.source, p.pid, (j) => setMsg(`Step 3 of 4: reading the label: ${j.message || j.state}`));
    }
    if (!p.confirmed) {
      setMsg('Step 4 of 4: confirming the fields read from the label');
      const ex = await A.extraction(p.scan.version_id);
      await A.confirmExtraction(p.scan.version_id, confirmFields(v, ex));
      p.confirmed = true;
    }
    const done = { pid: p.pid, template: p.template, version: p.scan.version_id };
    if (S.add.previewUrl) URL.revokeObjectURL(S.add.previewUrl);
    S.add = freshAdd();
    S.products = null;
    await loadProduct(done.pid);
    S.stage = 'check';
    S.flash = `Saved product ${done.pid}: record version 1, template ${done.template}, first label version ${done.version} (fields confirmed by you).`;
  }

  // ---------------------------------------------------------------- camera

  async function camStart() {
    S.add.camMsg = '';
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      S.add.camMsg = 'The camera is not available in this browser (it needs http://127.0.0.1 or https and camera support). Upload a file instead.';
      render(); return;
    }
    try {
      S.cam = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'environment', width: { ideal: 1920 } }, audio: false });
    } catch (e) {
      const n = e && e.name;
      S.add.camMsg = n === 'NotAllowedError' || n === 'SecurityError'
        ? 'Camera permission was denied. Allow the camera for this page in the browser settings, or upload a file instead.'
        : (n === 'NotFoundError' || n === 'OverconstrainedError'
          ? 'No camera was found on this computer. Upload a file instead.'
          : `The camera could not start (${n || 'error'}: ${e && e.message}). Upload a file instead.`);
    }
    render();
  }
  function camStop() {
    if (S.cam) S.cam.getTracks().forEach((t) => t.stop());
    S.cam = null;
    render();
  }
  function camCapture() {
    const video = $('#camVideo');
    if (!video || !video.videoWidth) { S.add.camMsg = 'The camera has no picture yet. Wait a moment and press Capture again.'; render(); return; }
    const canvas = document.createElement('canvas');
    canvas.width = video.videoWidth; canvas.height = video.videoHeight;
    canvas.getContext('2d').drawImage(video, 0, 0);
    canvas.toBlob((blob) => {
      setFile(new File([blob], 'camera.png', { type: 'image/png' }), 'camera');
      camStop();
    }, 'image/png');
  }

  // ---------------------------------------------------------------- change, artwork, review, export actions

  async function doAssess() {
    const value = S.change.value.trim();
    if (!value) throw new Error('Type the new value first.');
    setMsg('Assessing the change with the rules');
    const a = await A.assessChange(S.product.product.product_id, S.change.field, value);
    S.change.assessment = a; S.change.decisions = {}; S.change.confirmed = null;
  }

  async function doConfirm() {
    const a = S.change.assessment;
    const decisions = a.affected.map((i) => ({ impact_id: i.impact_id, user_decision: S.change.decisions[i.impact_id] }));
    setMsg('Recording your confirmation');
    S.change.confirmed = await A.confirmChange(a.change.change_id, decisions);
  }

  async function loadPreview(art) {
    if (S.previewUrl) { URL.revokeObjectURL(S.previewUrl); S.previewUrl = null; }
    const { blob } = await A.artifact(art.svg_url);
    S.previewUrl = URL.createObjectURL(new Blob([blob], { type: 'image/svg+xml' }));
  }

  async function doGenerate() {
    const change = (S.change.confirmed || S.change.assessment).change;
    setMsg('Filling the template');
    const art = await A.generate(change.change_id, S.labelId, (j) => setMsg(`Generating the draft: ${j.message || j.state}`));
    S.artwork = art;
    setMsg('Loading the new version');
    S.artworkL = (await A.labelVersion(art.version_id)).artwork_version;
    await loadProduct(S.product.product.product_id);
    setMsg('Loading the draft preview');
    await loadPreview(art);
  }

  async function doRecheck(v) {
    setMsg('Reading the rendered PDF back and running the checks');
    S.checks[v] = await A.recheck(v, (j) => setMsg(`Re-check: ${j.message || j.state}`));
  }

  async function shaFor(v) {
    if (S.artwork && S.artwork.version_id === v) return S.artwork.artifact_sha256;
    if (!S.exports[v]) S.exports[v] = await A.exports(v);
    return S.exports[v].pdf.sha256;
  }

  async function doReview(decision) {
    const v = latestGenerated().version_id;
    const body = { decision, artifact_sha256: await shaFor(v) };
    const check = S.checks[v];
    if (decision === 'approve' && check) body.check_id = check.check_id;
    if (S.reviewComment.trim()) body.comment = S.reviewComment.trim();
    setMsg(decision === 'approve' ? 'Recording the approval' : 'Recording the return');
    S.lastReview = await A.review(v, body);
    S.reviewComment = '';
    S.reviews[v] = await A.reviews(v);
    await loadProduct(S.product.product.product_id);
  }

  async function doDownload() {
    const v = latestGenerated().version_id;
    const pkg = S.exports[v] || (S.exports[v] = await A.exports(v));
    setMsg('Downloading the PDF');
    const { blob, draftMark } = await A.artifact(pkg.pdf.url);
    const buf = await blob.arrayBuffer();
    let digest = '';
    if (window.crypto && window.crypto.subtle) {
      const h = await window.crypto.subtle.digest('SHA-256', buf);
      digest = Array.from(new Uint8Array(h)).map((b) => b.toString(16).padStart(2, '0')).join('');
    }
    const url = URL.createObjectURL(new Blob([buf], { type: 'application/pdf' }));
    const a = document.createElement('a');
    a.href = url; a.download = `${v}.pdf`;
    document.body.appendChild(a); a.click(); a.remove();
    setTimeout(() => URL.revokeObjectURL(url), 10000);
    S.download = { v, bytes: buf.byteLength, digest, expected: pkg.pdf.sha256, draftMark };
  }

  async function doVerify() {
    const v = latestGenerated().version_id;
    if (!S.print.file) throw new Error('Choose a photo (PNG or JPEG) of the printed label first.');
    setMsg('Uploading the photo');
    S.print.result = await A.verifyPrint(v, S.print.file, S.print.condition, (j) => setMsg(`Comparing the photo: ${j.message || j.state}`));
    S.print.list[v] = await A.printVerifications(v);
  }

  // ---------------------------------------------------------------- rendering: shared pieces

  function citationHtml(c) {
    return `<div class="cite" data-testid="citation"><div><strong>21 CFR ${esc(c.section)}</strong>: ${esc(c.title)}`
      + `${c.url ? ` <a href="${esc(c.url)}" target="_blank" rel="noopener noreferrer">Open the regulation</a>` : ''}</div>`
      + `${c.quote ? `<div class="q">"${esc(c.quote)}"</div>` : ''}<div class="small muted">Source ${esc(c.source)}, passage ${esc(c.chunk_id)}</div></div>`;
  }

  const SEVERITY = { critical: ['danger', 'Critical'], review: ['warn', 'To review'], info: ['blue', 'Info'] };

  function checkHtml(c) {
    const findings = c.findings || [];
    const coverage = c.coverage || [];
    const human = coverage.filter((x) => x.outcome === 'needs_human');
    const skipped = coverage.filter((x) => x.outcome === 'not_checked' || x.outcome === 'not_applicable');
    const unreliable = findings.some((f) => f.kind === 'extraction_unreliable');
    const cfg = c.retrieval_config || {};
    return `<div data-testid="check-result">
      <div class="row"><span class="badge ${c.critical_count ? 'danger' : 'teal'}" data-testid="check-outcome">${c.critical_count ? `${esc(c.critical_count)} critical` : 'No critical finding'}</span>
        <span class="badge warn">${esc(c.needs_human_count || 0)} rule(s) need a person</span>
        <span class="small muted">${esc(c.review_count)} to review, ${esc(c.info_count)} info. Check ${esc(c.check_id)} (${esc(c.kind)}) on ${esc(c.version_id)}, ${when(c.run_at)}. Citations found with ${esc(cfg.method || 'retrieval')}.</span></div>
      ${c.passed
        ? '<div class="info">No critical finding was raised by the rules that ran. This does not mean the label meets the regulations: the human checks below still apply.</div>'
        : '<div class="note">At least one critical finding: this version cannot be approved until it is fixed.</div>'}
      ${unreliable ? '<div class="note" data-testid="unreliable-note"><strong>The label text could not be read reliably</strong> (for example, a rendered PDF page has no label edge for the reader to find), so the text checks were skipped and only the barcode checks ran. A person must compare the printed text with the product record by eye.</div>' : ''}
      <h3 class="mt">Findings (${findings.length})</h3>
      ${findings.length ? findings.map((f) => {
        const [cls, word] = SEVERITY[f.severity] || ['blue', f.severity];
        return `<div class="item" data-testid="finding" data-rule="${esc(f.rule_id || '')}">
          <div class="item-head"><span class="badge ${cls}">${esc(word)}</span><span class="item-title">${esc(String(f.kind || '').split('_').join(' '))}</span>
          ${f.rule_id ? `<span class="badge">rule ${esc(f.rule_id)}</span>` : ''}${f.field ? `<span class="badge">field ${esc(f.field)}</span>` : ''}
          ${f.needs_human ? '<span class="badge warn">a person must look</span>' : ''}</div>
          <div>${esc(f.message)}</div>
          ${f.field && (f.observed || f.expected) ? `<div class="small muted mt">Read on the label: <strong>${esc(f.observed || '(nothing)')}</strong>. Expected: <strong>${esc(f.expected || '(nothing)')}</strong>.</div>` : ''}
          ${(f.citations || []).length ? f.citations.map(citationHtml).join('') : '<div class="nocite" data-testid="no-citation">No regulation passage is attached to this finding. A person must look.</div>'}
        </div>`;
      }).join('') : '<div class="muted">No problem findings.</div>'}
      <h3 class="mt">A person must check (${human.length})</h3>
      ${human.length ? `<ul class="small" data-testid="human-review">${human.map((h) => `<li><strong>${esc(h.rule_id)}</strong>: ${esc(h.reason || 'needs a person')}</li>`).join('')}</ul>` : '<div class="muted small">No rule asked for a person.</div>'}
      ${skipped.length ? `<details class="mt small"><summary>Rules not checked or not applicable (${skipped.length})</summary><ul>${skipped.map((h) => `<li><strong>${esc(h.rule_id)}</strong> ${esc(h.outcome.split('_').join(' '))}: ${esc(h.reason || '')}</li>`).join('')}</ul></details>` : ''}
      ${c.disclaimer ? `<div class="small muted mt">${esc(c.disclaimer)}</div>` : ''}
    </div>`;
  }

  function versionsTable() {
    if (!S.versions.length) return '<div class="muted">This product has no label version yet.</div>';
    return `<table class="tbl" data-testid="version-history"><thead><tr><th>Version</th><th>Kind</th><th>Status</th><th>Marks</th><th>Made by</th><th>When</th></tr></thead><tbody>
      ${S.versions.slice().reverse().map((v) => `<tr><td><strong>L${esc(v.artwork_version)}</strong><div class="small mono">${esc(v.version_id)}</div></td>
        <td>${esc(v.kind)}</td><td><span class="badge ${v.status === 'reviewed' ? 'teal' : ''}">${esc(v.status)}</span></td>
        <td>${v.draft_watermark ? '<span class="badge draft">DRAFT</span>' : ''}</td><td>${esc(v.created_by)}</td><td class="small">${when(v.created_at)}</td></tr>`).join('')}
    </tbody></table>`;
  }

  function historyTable() {
    if (!S.history.length) return '<div class="muted">No events yet.</div>';
    return `<table class="tbl" data-testid="history"><thead><tr><th>When</th><th>Who</th><th>What</th><th>On</th></tr></thead><tbody>
      ${S.history.map((h) => `<tr><td class="small">${when(h.at)}</td><td>${esc(h.user_id)}</td><td>${esc(h.action)}</td><td class="small"><span class="mono">${esc(h.entity_type)} ${esc(h.entity_id)}</span></td></tr>`).join('')}
    </tbody></table>`;
  }

  function productHeader() {
    const rec = S.product.record; const v = currentVersion();
    return `<div class="card" data-testid="product-header"><div class="row" style="justify-content:space-between">
      <div><div style="font-size:1.2rem;font-weight:700">${esc(rec.name)}</div>
      <div class="small muted">${esc(S.product.product.product_id)} | model ${esc(rec.model || '(none)')} | ${esc(rec.manufacturer || '')} | record version ${esc(rec.version)}</div></div>
      <div class="row">${v ? `<span class="badge blue" data-testid="current-version">Current label L${esc(v.artwork_version)} (${esc(v.kind)})</span><span class="badge">${esc(v.status)}</span>${v.draft_watermark ? '<span class="badge draft">DRAFT</span>' : ''}` : '<span class="badge warn">No label version</span>'}</div>
    </div></div>`;
  }

  function roleNote(needed) {
    if (needed === 'editor' && !isEditor()) return '<div class="note" data-testid="role-note">This step is for an Editor. Switch to Editor at the top of the page.</div>';
    if (needed === 'reviewer' && isEditor()) return '<div class="note" data-testid="role-note">Approval is for a Reviewer. Switch to Reviewer at the top of the page.</div>';
    return '';
  }

  function head(title, help, right) {
    return `<div class="stage-head"><h2>${title}</h2><div class="row">${right || ''}</div></div><p class="help">${help}</p>`;
  }

  // ---------------------------------------------------------------- rendering: stages

  function productRows() {
    const all = (S.products || []).filter((p) => !isIntake(p));
    const hidden = (S.products || []).length - all.length;
    const q = S.filter.trim().toLowerCase();
    const rows = all.filter((p) => !q || [p.record.name, p.record.model, p.record.manufacturer, p.product.product_id]
      .some((x) => String(x || '').toLowerCase().includes(q)));
    let body;
    if (!all.length) body = '<tr><td colspan="7" data-testid="empty-products">No products yet. Press Add product to read a label and save it as a product.</td></tr>';
    else if (!rows.length) body = `<tr><td colspan="7" data-testid="no-match">No product matches "${esc(S.filter)}".</td></tr>`;
    else {
      body = rows.map((p) => `<tr class="click" data-open="${esc(p.product.product_id)}" data-testid="product-row">
        <td><strong>${esc(p.record.name)}</strong><div class="small mono muted">${esc(p.product.product_id)}</div></td>
        <td>${esc(p.record.model || '')}</td><td>${esc(p.record.manufacturer || '')}</td><td>${esc(p.record.version)}</td>
        <td>${esc(p.label_count)}</td><td>${p.open_findings ? `<span class="badge warn">${esc(p.open_findings)}</span>` : '0'}</td></tr>`).join('');
    }
    const note = `${rows.length} of ${all.length} product(s) shown${hidden ? `. ${hidden} internal intake record (label reads before saving) is hidden` : ''}.`;
    return { body, note };
  }

  function renderProducts() {
    const r = productRows();
    return head('Products', 'Your inventory of device products. Open a product to check its label, change a detail, revise the artwork and send it for review. Anyone can view; an Editor adds products.',
      btn('go-add', 'Add product', { primary: true }))
      + `<div class="card"><div class="row mb"><input class="input" style="flex:1 1 320px" id="prodFilter" data-model="filter" data-testid="product-filter" placeholder="Filter by name, model, manufacturer or product id" value="${esc(S.filter)}">
        ${btn('load-products', 'Refresh')}</div>
        ${statusHtml('products')}
        ${S.products ? `<table class="tbl"><thead><tr><th>Name</th><th>Model</th><th>Manufacturer</th><th>Version</th><th>Labels</th><th>Open findings</th></tr></thead><tbody id="prodRows">${r.body}</tbody></table>
        <div class="small muted mt" id="prodNote" data-testid="product-note">${esc(r.note)}</div>` : ''}</div>`;
  }

  function renderAdd() {
    const ad = S.add; const ed = isEditor();
    const file = ad.file ? `<div class="okbox" data-testid="chosen-file">Chosen: <strong>${esc(ad.file.name)}</strong> (${Math.round(ad.file.size / 1024)} KB, ${esc(ad.file.type || 'unknown type')}, source ${esc(ad.source)})</div>` : '';
    let html = head('Add a product from its label', 'Upload a PDF or a photo of the label, take a photo, or use the sample Golden Pump label. LabelLens reads the text (OCR) and the barcode. You check and correct every field, then save: that registers the product record, its label template and its first label version. Editor only.')
      + roleNote('editor')
      + `<div class="card"><h3>1. Choose the label</h3><div class="row">
          <label class="btn${ed && !S.busy ? '' : ' disabled'}" style="${ed && !S.busy ? '' : 'opacity:.5;pointer-events:none'}">Choose PDF or image<input type="file" id="addFile" data-file="add" data-testid="add-file" accept=".pdf,.png,.jpg,.jpeg,application/pdf,image/png,image/jpeg" hidden></label>
          ${btn('cam-start', 'Take a photo', { disabled: !ed || !!S.cam })}
          ${btn('sample', 'Use sample Golden Pump label', { disabled: !ed })}
        </div>
        ${ad.camMsg ? `<div class="note" data-testid="camera-msg">${esc(ad.camMsg)}</div>` : ''}
        ${S.cam ? `<div class="cam mt" data-testid="camera-panel"><video id="camVideo" autoplay playsinline muted></video><div class="row mt">${btn('cam-capture', 'Capture', { primary: true })}${btn('cam-stop', 'Cancel')}</div></div>` : ''}
        ${file}${ad.previewUrl ? `<img src="${ad.previewUrl}" alt="Chosen label photo" style="max-width:360px;border-radius:8px;margin-top:8px">` : ''}
        <div class="row mt">${btn('read', 'Read label', { primary: true, disabled: !ed || !ad.file })}</div>
        ${statusHtml('read')}</div>`;
    if (ad.read) {
      const ex = ad.read.ex;
      const unclearCount = RECORD_FIELDS.filter(([f]) => (ad.notes[f] || {}).why).length;
      html += `<div class="card" data-testid="read-result"><h3>2. Check what was read, then save</h3>
        <p class="small muted mb">Read from ${esc(ad.file ? ad.file.name : '')} (scan ${esc(ad.read.scan.scan_id)}). Highlighted fields need your attention (${unclearCount}). Nothing is saved until you press Save product.</p>
        <div class="grid2"><div><div class="form-grid">
          ${RECORD_FIELDS.map(([f, label]) => {
            const n = ad.notes[f] || {};
            return `<div class="field${n.why ? ' unclear' : ''}" data-testid="field-${f}"><label for="f_${f}">${esc(label)}</label>
              <input class="input" id="f_${f}" data-model="add.form.${f}" data-testid="input-${f}" value="${esc(ad.form[f] || '')}"${ed ? '' : ' disabled'}>
              ${n.why ? `<span class="why" data-testid="why-${f}">${esc(n.why)}</span>` : ''}${n.src ? `<span class="src">${esc(n.src)}</span>` : ''}</div>`;
          }).join('')}
        </div></div>
        <div><div class="card" style="background:var(--color-bg-subtle)"><h3>Barcode</h3>
          ${(ex.barcodes || []).length ? ex.barcodes.map((b) => `<div data-testid="barcode"><strong>${esc(b.type)}</strong><div class="mono">${esc(b.raw)}</div>
            ${b.parsed ? `<div class="small">${Object.entries(b.parsed).map(([k, v]) => `(${esc(k)}) ${fmtVal(v)}`).join(' &nbsp; ')}</div>` : ''}</div>`).join('') : '<div class="muted">No barcode was decoded.</div>'}
          <h3 class="mt">Reader notes</h3><ul class="small">${(ex.warnings || []).map((w) => `<li>${esc(w)}</li>`).join('') || '<li>None</li>'}</ul>
          <details class="small mt"><summary>Text lines read (${(ex.ocr_blocks || []).length})</summary><ul>${(ex.ocr_blocks || []).map((b) => `<li class="mono">${esc(b.text)}${b.conf !== undefined ? ` <span class="muted">${Math.round(b.conf * 100)}%</span>` : ''}</li>`).join('')}</ul></details>
        </div></div></div>
        <div class="row mt">${btn('save', 'Save product', { primary: true, disabled: !ed })}${btn('go-products', 'Cancel')}</div>
        ${ad.prog && ad.prog.pid ? `<div class="info small" data-testid="save-progress">Saved so far: product ${esc(ad.prog.pid)}${ad.prog.template ? `, template ${esc(ad.prog.template)}` : ''}${ad.prog.scan ? `, label version ${esc(ad.prog.scan.version_id)}` : ''}. Retry continues from here.</div>` : ''}
        ${statusHtml('save')}</div>`;
    }
    return html;
  }

  function renderEvidence() {
    const ev = S.evidence;
    let html = `<div class="card" data-testid="evidence"><h3>Evidence: search the device regulations</h3>
      <p class="small muted mb">Our own retrieval (BM25 plus dense, fused) over 21 CFR 801, 820 and 830. Results are passages with their section, title and quote.</p>
      <div class="row"><input class="input" style="flex:1 1 380px" data-model="evidence.query" data-enter="search" data-testid="evidence-query" value="${esc(ev.query)}">${btn('search', 'Search', { primary: true })}</div>
      ${statusHtml('search')}`;
    if (ev.search) {
      const s = ev.search;
      html += `<div class="small muted mt">Method ${esc((s.retrieval || {}).method)}; ${esc(s.hits.length)} passages.</div>
        <div class="grid2 mt" data-testid="evidence-results"><div><h3>Ranked passages</h3>${s.hits.map((h) => `<div class="item"><div class="item-head"><span class="badge">#${esc(h.rank)}</span><span class="mono">${esc(h.doc_id)}</span><span class="small muted">score ${Number(h.score).toFixed(4)}</span></div><div class="small">${esc(h.text)}</div></div>`).join('') || '<div class="muted">No passages found.</div>'}</div>
        <div><h3>Citations</h3>${s.citations.map(citationHtml).join('') || '<div class="muted">No citations.</div>'}</div></div>`;
    }
    html += `<h3 class="mt">Ask a question</h3><div class="row"><input class="input" style="flex:1 1 380px" data-model="evidence.question" data-enter="ask" data-testid="evidence-question" value="${esc(ev.question)}">${btn('ask', 'Ask', { primary: true })}</div>
      ${statusHtml('ask')}`;
    if (ev.answer) {
      const a = ev.answer;
      if (a.abstained) {
        html += `<div class="note" data-testid="abstained"><strong>No answer was given</strong> (${esc(a.reason)}). ${esc(a.message)}
          ${a.score !== null && a.score !== undefined ? `<div class="small mono mt">${esc(a.score_name)} ${esc(a.score)}${a.threshold !== null && a.threshold !== undefined ? `, threshold ${esc(a.threshold)}` : ''}</div>` : ''}</div>
          ${(a.sources || []).length ? `<div class="small muted">Closest passages (not an answer, a person should read them):</div>${a.sources.map(citationHtml).join('')}` : ''}`;
      } else {
        html += `<div class="okbox" data-testid="answer">${esc(a.answer)}</div>${(a.sources || []).map(citationHtml).join('')}`;
      }
    }
    return html + '</div>';
  }

  function renderCheck() {
    const rec = S.product.record; const v = currentVersion();
    const extra = rec.extra || {};
    let html = head('Product and label check', 'The check compares the label with the product record and attaches cited passages from 21 CFR 801, 820 and 830 found by our retrieval. Every finding has a citation or says a person must look. Rules decide; nothing here says a label meets the regulations. Anyone can run a check.',
      `${btn('check', v ? `Run check on L${esc(v.artwork_version)}` : 'Run check', { primary: true, disabled: !v })}${btn('go-change', 'Change a detail')}${btn('toggle-evidence', S.evidence.open ? 'Hide evidence' : 'Evidence')}`)
      + productHeader()
      + statusHtml('check');
    const c = v && S.checks[v.version_id];
    if (c) html += `<div class="card">${checkHtml(c)}</div>`;
    else if (v) html += `<div class="info small">No check has been run on L${esc(v.artwork_version)} in this session. ${v.kind === 'generated' ? 'For generated artwork the check reads the rendered PDF back (re-check).' : 'Press Run check.'}</div>`;
    if (S.evidence.open) html += renderEvidence();
    html += `<div class="grid2"><div class="card"><h3>Product record</h3><dl class="kv" data-testid="record">
        ${[['Name', rec.name], ['Model', rec.model], ['Manufacturer', rec.manufacturer], ['Manufacturer address', rec.manufacturer_address], ['UDI-DI', rec.udi_di], ['Sterilization', rec.sterilization], ['Storage', rec.storage]]
          .map(([k, val]) => `<dt>${k}</dt><dd>${fmtVal(val) || '<span class="muted">(empty)</span>'}</dd>`).join('')}
        ${Object.entries(extra).map(([k, val]) => `<dt>${esc(k)}</dt><dd>${fmtVal(val)}</dd>`).join('')}
        <dt>Record version</dt><dd>${esc(rec.version)} (by ${esc(rec.created_by)})</dd>
        <dt>Templates</dt><dd>${S.product.templates.map((t) => `${esc(t.template_id)} v${esc(t.version)} (${esc(t.size_mm.w)} x ${esc(t.size_mm.h)} mm)`).join(', ') || '(none)'}</dd></dl></div>
      <div class="card"><h3>Label versions</h3>${versionsTable()}</div></div>
      <details class="card"><summary><strong>Activity history (${S.history.length})</strong></summary><div class="mt">${historyTable()}</div></details>`;
    return html;
  }

  const KIND = { text: 'Label text', symbol: 'Symbol', barcode: 'Barcode', linked_label: 'Label without a template field' };
  const SUGGEST = { edit_required: 'Must be updated', review_suggested: 'A person should review', no_change: 'No change' };

  function barcodeSentence(bd) {
    if (bd.decision === 'REGENERATE') return 'This value is encoded in the barcode, so a new barcode is built.';
    if (bd.decision === 'KEEP') return 'This value is not in the barcode, so it stays.';
    if (String(bd.required_identifier || '').startsWith('confirm_')) return 'This value is encoded in the barcode. The new barcode is built only after a person confirms the change (Confirm below).';
    return 'An identifier is missing or invalid, a person must supply it.';
  }

  function decisionHtml(bd) {
    return `<div class="decision${bd.decision === 'NEEDS_INPUT' ? ' needs' : ''}" data-testid="barcode-decision" data-decision="${esc(bd.decision)}">
      <div class="row"><span class="big">${esc(bd.decision)}</span><span>${esc(barcodeSentence(bd))}</span></div>
      <div class="small mt">${esc(bd.reason)}</div>
      <div class="small mono mt">Before: ${esc(bd.old_payload || '(none)')}<br>After: ${esc(bd.new_payload || '(not built)')}<br>Symbology: ${esc(bd.symbology)}${bd.required_identifier ? `<br>Needs: ${esc(bd.required_identifier)}` : ''}</div></div>`;
  }

  function assessmentHtml(a, confirmed) {
    const byChunk = Object.fromEntries((a.citations || []).map((c) => [c.chunk_id, c]));
    const v = currentVersion();
    let html = `<div class="card" data-testid="assessment"><div class="row"><h3 style="margin:0">Change ${esc(a.change.change_id)}: ${esc(a.change.field)}</h3>
      <span class="badge">${esc(a.change.old_value || '(empty)')} to ${esc(a.change.new_value)}</span><span class="badge blue">decided by ${esc(a.parser)}</span>
      ${confirmed ? '<span class="badge teal" data-testid="change-confirmed">confirmed</span>' : '<span class="badge warn">not confirmed yet</span>'}</div>`;
    if ((a.unassessed_edits || []).length) {
      html += `<div class="err" data-testid="change-rejected"><div class="msg">${a.unassessed_edits.map((u) => `Not assessed (${u.reason}): ${u.message}`).map(esc).join('\n')}\nFix the value above and assess again.</div>${btn('assess', 'Retry', { small: true, testid: 'retry-unassessed' })}</div>`;
    }
    if (a.needs_human_review) html += `<div class="note small">${esc(a.needs_human_review)}</div>`;
    const items = a.affected || [];
    if (items.length) {
      html += `<h3 class="mt">What is affected (${items.length})</h3>` + items.map((i) => {
        const cites = (i.evidence_chunk_ids || []).map((id) => byChunk[id]).filter(Boolean);
        const dec = S.change.decisions[i.impact_id] || i.user_decision;
        return `<div class="item" data-testid="affected-item" data-kind="${esc(i.item_kind)}">
          <div class="item-head"><span class="badge blue">${esc(KIND[i.item_kind] || i.item_kind)}</span><span class="item-title">${esc(i.title)}</span>
            <span class="badge ${i.suggestion === 'edit_required' ? 'danger' : (i.suggestion === 'no_change' ? 'teal' : 'warn')}">${esc(SUGGEST[i.suggestion] || i.suggestion)}</span>
            ${i.needs_human ? '<span class="badge warn">a person must decide</span>' : ''}${(i.rule_ids || []).map((r) => `<span class="badge">${esc(r)}</span>`).join('')}</div>
          ${i.barcode_decision ? decisionHtml(i.barcode_decision) : `<div>${esc(i.reason || i.description)}</div>`}
          ${cites.length ? cites.map(citationHtml).join('') : '<div class="nocite">No regulation passage is attached to this item.</div>'}
          ${confirmed ? `<div class="small mt">Your decision: <strong>${esc(i.user_decision)}</strong></div>`
            : `<div class="choice" data-testid="decision-${esc(i.impact_id)}"><label><input type="radio" name="dec_${esc(i.impact_id)}" data-dec="${esc(i.impact_id)}" value="confirmed"${dec === 'confirmed' ? ' checked' : ''}${S.busy ? ' disabled' : ''}> Confirm</label>
               <label><input type="radio" name="dec_${esc(i.impact_id)}" data-dec="${esc(i.impact_id)}" value="dismissed"${dec === 'dismissed' ? ' checked' : ''}${S.busy ? ' disabled' : ''}> Dismiss</label></div>`}
        </div>`;
      }).join('');
      if (!items.some((i) => i.barcode_decision)) {
        html += v && v.kind === 'uploaded'
          ? '<div class="info" data-testid="no-barcode-decision">No barcode decision at this step: the current label version was uploaded, so it has no template slots to compare. The barcode decision for the revised artwork is shown after Generate.</div>'
          : '<div class="info" data-testid="no-barcode-decision">This assessment has no barcode item.</div>';
      }
    }
    return html + '</div>';
  }

  function renderChange() {
    const ch = S.change; const rec = S.product.record; const ed = isEditor();
    const a = ch.confirmed || ch.assessment;
    let html = head('Change a detail', 'Pick the field and type the new value. Rules (no language model) decide what happens to each label part and to the barcode: expiry, lot, serial and UDI are encoded in the GS1 barcode, so a change to them regenerates it; name, address, model, storage and sterilization keep it. A missing or invalid identifier needs input. You confirm the checklist. Editor only.')
      + productHeader() + roleNote('editor')
      + `<div class="card"><div class="form-grid">
        <div class="field"><label for="chField">Field</label><select class="input" id="chField" data-model="change.field" data-testid="change-field"${ed ? '' : ' disabled'}>
          ${CHANGE_FIELDS.map(([f, l]) => `<option value="${f}"${f === ch.field ? ' selected' : ''}>${esc(l)}</option>`).join('')}</select>
          <span class="src" data-testid="change-current">Current value in the record: ${fmtVal(recVal(rec, ch.field)) || '(empty)'}</span></div>
        <div class="field"><label for="chValue">New value</label><input class="input" id="chValue" data-model="change.value" data-enter="assess" data-testid="change-value" value="${esc(ch.value)}"${ed ? '' : ' disabled'}></div>
      </div><div class="row mt">${btn('assess', 'Assess', { primary: true, disabled: !ed })}</div>${statusHtml('assess')}</div>`;
    if (a) {
      html += assessmentHtml(a, !!ch.confirmed);
      const items = a.affected || [];
      if (!ch.confirmed && items.length) {
        const all = items.every((i) => S.change.decisions[i.impact_id]);
        html += `<div class="card"><h3>Checklist</h3><p class="small muted">Decide every item above (Confirm or Dismiss), then press Confirm. This is stored with the change before any artwork is made.</p>
          <div class="row">${btn('dec-all', 'Mark all items Confirm', { disabled: !ed })}${btn('confirm', 'Confirm', { primary: true, disabled: !ed || !all })}</div>${statusHtml('confirm')}</div>`;
      } else if (ch.confirmed) {
        html += `<div class="okbox">Confirmed. Next, generate the revised artwork for this change.</div><div class="row">${btn('go-artwork', 'Next: revise artwork', { primary: true })}</div>`;
      }
    }
    return html;
  }

  function renderArtwork() {
    const ch = S.change.confirmed; const ed = isEditor();
    let html = head('Revise artwork', 'Generate fills the product\'s label template with the confirmed values (never an image model). The result is a new label version marked DRAFT. Then run the re-check: it reads the rendered PDF back and checks it again. Editor only.')
      + productHeader() + roleNote('editor');
    if (!ch) return html + '<div class="info">Confirm a change first (stage Change). The artwork is generated for one confirmed change.</div>';
    html += `<div class="card"><div class="row"><strong>Change ${esc(ch.change.change_id)}</strong>: ${esc(ch.change.field)} from ${esc(ch.change.old_value || '(empty)')} to ${esc(ch.change.new_value)}</div>
      <div class="row mt">${btn('generate', 'Generate revised artwork', { primary: true, disabled: !ed })}</div>${statusHtml('generate')}</div>`;
    const art = S.artwork && S.artwork.change_id === ch.change.change_id ? S.artwork : null;
    if (art) {
      const chk = S.checks[art.version_id];
      html += `<div class="grid2" data-testid="artwork"><div class="card"><h3>Draft preview</h3>
          <div class="preview">${S.previewUrl ? `<img src="${S.previewUrl}" alt="Revised label artwork, draft" data-testid="artwork-preview">` : '<div class="muted">Preview not loaded.</div>'}<span class="badge draft tag">DRAFT</span></div>
          <div class="small muted mt">${esc(art.disclaimer)}</div></div>
        <div class="card"><h3>New version L${esc(S.artworkL)}</h3><dl class="kv">
          <dt>Version</dt><dd class="mono" data-testid="artwork-version">${esc(art.version_id)}</dd>
          <dt>Size</dt><dd>${esc(art.size_mm.w)} x ${esc(art.size_mm.h)} mm</dd>
          <dt>Marks</dt><dd>${art.draft_watermark ? '<span class="badge draft">DRAFT</span> ' : ''}${art.test_data ? '<span class="badge warn">TEST DATA</span>' : ''}</dd>
          <dt>Template</dt><dd>${esc(art.template_id)} v${esc(art.template_version)}</dd>
          <dt>PDF hash</dt><dd class="mono">${esc(art.artifact_sha256)}</dd>
          <dt>Layout problems</dt><dd>${art.layout_problems.length ? art.layout_problems.map(esc).join('; ') : 'none reported'}</dd></dl>
          ${decisionHtml(art.barcode_decision)}
          <h3 class="mt">Change log</h3><ul class="small">${art.change_log.map((l) => `<li>${when(l.at)} ${esc(l.user_id)}: ${esc(l.reason)}${(l.rules_fired || []).length ? ` (rules ${esc(l.rules_fired.join(', '))})` : ''}</li>`).join('')}</ul></div></div>
        <div class="card"><h3>Re-check the new version</h3><div class="row">${btn('recheck', `Run re-check on L${esc(S.artworkL)}`, { primary: true, data: { v: art.version_id } })}
          ${btn('go-review', 'Next: review and approve')}</div>${statusHtml('recheck')}${chk ? `<div class="mt">${checkHtml(chk)}</div>` : ''}</div>`;
    }
    return html;
  }

  function renderReview() {
    const v = latestGenerated();
    let html = head('Review and approve', 'A Reviewer reads the findings and the human checks, then approves this exact version. The approval is bound to the PDF hash and a passed re-check; the API refuses anything else and the page shows its message. A newer version voids an approval. Reviewer only.')
      + productHeader();
    if (!v) return html + '<div class="info">Nothing to review yet: the current label version was not generated. Generate revised artwork first.</div>';
    const chk = S.checks[v.version_id];
    const sha = S.artwork && S.artwork.version_id === v.version_id ? S.artwork.artifact_sha256 : (S.exports[v.version_id] ? S.exports[v.version_id].pdf.sha256 : '');
    const reviews = S.reviews[v.version_id] || [];
    html += roleNote('reviewer') + statusHtml('review-load')
      + `<div class="card"><div class="row"><strong>Version L${esc(v.artwork_version)}</strong><span class="mono small">${esc(v.version_id)}</span><span class="badge">${esc(v.status)}</span>${v.draft_watermark ? '<span class="badge draft">DRAFT</span>' : ''}</div>
        <div class="small mt">PDF hash the approval binds to: <span class="mono" data-testid="review-sha">${esc(sha || '(not loaded)')}</span></div></div>`;
    if (chk) html += `<div class="card"><h3>Re-check result</h3>${checkHtml(chk)}</div>`;
    else html += `<div class="note" data-testid="no-recheck">No re-check of L${esc(v.artwork_version)} in this session. Approval needs a passed check: run the re-check first.</div>`;
    html += `<div class="card"><h3>Decision</h3><div class="row mb">${btn('recheck', `Run re-check on L${esc(v.artwork_version)}`, { data: { v: v.version_id }, testid: 'btn-recheck-review' })}</div>
      <div class="field"><label for="revComment">Comment</label><textarea class="input" id="revComment" data-model="reviewComment" data-testid="review-comment">${esc(S.reviewComment)}</textarea></div>
      <div class="row mt">${btn('approve', 'Approve', { primary: true, disabled: isEditor() })}${btn('return', 'Return for correction', { disabled: isEditor() })}</div>
      ${statusHtml('recheck')}${statusHtml('review')}
      ${S.lastReview ? `<div class="okbox" data-testid="review-recorded">Recorded: ${esc(S.lastReview.decision)} by ${esc(S.lastReview.user_id)} (${esc(S.lastReview.review_id)}). Status is now ${esc(S.lastReview.resulting_status)}.</div>` : ''}
      ${S.lastReview && S.lastReview.decision === 'approve' ? `<div class="row">${btn('go-export', 'Next: export', { primary: true })}</div>` : ''}</div>
      <div class="grid2"><div class="card"><h3>Decisions on L${esc(v.artwork_version)}</h3>${reviews.length ? `<table class="tbl" data-testid="reviews"><thead><tr><th>Decision</th><th>Who</th><th>Comment</th><th>When</th></tr></thead><tbody>${reviews.map((r) => `<tr><td><span class="badge ${r.decision === 'approve' ? 'teal' : 'warn'}">${esc(r.decision)}</span></td><td>${esc(r.user_id)}</td><td>${esc(r.comment || '')}</td><td class="small">${when(r.decided_at)}</td></tr>`).join('')}</tbody></table>` : '<div class="muted">No decision yet.</div>'}</div>
      <div class="card"><h3>Version history</h3>${versionsTable()}</div></div>`;
    return html;
  }

  const OUTCOME = {
    match: ['teal', 'The photo agrees with the approved version on every compared field and the barcode.'],
    mismatch: ['danger', 'At least one compared field or the barcode differs from the approved version.'],
    rescan_needed: ['warn', 'The photo could not be compared reliably. Take a new photo.'],
  };

  function renderExport() {
    const v = latestGenerated();
    let html = head('Export', 'Download the stored PDF of the generated version at physical size. The file keeps its DRAFT mark (an unmarked variant is not built). Optionally compare a photo of the printed label with the approved version. Anyone can export.')
      + productHeader();
    if (!v) return html + '<div class="info">Nothing to export yet: only generated artwork has stored files. Generate revised artwork first.</div>';
    const pkg = S.exports[v.version_id];
    html += statusHtml('export-load');
    if (pkg) {
      const d = S.download && S.download.v === v.version_id ? S.download : null;
      html += `<div class="card" data-testid="export-package"><h3>PDF of L${esc(v.artwork_version)}</h3><dl class="kv">
          <dt>Status</dt><dd><span class="badge ${pkg.status === 'reviewed' ? 'teal' : ''}">${esc(pkg.status)}</span></dd>
          <dt>DRAFT mark on the file</dt><dd>${pkg.draft_watermark ? '<span class="badge draft">yes, DRAFT</span>' : 'no'}</dd>
          <dt>Physical size</dt><dd>${pkg.pdf.size_mm ? `${esc(pkg.pdf.size_mm.w)} x ${esc(pkg.pdf.size_mm.h)} mm` : '(not given)'}</dd>
          <dt>sha256</dt><dd class="mono">${esc(pkg.pdf.sha256)}</dd></dl>
        <div class="row mt">${btn('download', 'Download PDF', { primary: true })}</div>${statusHtml('download')}
        ${d ? `<div class="${d.digest && d.digest === d.expected ? 'okbox' : 'note'}" data-testid="download-result">Downloaded ${esc(d.bytes)} bytes as ${esc(v.version_id)}.pdf. ${d.digest ? (d.digest === d.expected ? 'The sha256 computed in this browser matches the recorded hash.' : 'The sha256 computed in this browser does NOT match the recorded hash.') : 'This browser could not compute the hash.'} ${d.draftMark ? `Mark on the file: ${esc(d.draftMark)}.` : ''}</div>` : ''}</div>`;
    }
    const pr = S.print.result && S.print.result.version_id === v.version_id ? S.print.result : null;
    const list = S.print.list[v.version_id] || [];
    html += `<div class="card" data-testid="print-verify"><h3>Print verification (optional)</h3>
      <div class="note small">Measured on simulated photos only. Real print photos were not measured, and symbols are not compared. The version must be approved first.</div>
      <div class="form-grid"><div class="field"><label for="printFile">Photo of the printed label (PNG or JPEG)</label><input class="input" type="file" id="printFile" data-file="print" data-testid="print-file" accept=".png,.jpg,.jpeg,image/png,image/jpeg"${S.busy ? ' disabled' : ''}></div>
        <div class="field"><label for="printCond">Photo condition</label><select class="input" id="printCond" data-model="print.condition" data-testid="print-condition">
          ${['clean_print_scan', 'phone_photo', 'blur', 'glare'].map((c) => `<option value="${c}"${c === S.print.condition ? ' selected' : ''}>${c.split('_').join(' ')}</option>`).join('')}</select></div></div>
      <div class="row mt">${btn('verify', 'Verify print', { primary: true, disabled: !S.print.file })}</div>${statusHtml('verify')}`;
    if (pr) {
      const [cls, sentence] = OUTCOME[pr.outcome] || ['', pr.outcome];
      html += `<div class="item" data-testid="print-result" data-outcome="${esc(pr.outcome)}"><div class="item-head"><span class="badge ${cls}" style="font-size:1rem">${esc(pr.outcome)}</span><span>${esc(sentence)}</span></div>
        ${pr.rescan_reason ? `<div>Reason: ${esc(pr.rescan_reason)}</div>` : ''}
        ${(pr.fields || []).length ? `<table class="tbl mt"><thead><tr><th>Field</th><th>Approved</th><th>Read on the photo</th><th>Result</th></tr></thead><tbody>${pr.fields.map((f) => `<tr><td>${esc(f.field)}</td><td>${esc(f.expected)}</td><td>${esc(f.observed === null ? '(not read)' : f.observed)}</td><td>${esc(f.status)}</td></tr>`).join('')}</tbody></table>` : ''}
        ${pr.barcode ? `<div class="small mt">Barcode: expected <span class="mono">${esc(pr.barcode.expected_payload)}</span>, ${pr.barcode.match ? 'matches' : 'does not match'}.</div>` : ''}
        <div class="small muted mt">Quality: blur ${esc(pr.quality.blur)}, glare ${esc(pr.quality.glare)}, confidence ${esc(pr.quality.confidence)}. Condition ${esc(pr.condition)}. ${esc(pr.verification_id)}</div></div>`;
    }
    if (list.length) html += `<details class="small mt"><summary>Earlier verifications of this version (${list.length})</summary><ul>${list.map((p) => `<li>${when(p.created_at)}: ${esc(p.outcome)} (${esc(p.condition)})</li>`).join('')}</ul></details>`;
    html += '</div>';
    html += `<div class="card"><h3>History</h3>${historyTable()}</div>`;
    return html;
  }

  // ---------------------------------------------------------------- top bar, steps and main render

  function renderSteps() {
    $('#proSteps').innerHTML = STAGES.map(([id, label], i) => {
      const off = !!S.busy || (NEEDS_PRODUCT.has(id) && !S.product);
      return `<button type="button" class="pro-step${S.stage === id ? ' on' : ''}" data-stage="${id}" data-testid="step-${id}"${off ? ' disabled' : ''}${S.stage === id ? ' aria-current="step"' : ''}><span class="n">${i + 1}</span>${esc(label)}</button>`;
    }).join('');
  }

  function render() {
    $('#proTitle').textContent = S.product ? S.product.record.name : 'LabelLens Professional';
    document.querySelectorAll('[data-role]').forEach((b) => { b.classList.toggle('on', b.dataset.role === S.role); b.disabled = !!S.busy; b.setAttribute('aria-pressed', String(b.dataset.role === S.role)); });
    $('#proWho').textContent = S.me ? `${S.me.name} (${S.me.role})` : '';
    renderSteps();
    const views = { products: renderProducts, add: renderAdd, check: renderCheck, change: renderChange, artwork: renderArtwork, review: renderReview, export: renderExport };
    const stage = NEEDS_PRODUCT.has(S.stage) && !S.product ? 'products' : S.stage;
    $('#app').innerHTML = statusHtml('role') + statusHtml('open')
      + (S.flash ? `<div class="okbox" data-testid="flash">${esc(S.flash)}</div>` : '')
      + views[stage]();
    const video = $('#camVideo');
    if (video && S.cam && video.srcObject !== S.cam) { video.srcObject = S.cam; video.play().catch(() => {}); }
  }

  // ---------------------------------------------------------------- events

  const HANDLERS = {
    'go-add': () => goStage('add'),
    'go-products': () => goStage('products'),
    'go-change': () => goStage('change'),
    'go-artwork': () => goStage('artwork'),
    'go-review': () => goStage('review'),
    'go-export': () => goStage('export'),
    'load-products': () => act('products', loadProducts),
    'toggle-evidence': () => { S.evidence.open = !S.evidence.open; render(); },
    'cam-start': camStart,
    'cam-stop': camStop,
    'cam-capture': camCapture,
    sample: () => act('read', async () => {
      setMsg('Loading the sample label file');
      const res = await fetch('/ui/pro/sample/golden_label.pdf', { cache: 'no-store' });
      if (!res.ok) throw new Error(`Could not load the sample label /ui/pro/sample/golden_label.pdf (HTTP ${res.status}).`);
      setFile(new File([await res.blob()], 'golden_label.pdf', { type: 'application/pdf' }), 'upload');
      await doRead();
    }),
    read: () => act('read', doRead),
    save: () => act('save', doSave),
    check: () => act('check', async () => {
      const v = currentVersion();
      setMsg(v.kind === 'generated' ? 'Re-checking the generated artwork' : 'Running the checks');
      const fn = v.kind === 'generated' ? A.recheck : A.inspect;
      S.checks[v.version_id] = await fn(v.version_id, (j) => setMsg(`Check: ${j.message || j.state}`));
      S.history = await A.history(S.product.product.product_id);
    }),
    search: () => act('search', async () => {
      if (!S.evidence.query.trim()) throw new Error('Type a search first.');
      setMsg('Searching the regulations');
      S.evidence.search = await A.search(S.evidence.query.trim());
    }),
    ask: () => act('ask', async () => {
      if (!S.evidence.question.trim()) throw new Error('Type a question first.');
      setMsg('Retrieving passages');
      S.evidence.answer = await A.ask(S.evidence.question.trim());
    }),
    assess: () => act('assess', doAssess),
    'dec-all': () => { (S.change.assessment.affected || []).forEach((i) => { S.change.decisions[i.impact_id] = 'confirmed'; }); render(); },
    confirm: () => act('confirm', doConfirm),
    generate: () => act('generate', doGenerate),
    recheck: (el) => act('recheck', () => doRecheck(el.dataset.v)),
    approve: () => act('review', () => doReview('approve')),
    return: () => act('review', () => doReview('return')),
    download: () => act('download', doDownload),
    verify: () => act('verify', doVerify),
  };

  function setPath(path, value) {
    const keys = path.split('.');
    let o = S;
    for (const k of keys.slice(0, -1)) o = o[k];
    o[keys[keys.length - 1]] = value;
  }

  document.addEventListener('click', (e) => {
    const t = e.target.closest('[data-act],[data-retry],[data-stage],[data-role],[data-open]');
    if (!t || t.disabled) return;
    if (t.dataset.role) { setRole(t.dataset.role); return; }
    if (t.dataset.stage) { goStage(t.dataset.stage); return; }
    if (t.dataset.open) { if (!S.busy) openProduct(t.dataset.open); return; }
    if (t.dataset.retry) { const err = S.errors[t.dataset.retry]; if (err && !S.busy) err.retry(); return; }
    const h = HANDLERS[t.dataset.act];
    if (h && !S.busy) h(t);
  });

  document.addEventListener('input', (e) => {
    const t = e.target;
    if (!t.dataset || !t.dataset.model) return;
    setPath(t.dataset.model, t.value);
    if (t.dataset.model === 'filter') {
      const r = productRows();
      const rows = $('#prodRows'); const note = $('#prodNote');
      if (rows) rows.innerHTML = r.body;
      if (note) note.textContent = r.note;
    }
    if (t.dataset.model === 'change.field') render();
  });

  document.addEventListener('change', (e) => {
    const t = e.target;
    if (t.dataset && t.dataset.dec) { S.change.decisions[t.dataset.dec] = t.value; render(); return; }
    if (t.dataset && t.dataset.model && t.tagName === 'SELECT') { setPath(t.dataset.model, t.value); if (t.dataset.model === 'change.field') render(); return; }
    if (t.dataset && t.dataset.file === 'add' && t.files && t.files[0]) { setFile(t.files[0], 'upload'); render(); }
    if (t.dataset && t.dataset.file === 'print') { S.print.file = t.files && t.files[0] ? t.files[0] : null; render(); }
  });

  document.addEventListener('keydown', (e) => {
    const t = e.target;
    if (e.key === 'Enter' && t.dataset && t.dataset.enter && !S.busy) { e.preventDefault(); const h = HANDLERS[t.dataset.enter]; if (h) h(t); }
  });

  // ---------------------------------------------------------------- start

  function start() {
    A.setUser(A.USERS.editor);
    healthLoop();
    setInterval(healthLoop, 5000);
    const m = /product=([^&]+)/.exec(location.hash);
    render();
    (async () => {
      await act('role', async () => { S.me = await A.me(); });
      if (m) openProduct(decodeURIComponent(m[1]));
      else act('products', loadProducts);
    })();
  }
  start();
})();
