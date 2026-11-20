/**
 * ui/js/render-d5.js
 * Renderer for Screen D5: Evidence (search the device regulations, and ask a cited question)
 *
 * Hard rules:
 * - Professional workspace only (21 CFR 801, 820, 830).
 * - Never invent data. Hits and citations come from the mock or the API.
 * - The ask panel is extractive first; the optional AI answer always falls back to passages.
 * - No em dashes.
 */

(function() {
  const esc = (s) => window.LabelLensData.escapeHtml(s);
  let typedSearch = '';
  let typedQuestion = '';

  function evidenceHtml(d) {
    const hits = d.hits || [];
    const citations = d.citations || [];
    if (hits.length === 0) {
      return `
        <div class="card" data-testid="evidence-empty" style="text-align: center; padding: 48px;">
          <h3>No regulatory evidence found</h3>
          <p class="text-muted text-sm" style="margin-top: 8px;">No sections in 21 CFR matched the given query above the minimum score threshold.</p>
        </div>`;
    }
    return `
      <div class="grid-two-col">
        <div class="card">
          <div class="card-header-clean flex-between">
            <span class="font-semibold text-sm">Retrieved hits (${hits.length})</span>
            <span class="text-xs text-muted">Ranked by score</span>
          </div>
          <div class="flex-col" style="gap: 12px;">
            ${hits.map(h => `
              <div class="card" style="border: 1px solid var(--color-border); padding: 12px;">
                <div class="flex-between">
                  <span class="font-semibold text-xs font-mono">#${esc(h.rank)} ${esc(h.doc_id)}</span>
                  <span class="badge badge-teal text-xs">Score: ${Number(h.score).toFixed(2)}</span>
                </div>
                <div class="text-xs text-muted" style="margin-top: 6px; line-height: 1.4;">"${esc(String(h.text || '').replace(/[–—]/g, '-'))}"</div>
              </div>`).join('')}
          </div>
        </div>
        <div class="card">
          <div class="card-header-clean font-semibold text-sm">Regulatory citations (${citations.length})</div>
          <div class="flex-col" style="gap: 12px;">
            ${citations.map(c => `
              <div style="background-color: var(--color-bg-subtle); padding: 14px; border-radius: var(--radius-md); border: 1px solid var(--color-border);">
                <div class="flex-between">
                  <span class="font-semibold text-sm" style="color: var(--color-primary-blue);">21 CFR ${esc(c.section || '')}</span>
                  <span class="badge badge-blue">${esc(c.source || 'FDA')}</span>
                </div>
                <div class="font-semibold text-xs" style="margin-top: 4px;">${esc(c.title || '')}</div>
                <div class="text-xs text-muted" style="margin-top: 8px; font-style: italic;">"${esc(c.quote || '')}"</div>
                ${c.url ? `<div style="margin-top: 10px;"><a href="${esc(c.url)}" target="_blank" rel="noopener noreferrer" class="text-xs" style="color: var(--color-primary-blue);">View in eCFR &rarr;</a></div>` : ''}
              </div>`).join('')}
          </div>
        </div>
      </div>`;
  }

  function renderScreenD5(container, state, meta, data) {
    if (!container) return;
    const d = data || {};
    const isApi = window.LabelLensData.CONFIG.mode === 'api';
    const A = window.LabelLensAsk;
    const view = { search: null, answer: null, ai: null, note: '', busy: false };
    if (A.isAskJob(d)) view.ai = d;
    else if (Object.prototype.hasOwnProperty.call(d, 'abstained')) view.answer = d;
    else view.search = d;
    const retrieval = (view.search || {}).retrieval || {};
    if (!typedSearch && view.search && view.search.query) typedSearch = view.search.query;

    function paint() {
      container.innerHTML = `
        <div class="flex-between" style="margin-bottom: 16px;">
          <div>
            <h2>Regulatory evidence</h2>
            <div class="text-xs text-muted">Corpus: 21 CFR 801, 820, 830 (medical device regulations)</div>
          </div>
          ${view.search ? `<span class="badge badge-blue">Method: ${esc(retrieval.method || 'search')}</span>` : ''}
        </div>

        <div class="card" style="margin-bottom: 16px;">
          <div class="font-semibold text-sm" style="margin-bottom: 6px;">Search the regulations</div>
          <div class="flex-row" style="background: var(--color-bg-subtle); padding: 8px 12px; border-radius: var(--radius-md); border: 1px solid var(--color-border); gap: 8px;">
            <input type="text" id="d5Search" value="${esc(typedSearch)}" placeholder="for example: format of expiration date on a device label" style="flex: 1; border: none; background: transparent; outline: none; font-size: 0.9rem;">
            <button class="btn btn-sm btn-primary" type="button" id="d5SearchBtn">Search</button>
          </div>
        </div>

        ${view.search ? `<div data-testid="evidence-results">${evidenceHtml(view.search)}</div>` : ''}

        <div class="card" style="margin-top: 16px;" data-testid="ask-card">
          <div class="font-semibold text-sm" style="margin-bottom: 6px;">Ask a cited question</div>
          <div class="flex-row" style="background: var(--color-bg-subtle); padding: 8px 12px; border-radius: var(--radius-md); border: 1px solid var(--color-border); gap: 8px;">
            <input type="text" id="d5Question" value="${esc(typedQuestion)}" placeholder="for example: how must a date be written on a device label?" style="flex: 1; border: none; background: transparent; outline: none; font-size: 0.9rem;">
            <button class="btn btn-sm btn-primary" type="button" id="d5Ask" ${view.busy ? 'disabled' : ''}>Ask</button>
            <button class="btn btn-sm btn-secondary" type="button" id="d5AskAI" ${view.busy ? 'disabled' : ''}>Ask AI (about 40 s)</button>
          </div>
          <div class="text-xs text-muted" id="d5Note" style="margin-top: 6px;">${esc(view.note)}</div>
          ${view.answer ? `<div class="font-semibold text-xs text-muted" style="margin: 12px 0 6px;">Extractive answer (instant)</div>${A.answerHtml(view.answer)}` : ''}
          ${view.ai ? A.aiPanelHtml(view.ai) : ''}
        </div>`;
      bind();
    }

    function bind() {
      const s = container.querySelector('#d5Search');
      const q = container.querySelector('#d5Question');
      s.addEventListener('input', (e) => { typedSearch = e.target.value; });
      q.addEventListener('input', (e) => { typedQuestion = e.target.value; });
      s.addEventListener('keydown', (e) => { if (e.key === 'Enter') container.querySelector('#d5SearchBtn').click(); });
      q.addEventListener('keydown', (e) => { if (e.key === 'Enter') container.querySelector('#d5Ask').click(); });
      const mockNote = 'Mock mode: nothing was sent. Pick a state in the dev panel, or open the page with ?mode=api.';
      const fail = (e) => { view.busy = false; view.note = e.message; paint(); };

      container.querySelector('#d5SearchBtn').addEventListener('click', async () => {
        typedSearch = s.value.trim();
        if (!typedSearch) { view.note = 'Type a search first.'; paint(); return; }
        if (!isApi) { view.note = mockNote; paint(); return; }
        try { view.search = await window.LabelLensActions.search(typedSearch); view.note = ''; paint(); } catch (e) { fail(e); }
      });
      container.querySelector('#d5Ask').addEventListener('click', async () => {
        typedQuestion = q.value.trim();
        if (!typedQuestion) { view.note = 'Type a question first.'; paint(); return; }
        if (!isApi) { view.note = mockNote; paint(); return; }
        try { view.answer = await window.LabelLensActions.ask('professional', typedQuestion); view.note = ''; paint(); } catch (e) { fail(e); }
      });
      container.querySelector('#d5AskAI').addEventListener('click', async () => {
        typedQuestion = q.value.trim();
        if (!typedQuestion) { view.note = 'Type a question first.'; paint(); return; }
        if (!isApi) { view.note = mockNote; paint(); return; }
        try {
          view.busy = true;
          view.ai = { job_id: '...', kind: 'ask', state: 'queued', progress: 0, message: 'Starting the AI answer (about 40 s).' };
          view.note = 'The instant passages stay above while the AI answer runs.';
          try { view.answer = await window.LabelLensActions.ask('professional', typedQuestion); } catch (e) { view.answer = null; }
          paint();
          view.ai = await window.LabelLensActions.askAI('professional', typedQuestion, (j) => { view.ai = j; paint(); });
          view.busy = false; view.note = ''; paint();
        } catch (e) { fail(e); }
      });
    }

    paint();
  }

  window.LabelLensRenderers = window.LabelLensRenderers || {};
  window.LabelLensRenderers['D5 Evidence'] = renderScreenD5;
  window.LabelLensRenderers['D5'] = renderScreenD5;

  if (typeof module !== 'undefined' && module.exports) {
    module.exports = { renderScreenD5 };
  }
})();
