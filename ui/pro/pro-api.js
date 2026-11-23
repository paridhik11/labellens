/**
 * ui/pro/pro-api.js
 * The only way the Professional page talks to the server. Every operation it uses is listed in
 * docs/PRO_UI_API_MAP.md. No mock data, no fallback: a failure becomes an Error with the API's own message.
 *
 * - X-User-Id header is set from the Editor / Reviewer switch (same header as ui/js/api.js and scripts/demo_flow.py).
 * - A response with X-Mock: true is refused (shown as an error), never shown as data.
 * - 202 jobs are polled at GET /jobs/{job_id} until done or failed.
 * - No em dashes.
 */
(function () {
  const USERS = { editor: 'usr_demo_editor', reviewer: 'usr_demo_reviewer' };
  const BASE = window.location.origin;
  let currentUser = USERS.editor;
  const enc = encodeURIComponent;

  class ApiError extends Error {
    constructor(message, info) {
      super(message);
      Object.assign(this, { status: 0, code: '', body: null, network: false }, info || {});
    }
  }

  /** Turn an API error body into readable text (the server's code and message, plus reasons or a task). */
  function describe(body, fallback) {
    if (body && typeof body === 'object' && body.error) {
      let text = `${body.error}: ${body.message || ''}`.trim();
      const d = body.details || {};
      if (Array.isArray(d.reasons) && d.reasons.length) text += ` (reasons: ${d.reasons.join(', ')})`;
      if (body.task && body.task.title) text += ` (task: ${body.task.title})`;
      return text;
    }
    if (body && typeof body === 'object' && Array.isArray(body.findings)) {
      // A 422 from generateArtwork can be a CheckResult (layout checks failed before rendering), not an Error.
      const msgs = body.findings.map((f) => `${f.severity}: ${f.message}`).join('; ');
      return `The ${body.kind || 'layout'} check ${body.check_id || ''} refused it: ${msgs || 'no finding text'}`;
    }
    if (body && typeof body === 'object' && body.detail) return `${fallback}: ${typeof body.detail === 'string' ? body.detail : JSON.stringify(body.detail)}`;
    return fallback;
  }

  /** One request. Network failure and X-Mock answers throw. */
  async function call(method, path, opts) {
    const o = opts || {};
    const headers = {};
    if (!o.noUser) headers['X-User-Id'] = currentUser;
    let body;
    if (o.json !== undefined) { headers['Content-Type'] = 'application/json'; body = JSON.stringify(o.json); }
    else if (o.form) body = o.form;
    let res;
    try {
      res = await fetch(BASE + path, { method, headers, body, cache: 'no-store' });
    } catch (e) {
      throw new ApiError(`Cannot reach the LabelLens API at ${BASE} (${e.message}). Check that scripts/run_demo.py is running, then press Retry.`, { network: true });
    }
    if (res.headers.get('X-Mock') === 'true') {
      throw new ApiError(`${method} ${path.split('?')[0]}: the server answered from a mock (X-Mock). This page never shows mock data.`, { status: res.status, code: 'mock' });
    }
    const type = res.headers.get('Content-Type') || '';
    let data = null;
    if (o.raw && res.ok) data = await res.blob();
    else if (type.includes('json')) data = await res.json().catch(() => null);
    else data = await res.text().catch(() => '');
    return { status: res.status, data, headers: res.headers };
  }

  /** A request that must answer one of `statuses`; otherwise throws with the API's message. */
  async function expect(method, path, statuses, opts) {
    const r = await call(method, path, opts);
    if (!statuses.includes(r.status)) {
      const body = r.data && typeof r.data === 'object' ? r.data : null;
      throw new ApiError(describe(body, `${method} ${path.split('?')[0]} answered HTTP ${r.status}`), { status: r.status, code: body && body.error, body });
    }
    return r;
  }

  /** Poll a 202 job until done (returns the envelope) or failed (throws the job's error). */
  async function waitJob(job, onTick, limitMs) {
    const end = Date.now() + (limitMs || 300000);
    for (;;) {
      const r = await expect('GET', `/jobs/${enc(job.job_id)}`, [200], { noUser: true });
      const s = r.data;
      if (onTick) onTick(s);
      if (s.state === 'done') return s;
      if (s.state === 'failed') {
        const e = s.error || {};
        throw new ApiError(describe(e, `The ${s.kind} job failed`), { code: e.error, body: e });
      }
      if (Date.now() > end) throw new ApiError(`The ${s.kind} job did not finish within ${Math.round((limitMs || 300000) / 1000)} s.`, {});
      await new Promise((res) => setTimeout(res, 1500));
    }
  }

  /** inspect and recheck: 200 CheckResult, or 202 job whose result_url is the CheckResult. */
  async function checkLike(path, onTick) {
    const r = await expect('POST', path, [200, 202]);
    if (r.status === 200) return r.data;
    const done = await waitJob(r.data, onTick);
    return (await expect('GET', done.result_url, [200])).data;
  }

  async function upload(file, source, productId, onTick) {
    const form = new FormData();
    form.append('file', file, file.name);
    form.append('source', source);
    form.append('product_id', productId);
    const r = await expect('POST', '/scans', [202], { form });
    const done = await waitJob(r.data, onTick);
    const scan = (await expect('GET', done.result_url, [200])).data;
    if (scan.state !== 'done') throw new ApiError(describe(scan.error, `The scan ended ${scan.state}`), { body: scan.error });
    return scan;
  }

  const api = {
    USERS, BASE, ApiError,
    setUser(id) { currentUser = id; },
    user() { return currentUser; },
    async health() { const r = await call('GET', '/health', { noUser: true }); return r.status === 200 && r.data && r.data.status === 'ok'; },
    async me() { return (await expect('GET', '/me', [200])).data; },
    async listProducts() { return (await expect('GET', '/products', [200])).data.items; },
    async registerProduct(body) { return (await expect('POST', '/products', [201], { json: body })).data; },
    async getProduct(id) { return (await expect('GET', `/products/${enc(id)}`, [200])).data; },
    async registerTemplate(id, body) { return (await expect('POST', `/products/${enc(id)}/templates`, [201], { json: body })).data; },
    async history(id) { return (await expect('GET', `/products/${enc(id)}/history`, [200])).data.items; },
    /** Every record version of a product, oldest first (the fields a change edited are the diff between two). */
    async productVersions(id) { return (await expect('GET', `/products/${enc(id)}/versions`, [200])).data.versions; },
    async getChange(id) { return (await expect('GET', `/changes/${enc(id)}`, [200])).data; },
    upload,
    async labelVersions(labelId) { return (await expect('GET', `/labels/${enc(labelId)}/versions`, [200])).data.versions; },
    async labelVersion(v) { return (await expect('GET', `/label-versions/${enc(v)}`, [200])).data; },
    async extraction(v) { return (await expect('GET', `/label-versions/${enc(v)}/extraction`, [200])).data; },
    async confirmExtraction(v, fields) { return (await expect('POST', `/label-versions/${enc(v)}/extraction/confirm`, [200], { json: { fields } })).data; },
    inspect(v, onTick) { return checkLike(`/label-versions/${enc(v)}/inspect`, onTick); },
    recheck(v, onTick) { return checkLike(`/label-versions/${enc(v)}/recheck`, onTick); },
    async search(query, k, method) {
      const json = { query, module: 'device', k: k || 10 };
      if (method) json.retrieval = { method };
      return (await expect('POST', '/search', [200], { json })).data;
    },
    /** The optional AI answer (CR-21): a 202 job, polled; the finished job carries result (AskJobResult). */
    async askAi(question, onTick) {
      const r = await expect('POST', '/ask?mode=ai', [202], { json: { question } });
      const done = await waitJob(r.data, onTick, 120000);
      if (!done.result) throw new ApiError('The AI job finished without a result.', {});
      return done.result;
    },
    async checkResult(id) { return (await expect('GET', `/check-results/${enc(id)}`, [200])).data; },
    async ask(question) { return (await expect('POST', '/ask', [200], { json: { question } })).data; },
    async assessChange(productId, field, newValue) {
      return (await expect('POST', '/changes', [201], { json: { product_id: productId, edits: [{ field, new_value: newValue }] } })).data;
    },
    async confirmChange(changeId, decisions) {
      return (await expect('POST', `/changes/${enc(changeId)}/confirm`, [200], { json: { parse_confirmed: true, decisions } })).data;
    },
    async generate(changeId, labelId, onTick) {
      const r = await expect('POST', `/changes/${enc(changeId)}/generate`, [202], { json: { label_id: labelId, test_data: true } });
      const done = await waitJob(r.data, onTick);
      return (await expect('GET', done.result_url, [200])).data;
    },
    async reviews(v) { return (await expect('GET', `/label-versions/${enc(v)}/reviews`, [200])).data.items; },
    async review(v, body) { return (await expect('POST', `/label-versions/${enc(v)}/reviews`, [201], { json: body })).data; },
    async exports(v) { return (await expect('GET', `/label-versions/${enc(v)}/exports`, [200])).data; },
    /** Download a stored file by sha256 path (/artifacts/<sha>). Returns {blob, draftMark}. */
    async artifact(url) {
      const r = await expect('GET', url, [200], { raw: true });
      return { blob: r.data, draftMark: r.headers.get('X-Draft-Mark') || '' };
    },
    async printVerifications(v) { return (await expect('GET', `/label-versions/${enc(v)}/print-verifications`, [200])).data.items; },
    async verifyPrint(v, photo, condition, onTick) {
      const form = new FormData();
      form.append('photo', photo, photo.name);
      form.append('condition', condition);
      const r = await expect('POST', `/label-versions/${enc(v)}/print-verifications`, [202], { form });
      const done = await waitJob(r.data, onTick);
      return (await expect('GET', done.result_url, [200])).data;
    },
  };

  window.ProApi = api;
})();
