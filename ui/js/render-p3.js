/**
 * ui/js/render-p3.js
 * Renderer for Screen P3: Ask about this label
 * 
 * Hard rules:
 * - Public medicine mode only (21 CFR 201, 208, 211).
 * - "Authenticity not verified. Based on a reference label match."
 * - Never invent data. Every value comes from mock.
 * - An abstained answer shows NO answer text.
 * - Shows the reason using exact reason names and meanings from the mocks.
 * - Shows score and threshold ONLY when they are not null. Never show "null" or "NaN".
 * - Citations show the regulation section, the verbatim quote and the source type (cfr or label_section).
 * - User typed question is preserved in UI state (not waiting on an API field).
 * - Any test identifier shows a visible TEST badge.
 * - No em dashes.
 */

(function() {
  // Retain user typed question in UI state
  let currentTypedQuestion = '';

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

  function renderTestBadge(val) {
    if (window.LabelLensData && window.LabelLensData.renderTestBadge) {
      return window.LabelLensData.renderTestBadge(val);
    }
    return '';
  }

  function renderScreenP3(container, state, meta, data) {
    if (!container) return;
    const safeData = data || {};
    const isAbstained = safeData.abstained === true;
    const testBadge = renderTestBadge(safeData);

    const hasScore = safeData.score !== null && safeData.score !== undefined && !Number.isNaN(safeData.score);
    const hasThreshold = safeData.threshold !== null && safeData.threshold !== undefined && !Number.isNaN(safeData.threshold);
    const hasScoreName = Boolean(safeData.score_name);

    // Build metric line without any "null" or "NaN"
    const metricParts = [];
    if (hasScoreName) {
      metricParts.push(`Metric: <strong>${escapeHtml(safeData.score_name)}</strong>`);
    }
    if (hasScore) {
      metricParts.push(`Score: <strong>${escapeHtml(String(safeData.score))}</strong>`);
    }
    if (hasThreshold) {
      metricParts.push(`Threshold: <strong>${escapeHtml(String(safeData.threshold))}</strong>`);
    }

    container.innerHTML = `
      <div class="card" style="max-width: 820px; margin: 0 auto;">
        <div class="card-header-clean flex-between">
          <div>
            <div class="flex-row" style="gap: 8px;">
              <h3>Ask about this label</h3>
              ${testBadge}
            </div>
            <div class="text-xs text-muted" style="margin-top: 4px;">
              Questions are answered only using retrieved passages from 21 CFR 201, 208, 211 and matched reference labels.
            </div>
          </div>
          <span class="badge badge-teal">Medicine Q&amp;A</span>
        </div>

        <!-- Question input box: uses user typed question held in UI state -->
        <div style="margin: 16px 0;">
          <div class="flex-row" style="background: var(--color-bg-subtle); padding: 8px 12px; border-radius: var(--radius-md); border: 1px solid var(--color-border); gap: 8px;">
            <input type="text" id="p3QuestionInput" value="${escapeHtml(currentTypedQuestion)}" placeholder="Ask a question about this medicine (e.g. storage, expiration, packaging requirements)..." style="flex: 1; border: none; background: transparent; outline: none; font-size: 0.92rem; color: var(--color-text-main);">
            <button class="btn btn-sm btn-primary" type="button" id="btnP3AskSubmit">Ask</button>
          </div>
        </div>

        ${isAbstained ? `
          <!-- Abstained State: NO answer text shown -->
          <div class="notice-banner notice-warning" style="margin-top: 20px;">
            <div class="notice-icon">i</div>
            <div style="flex: 1;">
              <div class="flex-between">
                <div class="notice-title">
                  Abstained: <code style="font-size: 0.9rem;">${escapeHtml(safeData.reason || 'abstained')}</code>
                </div>
                <span class="badge badge-warning">No clinical determination</span>
              </div>
              <div class="notice-text" style="margin-top: 8px; font-size: 0.925rem; line-height: 1.5; color: var(--color-text-dark);">
                ${escapeHtml(safeData.message || '')}
              </div>

              ${metricParts.length > 0 ? `
                <div class="text-xs font-mono" style="margin-top: 12px; padding: 6px 10px; background: rgba(0, 0, 0, 0.04); border-radius: var(--radius-sm); color: var(--color-text-muted);">
                  ${metricParts.join(' | ')}
                </div>
              ` : ''}
            </div>
          </div>
        ` : `
          <!-- Success State: Cited answer backed by official evidence -->
          <div style="background-color: var(--color-primary-teal-subtle); border: 1px solid var(--color-primary-teal-light); border-radius: var(--radius-md); padding: 20px; margin-top: 20px;">
            <div class="flex-between" style="margin-bottom: 8px;">
              <div class="font-semibold text-sm" style="color: var(--color-primary-teal);">
                Answer backed by official evidence:
              </div>
              ${safeData.based_on ? `
                <span class="text-xs text-muted">
                  Basis: <strong>${escapeHtml(safeData.based_on)}</strong>
                </span>
              ` : ''}
            </div>

            <div style="font-size: 0.95rem; line-height: 1.55; color: var(--color-text-dark); margin-bottom: 16px;">
              ${escapeHtml(safeData.answer || '')}
            </div>
            
            ${(safeData.sources || []).length > 0 ? `
              <div style="border-top: 1px solid rgba(11, 125, 126, 0.25); padding-top: 14px; margin-top: 12px;">
                <div class="text-xs font-semibold text-muted" style="margin-bottom: 8px;">
                  Regulatory Citations (${safeData.sources.length}):
                </div>
                <div style="display: flex; flex-direction: column; gap: 12px;">
                  ${safeData.sources.map(s => {
                    const citationTestBadge = renderTestBadge(s.chunk_id) || renderTestBadge(s);
                    return `
                      <div style="background: #ffffff; border: 1px solid var(--color-border); border-radius: var(--radius-md); padding: 12px;">
                        <div class="flex-between">
                          <div class="flex-row" style="gap: 6px;">
                            <span class="badge badge-teal">${escapeHtml(s.source_type || 'cfr')}</span>
                            <span class="font-semibold text-xs" style="color: var(--color-text-dark);">
                              21 CFR ${escapeHtml(s.section || '')}: ${escapeHtml(s.title || '')}
                            </span>
                            ${citationTestBadge}
                          </div>
                          ${s.url ? `
                            <a href="${escapeHtml(s.url)}" target="_blank" rel="noopener noreferrer" class="btn btn-sm btn-secondary" style="font-size: 0.75rem; padding: 2px 8px;">
                              View regulation &rarr;
                            </a>
                          ` : ''}
                        </div>
                        ${s.quote ? `
                          <div style="font-style: italic; font-size: 0.825rem; color: var(--color-text-dark); margin-top: 8px; border-left: 2px solid var(--color-primary-teal); padding-left: 10px;">
                            "${escapeHtml(s.quote)}"
                          </div>
                        ` : ''}
                        <div class="text-xs text-muted" style="margin-top: 6px;">
                          Source: ${escapeHtml(s.source || 'FDA')} | Chunk: <code>${escapeHtml(s.chunk_id || '')}</code>
                        </div>
                      </div>
                    `;
                  }).join('')}
                </div>
              </div>
            ` : ''}
          </div>
        `}

        <div class="flex-between" style="margin-top: 24px; padding-top: 16px; border-top: 1px solid var(--color-border);">
          <button class="btn btn-secondary btn-sm" type="button" id="btnP3BackToProduct">
            &larr; Back to product information
          </button>
          <span class="text-xs text-muted">
            Public corpus: 21 CFR 201, 208, 211
          </span>
        </div>
      </div>
    `;

    const backBtn = container.querySelector('#btnP3BackToProduct');
    if (backBtn) {
      backBtn.addEventListener('click', () => {
        if (window.LabelLensStateSwitcher) {
          window.LabelLensStateSwitcher.setScreen('P2 Product information', 'success');
        } else {
          window.dispatchEvent(new CustomEvent('labellens:screen-navigated', {
            detail: { screen: 'P2 Product information' }
          }));
        }
      });
    }

    const askSubmit = container.querySelector('#btnP3AskSubmit');
    const questionInput = container.querySelector('#p3QuestionInput');
    if (questionInput) {
      questionInput.addEventListener('input', (e) => {
        currentTypedQuestion = e.target.value;
      });
      questionInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
          currentTypedQuestion = questionInput.value.trim();
          if (askSubmit) askSubmit.click();
        }
      });
    }
    if (askSubmit && questionInput) {
      askSubmit.addEventListener('click', () => {
        currentTypedQuestion = questionInput.value.trim();
      });
    }
  }

  // Register renderer and state getter
  window.LabelLensRenderers = window.LabelLensRenderers || {};
  window.LabelLensRenderers['P3 Ask about this label'] = renderScreenP3;
  window.LabelLensRenderers['P3'] = renderScreenP3;

  if (typeof module !== 'undefined' && module.exports) {
    module.exports = { renderScreenP3 };
  }
})();
