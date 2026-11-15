/**
 * ui/js/render-d5.js
 * Renderer for Screen D5: Evidence
 * 
 * Hard rules:
 * - Professional workspace only (21 CFR 801, 820, 830).
 * - Information retrieval core: BM25/hybrid citations.
 * - Never invent data.
 * - No em dashes.
 */

(function() {
  function escapeHtml(str) {
    if (window.LabelLensData && window.LabelLensData.escapeHtml) {
      return window.LabelLensData.escapeHtml(str);
    }
    if (!str) return '';
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  }

  function renderScreenD5(container, state, meta, data) {
    if (!container) return;
    const safeData = data || {};
    const hits = safeData.hits || [];
    const citations = safeData.citations || [];
    const retrieval = safeData.retrieval || {};

    container.innerHTML = `
      <div class="flex-between" style="margin-bottom: 16px;">
        <div>
          <h2>Regulatory Evidence Retrieval</h2>
          <div class="text-xs text-muted">Corpus: 21 CFR 801, 820, 830 (Medical Device Regulations)</div>
        </div>
        <span class="badge badge-blue">Method: ${escapeHtml(retrieval.method || 'BM25')}</span>
      </div>

      <!-- Search Query Box -->
      <div class="card" style="margin-bottom: 20px;">
        <div class="flex-row" style="background: var(--color-bg-subtle); padding: 8px 12px; border-radius: var(--radius-md); border: 1px solid var(--color-border);">
          <span style="color: var(--color-text-muted); margin-right: 8px;">🔍</span>
          <input type="text" value="${escapeHtml(safeData.query || 'format of expiration date on a medical device label')}" style="flex: 1; border: none; background: transparent; outline: none; font-size: 0.9rem;" readonly>
          <button class="btn btn-sm btn-primary" type="button">Search</button>
        </div>
      </div>

      ${hits.length === 0 ? `
        <div class="card" style="text-align: center; padding: 48px;">
          <h3>No regulatory evidence found</h3>
          <p class="text-muted text-sm" style="margin-top: 8px;">No sections in 21 CFR matched the given query above the minimum score threshold.</p>
        </div>
      ` : `
        <div class="grid-two-col">
          <!-- Hits list -->
          <div class="card">
            <div class="card-header-clean flex-between">
              <span class="font-semibold text-sm">Retrieved Hits (${hits.length})</span>
              <span class="text-xs text-muted">Ranked by BM25 Score</span>
            </div>
            <div class="flex-col" style="gap: 12px;">
              ${hits.map(h => `
                <div class="card" style="border: 1px solid var(--color-border); padding: 12px;">
                  <div class="flex-between">
                    <span class="font-semibold text-xs font-mono">#${h.rank} ${escapeHtml(h.doc_id)}</span>
                    <span class="badge badge-teal text-xs">Score: ${Number(h.score).toFixed(2)}</span>
                  </div>
                  <div class="text-xs text-muted" style="margin-top: 6px; line-height: 1.4;">
                    "${escapeHtml(h.text.replace(/[\u2013\u2014]/g, '-'))}"
                  </div>
                </div>
              `).join('')}
            </div>
          </div>

          <!-- Official Citations -->
          <div class="card">
            <div class="card-header-clean font-semibold text-sm">Regulatory Citations (${citations.length})</div>
            <div class="flex-col" style="gap: 12px;">
              ${citations.map(c => `
                <div style="background-color: var(--color-bg-subtle); padding: 14px; border-radius: var(--radius-md); border: 1px solid var(--color-border);">
                  <div class="flex-between">
                    <span class="font-semibold text-sm" style="color: var(--color-primary-blue);">
                      21 CFR ${escapeHtml(c.section || '')}
                    </span>
                    <span class="badge badge-blue">${escapeHtml(c.source || 'FDA')}</span>
                  </div>
                  <div class="font-semibold text-xs" style="margin-top: 4px;">${escapeHtml(c.title || '')}</div>
                  <div class="text-xs text-muted" style="margin-top: 8px; font-style: italic;">
                    "${escapeHtml(c.quote || '')}"
                  </div>
                  ${c.url ? `
                    <div style="margin-top: 10px;">
                      <a href="${escapeHtml(c.url)}" target="_blank" rel="noopener noreferrer" class="text-xs" style="color: var(--color-primary-blue);">View in eCFR &rarr;</a>
                    </div>
                  ` : ''}
                </div>
              `).join('')}
            </div>
          </div>
        </div>
      `}
    `;
  }

  // Register renderer
  window.LabelLensRenderers = window.LabelLensRenderers || {};
  window.LabelLensRenderers['D5 Evidence'] = renderScreenD5;
  window.LabelLensRenderers['D5'] = renderScreenD5;

  if (typeof module !== 'undefined' && module.exports) {
    module.exports = { renderScreenD5 };
  }
})();
