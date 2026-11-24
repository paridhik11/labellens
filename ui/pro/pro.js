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
  // Plain names of record fields, used in "lot LOT1 -> LOT2" text.
  const FIELD_WORD = {
    name: 'name', model: 'model', manufacturer: 'manufacturer', manufacturer_address: 'manufacturer address', udi_di: 'UDI-DI',
    sterilization: 'sterilization', storage: 'storage', lot: 'lot', expiry: 'expiry', serial: 'serial',
  };
  // One fixed question per record field, used for the passage on its finding card ("Search used: ...").
  const FIELD_QUESTION = {
    name: 'What must a device label show for the name of the device?',
    model: 'What must a device label show for the catalog or model number?',
    manufacturer: 'Must a device label show the name and place of business of the manufacturer?',
    manufacturer_address: 'Must a device label show the name and place of business of the manufacturer?',
    udi_di: 'Must the label of every medical device bear a unique device identifier?',
    lot: 'How must the lot or batch number appear on a device label?',
    expiry: 'What must a label show for the expiration date?',
    serial: 'How must a serial number appear in the unique device identifier of a device label?',
    storage: 'What must the labeling of a device say about storage conditions?',
    sterilization: 'What must a device label say about sterilization?',
  };
  // The checker rules that look at each field (src/checker/runner.py). Serial, storage and sterilization have none.
  const FIELD_RULES = {
    name: ['P-NAME'], model: ['P-REF'], manufacturer: ['P-MFR', 'R-NAMEPLACE', 'S-MFR'], manufacturer_address: ['P-ADDR', 'R-NAMEPLACE'],
    udi_di: ['P-UDI', 'R-UDI', 'B-GS1'], lot: ['B-LOT'], expiry: ['D-FMT', 'B-EXP', 'S-EXP'], serial: [], storage: [], sterilization: [],
  };
  const EXAMPLES = [
    ['Expiration date', 'What must a label show for the expiration date?'],
    ['Lot number', 'How must the lot or batch number appear on a device label?'],
    ['Sterilization', 'What must a device label say about sterilization?'],
  ];
  // What 21 CFR 801 asks a device label to carry, with the question retrieval answers for each (shown in Add label).
  const REQUIRED = [
    ['manufacturer', 'Manufacturer name and place of business', (f) => (f.manufacturer && f.manufacturer_address ? 'found' : (f.manufacturer || f.manufacturer_address ? 'partly' : 'missing')), FIELD_QUESTION.manufacturer],
    ['udi', 'Unique device identifier (UDI-DI)', (f) => (f.udi_di ? 'found' : 'missing'), FIELD_QUESTION.udi_di],
    ['lot', 'Lot or batch number', (f) => (f.lot ? 'found' : 'missing'), FIELD_QUESTION.lot],
    ['expiry', 'Expiration date written year-month-day', (f) => (!f.expiry ? 'missing' : (/^\d{4}-\d{2}-\d{2}$/.test(f.expiry) ? 'found' : 'format')), FIELD_QUESTION.expiry],
    ['barcode', 'Machine-readable barcode with the identifier (AIDC)', (f, ex) => ((ex.barcodes || []).length ? 'found' : 'missing'), 'UDI automatic identification and data capture AIDC technology plain-text'],
  ];
  const REQ_WORD = { found: ['teal', 'Found'], partly: ['warn', 'Partly found'], format: ['warn', 'Found, not YYYY-MM-DD'], missing: ['danger', 'Not read'] };
  const HL_STOP = new Set(['what', 'must', 'should', 'shall', 'does', 'this', 'that', 'with', 'from', 'have', 'show', 'about', 'there', 'which', 'device', 'devices', 'label', 'labels']);
  // The five retrieval systems of the Retrieval lab (POST /search `retrieval.method`).
  const LAB_SYSTEMS = [
    ['bm25', 'BM25', 'our own inverted index'], ['tfidf', 'TF-IDF', 'our own index, cosine'], ['dense', 'Dense', 'embeddings plus FAISS'],
    ['hybrid_rrf', 'Hybrid', 'BM25 and dense, reciprocal rank fusion'], ['e5b', 'E5b (final)', 'stemming, query prefix, heading text, fused'],
  ];
  const LAB_EXAMPLES = ['What must a label show for the expiration date?', 'sterile device labeling', 'unique device identifier on a package',
    'who must put their name on the label'];
  // Fresh 30-query set, scored once (results/step18_final.md). LLM grades, not human grades. tests/test_pro_ui_static.py
  // checks these numbers against that file.
  const LAB_EVAL = [['Plain hybrid', '0.701', '0.927'], ['Hybrid + stemming + prefix', '0.762', '0.987'], ['E5b (final)', '0.783', '0.990']];
  let pendingScroll = null;
  // Label text field (extractor name) that carries each record field (src/checker/synthetic.py FIELD_ORDER).
  const LABEL_FIELD = { name: 'product_name', manufacturer: 'manufacturer', manufacturer_address: 'manufacturer_address', model: 'model', lot: 'lot', expiry: 'expiry' };
  const PREFIX_RE = /^\s*[A-Za-z][A-Za-z .#/]{0,15}:\s*/;
  const TEST_UDI = '00000000000000';

  function freshAdd() {
    return { file: null, extra: [], source: 'upload', previewUrl: null, read: null, form: {}, notes: {}, prog: null, camMsg: '', req: null };
  }

  /** Evidence card state: the free question, its answer, the on-demand extra passages and the per-field panel. */
  function freshEvidence(open) {
    return { open: !!open, question: '', thread: [] };
  }

  const S = {
    stage: 'products', role: 'editor', me: null,
    busy: null, busyMsg: '', busyStart: 0, errors: {}, flash: '',
    products: null, filter: '',
    add: freshAdd(), cam: null,
    product: null, versions: [], labelId: null, history: [],
    checks: {}, fieldPassages: {},
    recordVersions: [], changeInfo: {}, lab: { query: '', runs: null },
    evidence: freshEvidence(),
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

  /** A button with one line of help text under it. */
  function btnHelp(buttonHtml, help, testid) {
    return `<div class="bh">${buttonHtml}<span class="bh-help small muted" data-testid="${testid}">${esc(help)}</span></div>`;
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
    if (stage === 'lab') { render(); return; }
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
      S.restored = null;
      S.change = { field: 'lot', value: '', assessment: null, decisions: {}, confirmed: null };
      S.print = { file: null, condition: 'clean_print_scan', result: null, list: {} };
      S.evidence = freshEvidence(S.evidence.open);
      S.fieldPassages = {};
      S.changeInfo = {};
      if (S.previewUrl) { URL.revokeObjectURL(S.previewUrl); S.previewUrl = null; }
    }
    S.product = detail;
    S.labelId = detail.labels.length ? detail.labels[0].label_id : null;
    setMsg('Loading label versions and history');
    S.versions = S.labelId ? await A.labelVersions(S.labelId) : [];
    await refreshHistory(pid);
    await restoreCheck();
    history.replaceState(null, '', `#product=${encodeURIComponent(pid)}`);
  }

  /** After a reload the check results are gone from memory; read the newest saved one for the current version. */
  async function restoreCheck() {
    const v = currentVersion();
    if (!v || S.checks[v.version_id]) return;
    const ids = S.history.filter((h) => h.action === 'check.recorded' && (!h.details || h.details.kind !== 'layout')).slice(0, 4).map((h) => h.entity_id);
    for (const id of ids) {
      try {
        const c = await A.checkResult(id);
        if (c.version_id === v.version_id) { S.checks[v.version_id] = c; S.restored = c.check_id; return; }
      } catch (e) { /* an unreadable old check is skipped */ }
    }
  }

  /** Reload the activity history plus what it needs to say what changed: record versions and the changes behind them. */
  async function refreshHistory(pid) {
    S.history = await A.history(pid);
    S.recordVersions = await A.productVersions(pid);
    const ids = new Set(S.history.filter((h) => h.entity_type === 'change').map((h) => h.entity_id));
    S.recordVersions.forEach((r) => { if (r.source_change_id) ids.add(r.source_change_id); });
    for (const id of ids) {
      if (!S.changeInfo[id]) { try { S.changeInfo[id] = await A.getChange(id); } catch (e) { /* the text then names only the id */ } }
    }
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
    await refreshHistory(S.product.product.product_id);
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

  /** The server takes PNG, JPEG and PDF. WebP, BMP and GIF are redrawn as JPEG in the browser first (TIFF and HEIC cannot be). */
  async function toUploadable(file) {
    if (/^(application\/pdf|image\/(png|jpeg))$/.test(file.type)) return file;
    if (!/^image\/(webp|bmp|gif)$/.test(file.type)) throw new Error(`${file.name}: this file type (${file.type || 'unknown'}) cannot be read. Use PNG, JPEG, WebP, BMP or PDF. For TIFF or HEIC photos, export them as JPEG first.`);
    const bmp = await createImageBitmap(file);
    const canvas = document.createElement('canvas');
    canvas.width = bmp.width; canvas.height = bmp.height;
    canvas.getContext('2d').drawImage(bmp, 0, 0);
    const blob = await new Promise((res) => canvas.toBlob(res, 'image/jpeg', 0.92));
    if (!blob) throw new Error(`${file.name}: the browser could not convert this image.`);
    return new File([blob], file.name.replace(/\.[^.]+$/, '') + '.jpg', { type: 'image/jpeg' });
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
    const files = [S.add.file, ...S.add.extra];
    const reads = [];
    for (const [i, original] of files.entries()) {
      const tag = files.length > 1 ? `Image ${i + 1} of ${files.length}: ` : '';
      setMsg(`${tag}Preparing the file`);
      const file = await toUploadable(original);
      const scan = await A.upload(file, S.add.source, intake, (j) => setMsg(`${tag}Reading text and barcode: ${j.message || j.state}`));
      setMsg(`${tag}Loading what was read`);
      reads.push({ scan, ex: await A.extraction(scan.version_id) });
    }
    const ex = window.ReadHints.merge(reads.map((x) => x.ex));
    const scan = reads[0].scan;
    S.add.read = { intake, scan, ex, count: reads.length };
    const pre = prefill(ex);
    augment(pre.values, pre.notes, ex);
    // two images that read the same field differently: say so on the field
    const labelToRecord = Object.fromEntries(Object.entries(LABEL_FIELD).map(([rf, lf]) => [lf, rf]));
    Object.entries(ex.conflicts || {}).forEach(([lf, vals]) => {
      const rf = labelToRecord[lf];
      if (rf && pre.notes[rf]) pre.notes[rf].why = `The images disagree: ${vals.join(' | ')}. Check the label.`;
    });
    S.add.form = pre.values; S.add.notes = pre.notes; S.add.prog = null;
    S.add.req = {};
    for (const [key, , , question] of REQUIRED) {
      setMsg(`Looking up what the regulations require (${Object.keys(S.add.req).length + 1} of ${REQUIRED.length})`);
      try { S.add.req[key] = await A.ask(question); } catch (e) { S.add.req[key] = { error: e.message }; }
    }
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

  /** Fill still-empty fields from text lines no field accounts for. Every such value is marked "check it". */
  function augment(values, notes, ex) {
    const H = window.ReadHints;
    const ls = H.lines(ex);
    const st = H.sterilization(ls);
    if (st && !values.sterilization) {
      values.sterilization = st.value;
      notes.sterilization = { src: `Suggested from the text line "${st.line}"`, why: 'A rule suggested this from a printed line. Check it.' };
    }
    const sg = H.storage(ls);
    if (sg && !values.storage) {
      values.storage = sg.value;
      notes.storage = { src: `Suggested from the text line "${sg.lines.join('" and "')}"`, why: 'A rule suggested this from a printed line. Check it.' };
    }
    if (!values.model) {
      const cand = H.modelCandidate(H.unassigned(ex, values));
      if (cand) {
        values.model = cand.text;
        notes.model = { src: `Guessed from the text line "${cand.text}"`, why: 'Guess: the only unassigned line shaped like a model number. Check it.' };
      }
    }
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
    const res = await fetch('/ui/pro/sample/test_device.json', { cache: 'no-store' });
    if (!res.ok) throw new Error(`Could not load the template file /ui/pro/sample/test_device.json (HTTP ${res.status}).`);
    const t = await res.json();
    if (!p.pid) {
      // The template prints these text slots; the renderer refuses an empty one, so they must be filled before saving.
      const printed = t.slots.filter((sl) => sl.type === 'text').map((sl) => (sl.field === 'product_name' ? 'name' : sl.field));
      const missing = RECORD_FIELDS.filter(([f]) => printed.includes(f) && !v[f]).map(([, label]) => label);
      if (missing.length) throw new Error(`The label template prints these fields, so they cannot be empty: ${missing.join(', ')}. Type them from the product specification, then save. (A product record cannot be edited after saving.)`);
      setMsg('Step 1 of 4: registering the product record');
      const made = await A.registerProduct(recordBody(v));
      p.pid = made.product.product_id;
    }
    if (!p.template) {
      setMsg('Step 2 of 4: registering the label template');
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

  // ---------------------------------------------------------------- what changed (record version diffs)

  const recordVersion = (n) => S.recordVersions.find((r) => r.version === n);
  const plain = (v) => String(v === null || v === undefined ? '' : v).trim();

  /** Fields whose value differs between two record versions: [{field, from, to}]. Empty and missing count as equal. */
  function diffRecords(a, b) {
    const val = (r, f) => (EXTRA_KEYS.includes(f) || !(f in r) ? plain((r.extra || {})[f]) : plain(r[f]));
    const keys = ['name', 'model', 'manufacturer', 'manufacturer_address', 'udi_di', 'sterilization', 'storage',
      ...new Set([...Object.keys(a.extra || {}), ...Object.keys(b.extra || {})].filter((k) => k !== 'intake'))];
    return [...new Set(keys)].map((f) => ({ field: f, from: val(a, f), to: val(b, f) })).filter((d) => d.from !== d.to);
  }

  const arrowText = (ds) => ds.map((d) => `${FIELD_WORD[d.field] || d.field} ${d.from || '(empty)'} → ${d.to || '(empty)'}`).join(', ');

  /** "L2: lot LOT1 -> LOT2 (change chg_...)" or "L1: first upload", from the record versions the label versions point at. */
  function versionChangeText(v) {
    const i = S.versions.findIndex((x) => x.version_id === v.version_id);
    const tag = `L${v.artwork_version}`;
    if (i <= 0) return `${tag}: first upload`;
    const a = recordVersion(S.versions[i - 1].product_version);
    const b = recordVersion(v.product_version);
    if (!a || !b) return `${tag}: record version ${v.product_version} (details not loaded)`;
    const ds = diffRecords(a, b);
    if (!ds.length) return `${tag}: no record change (record v${b.version}), new ${v.kind === 'generated' ? 'artwork' : 'upload'}`;
    return `${tag}: ${arrowText(ds)}${b.source_change_id ? ` (change ${b.source_change_id})` : ''}`;
  }

  function versionsTable() {
    if (!S.versions.length) return '<div class="muted">This product has no label version yet.</div>';
    return `<table class="tbl" data-testid="version-history"><thead><tr><th>Version</th><th>What changed</th><th>Kind</th><th>Status</th><th>Marks</th><th>Made by</th><th>When</th></tr></thead><tbody>
      ${S.versions.slice().reverse().map((v) => `<tr><td><strong>L${esc(v.artwork_version)}</strong><div class="small mono">${esc(v.version_id)}</div></td>
        <td data-testid="what-changed">${esc(versionChangeText(v))}</td>
        <td>${esc(v.kind)}</td><td><span class="badge ${v.status === 'reviewed' ? 'teal' : ''}">${esc(v.status)}</span></td>
        <td>${v.draft_watermark ? '<span class="badge draft">DRAFT</span>' : ''}</td><td>${esc(v.created_by)}</td><td class="small">${when(v.created_at)}</td></tr>`).join('')}
    </tbody></table>`;
  }

  /** One plain sentence for the events that carry a change, else an empty string. */
  function historyDetail(h) {
    const ci = S.changeInfo[h.entity_id];
    if (h.action === 'change.created') {
      return ci ? `Change requested: ${FIELD_WORD[ci.field] || ci.field} ${ci.old_value || '(empty)'} → ${ci.new_value || '(empty)'}` : '';
    }
    if (h.action === 'product.version_created') {
      const n = h.version_after;
      if (!n || n === 1) return 'Record v1 created';
      const a = recordVersion(n - 1); const b = recordVersion(n);
      if (!a || !b) return `Record v${n} created`;
      const ds = diffRecords(a, b);
      return `Record v${n}: ${ds.length ? arrowText(ds) : 'no field differs'}${b.source_change_id ? ` (change ${b.source_change_id})` : ''}`;
    }
    if (h.action === 'label.version_created') {
      const v = S.versions.find((x) => x.version_id === h.entity_id);
      return v ? versionChangeText(v) : '';
    }
    return '';
  }

  function historyTable() {
    if (!S.history.length) return '<div class="muted">No events yet.</div>';
    return `<table class="tbl" data-testid="history"><thead><tr><th>When</th><th>Who</th><th>What</th><th>On</th><th>Detail</th></tr></thead><tbody>
      ${S.history.map((h) => `<tr><td class="small">${when(h.at)}</td><td>${esc(h.user_id)}</td><td>${esc(h.action)}</td><td class="small"><span class="mono">${esc(h.entity_type)} ${esc(h.entity_id)}</span></td><td class="small" data-testid="history-detail">${esc(historyDetail(h))}</td></tr>`).join('')}
    </tbody></table>`;
  }

  /** Text fields the product's newest template prints but the record leaves empty (the renderer refuses those). */
  function emptyPrinted() {
    const tpls = (S.product && S.product.templates) || [];
    if (!tpls.length) return [];
    const t = tpls.reduce((x, y) => (y.version > x.version ? y : x));
    const rec = S.product.record;
    const labels = Object.fromEntries(RECORD_FIELDS);
    return t.slots.filter((sl) => sl.type === 'text')
      .map((sl) => (sl.field === 'product_name' ? 'name' : sl.field))
      .filter((f) => labels[f] && !String(recVal(rec, f)).trim())
      .map((f) => labels[f]);
  }

  function productHeader() {
    const rec = S.product.record; const v = currentVersion();
    return `<div class="card" data-testid="product-header"><div class="row" style="justify-content:space-between">
      <div><div style="font-size:1.2rem;font-weight:700">${esc(rec.name)}</div>
      <div class="small muted">${esc(S.product.product.product_id)} | model ${esc(rec.model || '(none)')} | ${esc(rec.manufacturer || '')} | record version ${esc(rec.version)}</div></div>
      <div class="row">${v ? `<span class="badge blue" data-testid="current-version">Current label L${esc(v.artwork_version)} (${esc(v.kind)})</span><span class="badge">${esc(v.status)}</span>${v.draft_watermark ? '<span class="badge draft">DRAFT</span>' : ''}` : '<span class="badge warn">No label version</span>'}</div>
    </div>${emptyPrinted().length ? `<div class="note" data-testid="record-incomplete">This product record has no ${esc(emptyPrinted().join(', '))}, but the label template prints it, so revised artwork cannot be generated (the renderer refuses empty text). A saved record cannot be edited: add the product again with every printed field filled.</div>` : ''}</div>`;
  }

  function roleNote(needed) {
    if (needed === 'editor' && !isEditor()) return '<div class="note" data-testid="role-note">This step is for an Editor. Switch to Editor at the top of the page.</div>';
    if (needed === 'reviewer' && isEditor()) return '<div class="note" data-testid="role-note">Approval is for a Reviewer. Switch to Reviewer at the top of the page.</div>';
    return '';
  }

  function head(title, help, right) {
    return `<div class="stage-head"><h2>${title}</h2><div class="row">${right || ''}</div></div><p class="help">${help}</p>`;
  }

  // ---------------------------------------------------------------- Retrieval lab

  async function runLab() {
    const q = S.lab.query.trim();
    if (!q) throw new Error('Type a query first, or press an example.');
    const runs = [];
    for (const [method, label] of LAB_SYSTEMS) {
      setMsg(`Searching with ${label} (${runs.length + 1} of ${LAB_SYSTEMS.length})`);
      const t0 = performance.now();
      const r = await A.search(q, 5, method);
      const cite = Object.fromEntries((r.citations || []).map((c) => [c.chunk_id, c]));
      runs.push({ method, label, ms: Math.round(performance.now() - t0), hits: (r.hits || []).slice(0, 5).map((h) => ({ ...h, c: cite[h.doc_id] || null })) });
    }
    S.lab.runs = runs; S.lab.asked = q;
  }

  function renderLab() {
    const L = S.lab;
    let html = head('Retrieval lab', 'Retrieval is the core of LabelLens: it finds the regulation text that explains a check. Type one query and see what each of the five systems returns, side by side. Passages that several systems agree on are marked.',
      btn('go-products', 'Back to Products'));
    html += `<div class="card"><h3>Same query, five systems <span class="badge" data-testid="lab-raw">raw retrieval, unfiltered</span></h3><p class="small muted">Each system's top 5 as ranked, with no product filter and no merging of a section's chunks. Ask the regulations shows filtered passages.</p>
      <div class="row mb">${LAB_EXAMPLES.map((q, i) => btn('lab-example', esc(q), { small: true, data: { q }, testid: `lab-example-${i}` })).join('')}</div>
      <div class="row"><input class="input" style="flex:1 1 380px" data-model="lab.query" data-enter="lab-run" data-testid="lab-query" placeholder="A labeling question or keywords" value="${esc(L.query)}">${btn('lab-run', 'Run on all five', { primary: true })}</div>
      ${statusHtml('lab')}`;
    if (L.runs) {
      const count = {};
      L.runs.forEach((r) => r.hits.forEach((h) => { count[h.doc_id] = (count[h.doc_id] || 0) + 1; }));
      const agree = Object.values(count).filter((n) => n >= 3).length;
      html += `<div class="small muted mt" data-testid="lab-summary">${Object.keys(count).length} different passages in the five top-5 lists; ${agree} appear in three or more systems (marked). Question words are not highlighted here: ranking, not wording, is the point. Timings include the network.</div>
        <div class="labscroll"><table class="tbl lab" data-testid="lab-table"><thead><tr><th>Rank</th>${L.runs.map((r) => `<th>${esc(r.label)}<div class="small muted" style="text-transform:none;font-weight:400">${esc((LAB_SYSTEMS.find((x) => x[0] === r.method) || [])[2] || '')}, ${esc(r.ms)} ms</div></th>`).join('')}</tr></thead><tbody>
        ${[0, 1, 2, 3, 4].map((i) => `<tr><td>${i + 1}</td>${L.runs.map((r) => {
          const h = r.hits[i];
          if (!h) return '<td class="muted">none</td>';
          const c = h.c;
          return `<td class="${count[h.doc_id] >= 3 ? 'agree' : ''}" data-testid="lab-cell" data-chunk="${esc(h.doc_id)}" data-agree="${count[h.doc_id] >= 3}"><strong>${c ? `21 CFR ${esc(c.section)}` : esc(h.doc_id)}</strong><div class="small">${c ? esc(c.title) : ''}</div><div class="small muted mono">${esc(String(h.doc_id).split('_').pop())}, score ${esc(Number(h.score).toFixed(4))}</div></td>`;
        }).join('')}</tr>`).join('')}</tbody></table></div>`;
    }
    html += '</div>';
    html += `<div class="grid2"><div class="card" data-testid="lab-how"><h3>How a question becomes a cited passage</h3>
        <ol class="small" style="padding-left:18px;line-height:1.6">
          <li><strong>Index.</strong> The regulations are cut into passages. BM25 and TF-IDF are our own code, not a library. Dense retrieval embeds each passage once.</li>
          <li><strong>Rank.</strong> Each system ranks the passages for your query. Hybrid fuses BM25 and dense with reciprocal rank fusion. E5b adds stemming, a query prefix and the section heading.</li>
          <li><strong>Gate.</strong> If the best score is below a threshold fitted on development queries, nothing is shown (the "No regulation passage answers this" notice).</li>
          <li><strong>Pick sentences.</strong> A small cross-encoder picks the sentences of the top passages that best match the question.</li>
          <li><strong>Cite.</strong> The checker rules decide pass or fail. Retrieval only attaches the passage that explains why, with a verbatim quote and a link.</li>
        </ol></div>
      <div class="card" data-testid="lab-eval"><h3>How well does it work?</h3>
        <p class="small muted mb">30 fresh queries (20 device, 10 medicine), scored once. Relevance grades are LLM grades, not human grades.</p>
        <table class="tbl"><thead><tr><th>System</th><th>nDCG@10</th><th>Recall@20 (pool-based)</th></tr></thead><tbody>
        ${LAB_EVAL.map(([n, a, b]) => `<tr><td>${esc(n)}</td><td>${esc(a)}</td><td>${esc(b)}</td></tr>`).join('')}</tbody></table>
        <p class="small muted mt">E5b over plain hybrid: +0.082 nDCG@10, 95% interval [+0.037, +0.136]. Over hybrid with stemming and prefix: +0.021 [-0.011, +0.054], which includes zero. E5b was chosen on cross-validation, where the gains are optimistic. The abstention gate is weak (no score reaches AUROC 0.90). Source: results/step18_final.md.</p></div></div>`;
    return html;
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
        ${btnHelp(btn('load-products', 'Refresh'), 'Reloads the product list from the server.', 'help-refresh')}</div>
        ${statusHtml('products')}
        ${S.products ? `<table class="tbl"><thead><tr><th>Name</th><th>Model</th><th>Manufacturer</th><th>Version</th><th>Labels</th><th>Open findings</th></tr></thead><tbody id="prodRows">${r.body}</tbody></table>
        <div class="small muted mt" id="prodNote" data-testid="product-note">${esc(r.note)}</div>` : ''}</div>`;
  }

  function renderAdd() {
    const ad = S.add; const ed = isEditor();
    const file = ad.file ? `<div class="okbox" data-testid="chosen-file">Chosen: <strong>${esc(ad.file.name)}</strong> (${Math.round(ad.file.size / 1024)} KB, ${esc(ad.file.type || 'unknown type')}, source ${esc(ad.source)})${ad.extra.length ? ` and ${ad.extra.length} more image(s): ${esc(ad.extra.map((f) => f.name).join(', '))}` : ''}</div>` : '';
    let html = head('Add a product from its label', 'Upload a PDF or a photo of the label, take a photo, or use the sample Golden Pump label. LabelLens reads the text (OCR) and the barcode. You check and correct every field, then save: that registers the product record, its label template and its first label version. Editor only.')
      + roleNote('editor')
      + `<div class="card"><h3>1. Choose the label</h3><div class="row">
          <label class="btn${ed && !S.busy ? '' : ' disabled'}" style="${ed && !S.busy ? '' : 'opacity:.5;pointer-events:none'}">Choose PDF or image<input type="file" id="addFile" data-file="add" data-testid="add-file" accept=".pdf,.png,.jpg,.jpeg,.webp,.bmp,.gif,application/pdf,image/png,image/jpeg,image/webp,image/bmp,image/gif" multiple hidden></label>
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
        <p class="small muted mb">Read from ${esc(ad.file ? ad.file.name : '')}${ad.read.count > 1 ? ` and ${ad.read.count - 1} more image(s), merged` : ''} (scan ${esc(ad.read.scan.scan_id)}). Highlighted fields need your attention (${unclearCount}). Nothing is saved until you press Save product.</p>
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
          ${unassignedHtml(ex)}
          <details class="small mt"><summary>All text lines read (${(ex.ocr_blocks || []).length})</summary><ul>${(ex.ocr_blocks || []).map((b) => `<li class="mono">${esc(b.text)}${b.conf !== undefined ? ` <span class="muted">${Math.round(b.conf * 100)}%</span>` : ''}</li>`).join('')}</ul></details>
        </div></div></div>
        ${requiredHtml(ex)}
        <div class="row mt">${btn('save', 'Save product', { primary: true, disabled: !ed })}${btn('go-products', 'Cancel')}</div>
        ${ad.prog && ad.prog.pid ? `<div class="info small" data-testid="save-progress">Saved so far: product ${esc(ad.prog.pid)}${ad.prog.template ? `, template ${esc(ad.prog.template)}` : ''}${ad.prog.scan ? `, label version ${esc(ad.prog.scan.version_id)}` : ''}. Retry continues from here.</div>` : ''}
        ${statusHtml('save')}</div>`;
    }
    return html;
  }

  // ---------------------------------------------------------------- evidence

  const FIELD_OUTCOME = { pass: ['teal', 'Pass'], needs_human: ['warn', 'Needs a person'], not_checked: ['', 'Not checked'], not_applicable: ['', 'Not applicable'] };

  /** Escape text, then mark the words of the question that appear in it (word starts, so "label" marks "labeling"). */
  function markTerms(text, q) {
    const terms = [...new Set(String(q || '').toLowerCase().match(/[a-z]{4,}/g) || [])].filter((t) => !HL_STOP.has(t));
    const safe = esc(text);
    if (!terms.length) return safe;
    return safe.replace(new RegExp(`\\b(${terms.join('|')})`, 'gi'), '<mark>$1</mark>');
  }

  /** One regulation passage as a compact card: section and title, a two-line quote with the question words marked, a link. */
  function passageHtml(c, q) {
    return `<div class="cite compact" data-testid="passage"><div class="ptitle"><strong>21 CFR ${esc(c.section)}</strong> ${esc(c.title)}`
      + `${c.url ? ` <a href="${esc(c.url)}" target="_blank" rel="noopener noreferrer">Open the regulation</a>` : ''}</div>`
      + `${c.quote ? `<div class="q clamp2">"${markTerms(c.quote, q)}"</div>` : ''}</div>`;
  }

  // Display only (the gate itself is unchanged): a general question, not about labeling, whose top score sits just
  // above the gate or whose top passages do not name its key term, folds its passages. "what is sterilization in
  // medical?" retrieves 801.150 (processing and repacking), which does not define sterilization.
  const GATE_MARGIN = 0.0005;
  const LABELING_WORDS = /\b(label|labels|labeling|labelling|labeled|show|must|shall|require|required|requirements?|package|carton|udi|identifier|barcode|printed|appear|format|date|lot|batch|serial|expiration|expiry)\b/i;
  const TERM_STOP = new Set(['what', 'which', 'where', 'when', 'about', 'medical', 'device', 'devices', 'mean', 'means', 'meaning', 'define', 'definition', 'does', 'there', 'their', 'benefits', 'should', 'would', 'could', 'explain', 'tell']);
  function weakGeneral(res, q) {
    const question = String(q || '');
    if (!res || !(res.sources || []).length || LABELING_WORDS.test(question)) return false;
    const near = res.score !== null && res.score !== undefined && res.threshold !== null && res.threshold !== undefined && res.score - res.threshold < GATE_MARGIN;
    const terms = (question.toLowerCase().match(/[a-z]{5,}/g) || []).filter((t) => !TERM_STOP.has(t)).map((t) => t.slice(0, 7));
    const heads = res.sources.slice(0, 3).map((c) => `${c.section} ${c.title}`.toLowerCase()).join(' ');
    const named = terms.length && terms.some((t) => heads.includes(t));
    return near || !named;
  }

  /** The result of one /ask call: a no-answer notice, or the top 3 passages. more is the "show more" block. */
  function askResultHtml(res, more, q) {
    if (!res) return '';
    if (res.error) return `<div class="note">The lookup failed: ${esc(res.error)}</div>`;
    const sources = res.sources || [];
    if (res.abstained && weakGeneral(res, q)) {
      const det = res.score !== null && res.score !== undefined ? `<div class="small muted mt" data-testid="evidence-details-line">${esc(res.score_name)} ${esc(Number(res.score).toFixed(5))}, gate ${esc(Number(res.threshold).toFixed(5))}</div>` : '';
      return `<div class="note" data-testid="not-defined">The regulations don't define this directly. Ask about what a device label must show, or open the closest passages.</div>`
        + `<details class="small mt" data-testid="not-defined-passages"><summary>Show closest passages (${Math.min(3, sources.length)})</summary>${sources.slice(0, 3).map((c) => passageHtml(c, q)).join('')}</details>${det}`;
    }
    const gate = res.score !== null && res.score !== undefined
      ? `<div>${esc(res.score_name)} ${esc(Number(res.score).toFixed(5))}${res.threshold !== null && res.threshold !== undefined ? `, gate ${esc(Number(res.threshold).toFixed(5))}` : ''}</div>` : '';
    const ids = sources.length ? `<div>Passage ids: ${sources.map((c) => `<span class="mono">${esc(c.chunk_id)}</span>`).join(', ')}</div>` : '';
    const details = (gate || ids) ? `<details class="small muted mt" data-testid="evidence-details"><summary>details</summary>${gate}${ids}</details>` : '';
    if (!sources.length && res.abstained) {
      return `<div class="note" data-testid="no-passage">No regulation passage answers this. Try a labeling question.</div>${details}`;
    }
    let html = res.abstained
      ? '<div class="small muted mt" data-testid="closest">Closest regulation passages. Retrieval found these; no answer was written, so a person should read them.</div>'
      : `<div class="okbox" data-testid="answer">${esc(res.answer)}</div>`;
    html += `<div data-testid="evidence-results">${sources.slice(0, 3).map((c) => passageHtml(c, q)).join('')}</div>`;
    if (more) html += more;
    return html + details;
  }

  const AI_FALLBACK = {
    model_unavailable: 'The AI model is not available here. Showing the closest passages.',
    timeout: 'The AI did not answer within 3 minutes. Showing the closest passages instead.',
    verification_failed: 'The AI answer did not pass the citation checks. Showing the closest passages.',
  };

  /** Body of an AI turn: the verified answer, or the passages with the reason the model was not used. */
  function aiBody(t) {
    const ai = t.ai; const a = ai.answer || {};
    const meta = !ai.model ? '' : `<div class="small muted mt" data-testid="ai-meta">Model ${esc(ai.model)}${ai.latency_s !== undefined ? `, ${esc(Number(ai.latency_s).toFixed(1))} s` : ''}. The model may only use the retrieved passages; a checker rejects any sentence the passages do not support.</div>`;
    if (ai.fallback_reason) return `<div class="info small" data-testid="ai-fallback" data-reason="${esc(ai.fallback_reason)}">${esc(AI_FALLBACK[ai.fallback_reason] || ai.fallback_reason)}</div>${askResultHtml(a, '', t.q)}${meta}`;
    if (ai.model_used && a.abstained) return `<div class="note" data-testid="ai-no-answer">The model says the retrieved passages do not answer this question.</div>${meta}`;
    if (ai.model_used) return `<div class="okbox" data-testid="ai-answer">${esc(a.answer)}</div><div class="small muted">AI-generated, supported by the cited text only. Check the quotes. This is not a compliance decision.</div><div data-testid="evidence-results">${(a.sources || []).slice(0, 3).map((c) => passageHtml(c, t.q)).join('')}</div>${meta}`;
    return `${askResultHtml(a, '', t.q)}${meta}`;
  }

  /** "Show more passages" for one turn: the rest of retrieval's top 10 that are not already shown. */
  function moreHtml(t, i) {
    if (!t.res || !(t.res.sources || []).length) return '';
    // /search is raw retrieval: apply the same product filter, skip sections already shown, one chunk per section
    const shown = new Set((t.res.sources || []).map((c) => String(c.section)));
    const rest = (applicableOnly({ sources: t.more || [] }, S.product && S.product.record).sources || []).filter((c) => !shown.has(String(c.section))).slice(0, 7);
    return `<div class="mt">${btn('more-passages', t.showMore ? 'Hide more passages' : 'Show more passages', { small: true, data: { i }, testid: `more-${i}` })}${statusHtml('more')}</div>`
      + (t.showMore ? `<div data-testid="more-results">${rest.map((c) => passageHtml(c, t.q)).join('') || '<div class="muted small mt">No further passages.</div>'}</div>` : '');
  }

  function turnHtml(t, i) {
    const ai = t.mode === 'ai';
    return `<div class="turn" data-testid="turn" data-mode="${esc(t.mode)}"><div class="turn-q"><span class="badge ${ai ? 'draft' : 'blue'}">${ai ? 'AI answer' : 'Passages'}</span> ${esc(t.q)}</div>`
      + `${ai ? aiBody(t) : askResultHtml(t.res, moreHtml(t, i), t.q)}</div>`;
  }

  // Sections that only apply to some products (latex condoms) are dropped for other products; each section shows once.
  // Same table as src/rag/applicability.py, which filters /ask on the server when a product_id is sent.
  const PRODUCT_SPECIFIC = { '801.435': /latex|condom/i, '801.430': /tampon/i, '809.10': /in vitro|diagnostic|\bivd\b|reagent|assay/i };
  /** The open device product, sent with /ask so the server filters passages for it (CR-29). */
  const productId = () => (S.product && S.product.product ? S.product.product.product_id : undefined);
  function applicableOnly(res, rec) {
    if (!res || !res.sources) return res;
    const text = Object.values(rec || {}).filter((x) => typeof x === 'string').join(' ');
    const seen = new Set();
    const sources = res.sources.filter((c) => {
      const sec = String(c.section);
      if (PRODUCT_SPECIFIC[sec] && !PRODUCT_SPECIFIC[sec].test(text)) return false;
      if (seen.has(sec)) return false;
      seen.add(sec); return true;
    });
    return { ...res, sources };
  }

  // ---------------------------------------------------------------- finding cards (Check, read-only in Review)

  // Fields with a checker rule (src/checker/runner.py). Order follows the label.
  const CARD_FIELDS = ['name', 'model', 'manufacturer', 'manufacturer_address', 'udi_di', 'lot', 'expiry'];
  const RANK = { fail: 4, needs_human: 3, pass: 2, not_applicable: 1, not_checked: 0 };
  const RESULT_WORD = { fail: ['danger', 'Problem found'], needs_human: ['warn', 'A person must look'], pass: ['teal', 'Pass'], not_applicable: ['', 'Not applicable'], not_checked: ['', 'Not checked'] };

  /** One field's result from the check: the worst outcome over its rules, the rules with their outcome, its findings. */
  function fieldResult(c, f) {
    const rules = (FIELD_RULES[f] || []).map((rid) => {
      const cov = (c.coverage || []).find((x) => x.rule_id === rid);
      return { rid, outcome: cov ? cov.outcome : 'not_checked', reason: cov ? cov.reason || '' : 'not reported in this check' };
    });
    const findings = (c.findings || []).filter((x) => (FIELD_RULES[f] || []).includes(x.rule_id));
    const worst = rules.reduce((w, r) => (RANK[r.outcome] > RANK[w] ? r.outcome : w), 'not_checked');
    let [cls, word] = RESULT_WORD[worst] || ['', worst];
    if (worst === 'fail' && findings.some((x) => /mismatch$/.test(x.kind))) word = 'Mismatch';
    return { rules, findings, worst, cls, word };
  }

  /** Passages for one field question, loaded once per product through /ask with the product filter (CR-29). */
  const passageKey = (f) => `${productId() || ''}|${FIELD_QUESTION[f]}`;
  let loadingPassages = false;
  async function loadFieldPassages() {
    if (loadingPassages || !S.product) return;
    const todo = [...new Set(CARD_FIELDS.map(passageKey))].filter((k) => !S.fieldPassages[k]);
    if (!todo.length) return;
    loadingPassages = true;
    try {
      for (const k of todo) {
        const q = k.slice(k.indexOf('|') + 1);
        try { S.fieldPassages[k] = applicableOnly(await A.ask(q, productId()), S.product.record); } catch (e) { S.fieldPassages[k] = { error: e.message }; }
      }
    } finally { loadingPassages = false; }
    if (!S.busy) render();
  }

  /** Cited passages of a field's findings, one per section, in order. */
  function citedPassages(fr) {
    const seen = new Set();
    return fr.findings.flatMap((x) => (x.citations || []).map((cc) => ({ ...cc, by: x.rule_id })))
      .filter((cc) => { const k = String(cc.section); if (seen.has(k)) return false; seen.add(k); return true; });
  }

  /** The top passage, collapsed to two lines; the rest behind "Show related passages". */
  function cardPassagesHtml(f, fr) {
    const more = (list) => (list.length > 1 ? `<details class="small"><summary data-testid="card-more">Show related passages (${list.length - 1})</summary>${list.slice(1).map((cc) => passageHtml(cc, FIELD_QUESTION[f])).join('')}</details>` : '');
    const cited = citedPassages(fr);
    if (cited.length) {
      return `<div class="small" style="color:#888" data-testid="card-search-used">Cited by rule ${esc(cited[0].by)} (the checker's fixed query)</div>${passageHtml(cited[0], FIELD_QUESTION[f])}${more(cited)}`;
    }
    const res = S.fieldPassages[passageKey(f)];
    const used = `<div class="small" style="color:#888" data-testid="card-search-used">Search used: ${esc(FIELD_QUESTION[f])}</div>`;
    if (!res) return `${used}<div class="small muted" data-testid="card-loading">Retrieving the governing passage...</div>`;
    if (res.error) return `${used}<div class="small muted">The passage lookup failed: ${esc(res.error)}</div>`;
    const src = res.sources || [];
    if (!src.length) return `${used}<div class="small muted" data-testid="card-no-passage">No regulation passage answers this field's question. A person should look.</div>`;
    return `${used}${passageHtml(src[0], FIELD_QUESTION[f])}${more(src)}`;
  }

  /** Finding cards for every field with a rule. readOnly (Review) shows no Run check button. */
  function findingCardsHtml(v, readOnly) {
    const rec = S.product.record;
    const c = v && S.checks[v.version_id];
    if (!c) {
      return `<div class="card" data-testid="finding-cards"><h3>Findings by field</h3><div class="small muted" data-testid="cards-nocheck">No check yet on L${esc(v ? v.artwork_version : '?')}.</div>`
        + (readOnly ? '' : `<div class="mt">${btn('check', 'Run check', { primary: true, small: true, disabled: !v, testid: 'cards-run-check' })}</div>`) + '</div>';
    }
    return `<div class="card" data-testid="finding-cards"><h3>Findings by field (L${esc(v.artwork_version)})</h3>
      <p class="small muted mb">Each card: the product record value, what the check rules decided, and the top regulation passage retrieval found for that field. Rules decide; the passage explains. Pass is not a statement that the label meets the regulations.</p>
      <div class="fcards">${CARD_FIELDS.map((f) => {
        const fr = fieldResult(c, f);
        return `<div class="fcard" data-testid="finding-card" data-field="${esc(f)}" data-outcome="${esc(fr.worst)}">
          <div class="row"><strong>${esc(FIELD_WORD[f] || f)}</strong><span class="badge ${fr.cls}" data-testid="card-result">${esc(fr.word)}</span></div>
          <div class="small">Product: <strong data-testid="card-value">${fmtVal(recVal(rec, f)) || '<span class="muted">(empty)</span>'}</strong></div>
          ${fr.findings.map((x) => `<div class="small">${esc(String(x.message || '').replace(/([^.])$/, '$1.'))}${x.observed || x.expected ? ` Read: <strong>${esc(x.observed || '(nothing)')}</strong>. Expected: <strong>${esc(x.expected || '(nothing)')}</strong>.` : ''}</div>`).join('')}
          <div class="small muted" data-testid="card-rules">Rule${fr.rules.length > 1 ? 's' : ''}: ${fr.rules.map((r) => `<span class="mono" title="${esc(r.reason)}">${esc(r.rid)}</span> ${esc((RESULT_WORD[r.outcome] || ['', r.outcome])[1].toLowerCase())}`).join(', ')}</div>
          <div class="mt">${cardPassagesHtml(f, fr)}</div></div>`;
      }).join('')}</div></div>`;
  }

  /** Plain-text findings report for the export: every finding with its rule id and cited passages. */
  function findingsReport(v, c) {
    const rec = S.product.record;
    const lines = [`LabelLens findings report`, `Product: ${rec.name} (record version ${rec.version})`, `Label version: L${v.artwork_version} ${v.version_id}`,
      `Check: ${c.check_id} (${c.kind}) run ${c.run_at}, retrieval ${(c.retrieval_config || {}).method || ''}`,
      `Result: ${c.critical_count} critical, ${c.review_count} to review, ${c.info_count} info, ${c.needs_human_count || 0} rule(s) need a person.`,
      'Rules decide; passages explain. This is not a compliance determination.', ''];
    lines.push('By field:');
    CARD_FIELDS.forEach((f) => {
      const fr = fieldResult(c, f);
      lines.push(`- ${FIELD_WORD[f] || f}: product "${recVal(rec, f)}" -> ${fr.word} (${fr.rules.map((r) => `${r.rid} ${r.outcome}`).join(', ')})`);
    });
    lines.push('', `Findings (${(c.findings || []).length}):`);
    (c.findings || []).forEach((x, i) => {
      lines.push(`${i + 1}. [${x.severity}] rule ${x.rule_id || '-'} field ${x.field || '-'}: ${x.message}`);
      if (x.observed || x.expected) lines.push(`   read "${x.observed || ''}", expected "${x.expected || ''}"`);
      (x.citations || []).forEach((cc) => lines.push(`   cited: 21 CFR ${cc.section} ${cc.title} (${cc.chunk_id}) "${cc.quote}" ${cc.url || ''}`));
      if (!(x.citations || []).length) lines.push('   cited: none (a person must look)');
    });
    const human = (c.coverage || []).filter((x) => x.outcome === 'needs_human');
    lines.push('', `A person must check (${human.length}):`);
    human.forEach((h) => lines.push(`- ${h.rule_id}: ${h.reason || ''}`));
    return lines.join('\n') + '\n';
  }

  function renderEvidence() {
    const ev = S.evidence;
    return `<div class="card" data-testid="evidence"><h3>Evidence for ${esc(S.product.record.name)}</h3>
      <p class="small muted mb">Facts about this product come from the product record and the latest check. Regulation text comes from retrieval over 21 CFR 801, 820 and 830. (See Findings by field.) Passages are filtered for this product: sections that only govern other products are dropped and each section shows once.</p>
      <h3 class="mt">Ask the regulations</h3>
      <p class="small muted mb">Answers labeling-regulation questions, not questions about this product. The passages appear at once; the AI answer is optional (about 15 s once the model is loaded, about a minute the first time). Try:</p>
      <div class="row mb">${EXAMPLES.map(([label, q]) => btn('ask-example', esc(label), { small: true, data: { q }, testid: 'example-' + label.toLowerCase().split(' ')[0] })).join('')}</div>
      <label class="small" for="evQuestion"><strong>Regulation search (general)</strong></label>
      <div class="row"><input class="input" id="evQuestion" style="flex:1 1 380px" data-model="evidence.question" data-enter="ask" data-testid="evidence-question" placeholder="For example: what must a label show for the expiration date?" value="${esc(ev.question)}">${btn('ask', 'Ask', { primary: true })}${btn('ask-ai', 'Ask with AI (optional, first run about a minute)', { testid: 'btn-ask-ai' })}</div>
      ${statusHtml('ask')}${statusHtml('ask-ai')}
      <div data-testid="thread">${ev.thread.slice().reverse().map((t) => ({ t, i: ev.thread.indexOf(t) })).map(({ t, i }) => turnHtml(t, i)).join('')}</div>
      ${ev.thread.length ? `<div class="mt">${btn('clear-thread', 'Clear questions', { small: true })}</div>` : ''}</div>`;
  }

  // ---------------------------------------------------------------- Add label: lines not in a field, required elements

  function unassignedHtml(ex) {
    const list = window.ReadHints.unassigned(ex, S.add.form);
    const opts = RECORD_FIELDS.map(([f, label]) => `<option value="${f}">${esc(label)}</option>`).join('');
    return `<h3 class="mt">Other text read (${list.length})</h3>
      <p class="small muted">Lines the reader found that no field accounts for. Choose a field to move a line into it.</p>
      ${list.length ? list.map((l, i) => `<div class="uline" data-testid="unassigned-line"><span class="mono">${esc(l.text)}</span>${l.conf !== null ? ` <span class="muted small">${Math.round(l.conf * 100)}%</span>` : ''}
        <select class="input" data-assign="${i}" data-line="${esc(l.text)}" aria-label="Put this line into a field"><option value="">Put into...</option>${opts}</select></div>`).join('')
        : '<div class="muted small" data-testid="no-unassigned">Every line that was read is already in a field.</div>'}`;
  }

  function requiredHtml(ex) {
    const f = S.add.form;
    const rows = REQUIRED.map(([key, label, test]) => ({ key, label, status: test(f, ex), res: (S.add.req || {})[key] }));
    const found = rows.filter((r) => r.status === 'found').length;
    return `<div class="card mt" data-testid="required"><h3>What the regulations require on this label (${found} of ${rows.length} found)</h3>
      <p class="small muted mb">Found only means a value was read from the label or typed by you. It does not say the label complies. Each passage was retrieved for the question shown, through the same score gate as Evidence.</p>
      <table class="tbl"><thead><tr><th>Required element</th><th>On this label</th><th>Governing regulation (retrieval)</th></tr></thead><tbody>
      ${rows.map((r) => {
        const [cls, word] = REQ_WORD[r.status];
        const q = (REQUIRED.find((x) => x[0] === r.key) || [])[3];
        return `<tr data-testid="required-row" data-key="${esc(r.key)}" data-status="${esc(r.status)}"><td><strong>${esc(r.label)}</strong></td><td><span class="badge ${cls}">${esc(word)}</span></td>
          <td>${S.add.req ? askResultHtml(r.res, '', q) : '<span class="muted">Not looked up</span>'}</td></tr>`;
      }).join('')}</tbody></table></div>`;
  }

  function renderCheck() {
    const rec = S.product.record; const v = currentVersion();
    const extra = rec.extra || {};
    let html = head('Product and label check', 'The check compares the label with the product record and attaches cited passages from 21 CFR 801, 820 and 830 found by our retrieval. Every finding has a citation or says a person must look. Rules decide; nothing here says a label meets the regulations. Anyone can run a check.',
      `${btnHelp(btn('check', v ? `Run check on L${esc(v.artwork_version)}` : 'Run check', { primary: true, disabled: !v }), 'Compares this label version with the product record using 16 rules.', 'help-check')}`
      + `${btnHelp(btn('go-change', 'Change a detail'), 'Starts a change to one record field, for example the lot, and shows what the label needs.', 'help-change')}`
      + `${btnHelp(btn('toggle-evidence', S.evidence.open ? 'Hide Ask the regulations' : 'Ask the regulations'), 'A question box over the device regulations, filtered for this product, with an optional AI answer.', 'help-evidence')}`)
      + productHeader()
      + statusHtml('check');
    const c = v && S.checks[v.version_id];
    if (c) html += `<div class="card">${S.restored === c.check_id ? `<div class="small muted mb" data-testid="restored">Showing the saved check ${esc(c.check_id)} from ${when(c.run_at)}. Press Run check to check again.</div>` : ''}${checkHtml(c)}</div>`;
    else if (v) html += `<div class="info small">No saved check exists for L${esc(v.artwork_version)}. ${v.kind === 'generated' ? 'For generated artwork the check reads the rendered PDF back (re-check).' : 'Press Run check.'}</div>`;
    html += findingCardsHtml(v, false);
    if (S.evidence.open) html += renderEvidence();
    const fieldRow = (f, k, val) => `<dt>${k}</dt><dd>${fmtVal(val) || '<span class="muted">(empty)</span>'}</dd>`;
    html += `<div class="grid2"><div class="card"><h3>Product record</h3><dl class="kv" data-testid="record">
        ${[['name', 'Name', rec.name], ['model', 'Model', rec.model], ['manufacturer', 'Manufacturer', rec.manufacturer], ['manufacturer_address', 'Manufacturer address', rec.manufacturer_address], ['udi_di', 'UDI-DI', rec.udi_di], ['sterilization', 'Sterilization', rec.sterilization], ['storage', 'Storage', rec.storage]]
          .map(([f, k, val]) => fieldRow(f, k, val)).join('')}
        ${EXTRA_KEYS.map((k) => fieldRow(k, esc(k), extra[k])).join('')}
        ${Object.entries(extra).filter(([k]) => k !== 'intake' && !EXTRA_KEYS.includes(k)).map(([k, val]) => `<dt>${esc(k)}</dt><dd>${fmtVal(val)}</dd>`).join('')}
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
      <div class="row mt">${btn('generate', 'Generate revised artwork', { primary: true, disabled: !ed || emptyPrinted().length > 0 })}</div>${statusHtml('generate')}</div>`;
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
    html += findingCardsHtml(v, true);
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
    const chk = S.checks[v.version_id];
    html += `<div class="card" data-testid="export-findings"><h3>Findings report of L${esc(v.artwork_version)}</h3>`
      + (chk
        ? `<p class="small muted">Every finding of check ${esc(chk.check_id)} with its rule id and cited passages, the per-field results, and the rules that need a person. Plain text, made in this browser from the stored check.</p>
          <ul class="small" style="padding-left:18px" data-testid="export-findings-list">${(chk.findings || []).map((x) => `<li><span class="mono">${esc(x.rule_id || '-')}</span> ${esc(x.message)}${(x.citations || []).length ? ` (cited: ${x.citations.map((cc) => `21 CFR ${esc(cc.section)}`).join(', ')})` : ' (no citation, a person must look)'}</li>`).join('') || '<li>No problem findings.</li>'}</ul>
          <div class="row">${btn('download-report', 'Download findings report (.txt)')}</div>`
        : `<div class="small muted" data-testid="export-no-check">No check of L${esc(v.artwork_version)} in this session. Run the re-check in Review and approve first; the report is built from it.</div>`)
      + '</div>';
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
    const views = { lab: renderLab, products: renderProducts, add: renderAdd, check: renderCheck, change: renderChange, artwork: renderArtwork, review: renderReview, export: renderExport };
    const stage = NEEDS_PRODUCT.has(S.stage) && !S.product ? 'products' : S.stage;
    $('#app').innerHTML = statusHtml('role') + statusHtml('open')
      + (S.flash ? `<div class="okbox" data-testid="flash">${esc(S.flash)}</div>` : '')
      + views[stage]();
    if ((stage === 'check' || stage === 'review') && S.product && !S.busy) loadFieldPassages();
    const video = $('#camVideo');
    if (video && S.cam && video.srcObject !== S.cam) { video.srcObject = S.cam; video.play().catch(() => {}); }
    if (pendingScroll && !S.busy) {
      const el = document.querySelector(`[data-testid="${pendingScroll}"]`);
      pendingScroll = null;
      if (el) el.scrollIntoView({ block: 'start' });
    }
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
      await refreshHistory(S.product.product.product_id);
    }),
    ask: () => act('ask', async () => {
      const q = S.evidence.question.trim();
      if (!q) throw new Error('Type a question first, or press one of the examples.');
      setMsg('Retrieving regulation passages');
      S.evidence.thread.push({ q, mode: 'extractive', res: await A.ask(q, productId()), more: null, showMore: false });
    }),
    'ask-example': (el) => { S.evidence.question = el.dataset.q; HANDLERS.ask(); },
    'ask-ai': () => act('ask-ai', async () => {
      const q = S.evidence.question.trim();
      if (!q) throw new Error('Type a question first, or press one of the examples.');
      setMsg('Model is loading, the first run can take about a minute (waiting up to 180 s)');
      let ai;
      try {
        const t0 = Date.now();
        ai = await A.askAi(q, () => setMsg(`Model is loading, the first run can take about a minute (${Math.round((Date.now() - t0) / 1000)} s of up to 180 s)`), productId());
      } catch (e) {
        if (!e.timeout) throw e;
        ai = { fallback_reason: 'timeout', model_used: false, answer: await A.ask(q, productId()) };
      }
      S.evidence.thread.push({ q, mode: 'ai', ai });
    }),
    'lab-run': () => act('lab', runLab),
    'lab-example': (el) => { S.lab.query = el.dataset.q; HANDLERS['lab-run'](); },
    'clear-thread': () => { S.evidence.thread = []; render(); },
    'more-passages': (el) => {
      const t = S.evidence.thread[Number(el.dataset.i)];
      if (!t) return;
      if (t.showMore) { t.showMore = false; render(); return; }
      if (t.more) { t.showMore = true; render(); return; }
      act('more', async () => {
        setMsg('Loading the next passages');
        t.more = (await A.search(t.q, 10)).citations || [];
        t.showMore = true;
      });
    },
    'download-report': () => {
      const v = latestGenerated(); const c = v && S.checks[v.version_id];
      if (!c) return;
      const url = URL.createObjectURL(new Blob([findingsReport(v, c)], { type: 'text/plain' }));
      const a = document.createElement('a'); a.href = url; a.download = `${v.version_id}_findings.txt`;
      document.body.appendChild(a); a.click(); a.remove();
      setTimeout(() => URL.revokeObjectURL(url), 10000);
    },
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
    if (t.dataset && t.dataset.assign !== undefined && t.value) {
      const f = t.value; const text = t.dataset.line;
      S.add.form[f] = ['model', 'lot', 'expiry'].includes(f) ? strip(text) : text;
      S.add.notes[f] = { src: `Moved from the text line "${text}"`, why: '' };
      render();
      return;
    }
    if (t.dataset && t.dataset.dec) { S.change.decisions[t.dataset.dec] = t.value; render(); return; }
    if (t.dataset && t.dataset.model && t.tagName === 'SELECT') { setPath(t.dataset.model, t.value); if (t.dataset.model === 'change.field') render(); return; }
    if (t.dataset && t.dataset.file === 'add' && t.files && t.files[0]) { setFile(t.files[0], 'upload'); S.add.extra = [...t.files].slice(1); render(); }
    if (t.dataset && t.dataset.file === 'print') { S.print.file = t.files && t.files[0] ? t.files[0] : null; render(); }
  });

  document.addEventListener('keydown', (e) => {
    const t = e.target;
    if (e.key === 'Enter' && t.dataset && t.dataset.enter && !S.busy) { e.preventDefault(); const h = HANDLERS[t.dataset.enter]; if (h) h(t); }
  });

  // Opening a link with another #product= in the same tab does not reload the page, so follow the hash here.
  window.addEventListener('hashchange', () => {
    const m = /product=([^&]+)/.exec(location.hash);
    const id = m && decodeURIComponent(m[1]);
    if (id && !S.busy && (!S.product || S.product.product.product_id !== id)) openProduct(id);
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
