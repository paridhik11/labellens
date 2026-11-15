/**
 * ui/js/render-p3.js
 * Renderer for Screen P3: Ask about this label
 * 
 * Hard rules:
 * - Public medicine mode only (21 CFR 201, 208, 211).
 * - "Authenticity not verified. Based on a reference label match."
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

  function renderScreenP3(container, state, meta, data) {
    if (!container) return;
    const safeData = data || {};
    const isAbstained = safeData.abstained === true;

    container.innerHTML = `
      <div class="card" style="max-width: 800px; margin: 0 auto;">
        <div class="card-header-clean flex-between">
          <div>
            <h3>Ask about this label</h3>
            <div class="text-xs text-muted">Questions are answered only using retrieved evidence from 21 CFR 201, 208, 211 and matched reference labels.</div>
          </div>
          <span class="badge badge-teal">Medicine Q&amp;A</span>
        </div>

        <div style="margin: 16px 0;">
          <div class="flex-row" style="background: var(--color-bg-subtle); padding: 6px 12px; border-radius: var(--radius-md); border: 1px solid var(--color-border);">
            <input type="text" value="${isAbstained ? 'Can I give half of this tablet to my 5-year-old child?' : 'What is the required expiration date standard for this drug packaging?'}" style="flex: 1; border: none; background: transparent; outline: none; font-size: 0.9rem;" readonly>
            <button class="btn btn-sm btn-primary" type="button">Ask</button>
          </div>
        </div>

        ${isAbstained ? `
          <div class="notice-banner notice-warning" style="margin-top: 16px;">
            <div class="notice-icon">i</div>
            <div>
              <div class="notice-title">Abstained: ${escapeHtml(safeData.reason || 'out_of_scope')}</div>
              <div class="notice-text">${escapeHtml(safeData.message || 'I can only explain what the packaging label says.')}</div>
              <div class="text-xs font-mono" style="margin-top: 8px; opacity: 0.85;">
                Rule: ${escapeHtml(safeData.score_name || 'rule')} | Score: ${safeData.score !== null && safeData.score !== undefined ? safeData.score : 'null'} | Threshold: ${safeData.threshold !== null && safeData.threshold !== undefined ? safeData.threshold : 'null'}
              </div>
            </div>
          </div>
        ` : `
          <div style="background-color: var(--color-primary-teal-subtle); border: 1px solid var(--color-primary-teal-light); border-radius: var(--radius-md); padding: 16px; margin-top: 16px;">
            <div class="font-semibold text-sm" style="color: var(--color-primary-teal); margin-bottom: 6px;">Answer backed by official evidence:</div>
            <div style="font-size: 0.925rem; line-height: 1.5; color: var(--color-text-dark);">${escapeHtml(safeData.answer || '')}</div>
            
            <div style="margin-top: 14px; border-top: 1px solid rgba(11, 125, 126, 0.2); padding-top: 10px;">
              <div class="text-xs font-semibold text-muted">Basis: ${escapeHtml(safeData.based_on || '21 CFR 211.137')}</div>
              ${(safeData.sources || []).map(s => `
                <div class="text-xs" style="margin-top: 4px; color: var(--color-text-muted);">
                  <strong>${escapeHtml(s.section || '')} ${escapeHtml(s.title || '')}:</strong> 
                  <span style="font-style: italic;">"${escapeHtml(s.quote || '')}"</span>
                </div>
              `).join('')}
            </div>
          </div>
        `}
      </div>
    `;
  }

  // Register renderer
  window.LabelLensRenderers = window.LabelLensRenderers || {};
  window.LabelLensRenderers['P3 Ask about this label'] = renderScreenP3;
  window.LabelLensRenderers['P3'] = renderScreenP3;

  if (typeof module !== 'undefined' && module.exports) {
    module.exports = { renderScreenP3 };
  }
})();
