/**
 * ui/js/live-dailymed.js
 * Live DailyMed lookup for the public medicine mode (CR-28).
 *
 * A typed name that the 30 curated medicines do not match can be searched on DailyMed. The page lists labels
 * (name, labeler, form); the person picks one, nothing is chosen for them. The picked label is fetched (a 202 job),
 * shown with the line "Fetched live from DailyMed, not in the curated set", its set id and the fetch date, and can be
 * asked about on P3. Offline or a DailyMed error says so and the curated medicines keep working. Never a mock in api mode.
 *
 * Mock states (dev panel): live_candidates, live_none, live_offline, live_fetching, live_fetch_failed, live_success.
 * No em dashes.
 */
(function () {
  const LIVE_LABEL = 'Fetched live from DailyMed, not in the curated set';
  const current = { product_id: '', typed_name: '', product_name: '' };
  const state = { lastName: '' };

  function esc(s) {
    if (window.LabelLensData && window.LabelLensData.escapeHtml) return window.LabelLensData.escapeHtml(s);
    return String(s == null ? '' : s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
  }
  const isApi = () => window.LabelLensData && window.LabelLensData.CONFIG.mode === 'api';
  const norm = (s) => String(s || '').trim().toLowerCase();

  function banner(kind, title, text, testid) {
    return `<div class="notice-banner ${kind}" data-testid="${testid}" style="margin-top:16px;"><div class="notice-icon">i</div><div>
      <div class="notice-title">${esc(title)}</div><div class="notice-text">${esc(text)}</div></div></div>`;
  }

  function liveLabelHtml(live) {
    if (!live) return '';
    return `<div class="notice-banner notice-warning" data-testid="live-label" style="margin-bottom:16px;"><div class="notice-icon">i</div><div>
      <div class="notice-title">${esc(live.label || LIVE_LABEL)}</div>
      <div class="notice-text">DailyMed set id <code>${esc(live.setid)}</code>, version ${esc(live.version)}, effective ${esc(live.effective_date)}.
        Fetched on ${esc(live.fetched_on)}. ${live.source_url ? `<a href="${esc(live.source_url)}" target="_blank" rel="noopener noreferrer">Open the label on DailyMed</a>` : ''}</div>
    </div></div>`;
  }

  // ---------------------------------------------------------------- views

  function candidatesHtml(res) {
    const items = (res.candidates || []).map((c, i) => `
      <div class="card" data-testid="live-candidate" style="border:1px solid var(--color-border);padding:14px 16px;display:flex;justify-content:space-between;align-items:center;gap:12px;">
        <div>
          <div class="font-semibold">${esc(c.product_name || c.title)}</div>
          <div class="text-xs text-muted" style="margin-top:4px;">${[c.generic_name, c.dosage_form, c.labeler].filter(Boolean).map(esc).join(' | ')}</div>
          <div class="text-xs text-muted">Label updated ${esc(c.published_date || '')}</div>
        </div>
        <button class="btn btn-sm btn-primary" type="button" data-testid="live-select" data-index="${i}">Select</button>
      </div>`).join('');
    return `
      ${banner('', 'Pick the label that matches your pack', 'These labels come from DailyMed, in its own order. Nothing is chosen for you, even when only one is listed.', 'live-pick-note')}
      ${res.message ? `<p class="text-xs text-muted" data-testid="live-list-note" style="margin:8px 0;">${esc(res.message)}</p>` : ''}
      <div style="margin-top:12px;display:flex;flex-direction:column;gap:12px;">${items}</div>
      <div data-testid="live-fetch-area"></div>`;
  }

  function fetchingHtml(job, seconds) {
    const pct = Math.round(((job && job.progress) || 0) * 100);
    return `<div class="card" data-testid="live-fetching" style="text-align:center;padding:32px 24px;max-width:640px;margin:16px auto;">
      <div class="spinner" aria-hidden="true" style="margin:0 auto 12px auto;"></div>
      <h3>Fetching this label from DailyMed</h3>
      <p class="text-sm" style="margin-top:8px;">This can take a little while: the label is downloaded and prepared for questions.</p>
      <p class="text-xs text-muted" style="margin-top:8px;">${esc((job && job.state) || 'processing')} | ${pct}%${seconds != null ? ` | ${seconds} s` : ''}</p>
    </div>`;
  }

  function failedHtml(error) {
    const reason = (error && error.details && error.details.reason) || '';
    const offline = reason === 'offline' || reason === 'timeout' || reason === 'api_error';
    return banner('notice-warning', offline ? 'DailyMed could not be reached' : 'This label could not be used',
      (error && error.message) || 'The label could not be fetched.', 'live-failed') +
      `<p class="text-xs text-muted" style="margin:8px 0;">${reason ? `Reason: ${esc(reason)}. ` : ''}The 30 curated medicines still work: type one of their names or scan its pack.</p>`;
  }

  function searchResultHtml(res) {
    if (res.outcome === 'candidates') return candidatesHtml(res);
    if (res.outcome === 'no_candidates') return banner('notice-warning', 'DailyMed has no label with that name', res.message || '', 'live-none');
    return banner('notice-warning', 'DailyMed lookup is not available', res.message || '', 'live-offline');
  }

  // ---------------------------------------------------------------- api flow

  async function pollJob(jobId, onTick) {
    const t0 = Date.now();
    for (;;) {
      const r = await window.LabelLensApi.request('GET', `/jobs/${encodeURIComponent(jobId)}`);
      if (r.status !== 200) throw new Error(`job ${jobId}: HTTP ${r.status}`);
      onTick(r.body, Math.round((Date.now() - t0) / 1000));
      if (r.body.state === 'done' || r.body.state === 'failed') return r.body;
      if (Date.now() - t0 > 150000) throw new Error('The fetch took longer than 150 s. Try again later.');
      await new Promise((res) => setTimeout(res, 1500));
    }
  }

  async function search(name, out) {
    out.innerHTML = '<p class="text-sm text-muted" data-testid="live-searching">Searching DailyMed...</p>';
    let r;
    try {
      r = await window.LabelLensApi.request('POST', '/public/live/search', { json: { product_name: name } });
    } catch (e) {
      out.innerHTML = searchResultHtml({ outcome: 'unavailable', message: 'This page could not reach its server. The 30 curated medicines still work.' });
      return;
    }
    if (r.status !== 200 || !r.body || r.mock) {
      out.innerHTML = searchResultHtml({ outcome: 'unavailable', message: (r.body && r.body.message) || `The lookup failed (HTTP ${r.status}). The 30 curated medicines still work.` });
      return;
    }
    out.innerHTML = searchResultHtml(r.body);
    out.querySelectorAll('[data-testid="live-select"]').forEach((btn) => {
      btn.addEventListener('click', () => pick(r.body.candidates[Number(btn.dataset.index)], name, out));
    });
  }

  async function pick(candidate, typedName, out) {
    const area = out.querySelector('[data-testid="live-fetch-area"]') || out;
    out.querySelectorAll('[data-testid="live-select"]').forEach((b) => { b.disabled = true; });
    area.innerHTML = fetchingHtml(null, 0);
    try {
      const r = await window.LabelLensApi.request('POST', '/public/live/fetch', { json: { setid: candidate.setid, version: candidate.version } });
      if (r.status !== 202) { area.innerHTML = failedHtml(r.body); out.querySelectorAll('[data-testid="live-select"]').forEach((b) => { b.disabled = false; }); return; }
      const job = await pollJob(r.body.job_id, (j, s) => { area.innerHTML = fetchingHtml(j, s); });
      if (job.state !== 'done') { area.innerHTML = failedHtml(job.error); out.querySelectorAll('[data-testid="live-select"]').forEach((b) => { b.disabled = false; }); return; }
      const p = await window.LabelLensApi.request('GET', job.result_url);
      if (p.status !== 200) { area.innerHTML = failedHtml(p.body); return; }
      current.product_id = p.body.candidates[0].product_id;
      current.typed_name = typedName;
      current.product_name = p.body.candidates[0].product_name;
      window.dispatchEvent(new CustomEvent('labellens:state-changed', {
        detail: { screen: 'P2 Product information', state: 'live_success', meta: {}, data: p.body },
      }));
    } catch (e) {
      area.innerHTML = failedHtml({ message: e.message });
      out.querySelectorAll('[data-testid="live-select"]').forEach((b) => { b.disabled = false; });
    }
  }

  function panelHtml(name) {
    return `<div class="card" data-testid="live-search" style="margin-top:16px;padding:16px;text-align:left;">
      <div class="font-semibold text-sm">Not one of the 30 curated medicines?</div>
      <p class="text-xs text-muted" style="margin:4px 0 8px 0;">Search DailyMed (the US label database) for <strong>${esc(name)}</strong>. You will see a list and choose the label yourself. Labels found this way are not part of the curated set.</p>
      <button class="btn btn-secondary" type="button" data-testid="live-search-go">Search DailyMed</button>
      <div data-testid="live-results"></div>
    </div>`;
  }

  // ---------------------------------------------------------------- P2 wrapper

  function mockNote(out) {
    out.insertAdjacentHTML('beforeend', '<p class="text-xs text-muted" data-testid="live-mock-note" style="margin-top:8px;">Mock mode: nothing was fetched. Open the page with ?mode=api to use DailyMed.</p>');
  }

  function renderLive(container, st, data, base) {
    const d = data || {};
    if (st === 'live_success' || d.outcome === 'live_selected') {
      const cand = (d.candidates && d.candidates[0]) || {};
      const copy = Object.assign({}, d, { candidates: [Object.assign({}, cand)] });
      delete copy.candidates[0].match_confidence;
      base(container, 'success', {}, copy);
      container.insertAdjacentHTML('afterbegin', `<div data-testid="live-product">${liveLabelHtml(d.live)}</div>`);
      return;
    }
    const wrap = '<div style="max-width:720px;margin:0 auto;" data-testid="live-view">';
    if (st === 'live_candidates' || st === 'live_none' || st === 'live_offline') {
      container.innerHTML = wrap + searchResultHtml(d) + '</div>';
      container.querySelectorAll('[data-testid="live-select"]').forEach((btn) => {
        btn.addEventListener('click', () => {
          const area = container.querySelector('[data-testid="live-fetch-area"]');
          if (area) { area.innerHTML = ''; mockNote(area); }
        });
      });
    } else if (st === 'live_fetching') {
      container.innerHTML = wrap + fetchingHtml(d, null) + '</div>';
    } else if (st === 'live_fetch_failed') {
      container.innerHTML = wrap + failedHtml(d.error) + '</div>';
    }
  }

  function wrapP2() {
    const renderers = window.LabelLensRenderers || {};
    ['P2 Product information', 'P2'].forEach((key) => {
      const base = renderers[key];
      if (typeof base !== 'function' || base.__liveWrapped) return;
      const wrapped = (container, st, meta, data) => {
        if ((st && String(st).startsWith('live_')) || (data && data.outcome === 'live_selected')) {
          renderLive(container, st, data, base);
          return;
        }
        base(container, st, meta, data);
        const name = state.lastName;
        if (isApi() && name && (st === 'empty' || st === 'needs_review') && !(data && Array.isArray(data.read_lines) && !data.__typed)) {
          const holder = document.createElement('div');
          holder.style.cssText = 'max-width:640px;margin:0 auto;';
          holder.innerHTML = panelHtml(name);
          container.appendChild(holder);
          const out = holder.querySelector('[data-testid="live-results"]');
          holder.querySelector('[data-testid="live-search-go"]').addEventListener('click', () => search(name, out));
        }
      };
      wrapped.__liveWrapped = true;
      renderers[key] = wrapped;
    });
  }
  wrapP2();

  window.LabelLensLive = {
    LIVE_LABEL, current, setLastName(n) { state.lastName = n; }, currentName() { return current.typed_name || ''; },
    productIdFor(name) {
      const n = norm(name);
      if (current.product_id && n && (n === norm(current.typed_name) || n === norm(current.product_name))) return current.product_id;
      return '';
    },
    liveLabelHtml, searchResultHtml, candidatesHtml, fetchingHtml, failedHtml,
  };
})();
