/**
 * ui/js/render-p3.js
 * Renderer for Screen P3: Ask about this label
 *
 * Hard rules:
 * - Public medicine mode only (21 CFR 201, 208, 211).
 * - "Authenticity not verified. Based on a reference label match."
 * - Never invent data. Every value comes from the mock or the API.
 * - An abstained answer shows NO answer text, only the reason and the closest passages.
 * - Score and threshold only when not null. Never show "null" or "NaN".
 * - Panel 1 is the instant extractive answer. The optional AI answer (Ask AI) is panel 2 and always falls back
 *   to the passages (docs/UI_NOTES_AI_ANSWER.md).
 * - The question the user typed is kept in UI state.
 * - No em dashes.
 */

(function() {
  let currentTypedQuestion = '';
  let currentMedicine = '';

  const esc = (s) => window.LabelLensData.escapeHtml(s);

  function renderScreenP3(container, state, meta, data) {
    if (!container) return;
    const safeData = data || {};
    const askAvail = window.LabelLensAsk;
    const isApi = window.LabelLensData.CONFIG.mode === 'api';
    // Panel state for this render: an instant answer and/or an AI job.
    const view = { answer: null, ai: null, note: '', busy: false };
    if (askAvail.isAskJob(safeData)) view.ai = safeData;
    else view.answer = safeData;
    const testBadge = window.LabelLensData.renderTestBadge(safeData);

    function paint() {
      container.innerHTML = `
        <div class="card" style="max-width: 820px; margin: 0 auto;">
          <div class="card-header-clean flex-between">
            <div>
              <div class="flex-row" style="gap: 8px;"><h3>Ask about this label</h3>${testBadge}</div>
              <div class="text-xs text-muted" style="margin-top: 4px;">
                Questions are answered only using retrieved passages from 21 CFR 201, 208, 211 and matched reference labels.
              </div>
            </div>
            <span class="badge badge-teal">Medicine Q&amp;A</span>
          </div>

          ${isApi ? `
            <div style="margin-top: 12px;">
              <label class="text-xs text-muted" for="p3Medicine">Medicine name (matched to a reference label)</label>
              <input type="text" id="p3Medicine" value="${esc(currentMedicine || (window.LabelLensLive && window.LabelLensLive.currentName()) || '')}" placeholder="for example: Childrens Ibuprofen" style="width: 100%; padding: 6px 10px; border: 1px solid var(--color-border); border-radius: var(--radius-md);">
            </div>` : ''}

          <div style="margin: 16px 0;">
            <div class="flex-row" style="background: var(--color-bg-subtle); padding: 8px 12px; border-radius: var(--radius-md); border: 1px solid var(--color-border); gap: 8px;">
              <input type="text" id="p3QuestionInput" value="${esc(currentTypedQuestion)}" placeholder="Ask a question about this medicine (e.g. storage, expiration, packaging requirements)..." style="flex: 1; border: none; background: transparent; outline: none; font-size: 0.92rem;">
              <button class="btn btn-sm btn-primary" type="button" id="btnP3AskSubmit" ${view.busy ? 'disabled' : ''}>Ask</button>
              <button class="btn btn-sm btn-secondary" type="button" id="btnP3AskAI" ${view.busy ? 'disabled' : ''}>Ask AI (about 40 s)</button>
            </div>
            <div class="text-xs text-muted" id="p3Note" style="margin-top: 6px;">${esc(view.note)}</div>
          </div>

          ${view.answer ? `
            <div class="font-semibold text-xs text-muted" style="margin-bottom: 6px;">Extractive answer (instant)</div>
            ${askAvail.answerHtml(view.answer)}` : ''}
          ${view.ai ? askAvail.aiPanelHtml(view.ai) : ''}

          <div class="flex-between" style="margin-top: 24px; padding-top: 16px; border-top: 1px solid var(--color-border);">
            <button class="btn btn-secondary btn-sm" type="button" id="btnP3BackToProduct">&larr; Back to product information</button>
            <span class="text-xs text-muted">Public corpus: 21 CFR 201, 208, 211</span>
          </div>
        </div>`;
      bind();
    }

    /** Resolve the reference product id: match the typed medicine name (the real matcher, CR-23). */
    async function resolveProduct() {
      const name = (container.querySelector('#p3Medicine') || {}).value || currentMedicine;
      currentMedicine = name;
      const liveId = window.LabelLensLive && window.LabelLensLive.productIdFor(name);
      if (liveId) return liveId; // a label the person picked from DailyMed (CR-28)
      if (!name.trim()) throw new Error('Type a medicine name first.');
      const r = await window.LabelLensApi.request('POST', '/public/match', { json: { product_name: name.trim() } });
      if (r.status !== 200) throw new Error((r.body && r.body.message) || `matching failed (HTTP ${r.status})`);
      const best = (r.body.candidates || [])[0];
      if (!best) throw new Error('No reference label matched that name.');
      return best.product_id;
    }

    function bind() {
      const input = container.querySelector('#p3QuestionInput');
      const askBtn = container.querySelector('#btnP3AskSubmit');
      const aiBtn = container.querySelector('#btnP3AskAI');
      const back = container.querySelector('#btnP3BackToProduct');
      if (back) back.addEventListener('click', () => {
        if (window.LabelLensStateSwitcher) window.LabelLensStateSwitcher.setScreen('P2 Product information', 'success');
        else window.dispatchEvent(new CustomEvent('labellens:screen-navigated', { detail: { screen: 'P2 Product information' } }));
      });
      input.addEventListener('input', (e) => { currentTypedQuestion = e.target.value; });
      input.addEventListener('keydown', (e) => { if (e.key === 'Enter') askBtn.click(); });

      const run = async (kind) => {
        currentTypedQuestion = input.value.trim();
        if (!currentTypedQuestion) { setNote('Type a question first.'); return; }
        if (!isApi) { setNote('Mock mode: nothing was sent. Pick an ask state in the dev panel, or open the page with ?mode=api.'); return; }
        try {
          const product_id = await resolveProduct();
          const extra = { product_id };
          if (kind === 'instant') {
            view.answer = await window.LabelLensActions.ask('public', currentTypedQuestion, extra);
            view.note = '';
            paint();
          } else {
            view.ai = { job_id: '...', kind: 'ask', state: 'queued', progress: 0, message: 'Starting the AI answer (about 40 s).' };
            view.busy = true;
            view.note = 'The instant passages stay above while the AI answer runs.';
            // The instant answer shows first, the AI panel follows.
            try { view.answer = await window.LabelLensActions.ask('public', currentTypedQuestion, extra); } catch (e) { view.answer = null; }
            paint();
            view.ai = await window.LabelLensActions.askAI('public', currentTypedQuestion, (j) => { view.ai = j; paint(); }, extra);
            view.busy = false;
            view.note = '';
            paint();
          }
        } catch (e) {
          view.busy = false;
          view.note = e.message;
          paint();
        }
      };
      askBtn.addEventListener('click', () => run('instant'));
      aiBtn.addEventListener('click', () => run('ai'));
    }

    function setNote(t) {
      const n = container.querySelector('#p3Note');
      if (n) n.textContent = t;
    }

    paint();
  }

  window.LabelLensRenderers = window.LabelLensRenderers || {};
  window.LabelLensRenderers['P3 Ask about this label'] = renderScreenP3;
  window.LabelLensRenderers['P3'] = renderScreenP3;

  if (typeof module !== 'undefined' && module.exports) {
    module.exports = { renderScreenP3 };
  }
})();
