/**
 * ui/js/api.js
 * Live API access for CONFIG.mode "api". Loaded after data.js, before the renderers.
 *
 * - tryLive(mockPayload): GET the real operation behind a mock state, or say why not (so data.js falls back
 *   to the mock and shows the X-Mock badge). A response with the header X-Mock: true counts as a fallback.
 * - LabelLensActions: user actions (search, ask, ask with AI, upload, review, download, generate). Each one
 *   throws when the API is not reachable; the renderers show that message, they never invent a result.
 * - 202 Job envelopes are polled at GET /jobs/{job_id} every 2 s and given up after 120 s.
 * - Ids come from the mock payload of the state on screen (the seeded demo ids), never made up here.
 * - No em dashes.
 */

(function() {
  const D = () => window.LabelLensData;
  const base = () => D().CONFIG.apiBaseUrl.replace(/\/$/, '');

  /** One request. Returns {status, body, mock}. Network failure throws. */
  async function request(method, path, opts = {}) {
    const headers = Object.assign({ 'X-User-Id': D().CONFIG.currentUserHeader }, opts.headers || {});
    let body;
    if (opts.json !== undefined) {
      headers['Content-Type'] = 'application/json';
      body = JSON.stringify(opts.json);
    } else if (opts.form) {
      body = opts.form; // browser sets the multipart boundary
    }
    const res = await fetch(base() + path, { method, headers, body });
    const mock = res.headers.get('X-Mock') === 'true';
    // Actions (not reads or job polls) say where the data on screen now comes from.
    if (method !== 'GET') D().setDataSource(mock ? 'x-mock' : 'api', `${method} ${path.split('?')[0]}`);
    let parsed = null;
    const type = res.headers.get('Content-Type') || '';
    if (opts.raw) parsed = await res.blob();
    else if (type.includes('json')) parsed = await res.json();
    return { status: res.status, body: parsed, mock, headers: res.headers };
  }

  /** Poll a job until done or failed. onProgress gets each envelope. */
  async function pollJob(jobId, onProgress, intervalMs = 2000, timeoutMs = 120000) {
    const t0 = Date.now();
    for (;;) {
      const r = await request('GET', `/jobs/${encodeURIComponent(jobId)}`);
      if (r.status !== 200) throw new Error(`job ${jobId}: HTTP ${r.status}`);
      if (onProgress) onProgress(r.body);
      // A job id this server never issued is answered with a mock job that never finishes: stop and say so.
      if (r.mock) return Object.assign({}, r.body, { _mock: true });
      if (r.body.state === 'done' || r.body.state === 'failed') return r.body;
      if (Date.now() - t0 > timeoutMs) throw new Error(`The job took longer than ${Math.round(timeoutMs / 1000)} s. Try again later.`);
      await new Promise(res => setTimeout(res, intervalMs));
    }
  }

  /** Find the first value of `key` anywhere in a mock body. */
  function findKey(obj, key) {
    if (!obj || typeof obj !== 'object') return undefined;
    if (typeof obj[key] === 'string') return obj[key];
    for (const v of Object.values(obj)) {
      const f = findKey(v, key);
      if (f) return f;
    }
    return undefined;
  }

  const enc = encodeURIComponent;
  // operationId -> function(ids) returning [method, path, json?]. Only operations that read.
  const READS = {
    getCurrentUser: () => ['GET', '/me'],
    listProducts: () => ['GET', '/products'],
    getProduct: (i) => i.product_id && ['GET', `/products/${enc(i.product_id)}`],
    getProductHistory: (i) => i.product_id && ['GET', `/products/${enc(i.product_id)}/history`],
    listLabelVersions: (i) => i.label_id && ['GET', `/labels/${enc(i.label_id)}/versions`],
    getExtraction: (i) => i.version_id && ['GET', `/label-versions/${enc(i.version_id)}/extraction`],
    getExports: (i) => i.version_id && ['GET', `/label-versions/${enc(i.version_id)}/exports`],
    listReviews: (i) => i.version_id && ['GET', `/label-versions/${enc(i.version_id)}/reviews`],
    listPrintVerifications: (i) => i.version_id && ['GET', `/label-versions/${enc(i.version_id)}/print-verifications`],
    getPrintVerification: (i) => i.verification_id && ['GET', `/print-verifications/${enc(i.verification_id)}`],
    getArtwork: (i) => i.artwork_id && ['GET', `/artworks/${enc(i.artwork_id)}`],
    getChange: (i) => i.change_id && ['GET', `/changes/${enc(i.change_id)}`],
    listAffectedLabels: (i) => i.change_id && ['GET', `/changes/${enc(i.change_id)}/affected`],
    getScan: (i) => i.scan_id && ['GET', `/scans/${enc(i.scan_id)}`],
  };

  /**
   * Try the real operation behind a mock state.
   * @returns {Promise<{ok: boolean, data?: any, status?: number, reason?: string}>}
   */
  async function tryLive(mock) {
    const build = READS[mock.operationId];
    if (!build) return { ok: false, reason: `${mock.operationId}: no live read for this state (action or error sample)` };
    if (mock.status !== 200) return { ok: false, reason: `${mock.operationId}: sample status ${mock.status} is not a read` };
    const ids = {};
    for (const k of ['product_id', 'label_id', 'version_id', 'verification_id', 'artwork_id', 'change_id', 'scan_id']) {
      ids[k] = (D().CONFIG.ids || {})[k] || findKey(mock.data, k);
    }
    const call = build(ids);
    if (!call) return { ok: false, reason: `${mock.operationId}: id missing in sample` };
    try {
      const r = await request(call[0], call[1]);
      if (r.mock) return { ok: false, reason: `${mock.operationId}: server answered with its own mock (X-Mock)` };
      if (r.status !== 200) return { ok: false, reason: `${mock.operationId}: HTTP ${r.status}${r.body && r.body.error ? ' ' + r.body.error : ''}` };
      return { ok: true, data: r.body, status: r.status };
    } catch (e) {
      return { ok: false, reason: `${mock.operationId}: API not reachable (${e.message})` };
    }
  }

  function apiError(r) {
    const b = r.body || {};
    return new Error(b.message ? `${b.error || 'error'}: ${b.message}` : `HTTP ${r.status}`);
  }

  const actions = {
    /** Professional evidence search (module device). */
    async search(query) {
      const r = await request('POST', '/search', { json: { query, module: 'device', k: 10 } });
      if (r.status !== 200) throw apiError(r);
      D().setDataSource(r.mock ? 'x-mock' : 'api', 'searchEvidence');
      return r.body;
    },

    /** Instant extractive answer. moduleKind is "public" or "professional". */
    async ask(moduleKind, question, extra = {}) {
      const path = moduleKind === 'public' ? '/public/ask' : '/ask';
      const body = Object.assign({ question }, extra);
      const r = await request('POST', path, { json: body });
      if (r.status === 503) throw new Error('Search is not available right now (retrieval_unavailable).');
      if (r.status !== 200) throw apiError(r);
      D().setDataSource(r.mock ? 'x-mock' : 'api', moduleKind === 'public' ? 'askPublic' : 'askProfessional');
      return r.body;
    },

    /** Optional AI answer: 202 Job, polled. Resolves to the final job envelope. */
    async askAI(moduleKind, question, onProgress, extra = {}) {
      const path = (moduleKind === 'public' ? '/public/ask' : '/ask') + '?mode=ai';
      const r = await request('POST', path, { json: Object.assign({ question }, extra) });
      if (r.status === 200) {
        // The server answered instantly (extractive): wrap it like a finished job without a model.
        return { job_id: 'none', kind: 'ask', state: 'done', progress: 1, result: { answer: r.body, model: 'none', model_used: false } };
      }
      if (r.status !== 202) throw apiError(r);
      return pollJob(r.body.job_id, onProgress, 2000, 180000); // a cold model can take about a minute
    },

    /** Upload a label (product_id is required by the server, CR-20). Resolves {job, scan}. */
    async uploadScan(file, productId, source, onProgress) {
      const form = new FormData();
      form.append('file', file);
      form.append('source', source || 'upload');
      form.append('product_id', productId);
      const r = await request('POST', '/scans', { form });
      if (r.status !== 202) throw apiError(r);
      const job = await pollJob(r.body.job_id, onProgress);
      let scan = null;
      if (job.state === 'done' && job.result_url) {
        const s = await request('GET', job.result_url);
        if (s.status === 200) scan = s.body;
      }
      return { job, scan };
    },

    /** Approve or return a version. ctx holds version_id, check_id and artifact_sha256 from the screen. */
    async reviewArtwork(ctx, decision, comment) {
      const body = { decision, artifact_sha256: ctx.artifact_sha256 };
      if (comment) body.comment = comment;
      if (decision === 'approve') body.check_id = ctx.check_id;
      const r = await request('POST', `/label-versions/${enc(ctx.version_id)}/reviews`, { json: body });
      if (r.status === 201) return { message: `Recorded: ${r.body.decision} (${r.body.review_id}), status ${r.body.resulting_status}.` };
      throw apiError(r);
    },

    /** Generate draft artwork for a confirmed change. Resolves the artwork once the 202 job is done. */
    async generate(changeId, labelId, onProgress) {
      const r = await request('POST', `/changes/${enc(changeId)}/generate`, { json: { label_id: labelId, test_data: true } });
      if (r.status === 409 || r.status === 422) throw apiError(r);
      if (r.status !== 202) throw apiError(r);
      const job = await pollJob(r.body.job_id, onProgress);
      if (job.state !== 'done') throw new Error((job.error && job.error.message) || 'Generation failed.');
      const a = await request('GET', job.result_url);
      if (a.status !== 200) throw apiError(a);
      return a.body;
    },

    /**
     * Public photo scan (CR-27, no login, no product_id). Resolves {job, result}: result is the PublicMatchResult of a
     * finished scan; a failed job (retake_photo, busy, scan_failed) comes back as job.state 'failed' with job.error.
     * A server that still answers with its mock resolves {job, mock: true}.
     */
    async publicScan(file, onProgress) {
      const form = new FormData();
      form.append('file', file, file.name || 'photo.jpg');
      const r = await request('POST', '/public/scans', { form });
      if (r.status === 429) return { job: { state: 'failed', error: r.body } };
      if (r.status !== 202) throw apiError(r);
      D().setDataSource(r.mock ? 'x-mock' : 'api', 'publicScan');
      const job = await pollJob(r.body.job_id, onProgress);
      if (r.mock || job._mock) return { job, mock: true };
      let result = null;
      if (job.state === 'done' && job.result_url) {
        const s = await request('GET', job.result_url);
        if (s.status === 200) result = s.body;
      }
      return { job, result, mock: false };
    },

    /** Read the stored extraction of a version. */
    async getExtraction(versionId) {
      const r = await request('GET', `/label-versions/${enc(versionId)}/extraction`);
      if (r.status !== 200) throw apiError(r);
      return r.body;
    },

    /** Confirm an extraction. fields: {name: value} for the unclear fields (corrected or as read). */
    async confirmExtraction(versionId, fields) {
      const r = await request('POST', `/label-versions/${enc(versionId)}/extraction/confirm`, { json: { fields } });
      if (r.status !== 200) throw apiError(r);
      return r.body;
    },

    /** Inspect a version: 200 CheckResult, or 202 job (poll, then read result_url). */
    async inspect(versionId, onProgress) {
      const r = await request('POST', `/label-versions/${enc(versionId)}/inspect`, { json: {} });
      if (r.status === 200) return r.body;
      if (r.status !== 202) throw apiError(r);
      const job = await pollJob(r.body.job_id, onProgress);
      if (job.state !== 'done') throw new Error((job.error && job.error.message) || 'Inspection failed.');
      const c = await request('GET', job.result_url);
      if (c.status !== 200) throw apiError(c);
      return c.body;
    },

    /** Re-check a generated version (reads the rendered PDF back). 200, or 202 job. */
    async recheck(versionId, onProgress) {
      const r = await request('POST', `/label-versions/${enc(versionId)}/recheck`);
      if (r.status === 200) return r.body;
      if (r.status !== 202) throw apiError(r);
      const job = await pollJob(r.body.job_id, onProgress);
      if (job.state !== 'done') throw new Error((job.error && job.error.message) || 'Re-check failed.');
      const c = await request('GET', job.result_url);
      if (c.status !== 200) throw apiError(c);
      return c.body;
    },

    /** Register a template version for a product. Resolves {status, body}; 422 bodies are CheckResults. */
    async registerTemplate(productId, template) {
      const r = await request('POST', `/products/${enc(productId)}/templates`, { json: template });
      D().setDataSource(r.mock ? 'x-mock' : 'api', 'registerTemplate');
      if (r.status === 201 || r.status === 422 || r.status === 409) return { status: r.status, body: r.body, mock: r.mock };
      throw apiError(r);
    },

    /** Create a change from one structured edit. Resolves the ChangeAssessment. */
    async assessChange(productId, edits) {
      const r = await request('POST', '/changes', { json: { product_id: productId, edits } });
      if (r.status !== 201) throw apiError(r);
      return r.body;
    },

    /** Confirm the parsed change and every checklist decision. */
    async confirmChange(changeId, decisions) {
      const r = await request('POST', `/changes/${enc(changeId)}/confirm`, { json: { parse_confirmed: true, decisions } });
      if (r.status !== 200) throw apiError(r);
      return r.body;
    },

    /** Download one stored file by sha256 with the user header, then hand it to the browser. */
    async download(sha, name) {
      const r = await request('GET', `/artifacts/${enc(sha)}`, { raw: true });
      if (r.status !== 200) {
        let msg = `HTTP ${r.status}`;
        try { msg = JSON.parse(await r.body.text()).message || msg; } catch (e) { /* not json */ }
        throw new Error(msg);
      }
      const url = URL.createObjectURL(r.body);
      const a = document.createElement('a');
      a.href = url;
      a.download = name || 'label-file';
      document.body.appendChild(a);
      a.click();
      a.remove();
      setTimeout(() => URL.revokeObjectURL(url), 5000);
      const mark = r.headers.get('X-Draft-Mark');
      return `Downloaded ${name}.${mark ? ' Draft mark: ' + mark : ''}`;
    },
  };

  window.LabelLensApi = { request, pollJob, tryLive };
  window.LabelLensActions = actions;
})();
